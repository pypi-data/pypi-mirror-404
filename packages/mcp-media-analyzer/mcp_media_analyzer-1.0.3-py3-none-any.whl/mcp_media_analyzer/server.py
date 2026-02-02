#!/usr/bin/env python3
"""
MCP 媒體分析工具伺服器
分析多媒體檔案：視覺內容、音訊轉錄、metadata、建議檔名
"""

import asyncio
import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# 載入環境變數
load_dotenv()
load_dotenv(Path.cwd().parent / ".env")

# ============= 設定 =============

class Config:
    # LM Studio 本地 API
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
    LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "qwen/qwen3-vl-30b")
    
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Whisper
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")
    
    # 截圖設定
    FRAME_COUNT = 6
    FRAME_WIDTH = 768
    
    # 暫存目錄
    TEMP_DIR = Path(os.getenv("TEMP_DIR", tempfile.gettempdir())) / "mcp-media-analyzer"
    
    # 工作區根目錄
    WORKSPACE_ROOT = Path(os.getenv("CURSOR_WORKSPACE_ROOT", os.getenv("WORKSPACE_ROOT", os.getcwd())))
    
    # 支援的格式
    VIDEO_FORMATS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv"}
    IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".heic", ".heif"}
    AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".aiff"}
    FORMATS_NEED_CONVERT = {".heic", ".heif", ".tiff", ".bmp", ".raw", ".cr2", ".nef", ".arw"}

# 分析模式
MODE_DEFAULT = "default"  # LM Studio + Whisper，失敗用 Gemini
MODE_LOCAL = "local"      # 只用本地，失敗不用 Gemini
MODE_ONLINE = "online"    # 直接用 Gemini

# 確保暫存目錄存在
Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 初始化 Gemini
genai = None
if Config.GEMINI_API_KEY:
    try:
        from google import genai as google_genai
        genai = google_genai.Client(api_key=Config.GEMINI_API_KEY)
    except ImportError:
        pass

# ============= 工具函數 =============

def resolve_path(input_path: str) -> Path:
    """解析路徑（支援相對路徑）"""
    p = Path(input_path)
    if p.is_absolute():
        return p
    return Config.WORKSPACE_ROOT / p


def check_ffmpeg() -> bool:
    """檢查 ffmpeg 是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_whisper() -> bool:
    """檢查 MLX-Whisper 是否可用"""
    try:
        import mlx_whisper
        return True
    except ImportError:
        return False


def run_command(cmd: list[str], timeout: int = 300) -> tuple[str, str]:
    """執行命令"""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"命令失敗: {result.stderr}")
    return result.stdout, result.stderr


def get_file_type(file_path: Path) -> str:
    """判斷檔案類型"""
    ext = file_path.suffix.lower()
    if ext in Config.VIDEO_FORMATS:
        return "video"
    if ext in Config.IMAGE_FORMATS:
        return "image"
    if ext in Config.AUDIO_FORMATS:
        return "audio"
    return "unknown"


def format_timestamp(seconds: float) -> str:
    """格式化時間戳"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def image_to_base64(image_path: Path) -> str:
    """圖片轉 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ============= 影片處理 =============

async def get_video_metadata(video_path: Path) -> dict:
    """取得影片 metadata"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    stdout, _ = run_command(cmd)
    data = json.loads(stdout)
    
    format_info = data.get("format", {})
    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    tags = format_info.get("tags", {})
    
    # 解析 GPS 地點
    location = tags.get("location") or tags.get("com.apple.quicktime.location.ISO6709")
    
    return {
        "filename": video_path.name,
        "duration": float(format_info.get("duration", 0)),
        "size": int(format_info.get("size", 0)),
        "format": format_info.get("format_name", "unknown"),
        "video": {
            "codec": video_stream.get("codec_name", "unknown"),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
        },
        "audio": {
            "codec": audio_stream.get("codec_name"),
            "sample_rate": audio_stream.get("sample_rate"),
        } if audio_stream.get("codec_name") else None,
        "creation_time": tags.get("creation_time") or tags.get("date"),
        "location": location,
    }


async def extract_frames(video_path: Path, frame_count: int = None) -> tuple[list[Path], Path]:
    """從影片截取多張圖片"""
    frame_count = frame_count or Config.FRAME_COUNT
    
    # 取得影片時長
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)]
    stdout, _ = run_command(cmd)
    duration = float(stdout.strip())
    
    interval = duration / (frame_count + 1)
    frame_dir = Config.TEMP_DIR / f"frames_{os.getpid()}_{hash(str(video_path))}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    
    frames = []
    for i in range(1, frame_count + 1):
        timestamp = interval * i
        frame_path = frame_dir / f"frame_{i}.jpg"
        
        cmd = [
            "ffmpeg", "-ss", str(timestamp), "-i", str(video_path),
            "-vframes", "1", "-vf", f"scale={Config.FRAME_WIDTH}:-1",
            "-q:v", "2", "-y", str(frame_path)
        ]
        try:
            run_command(cmd)
            if frame_path.exists():
                frames.append(frame_path)
        except RuntimeError:
            pass
    
    return frames, frame_dir


async def extract_audio(video_path: Path) -> Path:
    """從影片提取音訊"""
    audio_path = Config.TEMP_DIR / f"audio_{os.getpid()}_{hash(str(video_path))}.mp3"
    
    cmd = [
        "ffmpeg", "-i", str(video_path), "-vn",
        "-acodec", "libmp3lame", "-q:a", "2", "-y", str(audio_path)
    ]
    run_command(cmd)
    return audio_path


