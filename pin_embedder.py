from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


def main() -> int:
    parser = argparse.ArgumentParser(description="Export and pin the embedding backend locally.")
    parser.add_argument("--work-dir", default="rag_ingest_state")
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--backend", default=None)
    args = parser.parse_args()

    work_dir = Path(args.work_dir).resolve()
    profile_path = work_dir / "runtime_profile.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"Missing runtime profile: {profile_path}")

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    model_name = args.model_name or profile.get("model_name")
    backend = args.backend or profile.get("backend") or "openvino"
    if not model_name:
        raise ValueError("runtime_profile.json does not contain model_name")

    safe_name = model_name.replace("/", "__")
    export_dir = work_dir / "models" / f"{safe_name}-{backend}"
    export_dir.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(model_name, backend=backend, device="cpu")
    model.save_pretrained(str(export_dir))

    profile["exported_model_dir"] = str(export_dir.relative_to(work_dir))
    profile["backend"] = backend
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    print(f"Pinned embedder to: {export_dir}")
    print(f"Updated runtime profile: {profile_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
