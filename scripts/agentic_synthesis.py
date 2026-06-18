#!/usr/bin/env python3
"""Autonomous synthesis runner for the Agent OS vault."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


DEFAULT_VAULT = Path.home() / "obsidian-agentic-vault"
RAW_SUFFIXES = {".md", ".txt"}
STATE_REL = Path("System/synthesis-state.json")
AUDIT_REL = Path("System/audit.jsonl")
CONTRADICTIONS_REL = Path("System/contradictions.md")
PROMPT_REL = Path("System/synthesis-prompt.md")
LOG_DIR_REL = Path("System/logs")
LOCK_REL = Path("System/synthesis.lock")
MANAGED_ROOTS = {
    "Archive",
    "Memory",
    "Organizations",
    "People",
    "Projects",
    "Research",
    "System",
    "Tasks",
}
MANAGED_FILES = {"CLAUDE.md", "Index.md"}
RAW_SINGLE_FILES = {Path("Tasks/inbox.md")}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"pat[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^\s'\"]{16,}"
    ),
]


@dataclass(frozen=True)
class InputRecord:
    rel: str
    sha256: str
    size: int
    mtime: float
    content: str
    truncated: bool = False


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def stamp_for_filename() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def run(
    args: list[str],
    cwd: Path,
    *,
    check: bool = True,
    input_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        cmd = " ".join(args)
        raise RuntimeError(
            f"Command failed ({result.returncode}): {cmd}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def relpath(vault: Path, path: Path) -> str:
    return path.relative_to(vault).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_state(vault: Path) -> dict:
    state_path = vault / STATE_REL
    if not state_path.exists():
        return {
            "version": 1,
            "last_run_at": None,
            "last_mode": None,
            "processed_inputs": {},
            "recent_runs": [],
        }
    return json.loads(state_path.read_text())


def write_state(vault: Path, state: dict) -> None:
    state_path = vault / STATE_REL
    tmp = state_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    tmp.replace(state_path)


def ensure_layout(vault: Path) -> None:
    for rel in [
        "Archive",
        "Inbox",
        "Organizations",
        "People",
        "System",
        "Tasks",
        "System/logs",
    ]:
        (vault / rel).mkdir(parents=True, exist_ok=True)
    if not (vault / AUDIT_REL).exists():
        (vault / AUDIT_REL).write_text("")
    if not (vault / CONTRADICTIONS_REL).exists():
        (vault / CONTRADICTIONS_REL).write_text("# Contradictions\n\n")
    if not (vault / STATE_REL).exists():
        write_state(vault, read_state(vault))


def iter_raw_paths(vault: Path) -> list[Path]:
    paths: set[Path] = set()
    inbox = vault / "Inbox"
    if inbox.exists():
        for path in inbox.rglob("*"):
            if path.is_file() and path.suffix.lower() in RAW_SUFFIXES:
                paths.add(path)

    for rel in RAW_SINGLE_FILES:
        path = vault / rel
        if path.exists() and path.is_file():
            paths.add(path)

    journal = vault / "Journal"
    if journal.exists():
        paths.update(p for p in journal.glob("*.md") if p.is_file())

    research = vault / "Research"
    if research.exists():
        paths.update(p for p in research.glob("*.md") if p.is_file())

    return sorted(paths)


def decode_excerpt(data: bytes, remaining_budget: int) -> tuple[str, bool, int]:
    if remaining_budget <= 0:
        return "", True, 0
    truncated = len(data) > remaining_budget
    excerpt = data[:remaining_budget].decode("utf-8", errors="replace")
    return excerpt, truncated, min(len(data), remaining_budget)


def build_input_records(
    vault: Path,
    paths: list[Path],
    *,
    max_input_bytes: int,
) -> tuple[list[InputRecord], dict[str, str], dict[str, bytes]]:
    budget = max_input_bytes
    records: list[InputRecord] = []
    hashes: dict[str, str] = {}
    original_bytes: dict[str, bytes] = {}

    for path in paths:
        data = path.read_bytes()
        rel = relpath(vault, path)
        digest = sha256_bytes(data)
        hashes[rel] = digest
        original_bytes[rel] = data
        content, truncated, used = decode_excerpt(data, budget)
        budget -= used
        records.append(
            InputRecord(
                rel=rel,
                sha256=digest,
                size=len(data),
                mtime=path.stat().st_mtime,
                content=content,
                truncated=truncated,
            )
        )
    return records, hashes, original_bytes


def changed_records(mode: str, records: list[InputRecord], state: dict) -> list[InputRecord]:
    if mode == "nightly":
        return records
    processed = state.get("processed_inputs", {})
    return [r for r in records if processed.get(r.rel) != r.sha256]


def canonical_manifest(vault: Path, raw_rels: set[str]) -> list[dict[str, str | int]]:
    manifest: list[dict[str, str | int]] = []
    for root in sorted(MANAGED_ROOTS):
        base = vault / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = relpath(vault, path)
            if rel in raw_rels or rel.startswith("System/logs/"):
                continue
            try:
                first_line = path.read_text(errors="replace").splitlines()[0]
            except IndexError:
                first_line = ""
            manifest.append(
                {
                    "path": rel,
                    "bytes": path.stat().st_size,
                    "title": first_line.strip("# ").strip(),
                }
            )
    for rel in sorted(MANAGED_FILES):
        path = vault / rel
        if path.exists():
            try:
                first_line = path.read_text(errors="replace").splitlines()[0]
            except IndexError:
                first_line = ""
            manifest.append(
                {
                    "path": rel,
                    "bytes": path.stat().st_size,
                    "title": first_line.strip("# ").strip(),
                }
            )
    return manifest


def build_prompt(
    vault: Path,
    *,
    mode: str,
    records: list[InputRecord],
    all_hashes: dict[str, str],
    state: dict,
    max_input_bytes: int,
) -> str:
    template = (vault / PROMPT_REL).read_text()
    raw_rels = set(all_hashes)
    context = {
        "timestamp": now_iso(),
        "mode": mode,
        "vault": str(vault),
        "raw_input_count": len(records),
        "raw_inputs": [
            {
                "path": r.rel,
                "sha256": r.sha256,
                "bytes": r.size,
                "truncated": r.truncated,
            }
            for r in records
        ],
        "canonical_manifest": canonical_manifest(vault, raw_rels),
        "state_summary": {
            "last_run_at": state.get("last_run_at"),
            "last_mode": state.get("last_mode"),
            "processed_input_count": len(state.get("processed_inputs", {})),
        },
        "max_input_bytes": max_input_bytes,
    }

    sections = []
    for record in records:
        sections.append(
            "\n".join(
                [
                    f"### {record.rel}",
                    f"- sha256: `{record.sha256}`",
                    f"- bytes: {record.size}",
                    f"- truncated: {str(record.truncated).lower()}",
                    "",
                    "```text",
                    record.content,
                    "```",
                ]
            )
        )

    return "\n\n".join(
        [
            template,
            "## Run Context",
            "```json",
            json.dumps(context, indent=2, sort_keys=True),
            "```",
            "## Raw Inputs For This Run",
            "\n\n".join(sections) if sections else "(none)",
        ]
    )


def git_status_paths(vault: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], vault)
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def dirty_raw_paths(vault: Path, raw_rels: Iterable[str]) -> list[str]:
    raw_set = set(raw_rels)
    return [p for p in git_status_paths(vault) if p in raw_set]


def git_commit_paths(vault: Path, rels: list[str], message: str) -> str | None:
    if not rels:
        return None
    run(["git", "add", "--", *rels], vault)
    commit = run(["git", "commit", "-m", message], vault, check=False)
    if commit.returncode != 0:
        if "nothing to commit" in commit.stdout.lower() or "nothing to commit" in commit.stderr.lower():
            return None
        raise RuntimeError(f"git commit failed:\n{commit.stdout}\n{commit.stderr}")
    head = run(["git", "rev-parse", "--short", "HEAD"], vault).stdout.strip()
    return head


def is_managed_path(rel: str) -> bool:
    if rel.startswith("System/logs/") or rel == str(LOCK_REL):
        return False
    if rel in MANAGED_FILES:
        return True
    root = rel.split("/", 1)[0]
    return root in MANAGED_ROOTS


def managed_changed_paths(vault: Path) -> list[str]:
    return sorted(p for p in git_status_paths(vault) if is_managed_path(p))


def scan_for_secrets(vault: Path, rels: Iterable[str]) -> list[str]:
    findings: list[str] = []
    for rel in rels:
        path = vault / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{line_no}: secret-like value matched")
                    break
    return findings


def append_audit(vault: Path, entry: dict) -> None:
    audit_path = vault / AUDIT_REL
    with audit_path.open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def validate_raw_unchanged(vault: Path, before: dict[str, bytes]) -> None:
    changed: list[str] = []
    for rel, original in before.items():
        path = vault / rel
        if not path.exists():
            changed.append(f"{rel} was deleted")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(original)
            continue
        current = path.read_bytes()
        if current != original:
            changed.append(f"{rel} was modified")
            path.write_bytes(original)
    if changed:
        raise RuntimeError(
            "Raw input preservation failed; original raw bytes were restored:\n"
            + "\n".join(f"- {item}" for item in changed)
        )


def call_claude(
    vault: Path,
    *,
    prompt: str,
    claude_command: str,
    mode: str,
    timeout_seconds: int,
) -> Path:
    log_dir = vault / LOG_DIR_REL
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"synthesis-{stamp_for_filename()}-{mode}.log"
    tools = "Read,Edit,MultiEdit,Write,Bash(git *),Bash(rg *),Bash(find *),Bash(sed *),Bash(python3 *)"
    cmd = [
        claude_command,
        "-p",
        "--permission-mode",
        "auto",
        "--add-dir",
        str(vault),
        "--strict-mcp-config",
        "--allowedTools",
        tools,
        "--no-session-persistence",
    ]
    result = run(cmd, vault, check=False, input_text=prompt, timeout=timeout_seconds)
    log_path.write_text(
        "\n".join(
            [
                f"timestamp={now_iso()}",
                f"mode={mode}",
                f"returncode={result.returncode}",
                "",
                "STDOUT:",
                result.stdout,
                "",
                "STDERR:",
                result.stderr,
                "",
            ]
        )
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude synthesis failed; see {log_path}")
    return log_path


def update_processed_state(
    state: dict,
    *,
    mode: str,
    all_hashes: dict[str, str],
    processed: list[InputRecord],
    changed_paths: list[str],
) -> dict:
    updated = dict(state)
    processed_inputs = dict(updated.get("processed_inputs", {}))
    for record in processed:
        processed_inputs[record.rel] = record.sha256
    updated["processed_inputs"] = processed_inputs
    updated["last_run_at"] = now_iso()
    updated["last_mode"] = mode
    run_entry = {
        "timestamp": updated["last_run_at"],
        "mode": mode,
        "processed_inputs": [r.rel for r in processed],
        "known_input_count": len(all_hashes),
        "changed_paths": changed_paths,
    }
    recent_runs = list(updated.get("recent_runs", []))
    recent_runs.append(run_entry)
    updated["recent_runs"] = recent_runs[-20:]
    return updated


def acquire_lock(vault: Path):
    lock_path = vault / LOCK_REL
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"Another synthesis run is active: {lock_path}") from exc
    lock_file.write(f"{os.getpid()}\n")
    lock_file.flush()
    return lock_file


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["incremental", "nightly", "dry-run"],
        default="incremental",
        help="Synthesis mode. dry-run prints what would be processed and exits.",
    )
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--claude-command", default=os.environ.get("CLAUDE_COMMAND", "claude"))
    parser.add_argument("--max-input-bytes", type=int, default=200_000)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Run synthesis and validation without creating git commits.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    vault = args.vault.expanduser().resolve()
    if not (vault / ".git").exists():
        raise RuntimeError(f"Vault is not a git repo: {vault}")

    ensure_layout(vault)
    lock_file = acquire_lock(vault)
    try:
        state = read_state(vault)
        raw_paths = iter_raw_paths(vault)
        all_records, all_hashes, original_bytes = build_input_records(
            vault, raw_paths, max_input_bytes=args.max_input_bytes
        )
        records = changed_records(args.mode, all_records, state)

        if args.mode == "incremental" and not records:
            print(
                json.dumps(
                    {
                        "status": "noop",
                        "mode": args.mode,
                        "raw_input_count": len(all_records),
                        "changed_input_count": 0,
                    },
                    indent=2,
                )
            )
            return 0

        if args.mode == "dry-run":
            print(
                json.dumps(
                    {
                        "status": "dry-run",
                        "raw_input_count": len(all_records),
                        "changed_input_count": len(records),
                        "changed_inputs": [r.rel for r in records],
                        "would_run_claude": bool(records),
                    },
                    indent=2,
                )
            )
            return 0

        dirty_raw = dirty_raw_paths(vault, all_hashes.keys())
        if dirty_raw and not args.no_commit:
            git_commit_paths(
                vault,
                dirty_raw,
                f"Vault raw checkpoint - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )

        preexisting_managed = managed_changed_paths(vault)
        if preexisting_managed and not args.no_commit:
            raise RuntimeError(
                "Refusing autonomous synthesis commit because managed vault files "
                "already have uncommitted changes. Commit or stash these paths, "
                "or rerun with --no-commit:\n"
                + "\n".join(f"- {path}" for path in preexisting_managed)
            )

        prompt = build_prompt(
            vault,
            mode=args.mode,
            records=records,
            all_hashes=all_hashes,
            state=state,
            max_input_bytes=args.max_input_bytes,
        )
        log_path = call_claude(
            vault,
            prompt=prompt,
            claude_command=args.claude_command,
            mode=args.mode,
            timeout_seconds=args.timeout_seconds,
        )
        validate_raw_unchanged(vault, {r.rel: original_bytes[r.rel] for r in records})

        changed = managed_changed_paths(vault)
        findings = scan_for_secrets(vault, changed)
        if findings:
            raise RuntimeError(
                "Secret scan blocked synthesis commit:\n"
                + "\n".join(f"- {finding}" for finding in findings)
            )

        append_audit(
            vault,
            {
                "timestamp": now_iso(),
                "actor": "agentic_synthesis.py",
                "mode": args.mode,
                "action": "synthesis_run",
                "sources": [r.rel for r in records],
                "targets": changed,
                "notes": f"Claude log: {log_path.relative_to(vault).as_posix()}",
            },
        )
        changed = managed_changed_paths(vault)
        state = update_processed_state(
            state,
            mode=args.mode,
            all_hashes=all_hashes,
            processed=records,
            changed_paths=changed,
        )
        write_state(vault, state)
        changed = managed_changed_paths(vault)
        findings = scan_for_secrets(vault, changed)
        if findings:
            raise RuntimeError(
                "Secret scan blocked synthesis commit:\n"
                + "\n".join(f"- {finding}" for finding in findings)
            )

        commit = None
        if changed and not args.no_commit:
            commit = git_commit_paths(
                vault,
                changed,
                f"Autonomous vault synthesis - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )

        print(
            json.dumps(
                {
                    "status": "ok",
                    "mode": args.mode,
                    "processed_inputs": [r.rel for r in records],
                    "changed_paths": changed,
                    "commit": commit,
                    "log": log_path.relative_to(vault).as_posix(),
                },
                indent=2,
            )
        )
        return 0
    finally:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"agentic_synthesis.py: {exc}", file=sys.stderr)
        raise SystemExit(1)