# ============= 圖片處理 =============

async def get_image_metadata(image_path: Path) -> dict:
    """取得圖片 metadata"""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", str(image_path)]
        stdout, _ = run_command(cmd)
        data = json.loads(stdout)
        
        stream = data.get("streams", [{}])[0]
        format_info = data.get("format", {})
        tags = format_info.get("tags", {})
        
        return {
            "filename": image_path.name,
            "width": stream.get("width", 0),
            "height": stream.get("height", 0),
            "format": stream.get("codec_name") or format_info.get("format_name", "unknown"),
            "size": int(format_info.get("size", 0)),
            "creation_time": tags.get("creation_time") or tags.get("date"),
        }
    except Exception:
        stat = image_path.stat()
        return {
            "filename": image_path.name,
            "width": 0,
            "height": 0,
            "format": image_path.suffix[1:],
            "size": stat.st_size,
            "creation_time": None,
        }


async def convert_and_resize_image(image_path: Path) -> tuple[Path, bool, bool]:
    """轉換並縮小圖片"""
    ext = image_path.suffix.lower()
    needs_convert = ext in Config.FORMATS_NEED_CONVERT
    output_path = Config.TEMP_DIR / f"converted_{os.getpid()}_{hash(str(image_path))}.jpg"
    
    # 使用 ffmpeg
    try:
        cmd = [
            "ffmpeg", "-i", str(image_path),
            "-vf", f"scale='min({Config.FRAME_WIDTH},iw)':-1",
            "-q:v", "2", "-y", str(output_path)
        ]
        run_command(cmd)
        if output_path.exists():
            return output_path, True, needs_convert
    except RuntimeError:
        pass
    
    # 使用 sips (macOS)
    try:
        if needs_convert:
            temp_jpg = Config.TEMP_DIR / f"temp_{os.getpid()}.jpg"
            run_command(["sips", "-s", "format", "jpeg", str(image_path), "--out", str(temp_jpg)])
            run_command(["sips", "-Z", str(Config.FRAME_WIDTH), str(temp_jpg), "--out", str(output_path)])
            temp_jpg.unlink(missing_ok=True)
        else:
            run_command(["sips", "-Z", str(Config.FRAME_WIDTH), str(image_path), "--out", str(output_path)])
        
        if output_path.exists():
            return output_path, True, needs_convert
    except RuntimeError:
        pass
    
    if needs_convert:
        raise RuntimeError(f"無法轉換 {ext} 格式")
    
    return image_path, False, False


# ============= 視覺分析 =============

async def analyze_with_lm_studio(frames: list[Path], prompt: str = None) -> dict:
    """使用 LM Studio 分析圖片"""
    default_prompt = """請根據這些影片/圖片截圖分析以下內容：
1. 地點（Location）：描述可能的拍攝地點
2. 活動（Activity）：描述正在進行的活動或事件
3. 人物（People）：描述出現的人物特徵
4. 物品（Objects）：描述重要的物品
5. 氛圍（Atmosphere）：描述整體氛圍
6. 時間推測（Time）：根據光線推測時間

請用繁體中文回答。"""

    image_contents = []
    for frame in frames:
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_to_base64(frame)}"}
        })
    
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt or default_prompt},
            *image_contents
        ]
    }]
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                Config.LM_STUDIO_URL,
                json={
                    "model": Config.LM_STUDIO_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "source": "lm_studio",
                    "model": Config.LM_STUDIO_MODEL,
                    "content": data["choices"][0]["message"]["content"]
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def analyze_with_gemini(frames: list[Path], prompt: str = None) -> dict:
    """使用 Gemini 分析圖片"""
    if not genai:
        return {"success": False, "error": "Gemini API key 未設定"}
    
    default_prompt = """請根據這些影片/圖片截圖分析以下內容：
1. 地點（Location）：描述可能的拍攝地點
2. 活動（Activity）：描述正在進行的活動或事件
3. 人物（People）：描述出現的人物特徵
4. 物品（Objects）：描述重要的物品
5. 氛圍（Atmosphere）：描述整體氛圍
6. 時間推測（Time）：根據光線推測時間

請用繁體中文回答。"""

    try:
        from google.genai import types
        
        contents = [prompt or default_prompt]
        for frame in frames:
            with open(frame, "rb") as f:
                contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))
        
        response = genai.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=contents
        )
        
        return {
            "success": True,
            "source": "gemini",
            "model": Config.GEMINI_MODEL,
            "content": response.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def analyze_frames(frames: list[Path], prompt: str = None, mode: str = MODE_DEFAULT) -> dict:
    """分析畫面（根據模式選擇策略）"""
    
    # online 模式：直接用 Gemini
    if mode == MODE_ONLINE:
        if genai:
            return await analyze_with_gemini(frames, prompt)
        return {"success": False, "error": "Gemini API key 未設定"}
    
    # default / local 模式：先嘗試 LM Studio
    result = await analyze_with_lm_studio(frames, prompt)
    if result["success"]:
        return result
    
    # default 模式：Fallback 到 Gemini
    if mode == MODE_DEFAULT and genai:
        result = await analyze_with_gemini(frames, prompt)
        if result["success"]:
            return result
    
    # local 模式或全部失敗
    if mode == MODE_LOCAL:
        return {"success": False, "error": "LM Studio 連線失敗（local 模式不使用 Gemini）"}
    
    return None


async def analyze_single_image(image_path: Path, query: str = None, mode: str = MODE_DEFAULT) -> dict:
    """分析單張圖片"""
    frames = [image_path]
    return await analyze_frames(frames, query, mode)


# ============= 音訊轉錄 =============

# 分段設定
CHUNK_DURATION = 30  # 每段 30 秒
CHUNK_OVERLAP = 2    # 段落重疊 2 秒（用於智慧組合）


async def transcribe_with_gemini(audio_path: Path) -> dict:
    """使用 Gemini 轉錄"""
    if not genai:
        return {"success": False, "error": "Gemini API key 未設定"}
    
    try:
        from google.genai import types
        
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        mime_type = "audio/mpeg" if audio_path.suffix == ".mp3" else "audio/wav"
        
        response = genai.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[
                "請將這段音訊轉錄為文字。請提供完整的逐字稿，使用繁體中文。如果有多個說話者，請標註不同的說話者。如果音訊是環境音或無語音內容，請回覆「無語音內容」。",
                types.Part.from_bytes(data=audio_data, mime_type=mime_type)
            ]
        )
        
        return {
            "success": True,
            "transcript": response.text,
            "source": "gemini"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def split_audio(audio_path: Path, chunk_duration: int = CHUNK_DURATION) -> list[Path]:
    """將音訊分割成多個片段"""
    # 取得音訊長度
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)]
    stdout, _ = run_command(cmd)
    total_duration = float(stdout.strip())
    
    # 如果音訊很短，不需要分割
    if total_duration <= chunk_duration:
        return [audio_path]
    
    chunks = []
    chunk_dir = Config.TEMP_DIR / f"chunks_{os.getpid()}_{hash(str(audio_path))}"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    
    start = 0
    chunk_idx = 0
    
    while start < total_duration:
        chunk_path = chunk_dir / f"chunk_{chunk_idx:03d}.mp3"
        end = min(start + chunk_duration, total_duration)
        
        cmd = [
            "ffmpeg", "-i", str(audio_path),
            "-ss", str(start), "-t", str(chunk_duration + CHUNK_OVERLAP),
            "-acodec", "libmp3lame", "-q:a", "2", "-y", str(chunk_path)
        ]
        
        try:
            run_command(cmd)
            if chunk_path.exists():
                chunks.append(chunk_path)
        except RuntimeError:
            pass
        
        start = end
        chunk_idx += 1
    
    return chunks


