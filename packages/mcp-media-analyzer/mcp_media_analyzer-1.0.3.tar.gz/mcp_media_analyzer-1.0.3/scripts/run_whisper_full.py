#!/usr/bin/env python3
"""Local Whisper 整段轉錄（不切段）。傳入音檔路徑，輸出寫入同目錄 {檔名}_full_whisper.md"""
import os
import sys
from pathlib import Path

# 專案 src 可被 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")


def main():
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/run_whisper_full.py <音檔路徑>", file=sys.stderr)
        sys.exit(1)
    audio_path = Path(sys.argv[1]).resolve()
    if not audio_path.exists():
        print(f"錯誤：找不到檔案 {audio_path}", file=sys.stderr)
        sys.exit(1)

    try:
        import mlx_whisper
    except ImportError:
        print("錯誤：請先安裝 mlx-whisper（僅 Apple Silicon）", file=sys.stderr)
        sys.exit(1)

    print("整段轉錄（不切段）:", audio_path, flush=True)
    print("模型:", WHISPER_MODEL, "語言:", WHISPER_LANGUAGE, flush=True)
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=WHISPER_MODEL,
        language=WHISPER_LANGUAGE,
    )
    text = (result.get("text") or "").strip()

    out_path = audio_path.parent / f"{audio_path.stem}_full_whisper.md"
    body = f"# {audio_path.name} 逐字稿（整段 Local Whisper）\n\n## 轉錄來源\n\nwhisper_local_full ({WHISPER_MODEL})\n\n## 逐字稿\n\n{text}\n"
    out_path.write_text(body, encoding="utf-8")
    print("已寫入:", out_path, flush=True)
    print("字數:", len(text), flush=True)


if __name__ == "__main__":
    main()
