import yt_dlp
from pydub import AudioSegment
import os
import subprocess
from pathlib import Path

DENO_EXE=r"C:\Users\suhan\AppData\Local\Microsoft\WinGet\Links\deno.exe"

DOWNLOAD_DIR = 'downloads'

os.makedirs(DOWNLOAD_DIR,exist_ok = True)

def download_youtube_audio(url: str) -> str:
    existing_wavs = [
        os.path.join(DOWNLOAD_DIR, file_name)
        for file_name in os.listdir(DOWNLOAD_DIR)
        if file_name.lower().endswith(".wav")
    ]

    if existing_wavs:
        print(f"Using existing WAV file: {existing_wavs[0]}")
        return existing_wavs[0]

    output_path = os.path.join(DOWNLOAD_DIR,
                                "%(title)s [%(id)s].%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,

        "js_runtimes": {
            "deno": {
                "paths": [DENO_EXE]
            }
        },

        "remote_components": ["ejs:github"],

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        "quiet": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return os.path.splitext(filename)[0] + ".wav"

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    wav_path = Path(wav_path)
    chunk_dir = wav_path.parent / f"{wav_path.stem}_chunks"
    chunk_dir.mkdir(exist_ok=True)

    output_pattern = str(chunk_dir / "chunk_%03d.wav")
    chunk_seconds = chunk_minutes * 60

    command = [
        "ffmpeg",
        "-y",
        "-i", str(wav_path),
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-segment_start_number", "0",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_pattern,
    ]

    print("Creating audio chunks with FFmpeg...")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg chunking failed:\n" + result.stderr
        )

    chunks = sorted(chunk_dir.glob("chunk_*.wav"))

    if not chunks:
        raise FileNotFoundError("FFmpeg did not create any audio chunks.")

    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return [str(chunk) for chunk in chunks]


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks