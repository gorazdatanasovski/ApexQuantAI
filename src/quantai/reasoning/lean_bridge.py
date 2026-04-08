from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class LeanExportConfig:
    """
    Configuration for exporting QuantAI theorem artifacts to Lean 4.

    This bridge is intentionally conservative:
    - it exports theorem packages as Lean skeletons
    - it preserves provenance and assumptions in comments
    - it can optionally emit `axiom` declarations for assumptions
    - it does not pretend to automatically prove arbitrary mathematics

    The goal is to move theorem candidates into a formal workflow without
    overstating what can be derived automatically.
    """

    project_name: str = "QuantAIFormal"
    theorem_namespace: str = "QuantAI"
    theorem_name: Optional[str] = None
    emit_axioms: bool = False
    emit_sorries: bool = True
    include_metadata_comments: bool = True
    use_mathlib_imports: bool = True
    imports: tuple[str, ...] = (
        "Mathlib",
    )


@dataclass(frozen=True)
class LeanExportArtifact:
    theorem_name: str
    lean_path: str
    metadata_path: str
    namespace: str
    rendered_code: str
    metadata: dict[str, Any] = field(default_factory=dict)
    check: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LeanBridge:
    """
    Export QuantAI theorem candidates into Lean 4 skeletons.

    Supported inputs:
    - TheoremArtifact-like objects with `.as_dict()`
    - TheoremLabResult-like objects with `.selected`
    - plain mappings

    Output:
    - `.lean` theorem skeleton with assumptions, statement comments, and proof stub
    - `.json` metadata sidecar for provenance and later round-tripping

    This is a formalization bridge, not a theorem prover.
    """

    _RESERVED = {
        "theorem",
        "axiom",
        "def",
        "let",
        "in",
        "if",
        "then",
        "else",
        "match",
        "namespace",
        "end",
        "import",
        "open",
        "where",
        "have",
        "show",
        "by",
        "fun",
        "Type",
        "Prop",
    }

    def __init__(self, root_dir: str | Path = "formal", config: Optional[LeanExportConfig] = None):
        self.root_dir = Path(root_dir)
        self.config = config or LeanExportConfig()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def export_theorem_artifact(
        self,
        artifact: Any,
        *,
        theorem_name: Optional[str] = None,
        namespace: Optional[str] = None,
        root_dir: str | Path | None = None,
        run_check: bool = False,
    ) -> LeanExportArtifact:
        payload = self._coerce_artifact(artifact)
        project_root = Path(root_dir) if root_dir is not None else self.root_dir
        theorem_name = self._build_theorem_name(payload, theorem_name)
        namespace = namespace or self.config.theorem_namespace

        lean_dir = project_root / self.config.project_name / namespace
        meta_dir = project_root / self.config.project_name / "metadata"
        lean_dir.mkdir(parents=True, exist_ok=True)
        meta_dir.mkdir(parents=True, exist_ok=True)

        lean_path = lean_dir / f"{theorem_name}.lean"
        metadata_path = meta_dir / f"{theorem_name}.json"

        rendered_code = self._render_lean(payload, theorem_name=theorem_name, namespace=namespace)
        lean_path.write_text(rendered_code, encoding="utf-8")

        metadata = {
            "theorem_name": theorem_name,
            "namespace": namespace,
            "export_root": str(project_root.resolve()),
            "artifact": payload,
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        self._ensure_project_scaffold(project_root / self.config.project_name)

        check: dict[str, Any] = {}
        if run_check:
            check = self.check_lean_file(lean_path)

        return LeanExportArtifact(
            theorem_name=theorem_name,
            lean_path=str(lean_path),
            metadata_path=str(metadata_path),
            namespace=namespace,
            rendered_code=rendered_code,
            metadata=metadata,
            check=check,
        )

    def export_lab_result(
        self,
        lab_result: Any,
        *,
        theorem_name: Optional[str] = None,
        namespace: Optional[str] = None,
        root_dir: str | Path | None = None,
        run_check: bool = False,
    ) -> LeanExportArtifact:
        selected = getattr(lab_result, "selected", None)
        if selected is None and isinstance(lab_result, Mapping):
            selected = lab_result.get("selected")
        if selected is None:
            raise ValueError("lab_result does not contain a selected theorem artifact")
        return self.export_theorem_artifact(
            selected,
            theorem_name=theorem_name,
            namespace=namespace,
            root_dir=root_dir,
            run_check=run_check,
        )

    def check_lean_file(self, lean_path: str | Path) -> dict[str, Any]:
        lean_path = Path(lean_path)
        if not lean_path.exists():
            return {"ok": False, "error": f"Lean file not found: {lean_path}"}

        lean_bin = shutil.which("lean")
        lake_bin = shutil.which("lake")

        if lean_bin is None and lake_bin is None:
            return {
                "ok": False,
                "error": "Lean is not installed or not on PATH.",
                "hint": "Install Lean 4 / elan, or open the exported file in a Lean-enabled VS Code workspace.",
            }

        project_root = self._find_project_root(lean_path)
        if lake_bin is not None and project_root is not None:
            cmd = [lake_bin, "env", "lean", str(lean_path)]
            cwd = str(project_root)
        else:
            cmd = [lean_bin or "lean", str(lean_path)]
            cwd = str(lean_path.parent)

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc), "command": cmd}

        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "command": cmd,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    # ------------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------------
    def _render_lean(self, payload: Mapping[str, Any], *, theorem_name: str, namespace: str) -> str:
        title = str(payload.get("title") or theorem_name)
        status = str(payload.get("status") or "candidate")
        score = payload.get("score")
        statement = str(payload.get("statement") or "No statement available.")
        assumptions = self._normalize_list(payload.get("assumptions"))
        variables = self._normalize_variables(payload.get("variables"))
        symbolic_agenda = self._normalize_list(payload.get("symbolic_agenda"))
        failure_conditions = self._normalize_list(payload.get("failure_conditions"))
        next_actions = self._normalize_list(payload.get("next_actions"))
        tags = self._normalize_list(payload.get("tags"))

        imports_block = self._render_imports()
        comments = []
        if self.config.include_metadata_comments:
            comments.extend(
                [
                    "/-!",
                    f"QuantAI theorem export: {title}",
                    f"Status: {status}",
                    f"Score: {score}",
                    "",
                    "Original natural-language statement:",
                    *[f"  {line}" for line in statement.splitlines() or [statement]],
                    "",
                    "Tags:",
                    *([f"  - {x}" for x in tags] or ["  - none"]),
                    "",
                    "Failure conditions:",
                    *([f"  - {x}" for x in failure_conditions] or ["  - none"]),
                    "",
                    "Next actions:",
                    *([f"  - {x}" for x in next_actions] or ["  - none"]),
                    "-/'",
                ]
            )

        lines: list[str] = []
        if imports_block:
            lines.extend(imports_block)
            lines.append("")
        lines.extend(comments)
        if comments:
            lines.append("")
        lines.append(f"namespace {namespace}")
        lines.append("")

        variable_lines = self._render_variables(variables)
        if variable_lines:
            lines.extend(variable_lines)
            lines.append("")

        axiom_lines = self._render_axioms(assumptions) if self.config.emit_axioms else []
        if axiom_lines:
            lines.extend(axiom_lines)
            lines.append("")

        theorem_lines = self._render_theorem_skeleton(
            theorem_name=theorem_name,
            assumptions=assumptions,
            statement=statement,
            symbolic_agenda=symbolic_agenda,
        )
        lines.extend(theorem_lines)
        lines.append("")
        lines.append(f"end {namespace}")
        lines.append("")
        return "\n".join(lines)

    def _render_imports(self) -> list[str]:
        if not self.config.use_mathlib_imports:
            return []
        return [f"import {imp}" for imp in self.config.imports]

    def _render_variables(self, variables: Mapping[str, str]) -> list[str]:
        if not variables:
            return []
        lines = ["/- Variable declarations inferred by QuantAI. Edit types as needed. -/"]
        for raw_name, raw_desc in variables.items():
            name = self._sanitize_identifier(raw_name)
            desc = str(raw_desc) if raw_desc is not None else ""
            inferred_type = self._infer_lean_type(name, desc)
            comment = f" -- {desc}" if desc else ""
            lines.append(f"variable ({name} : {inferred_type}){comment}")
        return lines

    def _render_axioms(self, assumptions: Sequence[str]) -> list[str]:
        if not assumptions:
            return []
        lines = ["/- Assumption placeholders generated from the theorem artifact. -/"]
        for idx, assumption in enumerate(assumptions, start=1):
            ident = self._sanitize_identifier(f"assumption_{idx}")
            lines.append(f"axiom {ident} : Prop  -- {assumption}")
        return lines

    def _render_theorem_skeleton(
        self,
        *,
        theorem_name: str,
        assumptions: Sequence[str],
        statement: str,
        symbolic_agenda: Sequence[str],
    ) -> list[str]:
        lines = ["/-", "Natural-language assumptions carried over from QuantAI:"]
        lines.extend([f"* {x}" for x in assumptions] or ["* none recorded"])
        lines.append("")
        lines.append("Symbolic agenda:")
        lines.extend([f"* {x}" for x in symbolic_agenda] or ["* none recorded"])
        lines.append("-/")

        theorem_header = f"theorem {theorem_name} : Prop := by"
        lines.append(theorem_header)
        lines.append("  /-")
        lines.append("  Original statement to formalize:")
        for line in statement.splitlines() or [statement]:
            lines.append(f"  {line}")
        lines.append("  -/")
        if self.config.emit_sorries:
            lines.append("  sorry")
        else:
            lines.append("  trivial")
        return lines

    # ------------------------------------------------------------------
    # scaffolding
    # ------------------------------------------------------------------
    def _ensure_project_scaffold(self, project_root: Path) -> None:
        project_root.mkdir(parents=True, exist_ok=True)
        lakefile = project_root / "lakefile.lean"
        lean_toolchain = project_root / "lean-toolchain"
        root_lean = project_root / f"{self.config.project_name}.lean"
        namespace_dir = project_root / self.config.theorem_namespace
        namespace_dir.mkdir(exist_ok=True)

        if not lakefile.exists():
            lakefile.write_text(self._render_lakefile(), encoding="utf-8")
        if not lean_toolchain.exists():
            lean_toolchain.write_text("leanprover/lean4:stable\n", encoding="utf-8")
        if not root_lean.exists():
            root_lean.write_text(
                f"import {self.config.project_name}.{self.config.theorem_namespace}\n",
                encoding="utf-8",
            )

    def _render_lakefile(self) -> str:
        project = self.config.project_name
        return f'''import Lake\nopen Lake DSL\n\npackage \"{project}\" where\n\n@[default_target]\nlean_lib {project} where\n'''

    def _find_project_root(self, lean_path: Path) -> Optional[Path]:
        for parent in [lean_path.parent, *lean_path.parents]:
            if (parent / "lakefile.lean").exists():
                return parent
        return None

    # ------------------------------------------------------------------
    # coercion / normalization
    # ------------------------------------------------------------------
    def _coerce_artifact(self, artifact: Any) -> dict[str, Any]:
        if hasattr(artifact, "as_dict"):
            payload = artifact.as_dict()
        elif isinstance(artifact, Mapping):
            payload = dict(artifact)
        else:
            raise TypeError("artifact must be a mapping or expose an as_dict() method")

        if "selected" in payload and isinstance(payload["selected"], Mapping):
            payload = dict(payload["selected"])

        return payload

    def _build_theorem_name(self, payload: Mapping[str, Any], theorem_name: Optional[str]) -> str:
        if theorem_name:
            return self._sanitize_identifier(theorem_name, upper_camel=True)
        if self.config.theorem_name:
            return self._sanitize_identifier(self.config.theorem_name, upper_camel=True)

        base = str(payload.get("title") or payload.get("statement") or "QuantAITheorem")
        if len(base) > 96:
            base = base[:96]
        return self._sanitize_identifier(base, upper_camel=True)

    def _normalize_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, Sequence):
            return [str(x) for x in value]
        return [str(value)]

    def _normalize_variables(self, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if isinstance(value, Mapping):
            out: dict[str, str] = {}
            for k, v in value.items():
                if isinstance(v, Mapping):
                    desc = v.get("description") or v.get("type") or json.dumps(v, ensure_ascii=False)
                else:
                    desc = str(v)
                out[str(k)] = str(desc)
            return out
        return {}

    def _sanitize_identifier(self, raw: str, *, upper_camel: bool = False) -> str:
        text = re.sub(r"[^0-9A-Za-z_]+", "_", raw.strip())
        text = re.sub(r"_+", "_", text).strip("_")
        if not text:
            text = "QuantAITheorem"
        if text[0].isdigit():
            text = f"q_{text}"
        if text in self._RESERVED:
            text = f"q_{text}"
        if upper_camel:
            parts = [p for p in text.split("_") if p]
            text = "".join(p[:1].upper() + p[1:] for p in parts) or "QuantAITheorem"
        return text

    def _infer_lean_type(self, name: str, desc: str) -> str:
        probe = f"{name} {desc}".lower()
        if any(tok in probe for tok in ["nat", "integer", "count", "index", "n "]):
            return "ℕ"
        if any(tok in probe for tok in ["prob", "measure", "prop", "predicate", "event"]):
            return "Prop"
        if any(tok in probe for tok in ["matrix", "operator", "function", "kernel", "mapping"]):
            return "Type"
        return "ℝ"


def export_theorem_to_lean(
    artifact: Any,
    *,
    root_dir: str | Path = "formal",
    theorem_name: Optional[str] = None,
    namespace: str = "QuantAI",
    emit_axioms: bool = False,
    run_check: bool = False,
) -> dict[str, Any]:
    bridge = LeanBridge(
        root_dir=root_dir,
        config=LeanExportConfig(
            theorem_namespace=namespace,
            theorem_name=theorem_name,
            emit_axioms=emit_axioms,
        ),
    )
    return bridge.export_theorem_artifact(artifact, run_check=run_check).as_dict()
