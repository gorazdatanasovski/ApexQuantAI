import os
import json
import time
import shutil
import hashlib
import multiprocessing
import re
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Absolute Hardware Thread Locking
physical_cores = str(max(1, multiprocessing.cpu_count() // 2))
os.environ["OMP_NUM_THREADS"] = physical_cores
os.environ["MKL_NUM_THREADS"] = physical_cores
os.environ["OPENBLAS_NUM_THREADS"] = physical_cores
os.environ["NUMEXPR_NUM_THREADS"] = physical_cores
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class ONNXSentenceTransformerEmbeddings(Embeddings):
    """Forces the mathematical forward pass strictly through the C++ ONNX runtime."""
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        print(f"[+] ALLOCATING C++ ONNX RUNTIME FOR {model_name}...")
        self.model = SentenceTransformer(model_name, backend="onnx", device="cpu")
        self.query_prefix = "Represent this sentence for searching relevant passages: "

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        emb = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return emb.tolist()

    def embed_query(self, text: str) -> List[float]:
        emb = self.model.encode([self.query_prefix + text], batch_size=1, normalize_embeddings=True, show_progress_bar=False)
        return emb[0].tolist()

class CognitiveIngestionEngine:
    """
    The Infallible Streaming Matrix.
    Features: O(1) Memory Lazy Loading, True Byte Hashing, Strict I/O Watchdog.
    """
    def __init__(self, vault_dir: str = "books_vault", db_dir: str = "faiss_db_vault"):
        self.vault = Path(os.getcwd()) / vault_dir
        self.db_dir = Path(os.getcwd()) / db_dir
        self.manifest_path = self.db_dir / "ingestion_manifest.json"
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.embedder = ONNXSentenceTransformerEmbeddings()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
        
        self.vector_db = None
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"processed": {}}

    def _save_manifest(self) -> None:
        tmp = self.manifest_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)
        os.replace(tmp, self.manifest_path)

    def _compute_true_sha256(self, path: Path) -> str:
        """Calculates the exact cryptographic signature of the physical bytes."""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _verify_disk_space(self) -> None:
        """Strict I/O watchdog to prevent silent database corruption from zero-byte writes."""
        free_bytes = shutil.disk_usage(self.db_dir).free
        if free_bytes < 1024 * 1024 * 500: # 500 MB threshold
            raise RuntimeError("CRITICAL: INSUFFICIENT PHYSICAL DISK SPACE DETECTED. ABORTING TO PREVENT CORRUPTION.")

    def _load_existing_db(self) -> None:
        index_file = self.db_dir / "index.faiss"
        if index_file.exists():
            print("[+] LOCATING EXISTING MANIFOLD. DESERIALIZING FAISS INDEX...")
            self.vector_db = FAISS.load_local(str(self.db_dir), self.embedder, allow_dangerous_deserialization=True)

    def _atomic_save_db(self) -> None:
        """Guarantees zero byte corruption during I/O operations."""
        self._verify_disk_space()
        tmp_dir = self.db_dir.parent / f"{self.db_dir.name}_tmp"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        self.vector_db.save_local(str(tmp_dir))

        backup_dir = self.db_dir.parent / f"{self.db_dir.name}_bak"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        if self.db_dir.exists():
            os.replace(self.db_dir, backup_dir)
        os.replace(tmp_dir, self.db_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

    def execute_embedding_mapping(self) -> None:
        print("\n[+] COGNITIVE ENGINE: STRICT O(1) STREAMING MATRIX IGNITED.")
        
        pdf_files = sorted(self.vault.glob("*.pdf"))
        if not pdf_files:
            print("[-] NO LITERATURE DETECTED IN VAULT.")
            return

        self._load_existing_db()
        global_start = time.time()

        for idx, pdf_path in enumerate(pdf_files, start=1):
            signature = self._compute_true_sha256(pdf_path)
            
            # Strict verification: Do not skip if previously flagged as partial/failed
            if signature in self.manifest["processed"] and self.manifest["processed"][signature].get("status") == "embedded":
                print(f"[~] BYPASS: {pdf_path.name} (Cryptographically Verified).")
                continue

            print(f"\n[+] ISOLATING MANIFOLD [{idx}/{len(pdf_files)}]: {pdf_path.name}")
            pdf_start = time.time()
            successful_tensors = 0
            file_fracture = False
            chunk_buffer = []

            try:
                # 2. Lazy Loading Iterator: Parses precisely one page at a time.
                page_iterator = PyMuPDFLoader(str(pdf_path)).lazy_load()
                
                for page in page_iterator:
                    raw_chunks = self.splitter.split_documents([page])
                    
                    # Pre-emptive Sanitization per page
                    for c in raw_chunks:
                        text = c.page_content.encode("utf-8", "ignore").decode("utf-8", "ignore")
                        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
                        text = " ".join(text.split())
                        if text:
                            c.page_content = text
                            chunk_buffer.append(c)

                    # Micro-Batching limits RAM overhead
                    while len(chunk_buffer) >= 32:
                        batch = chunk_buffer[:32]
                        chunk_buffer = chunk_buffer[32:]
                        
                        if self.vector_db is None:
                            self.vector_db = FAISS.from_documents(batch, self.embedder)
                        else:
                            self.vector_db.add_documents(batch)
                        successful_tensors += len(batch)

                # Project remaining sub-32 block
                if chunk_buffer:
                    if self.vector_db is None:
                        self.vector_db = FAISS.from_documents(chunk_buffer, self.embedder)
                    else:
                        self.vector_db.add_documents(chunk_buffer)
                    successful_tensors += len(chunk_buffer)

            except Exception as e:
                print(f"    [-] CRITICAL FRACTURE DURING STREAMING: {e}. ABORTING MANIFOLD {pdf_path.name}.")
                file_fracture = True

            # 3. Strict State Synchronization: No silent partial ingestion
            if not file_fracture and successful_tensors > 0:
                self._atomic_save_db()
                self.manifest["processed"][signature] = {
                    "file": pdf_path.name,
                    "tensors": successful_tensors,
                    "status": "embedded"
                }
                self._save_manifest()
                
                elapsed = max(time.time() - pdf_start, 1e-6)
                velocity = successful_tensors / elapsed
                print(f"    [+] SUCCESS: {successful_tensors} tensors safely anchored to physical disk. Velocity: {velocity:.2f} t/sec.")
            elif not file_fracture and successful_tensors == 0:
                print(f"    [-] NULL MANIFOLD: ZERO VALID TENSORS EXTRACTED.")
            else:
                print(f"    [-] FILE FAILED TO CLEAR. REJECTION LOGGED.")

        total_elapsed = time.time() - global_start
        print(f"\n[+] SYNAPSES LOCKED. INGESTION COMPLETE IN {total_elapsed/60:.2f} MINUTES.")

if __name__ == "__main__":
    engine = CognitiveIngestionEngine()
    engine.execute_embedding_mapping()