async def transcribe_chunk(chunk_path: Path, chunk_idx: int) -> dict:
    """轉錄單一音訊片段"""
    if not check_whisper():
        return {"idx": chunk_idx, "success": False, "error": "MLX-Whisper 未安裝"}
    
    try:
        import mlx_whisper
        
        result = mlx_whisper.transcribe(
            str(chunk_path),
            path_or_hf_repo=Config.WHISPER_MODEL,
            language=Config.WHISPER_LANGUAGE
        )
        
        return {
            "idx": chunk_idx,
            "success": True,
            "text": result["text"].strip(),
            "segments": result.get("segments", [])
        }
    except Exception as e:
        return {"idx": chunk_idx, "success": False, "error": str(e)}


async def smart_merge_segments(segments: list[dict]) -> str:
    """使用 LLM 智慧合併段落"""
    if not segments:
        return ""
    
    if len(segments) == 1:
        return segments[0].get("text", "")
    
    # 準備合併資料
    merge_data = []
    for i, seg in enumerate(segments):
        text = seg.get("text", "")
        if text:
            # 取前後各 50 字作為邊界
            merge_data.append({
                "idx": i,
                "full": text,
                "tail": text[-50:] if len(text) > 50 else text,
                "head": text[:50] if len(text) > 50 else text
            })
    
    if len(merge_data) <= 1:
        return merge_data[0]["full"] if merge_data else ""
    
    # 用 LLM 處理邊界
    merged_parts = [merge_data[0]["full"]]
    
    for i in range(1, len(merge_data)):
        prev_tail = merge_data[i-1]["tail"]
        curr_head = merge_data[i]["head"]
        curr_full = merge_data[i]["full"]
        
        prompt = f"""請檢查兩段語音轉錄的邊界是否有重疊或斷句問題，並提供修正後的第二段開頭。

第一段結尾：「{prev_tail}」
第二段開頭：「{curr_head}」

如果有重疊（相同的字詞出現在兩段），請移除第二段開頭重複的部分。
如果斷句不完整，請適當調整。
如果沒有問題，請回覆原本的第二段開頭。

只回覆修正後的第二段開頭文字，不要其他說明："""

        corrected_head = curr_head
        
        # 嘗試 LM Studio
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    Config.LM_STUDIO_URL,
                    json={
                        "model": Config.LM_STUDIO_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 100,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    corrected_head = response.json()["choices"][0]["message"]["content"].strip()
                    corrected_head = corrected_head.strip('「」"\'')
        except Exception:
            # Fallback 到 Gemini
            if genai:
                try:
                    response = genai.models.generate_content(
                        model=Config.GEMINI_MODEL,
                        contents=[prompt]
                    )
                    corrected_head = response.text.strip()
                    corrected_head = corrected_head.strip('「」"\'')
                except Exception:
                    pass
        
        # 替換開頭
        if corrected_head and corrected_head != curr_head:
            # 找到原本開頭在完整文字中的位置並替換
            if curr_full.startswith(curr_head):
                curr_full = corrected_head + curr_full[len(curr_head):]
        
        merged_parts.append(curr_full)
    
    return " ".join(merged_parts)


async def transcribe_with_whisper_batched(audio_path: Path) -> dict:
    """使用 MLX-Whisper 分段轉錄（循序處理避免 multiprocessing 衝突）"""
    if not check_whisper():
        return {"success": False, "error": "MLX-Whisper 未安裝。請執行: pip install mlx-whisper"}
    
    chunk_dir = None
    
    try:
        # 1. 分割音訊
        chunks = await split_audio(audio_path)
        is_chunked = len(chunks) > 1
        
        if is_chunked:
            chunk_dir = chunks[0].parent
        
        # 2. 循序轉錄（避免 ThreadPoolExecutor + MLX multiprocessing 衝突導致 semaphore 洩漏）
        results = []
        for i, chunk in enumerate(chunks):
            result = await transcribe_chunk(chunk, i)
            results.append(result)
        
        # 排序結果
        results = sorted(results, key=lambda x: x["idx"])
        
        # 3. 收集所有成功轉錄的段落（不做幻覺過濾）
        valid_segments = [r for r in results if r.get("success") and r.get("text")]
        
        # 4. 智慧合併
        if not valid_segments:
            return {
                "success": True,
                "transcript": "",
                "source": "whisper_local_batched",
                "model": Config.WHISPER_MODEL,
                "note": "音訊無明確語音內容（環境音/靜音）",
                "chunks_processed": len(chunks)
            }
        
        if len(valid_segments) == 1:
            final_text = valid_segments[0]["text"]
        else:
            final_text = await smart_merge_segments(valid_segments)
        
        return {
            "success": True,
            "transcript": final_text,
            "source": "whisper_local_batched",
            "model": Config.WHISPER_MODEL,
            "chunks_processed": len(chunks),
            "valid_chunks": len(valid_segments)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    finally:
        # 清理分割的片段
        if chunk_dir and chunk_dir.exists():
            shutil.rmtree(chunk_dir, ignore_errors=True)


async def transcribe_with_whisper(audio_path: Path, use_batch: bool = False) -> dict:
    """使用 MLX-Whisper 本地轉錄。預設整段處理；use_batch=True 時長音檔才分段。"""
    if use_batch:
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)]
            stdout, _ = run_command(cmd)
            duration = float(stdout.strip())
            if duration > CHUNK_DURATION:
                return await transcribe_with_whisper_batched(audio_path)
        except Exception:
            pass

    if not check_whisper():
        return {"success": False, "error": "MLX-Whisper 未安裝。請執行: pip install mlx-whisper"}
    
    try:
        import mlx_whisper
        
        result = mlx_whisper.transcribe(
            str(audio_path),
            path_or_hf_repo=Config.WHISPER_MODEL,
            language=Config.WHISPER_LANGUAGE
        )
        
        transcript = result["text"].strip()
        
        return {
            "success": True,
            "transcript": transcript,
            "source": "whisper_local",
            "model": Config.WHISPER_MODEL
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def transcribe_audio(audio_path: Path, mode: str = MODE_LOCAL, use_batch: bool = False) -> dict:
    """智慧轉錄。預設 local Whisper 整段；use_batch=True 可選分段。"""
    def _run_whisper():
        return transcribe_with_whisper(audio_path, use_batch=use_batch)

    if mode == MODE_ONLINE:
        if genai:
            result = await transcribe_with_gemini(audio_path)
            if result["success"]:
                if "無語音內容" in result.get("transcript", ""):
                    result["note"] = "音訊無明確語音內容"
                    result["transcript"] = ""
                return result
        return {"success": False, "error": "Gemini API key 未設定"}

    result = await _run_whisper()
    if result["success"]:
        return result
    if mode == MODE_LOCAL:
        result["error"] = f"Whisper 失敗（local 模式不使用 Gemini）: {result.get('error', '')}"
        return result
    if mode == MODE_DEFAULT and genai:
        result = await transcribe_with_gemini(audio_path)
        if result["success"]:
            if "無語音內容" in result.get("transcript", ""):
                result["note"] = "音訊無明確語音內容"
                result["transcript"] = ""
            return result
    return {"success": False, "error": "Whisper 和 Gemini 都失敗"}


# ============= 檔名建議 =============

def parse_location(location_str: str) -> tuple[float, float] | None:
    """解析 GPS 座標"""
    if not location_str:
        return None
    import re
    matches = re.findall(r"([+-]?\d+\.?\d*)", location_str)
    if len(matches) >= 2:
        return float(matches[0]), float(matches[1])
    return None


async def generate_rename_with_llm(
    frames: list[Path],
    metadata: dict,
    transcript: str = "",
    mode: str = MODE_DEFAULT
) -> dict:
    """使用 LLM 多模態生成檔名建議（根據模式選擇策略）"""
    import re
    from datetime import datetime
    
    # 準備資訊
    original_name = metadata.get("filename", "unknown")
    original_parts = re.findall(r"\d+|[A-Z]+\d+", original_name.rsplit(".", 1)[0], re.I)
    original_id = original_parts[0] if original_parts else original_name.rsplit(".", 1)[0][:10]
    
    # 年月
    date_str = ""
    if metadata.get("creation_time"):
        try:
            dt = datetime.fromisoformat(metadata["creation_time"].replace("Z", "+00:00"))
            date_str = f"{dt.year}{dt.month:02d}"
        except ValueError:
            pass
    
    # GPS 座標
    gps_info = ""
    if metadata.get("location"):
        loc = parse_location(metadata["location"])
        if loc:
            gps_info = f"GPS 座標: {loc[0]:.4f}, {loc[1]:.4f}"
    
    prompt = f"""根據以下圖片和資訊，為這個影片/圖片建議一個檔案名稱。

**原始編號**: {original_id}
**拍攝年月**: {date_str or "未知"}
**{gps_info}** (請根據 GPS 推測地點名稱)
**音訊內容**: {transcript[:200] if transcript else "無語音/環境音"}

請按照以下格式回覆，只回覆一行檔名，不要其他說明：
{original_id}_{date_str}_地點簡稱_活動描述

規則：
1. 保留原始編號 ({original_id})
2. 年月格式 YYYYMM (如 {date_str or "202601"})
3. 地點簡稱：2-8 個字，如「北海道」「台北101」「日本鄉村」
4. 活動描述：2-10 個字，如「稻田散步」「家庭聚餐」「演唱會」
5. 用底線 _ 連接各部分
6. 不要副檔名
7. 不要使用特殊字元（只用中英文、數字、底線）
8. 檔名中的中文請一律使用繁體中文（台灣用字）

範例：
7096_202506_北海道美瑛_稻田散步
IMG1234_202401_台北101_跨年煙火"""

    image_contents = []
    for frame in frames[:3]:  # 最多 3 張圖
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_to_base64(frame)}"}
        })
    
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            *image_contents
        ]
    }]
    
    def clean_response(raw_name: str) -> str:
        clean_name = raw_name.split("\n")[0].strip()
        clean_name = re.sub(r'^[`"\']|[`"\']$', '', clean_name)
        clean_name = re.sub(r'[\/\\:*?"<>|]', '_', clean_name)
        return clean_name
    
    # online 模式：直接用 Gemini
    if mode == MODE_ONLINE:
        if genai:
            try:
                from google.genai import types
                contents = [prompt]
                for frame in frames[:3]:
                    with open(frame, "rb") as f:
                        contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))
                response = genai.models.generate_content(model=Config.GEMINI_MODEL, contents=contents)
                return {"success": True, "source": "gemini", "suggestion": clean_response(response.text)}
            except Exception:
                pass
        return {"success": False, "error": "Gemini API key 未設定"}
    
    # default / local 模式：先嘗試 LM Studio
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                Config.LM_STUDIO_URL,
                json={
                    "model": Config.LM_STUDIO_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 100,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_name = data["choices"][0]["message"]["content"].strip()
                return {"success": True, "source": "lm_studio", "suggestion": clean_response(raw_name)}
    except Exception:
        pass
    
    # default 模式：Fallback 到 Gemini
    if mode == MODE_DEFAULT and genai:
        try:
            from google.genai import types
            contents = [prompt]
            for frame in frames[:3]:
                with open(frame, "rb") as f:
                    contents.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))
            response = genai.models.generate_content(model=Config.GEMINI_MODEL, contents=contents)
            return {"success": True, "source": "gemini", "suggestion": clean_response(response.text)}
        except Exception:
            pass
    
    # local 模式失敗
    if mode == MODE_LOCAL:
        return {"success": False, "error": "LM Studio 連線失敗（local 模式不使用 Gemini）"}
    
    return {"success": False}


