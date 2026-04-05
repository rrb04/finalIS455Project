"""One-off: build chats/cursor-is455-thread.md from Cursor JSONL transcript."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"C:\Users\Ryan\.cursor\projects\c-Users-Ryan-Desktop-IS455Project"
    r"\agent-transcripts\6596d58d-8893-4a5c-a8a7-03272ccf102b"
    r"\6596d58d-8893-4a5c-a8a7-03272ccf102b.jsonl"
)
OUT_DIR = ROOT / "chats"
OUT_FILE = OUT_DIR / "cursor-is455-thread.md"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = SRC.read_text(encoding="utf-8").splitlines()
    parts: list[str] = [
        "# Cursor chat — line-by-line export",
        "",
        "**Transcript ID:** `6596d58d-8893-4a5c-a8a7-03272ccf102b`",
        "",
        "**Source:** Cursor agent transcript (JSONL). Part A matches the file exactly: one JSON object per line.",
        "",
        "---",
        "",
        "## Part A — Raw JSONL (line-by-line)",
        "",
        "```jsonl",
    ]
    parts.extend(lines)
    parts.extend(
        [
            "```",
            "",
            "---",
            "",
            "## Part B — Same messages (readable text)",
            "",
        ]
    )
    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        o = json.loads(raw)
        role = o.get("role", "?")
        parts.append(f"### Line {i} ({role})")
        parts.append("")
        for p in o.get("message", {}).get("content", []):
            if isinstance(p, dict) and p.get("type") == "text":
                t = p.get("text", "")
                if t.strip():
                    parts.append(t)
                    parts.append("")
    OUT_FILE.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT_FILE} ({len(lines)} jsonl lines)")


if __name__ == "__main__":
    main()
