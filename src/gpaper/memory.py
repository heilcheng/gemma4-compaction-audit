"""Memory-policy renderers for the freshness study.

Arms 3 and 4 share one evidence body. They differ only in a per-record tag:
flat gets a neutral id, fresh gets a validity status against the current workspace.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

SKIP = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".tox", ".venv"}


def fingerprint(root: str | Path) -> str:
    """Hash of every tracked-or-new source file under root (conservative global version).
    Covers files created or edited through shell commands, since it reads the tree itself."""
    h = hashlib.sha256()
    root = Path(root)
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (SKIP & set(p.relative_to(root).parts)):
            h.update(str(p.relative_to(root)).encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


@dataclass
class Record:
    idx: int
    kind: str          # read | edit | test | other
    text: str
    state: str         # workspace fingerprint when the record was produced
    paths: tuple[str, ...] = ()


@dataclass
class Memory:
    records: list[Record] = field(default_factory=list)

    def add(self, kind: str, text: str, state: str, paths: tuple[str, ...] = ()) -> Record:
        r = Record(len(self.records) + 1, kind, text, state, paths)
        self.records.append(r)
        return r

    def _body(self, tag) -> str:
        return "\n".join(f"[{tag(r)}] {r.kind}: {r.text}" for r in self.records)

    def render_flat(self) -> str:
        return self._body(lambda r: f"#{r.idx}")

    def render_fresh(self, current_state: str) -> str:
        def tag(r: Record) -> str:
            ok = r.state == current_state
            return f"#{r.idx} " + ("current" if ok else "older code state, not validated on current")
        return self._body(tag)

    def render_control(self, current_state: str) -> str:
        """Coded metadata, near fresh's tag length on stale records only: same chronology, same evidence, no validity signal."""
        def tag(r: Record) -> str:
            ok = r.state == current_state
            return f"#{r.idx} " + ("seq-a" if ok else "seq-b") + ", no validity claim made here"
        return self._body(tag)


def mask_observations(history: list[tuple[str, str]], keep_recent: int, placeholder: str = "[output omitted]") -> list[tuple[str, str]]:
    """Arm 1: keep all actions, mask observations older than the last keep_recent."""
    n = len(history)
    return [(a, o if i >= n - keep_recent else placeholder) for i, (a, o) in enumerate(history)]