async def generate_audio_rename_with_llm(
    metadata: dict,
    transcript: str = "",
    mode: str = MODE_DEFAULT
) -> dict:
    """使用 LLM 為音檔生成檔名建議"""
    import re
    from datetime import datetime
    
    original_name = metadata.get("filename", "unknown")
    original_parts = re.findall(r"\d+|[A-Z]+\d+", original_name.rsplit(".", 1)[0], re.I)
    original_id = original_parts[0] if original_parts else original_name.rsplit(".", 1)[0][:10]
    
    # 從 metadata 取得資訊
    title = metadata.get("title", "")
    artist = metadata.get("artist", "")
    album = metadata.get("album", "")
    duration = metadata.get("duration", 0)
    
    prompt = f"""根據以下音檔資訊，建議一個檔案名稱。

**原始編號**: {original_id}
**時長**: {format_timestamp(duration)}
**標題**: {title or "無"}
**演出者**: {artist or "無"}
**專輯**: {album or "無"}
**轉錄內容**: {transcript[:300] if transcript else "無語音/環境音"}

請按照以下格式回覆，只回覆一行檔名，不要其他說明：
{original_id}_主題描述_類型或來源

規則：
1. 保留原始編號 ({original_id})
2. 主題描述：2-15 個字，描述音檔內容（如「會議記錄」「英文教學」「鋼琴演奏」）
3. 類型或來源：2-8 個字（如「講座」「訪談」「歌曲」「Podcast」）
4. 用底線 _ 連接各部分
5. 不要副檔名
6. 不要使用特殊字元（只用中英文、數字、底線）
7. 檔名中的中文請一律使用繁體中文（台灣用字）

範例：
001_專案進度報告_會議記錄
podcast_AI未來發展_訪談
rec_英文發音練習_教學"""

    messages = [{
        "role": "user",
        "content": prompt
    }]
    
    # online 模式：直接用 Gemini
    if mode == MODE_ONLINE:
        if genai:
            try:
                response = genai.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents=[prompt]
                )
                raw_name = response.text.strip()
                clean_name = raw_name.split("\n")[0].strip()
                clean_name = re.sub(r'^[`"\']|[`"\']$', '', clean_name)
                clean_name = re.sub(r'[\/\\:*?"<>|]', '_', clean_name)
                return {"success": True, "source": "gemini", "suggestion": clean_name}
            except Exception:
                pass
        return {"success": False, "error": "Gemini API key 未設定"}
    
    # default / local 模式：先嘗試 LM Studio
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                Config.LM_STUDIO_URL,
                json={
                    "model": Config.LM_STUDIO_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 100,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_name = data["choices"][0]["message"]["content"].strip()
                clean_name = raw_name.split("\n")[0].strip()
                clean_name = re.sub(r'^[`"\']|[`"\']$', '', clean_name)
                clean_name = re.sub(r'[\/\\:*?"<>|]', '_', clean_name)
                return {"success": True, "source": "lm_studio", "suggestion": clean_name}
    except Exception:
        pass
    
    # default 模式：Fallback 到 Gemini
    if mode == MODE_DEFAULT and genai:
        try:
            response = genai.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=[prompt]
            )
            raw_name = response.text.strip()
            clean_name = raw_name.split("\n")[0].strip()
            clean_name = re.sub(r'^[`"\']|[`"\']$', '', clean_name)
            clean_name = re.sub(r'[\/\\:*?"<>|]', '_', clean_name)
            return {"success": True, "source": "gemini", "suggestion": clean_name}
        except Exception:
            pass
    
    # local 模式失敗
    if mode == MODE_LOCAL:
        return {"success": False, "error": "LM Studio 連線失敗（local 模式不使用 Gemini）"}
    
    return {"success": False}


