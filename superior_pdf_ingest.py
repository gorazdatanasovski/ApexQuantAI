import argparse
import contextlib
import gc
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import faiss  # type: ignore
except ImportError as e:
    raise SystemExit("Missing dependency: faiss-cpu. Install it with: pip install faiss-cpu") from e

try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise SystemExit("Missing dependency: PyMuPDF. Install it with: pip install pymupdf") from e

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


# Let the runtime pick sensible defaults unless the user explicitly overrides them.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


@dataclass
class IngestConfig:
    books_dir: str = "books_vault"
    work_dir: str = "rag_ingest_state"
    model_name: str = "BAAI/bge-base-en-v1.5"
    candidate_backends: Tuple[str, ...] = ("openvino", "onnx", "torch")
    candidate_batch_sizes: Tuple[int, ...] = (16, 32, 64)
    chunk_size: int = 1100
    chunk_overlap: int = 150
    embed_commit_size: int = 128
    min_text_chars: int = 40
    benchmark_pages: int = 12
    benchmark_chunks: int = 96
    top_k_default: int = 5

    @property
    def books_path(self) -> Path:
        return Path(self.books_dir).resolve()

    @property
    def work_path(self) -> Path:
        return Path(self.work_dir).resolve()

    @property
    def sqlite_path(self) -> Path:
        return self.work_path / "state.sqlite3"

    @property
    def stage_dir(self) -> Path:
        return self.work_path / "staging"

    @property
    def embeddings_dir(self) -> Path:
        return self.stage_dir / "embeddings"

    @property
    def batch_meta_dir(self) -> Path:
        return self.stage_dir / "batch_meta"

    @property
    def final_dir(self) -> Path:
        return self.work_path / "final"

    @property
    def faiss_index_path(self) -> Path:
        return self.final_dir / "index.faiss"

    @property
    def runtime_json_path(self) -> Path:
        return self.work_path / "runtime_profile.json"


def sha256_bytes_iter(chunks: Iterable[bytes]) -> str:
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    def gen() -> Iterable[bytes]:
        with open(path, "rb") as f:
            while True:
                block = f.read(block_size)
                if not block:
                    break
                yield block

    return sha256_bytes_iter(gen())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_name)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_bytes(path, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))


def atomic_write_npy(path: Path, array: np.ndarray) -> None:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            np.save(f, array)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp_name)


def atomic_write_faiss(path: Path, index: faiss.Index) -> None:
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    faiss.write_index(index, str(tmp_path))
    os.replace(tmp_path, path)


def normalize_text(text: str) -> str:
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    text = text.replace("\x00", " ")
    text = " ".join(text.split())
    return text.strip()


