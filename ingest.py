from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from superior_pdf_ingest import IngestConfig, SuperiorPDFIngestor
except ImportError as exc:
    raise SystemExit(
        "superior_pdf_ingest.py was not found in the project root. "
        "Place the file beside ingest.py before running this command."
    ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Front door for the crash-resistant PDF ingestion pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--books-dir", default="books_vault")
        sp.add_argument("--work-dir", default="rag_ingest_state")
        sp.add_argument("--model-name", default="BAAI/bge-base-en-v1.5")
        sp.add_argument("--chunk-size", type=int, default=1100)
        sp.add_argument("--chunk-overlap", type=int, default=150)
        sp.add_argument("--embed-commit-size", type=int, default=128)

    for name in ("parse", "embed", "build", "all"):
        add_common(sub.add_parser(name))

    query = sub.add_parser("query")
    add_common(query)
    query.add_argument("text")
    query.add_argument("--top-k", type=int, default=5)

    return parser


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
    args = build_parser().parse_args()
    engine = SuperiorPDFIngestor(config_from_args(args))
    try:
        match args.cmd:
            case "parse":
                engine.parse_documents()
            case "embed":
                engine.embed_pending_chunks()
            case "build":
                engine.build_faiss_index()
            case "all":
                engine.run_all()
            case "query":
                results = engine.query(args.text, args.top_k)
                for row in results:
                    print(
                        f"[{row['score']:.4f}] {row['file_name']} p.{row['page_no']} "
                        f"chunk {row['chunk_no']}\n{row['text']}\n"
                    )
            case _:
                raise ValueError(f"Unknown command: {args.cmd}")
        return 0
    finally:
        engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