def generate_rename_fallback(metadata: dict, original_name: str) -> str:
    """Fallback：簡單規則生成檔名"""
    import re
    from datetime import datetime
    
    parts = []
    
    # 原始編號
    original_parts = re.findall(r"\d+|[A-Z]+\d+", original_name.rsplit(".", 1)[0], re.I)
    if original_parts:
        parts.append(original_parts[0])
    else:
        parts.append(original_name.rsplit(".", 1)[0][:10])
    
    # 年月
    if metadata.get("creation_time"):
        try:
            dt = datetime.fromisoformat(metadata["creation_time"].replace("Z", "+00:00"))
            parts.append(f"{dt.year}{dt.month:02d}")
        except ValueError:
            pass
    
    ext = Path(original_name).suffix
    return "_".join(parts) + ext


# ============= MCP Server =============

server = Server("mcp-media-analyzer")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="analyze",
            description="分析影片、圖片或音檔，自動偵測類型。回傳：視覺內容分析、metadata、音訊轉錄、建議檔名。預設 local Whisper 整段轉錄；可選 use_batch 分段。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "檔案路徑"
                    },
                    "query": {
                        "type": "string",
                        "description": "自訂詢問（可選）"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["default", "local", "online"],
                        "description": "分析模式：local=只用本地 Whisper（預設）, default=本地+Gemini fallback, online=只用 Gemini"
                    },
                    "use_batch": {
                        "type": "boolean",
                        "description": "音訊轉錄是否分段處理。預設 false（整段）；長音檔可設 true 以分段轉錄",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """執行工具"""
    if name == "analyze":
        return await tool_analyze(arguments)
    return [TextContent(type="text", text=f"未知的工具: {name}")]


async def get_audio_metadata(audio_path: Path) -> dict:
    """取得音檔 metadata"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(audio_path)
    ]
    try:
        stdout, _ = run_command(cmd)
        data = json.loads(stdout)
        
        format_info = data.get("format", {})
        streams = data.get("streams", [])
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
        tags = format_info.get("tags", {})
        
        return {
            "filename": audio_path.name,
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
            "format": format_info.get("format_name", "unknown"),
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": audio_stream.get("sample_rate"),
            "channels": audio_stream.get("channels"),
            "bit_rate": format_info.get("bit_rate"),
            "title": tags.get("title"),
            "artist": tags.get("artist"),
            "album": tags.get("album"),
        }
    except Exception:
        stat = audio_path.stat()
        return {
            "filename": audio_path.name,
            "duration": 0,
            "size": stat.st_size,
            "format": audio_path.suffix[1:],
            "codec": "unknown",
        }


async def tool_analyze(args: dict) -> list[TextContent]:
    """analyze 工具實作"""
    file_path = resolve_path(args["file_path"])
    query = args.get("query")
    include_transcript = args.get("include_transcript", True)
    mode = args.get("mode", MODE_LOCAL)
    use_batch = args.get("use_batch", False)
    
    if not file_path.exists():
        return [TextContent(type="text", text=f"錯誤：找不到檔案 {file_path}")]
    
    file_type = get_file_type(file_path)
    
    if file_type == "unknown":
        return [TextContent(type="text", text=f"錯誤：不支援的檔案格式 {file_path.suffix}")]
    
    # 模式提示
    mode_desc = {"default": "預設（本地優先）", "local": "本地模式", "online": "線上模式"}
    
    # === 音檔分析 ===
    if file_type == "audio":
        if not check_ffmpeg():
            return [TextContent(type="text", text="錯誤：系統未安裝 ffmpeg")]
        
        results = []
        
        try:
            # Metadata
            metadata = await get_audio_metadata(file_path)
            results.append(f"## 音檔資訊\n")
            results.append(f"- **檔案**: {metadata['filename']}")
            results.append(f"- **時長**: {format_timestamp(metadata['duration'])}")
            results.append(f"- **格式**: {metadata['format']}")
            results.append(f"- **編碼**: {metadata['codec']}")
            if metadata.get("sample_rate"):
                results.append(f"- **取樣率**: {metadata['sample_rate']} Hz")
            if metadata.get("bit_rate"):
                results.append(f"- **位元率**: {int(metadata['bit_rate']) // 1000} kbps")
            if metadata.get("title"):
                results.append(f"- **標題**: {metadata['title']}")
            if metadata.get("artist"):
                results.append(f"- **演出者**: {metadata['artist']}")
            results.append(f"- **模式**: {mode_desc.get(mode, mode)}")
            results.append("")
            
            # 轉錄
            results.append("## 音訊轉錄\n")
            transcription = await transcribe_audio(file_path, mode, use_batch=use_batch)
            
            transcript_content = ""
            if transcription["success"]:
                transcript_content = transcription["transcript"]
                source = transcription["source"]
                model_name = transcription.get("model", "")
                results.append(f"**轉錄來源**: {source}{f' ({model_name})' if model_name else ''}\n")
                
                if transcription.get("note"):
                    results.append(f"*{transcription['note']}*")
                elif transcript_content:
                    results.append(transcript_content)
                else:
                    results.append("*無語音內容*")
            else:
                results.append(f"轉錄失敗: {transcription['error']}")
            results.append("")
            
            if transcript_content and len(transcript_content.strip()) > 0:
                results.append("## 後續建議（Agent TODO）\n")
                results.append("請依據上述逐字稿內容進行**校稿**與**排版**。\n")
                results.append("")
            
            # 建議檔名（使用 LLM）
            results.append("## 建議檔名\n")
            rename_result = await generate_audio_rename_with_llm(metadata, transcript_content, mode)
            
            if rename_result["success"]:
                ext = file_path.suffix
                suggestion = rename_result["suggestion"]
                if not suggestion.lower().endswith(ext.lower()):
                    suggestion += ext
                results.append(f"**來源**: {rename_result['source']}")
                results.append(f"\n`{suggestion}`")
            else:
                # Fallback 到簡單規則
                import re
                parts = []
                original_parts = re.findall(r"\d+|[A-Z]+\d+", file_path.stem, re.I)
                if original_parts:
                    parts.append(original_parts[0])
                else:
                    parts.append(file_path.stem[:10])
                if metadata.get("title"):
                    parts.append(re.sub(r'[\/\\:*?"<>|]', '_', metadata["title"])[:20])
                suggestion = "_".join(parts) + file_path.suffix
                results.append(f"**來源**: fallback（LLM 不可用）")
                results.append(f"\n`{suggestion}`")
            
            # 儲存報告（只在有語音內容時）
            report_content = "\n".join(results)
            if transcript_content and len(transcript_content.strip()) > 0:
                report_path = file_path.parent / f"{file_path.stem}.md"
                report_path.write_text(f"# {file_path.name} 分析報告\n\n{report_content}", encoding="utf-8")
                results.append(f"\n\n---\n**報告已儲存**: `{report_path}`")
            
            return [TextContent(type="text", text="\n".join(results))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"分析錯誤: {e}")]
    
    # === 影片分析 ===
    if file_type == "video":
        if not check_ffmpeg():
            return [TextContent(type="text", text="錯誤：系統未安裝 ffmpeg")]
        
        results = []
        frame_dir = None
        
        try:
            # Metadata
            metadata = await get_video_metadata(file_path)
            results.append("## 影片資訊\n")
            results.append(f"- **檔案**: {metadata['filename']}")
            results.append(f"- **時長**: {format_timestamp(metadata['duration'])}")
            results.append(f"- **解析度**: {metadata['video']['width']}x{metadata['video']['height']}")
            results.append(f"- **格式**: {metadata['format']}")
            if metadata.get("creation_time"):
                results.append(f"- **拍攝時間**: {metadata['creation_time']}")
            if metadata.get("location"):
                loc = parse_location(metadata["location"])
                results.append(f"- **拍攝地點**: {f'{loc[0]}, {loc[1]}' if loc else metadata['location']}")
            results.append(f"- **模式**: {mode_desc.get(mode, mode)}")
            results.append("")
            
            # 截取畫面
            results.append("## 視覺分析\n")
            frames, frame_dir = await extract_frames(file_path)
            
            # 分析（根據模式）
            analysis = await analyze_frames(frames, query, mode)
            analysis_content = ""
            if analysis and analysis.get("success", True):
                results.append(f"**分析來源**: {analysis['source']} ({analysis['model']})\n")
                results.append(analysis["content"])
                analysis_content = analysis["content"]
            elif analysis and analysis.get("error"):
                results.append(f"**分析失敗**: {analysis['error']}")
            else:
                results.append("**注意**: 視覺分析不可用")
            results.append("")
            
            # 音訊轉錄
            transcript_content = ""
            if include_transcript:
                results.append("## 音訊轉錄\n")
                try:
                    audio_path = await extract_audio(file_path)
                    transcription = await transcribe_audio(audio_path, mode, use_batch=use_batch)
                    
                    if transcription["success"]:
                        transcript_content = transcription["transcript"]
                        source = transcription["source"]
                        model_name = transcription.get("model", "")
                        results.append(f"**轉錄來源**: {source}{f' ({model_name})' if model_name else ''}\n")
                        
                        if transcription.get("note"):
                            results.append(f"*{transcription['note']}*")
                        elif transcript_content:
                            results.append(transcript_content)
                        else:
                            results.append("*無語音內容*")
                    else:
                        results.append(f"轉錄失敗: {transcription['error']}")
                    
                    audio_path.unlink(missing_ok=True)
                except Exception as e:
                    results.append(f"轉錄錯誤: {e}")
                results.append("")
                if transcript_content and len(transcript_content.strip()) > 0:
                    results.append("## 後續建議（Agent TODO）\n")
                    results.append("請依據上述逐字稿內容進行**校稿**與**排版**。\n")
                    results.append("")
            
            # 建議檔名（使用 LLM）
            results.append("## 建議檔名\n")
            rename_result = await generate_rename_with_llm(frames, metadata, transcript_content, mode)
            
            if rename_result["success"]:
                ext = file_path.suffix
                suggestion = rename_result["suggestion"]
                if not suggestion.lower().endswith(ext.lower()):
                    suggestion += ext
                results.append(f"**來源**: {rename_result['source']}")
                results.append(f"\n`{suggestion}`")
            else:
                suggestion = generate_rename_fallback(metadata, file_path.name)
                results.append(f"**來源**: fallback（LLM 不可用）")
                results.append(f"\n`{suggestion}`")
            
            # 儲存報告（只在有語音內容時）
            report_content = "\n".join(results)
            has_valid_transcript = transcript_content and len(transcript_content.strip()) > 0
            
            if has_valid_transcript or analysis_content:
                report_path = file_path.parent / f"{file_path.stem}.md"
                report_path.write_text(f"# {file_path.name} 分析報告\n\n{report_content}", encoding="utf-8")
                results.append(f"\n\n---\n**報告已儲存**: `{report_path}`")
            
            return [TextContent(type="text", text="\n".join(results))]
            
        finally:
            if frame_dir and frame_dir.exists():
                shutil.rmtree(frame_dir, ignore_errors=True)
    
    # === 圖片分析 ===
    if file_type == "image":
        processed_path = file_path
        needs_cleanup = False
        
        try:
            # 轉檔 + 縮圖
            processed_path, needs_cleanup, was_converted = await convert_and_resize_image(file_path)
            
            results = []
            
            # Metadata
            metadata = await get_image_metadata(file_path)
            results.append("## 圖片資訊\n")
            results.append(f"- **檔案**: {metadata['filename']}")
            if metadata["width"] and metadata["height"]:
                results.append(f"- **解析度**: {metadata['width']}x{metadata['height']}")
            results.append(f"- **格式**: {metadata['format']}")
            results.append(f"- **大小**: {metadata['size'] / 1024:.1f} KB")
            if metadata.get("creation_time"):
                results.append(f"- **建立時間**: {metadata['creation_time']}")
            if was_converted:
                results.append(f"- **處理**: 已從 {file_path.suffix} 轉換為 JPG")
            results.append(f"- **模式**: {mode_desc.get(mode, mode)}")
            results.append("")
            
            # 分析（根據模式）
            results.append("## 圖片分析\n")
            analysis = await analyze_single_image(processed_path, query, mode)
            
            analysis_content = ""
            if analysis and analysis.get("success"):
                results.append(f"**分析來源**: {analysis['source']} ({analysis['model']})\n")
                results.append(analysis["content"])
                analysis_content = analysis["content"]
            elif analysis and analysis.get("error"):
                results.append(f"**分析失敗**: {analysis['error']}")
            else:
                results.append("**分析失敗**: 視覺分析不可用")
            
            # 建議檔名（使用 LLM）
            results.append("\n## 建議檔名\n")
            rename_result = await generate_rename_with_llm([processed_path], metadata, "", mode)
            
            if rename_result["success"]:
                ext = file_path.suffix
                suggestion = rename_result["suggestion"]
                if not suggestion.lower().endswith(ext.lower()):
                    suggestion += ext
                results.append(f"**來源**: {rename_result['source']}")
                results.append(f"\n`{suggestion}`")
            else:
                suggestion = generate_rename_fallback(metadata, file_path.name)
                results.append(f"**來源**: fallback（LLM 不可用）")
                results.append(f"\n`{suggestion}`")
            
            # 儲存報告（只在有分析內容時）
            report_content = "\n".join(results)
            if analysis_content:
                report_path = file_path.parent / f"{file_path.stem}.md"
                report_path.write_text(f"# {file_path.name} 分析報告\n\n{report_content}", encoding="utf-8")
                results.append(f"\n\n---\n**報告已儲存**: `{report_path}`")
            
            return [TextContent(type="text", text="\n".join(results))]
            
        finally:
            if needs_cleanup and processed_path.exists():
                processed_path.unlink(missing_ok=True)


async def run_server():
    """啟動 MCP Server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """主程式進入點"""
    import sys
    print("MCP Video Analyzer server started", file=sys.stderr)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