class StateStore:
    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        ensure_dir(sqlite_path.parent)
        self.conn = sqlite3.connect(str(sqlite_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=FULL;")
        self.conn.execute("PRAGMA temp_store=MEMORY;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                file_sha TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL NOT NULL,
                page_count INTEGER DEFAULT 0,
                parse_status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS parsed_pages (
                file_sha TEXT NOT NULL,
                page_no INTEGER NOT NULL,
                ok INTEGER NOT NULL,
                error TEXT,
                PRIMARY KEY (file_sha, page_no),
                FOREIGN KEY (file_sha) REFERENCES documents(file_sha) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_key TEXT NOT NULL UNIQUE,
                file_sha TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                page_no INTEGER NOT NULL,
                chunk_no INTEGER NOT NULL,
                text TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                batch_id TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (file_sha) REFERENCES documents(file_sha) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS embedding_batches (
                batch_id TEXT PRIMARY KEY,
                emb_path TEXT NOT NULL,
                meta_path TEXT NOT NULL,
                model_name TEXT NOT NULL,
                backend TEXT NOT NULL,
                batch_size INTEGER NOT NULL,
                dim INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )
        self.conn.commit()

    @contextlib.contextmanager
    def tx(self):
        cur = self.conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def put_runtime(self, key: str, value: Any) -> None:
        with self.tx() as cur:
            cur.execute(
                "INSERT INTO runtime(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    def get_runtime(self, key: str) -> Optional[Any]:
        row = self.conn.execute("SELECT value FROM runtime WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])

    def upsert_document(self, file_sha: str, pdf_path: Path, page_count: int) -> None:
        now = time.time()
        st = pdf_path.stat()
        with self.tx() as cur:
            cur.execute(
                """
                INSERT INTO documents(file_sha, file_path, file_name, file_size, file_mtime, page_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_sha) DO UPDATE SET
                    file_path=excluded.file_path,
                    file_name=excluded.file_name,
                    file_size=excluded.file_size,
                    file_mtime=excluded.file_mtime,
                    page_count=excluded.page_count,
                    updated_at=excluded.updated_at
                """,
                (file_sha, str(pdf_path), pdf_path.name, int(st.st_size), float(st.st_mtime), int(page_count), now, now),
            )

    def set_document_parse_status(self, file_sha: str, status: str) -> None:
        with self.tx() as cur:
            cur.execute(
                "UPDATE documents SET parse_status=?, updated_at=? WHERE file_sha=?",
                (status, time.time(), file_sha),
            )

    def parsed_page_exists(self, file_sha: str, page_no: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM parsed_pages WHERE file_sha=? AND page_no=?",
            (file_sha, page_no),
        ).fetchone()
        return row is not None

    def mark_page_parsed(self, file_sha: str, page_no: int, ok: bool, error: Optional[str] = None) -> None:
        with self.tx() as cur:
            cur.execute(
                """
                INSERT INTO parsed_pages(file_sha, page_no, ok, error)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(file_sha, page_no) DO UPDATE SET ok=excluded.ok, error=excluded.error
                """,
                (file_sha, page_no, int(ok), error),
            )

    def insert_chunks(self, rows: Sequence[Tuple[str, str, str, str, int, int, str, int, float]]) -> None:
        if not rows:
            return
        with self.tx() as cur:
            cur.executemany(
                """
                INSERT OR IGNORE INTO chunks(
                    chunk_key, file_sha, file_name, file_path, page_no, chunk_no, text, char_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def count_pending_chunks(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM chunks WHERE status='pending'").fetchone()
        return int(row["n"])

    def get_pending_chunks(self, limit: int) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT id, text FROM chunks WHERE status='pending' ORDER BY id LIMIT ?",
            (int(limit),),
        )
        return cur.fetchall()

    def batch_exists(self, batch_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM embedding_batches WHERE batch_id=?",
            (batch_id,),
        ).fetchone()
        return row is not None

    def commit_embedded_batch(
        self,
        batch_id: str,
        emb_path: Path,
        meta_path: Path,
        model_name: str,
        backend: str,
        batch_size: int,
        dim: int,
        chunk_ids: Sequence[int],
    ) -> None:
        now = time.time()
        with self.tx() as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO embedding_batches(
                    batch_id, emb_path, meta_path, model_name, backend, batch_size, dim, chunk_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (batch_id, str(emb_path), str(meta_path), model_name, backend, int(batch_size), int(dim), len(chunk_ids), now),
            )
            cur.executemany(
                "UPDATE chunks SET status='embedded', batch_id=? WHERE id=? AND status='pending'",
                [(batch_id, int(cid)) for cid in chunk_ids],
            )

    def embedded_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM chunks WHERE status='embedded'").fetchone()
        return int(row["n"])

    def iter_embedding_batches(self) -> Iterable[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT batch_id, emb_path, meta_path, dim FROM embedding_batches ORDER BY created_at, batch_id"
        )
        yield from cur

    def chunk_by_id(self, chunk_id: int) -> sqlite3.Row:
        row = self.conn.execute(
            "SELECT id, file_name, file_path, page_no, chunk_no, text FROM chunks WHERE id=?",
            (int(chunk_id),),
        ).fetchone()
        if row is None:
            raise KeyError(chunk_id)
        return row

    def all_documents(self) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM documents ORDER BY file_name"
        ).fetchall()


class RuntimeProfile:
    def __init__(self, model_name: str, backend: str, batch_size: int):
        self.model_name = model_name
        self.backend = backend
        self.batch_size = int(batch_size)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backend": self.backend,
            "batch_size": self.batch_size,
        }

    @property
    def profile_id(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


class EncoderFactory:
    def __init__(self, config: IngestConfig, state: StateStore):
        self.config = config
        self.state = state
        self._model: Optional[SentenceTransformer] = None
        self.profile = self._load_or_select_profile()

    def _collect_benchmark_samples(self) -> List[str]:
        samples: List[str] = []
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        pdfs = sorted(self.config.books_path.glob("*.pdf"))
        for pdf_path in pdfs:
            try:
                with fitz.open(pdf_path) as doc:
                    for page_no in range(min(len(doc), self.config.benchmark_pages)):
                        text = normalize_text(doc.load_page(page_no).get_text("text", sort=True))
                        if len(text) < self.config.min_text_chars:
                            continue
                        for chunk in splitter.split_text(text):
                            chunk = normalize_text(chunk)
                            if len(chunk) >= self.config.min_text_chars:
                                samples.append(chunk)
                                if len(samples) >= self.config.benchmark_chunks:
                                    return samples
            except Exception:
                continue
        if not samples:
            samples = [
                "Stochastic calculus and martingale pricing in continuous time.",
                "A diffusion process with drift and volatility can be discretized for numerical analysis.",
                "Semimartingale methods support general no-arbitrage modeling under equivalent martingale measures.",
                "Measure changes and Girsanov transformations are central in derivative pricing.",
            ] * 24
        return samples[: self.config.benchmark_chunks]

    def _load_or_select_profile(self) -> RuntimeProfile:
        existing = self.state.get_runtime("runtime_profile")
        if existing is not None:
            return RuntimeProfile(
                model_name=existing["model_name"],
                backend=existing["backend"],
                batch_size=int(existing["batch_size"]),
            )

        samples = self._collect_benchmark_samples()
        candidates: List[Tuple[float, str, int]] = []

        for backend in self.config.candidate_backends:
            try:
                model = SentenceTransformer(self.config.model_name, backend=backend, device="cpu")
            except Exception:
                continue

            try:
                model.encode(samples[: min(8, len(samples))], batch_size=8, normalize_embeddings=True, show_progress_bar=False)
                for batch_size in self.config.candidate_batch_sizes:
                    t0 = time.perf_counter()
                    model.encode(samples, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
                    dt = time.perf_counter() - t0
                    if dt <= 0:
                        continue
                    rate = len(samples) / dt
                    candidates.append((rate, backend, batch_size))
            finally:
                del model
                gc.collect()

        if not candidates:
            raise RuntimeError(
                "No embedding backend could be initialized. Install a supported backend for SentenceTransformers."
            )

        candidates.sort(reverse=True)
        _, backend, batch_size = candidates[0]
        profile = RuntimeProfile(self.config.model_name, backend, batch_size)
        self.state.put_runtime("runtime_profile", profile.as_dict())
        return profile

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self.profile.model_name,
                backend=self.profile.backend,
                device="cpu",
            )
        return self._model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self.get_model()
        emb = model.encode(
            list(texts),
            batch_size=self.profile.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        arr = np.asarray(emb, dtype=np.float32)
        if arr.ndim != 2:
            raise RuntimeError(f"Unexpected embedding shape: {arr.shape}")
        return arr

    def encode_query(self, query: str) -> np.ndarray:
        model = self.get_model()
        q = model.encode([query], batch_size=1, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
        return np.asarray(q[0], dtype=np.float32)


class SuperiorPDFIngestor:
    def __init__(self, config: IngestConfig):
        self.config = config
        for p in [config.work_path, config.stage_dir, config.embeddings_dir, config.batch_meta_dir, config.final_dir]:
            ensure_dir(p)
        self.state = StateStore(config.sqlite_path)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.encoder_factory = EncoderFactory(config, self.state)

    def close(self) -> None:
        self.state.close()

    def scan_documents(self) -> List[Tuple[str, Path, int]]:
        pdfs = sorted(self.config.books_path.glob("*.pdf"))
        docs: List[Tuple[str, Path, int]] = []
        for pdf_path in pdfs:
            try:
                with fitz.open(pdf_path) as doc:
                    page_count = len(doc)
                file_sha = sha256_file(pdf_path)
                self.state.upsert_document(file_sha, pdf_path, page_count)
                docs.append((file_sha, pdf_path, page_count))
            except Exception as e:
                print(f"[scan-fail] {pdf_path.name}: {e}")
        return docs

    def parse_documents(self) -> None:
        docs = self.scan_documents()
        total_pages_done = 0
        t0 = time.time()

        for file_sha, pdf_path, page_count in docs:
            print(f"[parse] {pdf_path.name} ({page_count} pages)")
            self.state.set_document_parse_status(file_sha, "parsing")
            saw_error = False

            try:
                with fitz.open(pdf_path) as doc:
                    for page_ix in range(page_count):
                        page_no = page_ix + 1
                        if self.state.parsed_page_exists(file_sha, page_no):
                            continue

                        try:
                            text = normalize_text(doc.load_page(page_ix).get_text("text", sort=True))
                            rows: List[Tuple[str, str, str, str, int, int, str, int, float]] = []
                            if len(text) >= self.config.min_text_chars:
                                chunks = self.splitter.split_text(text)
                                now = time.time()
                                for chunk_no, chunk in enumerate(chunks, start=1):
                                    chunk = normalize_text(chunk)
                                    if len(chunk) < self.config.min_text_chars:
                                        continue
                                    chunk_key = hashlib.sha256(
                                        f"{file_sha}|{page_no}|{chunk_no}|{chunk}".encode("utf-8")
                                    ).hexdigest()
                                    rows.append(
                                        (
                                            chunk_key,
                                            file_sha,
                                            pdf_path.name,
                                            str(pdf_path),
                                            page_no,
                                            chunk_no,
                                            chunk,
                                            len(chunk),
                                            now,
                                        )
                                    )
                            self.state.insert_chunks(rows)
                            self.state.mark_page_parsed(file_sha, page_no, ok=True, error=None)
                            total_pages_done += 1
                        except Exception as e:
                            saw_error = True
                            self.state.mark_page_parsed(file_sha, page_no, ok=False, error=str(e))
                            print(f"  [page-fail] {pdf_path.name} p.{page_no}: {e}")

                self.state.set_document_parse_status(file_sha, "parsed_with_errors" if saw_error else "parsed")
            except Exception as e:
                self.state.set_document_parse_status(file_sha, "parse_failed")
                print(f"[file-parse-fail] {pdf_path.name}: {e}")

        dt = time.time() - t0
        print(f"[parse-done] parsed pages this run: {total_pages_done} in {dt/60:.2f} min")

    def embed_pending_chunks(self) -> None:
        profile = self.encoder_factory.profile
        self._assert_or_set_profile(profile)
        pending = self.state.count_pending_chunks()
        print(
            f"[embed] pending chunks={pending} | model={profile.model_name} | backend={profile.backend} | batch_size={profile.batch_size}"
        )
        t0 = time.time()
        embedded_now = 0

        while True:
            rows = self.state.get_pending_chunks(self.config.embed_commit_size)
            if not rows:
                break

            chunk_ids = [int(r["id"]) for r in rows]
            texts = [str(r["text"]) for r in rows]
            batch_id = hashlib.sha256(
                (profile.profile_id + "|" + ",".join(map(str, chunk_ids))).encode("utf-8")
            ).hexdigest()

            if self.state.batch_exists(batch_id):
                # Defensive reconciliation path.
                self.state.commit_embedded_batch(
                    batch_id=batch_id,
                    emb_path=self.config.embeddings_dir / f"{batch_id}.npy",
                    meta_path=self.config.batch_meta_dir / f"{batch_id}.json",
                    model_name=profile.model_name,
                    backend=profile.backend,
                    batch_size=profile.batch_size,
                    dim=0,
                    chunk_ids=chunk_ids,
                )
                continue

            emb_path = self.config.embeddings_dir / f"{batch_id}.npy"
            meta_path = self.config.batch_meta_dir / f"{batch_id}.json"

            embeddings = self.encoder_factory.encode(texts)
            meta = {
                "batch_id": batch_id,
                "profile": profile.as_dict(),
                "chunk_ids": chunk_ids,
                "count": int(embeddings.shape[0]),
                "dim": int(embeddings.shape[1]),
            }

            atomic_write_npy(emb_path, embeddings)
            # read-back verification before marking committed
            verify = np.load(emb_path, mmap_mode="r")
            if tuple(verify.shape) != tuple(embeddings.shape):
                raise RuntimeError(f"Verification failed for {emb_path.name}: {verify.shape} != {embeddings.shape}")

            atomic_write_json(meta_path, meta)
            self.state.commit_embedded_batch(
                batch_id=batch_id,
                emb_path=emb_path,
                meta_path=meta_path,
                model_name=profile.model_name,
                backend=profile.backend,
                batch_size=profile.batch_size,
                dim=int(embeddings.shape[1]),
                chunk_ids=chunk_ids,
            )

            embedded_now += len(chunk_ids)
            elapsed = max(time.time() - t0, 1e-9)
            rate = embedded_now / elapsed
            print(f"  [embed-ok] total_this_run={embedded_now} | rate={rate:.2f} chunks/sec")
            del embeddings, verify
            gc.collect()

        dt = time.time() - t0
        print(f"[embed-done] embedded this run: {embedded_now} in {dt/60:.2f} min")

    def _assert_or_set_profile(self, profile: RuntimeProfile) -> None:
        stored = self.state.get_runtime("committed_profile")
        if stored is None:
            self.state.put_runtime("committed_profile", profile.as_dict())
            atomic_write_json(self.config.runtime_json_path, profile.as_dict())
            return
        if stored != profile.as_dict():
            raise RuntimeError(
                "Embedding profile mismatch. Existing staged embeddings were created with a different model/backend/batch-size. "
                "Use a fresh work_dir if you want to change the embedding setup."
            )

    def build_faiss_index(self) -> None:
        first_batch = next(iter(self.state.iter_embedding_batches()), None)
        if first_batch is None:
            raise RuntimeError("No committed embedding batches found. Run parse + embed first.")

        dim = int(first_batch["dim"])
        index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
        total = 0
        first_vec: Optional[np.ndarray] = None
        first_id: Optional[int] = None

        for row in self.state.iter_embedding_batches():
            emb_path = Path(str(row["emb_path"]))
            meta_path = Path(str(row["meta_path"]))
            arr = np.load(emb_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ids = np.asarray(meta["chunk_ids"], dtype=np.int64)
            if arr.shape[0] != ids.shape[0]:
                raise RuntimeError(f"Batch cardinality mismatch for {emb_path.name}")
            arr = np.asarray(arr, dtype=np.float32)
            index.add_with_ids(arr, ids)
            total += arr.shape[0]
            if first_vec is None and arr.shape[0] > 0:
                first_vec = arr[:1].copy()
                first_id = int(ids[0])

        atomic_write_faiss(self.config.faiss_index_path, index)
        loaded = faiss.read_index(str(self.config.faiss_index_path))
        if loaded.ntotal != index.ntotal:
            raise RuntimeError(f"FAISS verify failed: {loaded.ntotal} != {index.ntotal}")

        if first_vec is not None and first_id is not None:
            sims, ids = loaded.search(first_vec, 1)
            if int(ids[0][0]) != first_id:
                raise RuntimeError("FAISS sanity check failed: first vector did not retrieve itself.")
            if float(sims[0][0]) < 0.99:
                raise RuntimeError("FAISS sanity check failed: self similarity too low.")

        manifest = {
            "chunks_indexed": int(total),
            "faiss_ntotal": int(loaded.ntotal),
            "profile": self.state.get_runtime("committed_profile"),
            "built_at": time.time(),
        }
        atomic_write_json(self.config.final_dir / "index_manifest.json", manifest)
        print(f"[index-done] built FAISS index with {total} vectors -> {self.config.faiss_index_path}")

    def query(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        if not self.config.faiss_index_path.exists():
            raise RuntimeError("FAISS index not found. Run the build step first.")
        index = faiss.read_index(str(self.config.faiss_index_path))
        q = self.encoder_factory.encode_query(query_text).reshape(1, -1)
        scores, ids = index.search(q, top_k)
        out: List[Dict[str, Any]] = []
        for score, chunk_id in zip(scores[0].tolist(), ids[0].tolist()):
            if int(chunk_id) < 0:
                continue
            row = self.state.chunk_by_id(int(chunk_id))
            out.append(
                {
                    "score": float(score),
                    "file_name": row["file_name"],
                    "file_path": row["file_path"],
                    "page_no": int(row["page_no"]),
                    "chunk_no": int(row["chunk_no"]),
                    "text": row["text"],
                }
            )
        return out

    def run_all(self) -> None:
        self.parse_documents()
        self.embed_pending_chunks()
        self.build_faiss_index()


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Crash-resistant PDF -> embeddings -> FAISS ingestion pipeline.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--books-dir", default="books_vault")
        sp.add_argument("--work-dir", default="rag_ingest_state")
        sp.add_argument("--model-name", default="BAAI/bge-base-en-v1.5")
        sp.add_argument("--chunk-size", type=int, default=1100)
        sp.add_argument("--chunk-overlap", type=int, default=150)
        sp.add_argument("--embed-commit-size", type=int, default=128)

    for name in ["parse", "embed", "build", "all"]:
        sp = sub.add_parser(name)
        add_common(sp)

    q = sub.add_parser("query")
    add_common(q)
    q.add_argument("text")
    q.add_argument("--top-k", type=int, default=5)

    return p


def config_from_args(args: argparse.Namespace) -> IngestConfig:
    return IngestConfig(
        books_dir=args.books_dir,
        work_dir=args.work_dir,
        model_name=args.model_name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embed_commit_size=args.embed_commit_size,
    )


def main() -> int:
    args = make_parser().parse_args()
    config = config_from_args(args)
    ingestor = SuperiorPDFIngestor(config)
    try:
        if args.cmd == "parse":
            ingestor.parse_documents()
        elif args.cmd == "embed":
            ingestor.embed_pending_chunks()
        elif args.cmd == "build":
            ingestor.build_faiss_index()
        elif args.cmd == "all":
            ingestor.run_all()
        elif args.cmd == "query":
            results = ingestor.query(args.text, args.top_k)
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            raise ValueError(args.cmd)
        return 0
    finally:
        ingestor.close()


if __name__ == "__main__":
    raise SystemExit(main())
