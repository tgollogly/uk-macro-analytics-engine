#!/usr/bin/env python3
"""
Lightweight security posture scan for this repository.

Checks:
- Python files for broad except Exception patterns that may leak internals in logs.
- High-entropy or common secret-like string patterns in source.
- Dependency pins in requirements.txt for known risky patterns (placeholder / git+http).

Exit code 0 when no findings above thresholds; non-zero when violations found.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    severity: str
    path: str
    line: int | None
    message: str


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, path: Path, line: int | None, message: str) -> None:
        self.findings.append(Finding(severity, str(path), line, message))


SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)aws_(access|secret)_key_id\s*=\s*['\"][^'\"]+['\"]"), "AWS key-like assignment"),
    (re.compile(r"(?i)api_key\s*=\s*['\"][^'\"]{16,}['\"]"), "api_key assignment with long literal"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-_]{20,}"), "Bearer token literal"),
    (re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"), "OpenAI-style sk- secret"),
    (re.compile(r"(?i)ghp_[A-Za-z0-9]{20,}"), "GitHub PAT ghp_"),
)

BROAD_EXCEPT_RE = re.compile(r"except\s+Exception\b")
BARE_EXCEPT_RE = re.compile(r"except\s*:")


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*.py")
        if ".venv" not in p.parts
        and "node_modules" not in p.parts
        and "__pycache__" not in p.parts
        and ".git" not in p.parts
    )


def _scan_text_secrets(path: Path, result: ScanResult) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for i, line in enumerate(text.splitlines(), start=1):
        for pattern, name in SECRET_PATTERNS:
            if pattern.search(line):
                result.add("error", path, i, f"Possible secret pattern ({name})")
        if "password" in line.lower() and "=" in line and re.search(r"['\"][^'\"]{8,}['\"]", line):
            if not line.strip().startswith("#"):
                result.add("warning", path, i, "Possible hardcoded password")


def _scan_exception_handling(path: Path, result: ScanResult) -> None:
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = src.splitlines()
    if BROAD_EXCEPT_RE.search(src) or BARE_EXCEPT_RE.search(src):
        # AST pass for bare except / except Exception without re-raise
        try:
            tree = ast.parse(src)
        except SyntaxError:
            result.add("warning", path, None, "File has syntax errors; skipped AST scan")
            return

        class V(ast.NodeVisitor):
            def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
                if node.type is None:
                    result.add(
                        "error",
                        path,
                        node.lineno,
                        "Bare except: catches BaseException and may hide failures",
                    )
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    body = node.body
                    re_raises = any(isinstance(s, ast.Raise) for s in body)
                    logs = any(
                        isinstance(s, ast.Expr)
                        and isinstance(s.value, ast.Call)
                        and isinstance(s.value.func, ast.Attribute)
                        and s.value.func.attr in ("warning", "error", "exception", "critical")
                        for s in body
                    )
                    if not re_raises and not logs:
                        result.add(
                            "warning",
                            path,
                            node.lineno,
                            "except Exception without raise or logging: may swallow errors",
                        )
                self.generic_visit(node)

        V().visit(tree)

        # Line-based hints for reviewers
        for i, line in enumerate(lines, start=1):
            if BARE_EXCEPT_RE.search(line):
                result.add("error", path, i, "Bare except on line (see AST finding)")


def _scan_requirements(req: Path, result: ScanResult) -> None:
    if not req.is_file():
        result.add("warning", req, None, "requirements.txt missing")
        return
    for i, line in enumerate(req.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("-e "):
            result.add("warning", req, i, "Editable install (-e); ensure trust for CI supply chain")
        if s.startswith("git+http://"):
            result.add("error", req, i, "Insecure git+http dependency")
        if "==" not in s and not s.startswith(("-r ", "-e ", "-c ")):
            result.add("warning", req, i, "Unpinned dependency")


def scan_repo(repo_root: Path) -> ScanResult:
    result = ScanResult()
    for py in _iter_py_files(repo_root):
        if py.name == "security_audit.py":
            continue
        _scan_text_secrets(py, result)
        _scan_exception_handling(py, result)
    _scan_requirements(repo_root / "requirements.txt", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Security audit for uk-macro-analytics-engine")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit)",
    )
    args = parser.parse_args(argv)

    r = scan_repo(args.root)
    errors = [f for f in r.findings if f.severity == "error"]
    warnings = [f for f in r.findings if f.severity == "warning"]

    for f in r.findings:
        loc = f":{f.line}" if f.line is not None else ""
        print(f"[{f.severity.upper()}] {f.path}{loc}: {f.message}")

    if errors:
        print(f"\nAudit failed with {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    if args.strict and warnings:
        print(f"\nAudit failed (--strict) with {len(warnings)} warning(s).")
        return 1
    print(f"\nAudit passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
