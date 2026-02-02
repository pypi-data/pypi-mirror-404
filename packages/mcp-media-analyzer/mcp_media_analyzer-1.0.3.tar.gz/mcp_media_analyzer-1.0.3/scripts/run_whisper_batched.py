#!/usr/bin/env python3
"""Local Whisper 分段轉錄（切段 + 智慧合併，已移除幻覺過濾）。傳入音檔路徑，輸出寫入同目錄 {檔名}_localWhisper_batched.md"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv()


async def main():
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/run_whisper_batched.py <音檔路徑>", file=sys.stderr)
        sys.exit(1)
    audio_path = Path(sys.argv[1]).resolve()
    if not audio_path.exists():
        print(f"錯誤：找不到檔案 {audio_path}", file=sys.stderr)
        sys.exit(1)

    from mcp_media_analyzer.server import (
        transcribe_with_whisper,
        Config,
    )

    print("分段轉錄（切段，已移除幻覺過濾）:", audio_path, flush=True)
    print("模型:", Config.WHISPER_MODEL, flush=True)
    result = await transcribe_with_whisper(audio_path)
    if not result.get("success"):
        print("轉錄失敗:", result.get("error"), file=sys.stderr)
        sys.exit(1)

    text = (result.get("transcript") or "").strip()
    note = result.get("note", "")
    chunks = result.get("chunks_processed")
    valid = result.get("valid_chunks")

    out_path = audio_path.parent / f"{audio_path.stem}_localWhisper_batched.md"
    lines = [
        f"# {audio_path.name} 逐字稿（分段 Local Whisper，已移除幻覺過濾）",
        "",
        "## 轉錄來源",
        "",
        f"whisper_local_batched ({Config.WHISPER_MODEL})",
        f"chunks_processed: {chunks}" + (f", valid_chunks: {valid}" if valid is not None else ""),
        "",
        "## 逐字稿",
        "",
        text or (note if note else "(無內容)"),
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("已寫入:", out_path, flush=True)
    print("字數:", len(text), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
