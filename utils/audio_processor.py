import yt_dlp  # For downloading videos/audio from YouTube and supported websites
from pydub import AudioSegment  # For processing audio and converting to WAV
import os


# ------------------------- SETTINGS -------------------------

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Path to FFmpeg
FFMPEG_PATH = r"C:\Users\Shivansh jha\Downloads\ffmpeg-9.0.2-essentials_build\bin"


# ------------------------- DOWNLOAD YOUTUBE AUDIO -------------------------

def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",

        "outtmpl": output_path,

        # Tell yt-dlp exactly where FFmpeg and FFprobe are
        "ffmpeg_location": FFMPEG_PATH,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        filename = (
            ydl.prepare_filename(info)
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
        )

    return filename


# ------------------------- CONVERT TO WAV -------------------------

def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to WAV using Pydub.
    """

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)

    # Mono + 16 kHz → suitable for speech recognition
    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(
        output_path,
        format="wav"
    )

    return output_path


# ------------------------- CHUNK AUDIO -------------------------

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into smaller chunks.
    """

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):

        chunk = audio[
            start:start + chunk_ms
        ]

        chunk_path = (
            f"{wav_path}_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(chunk_path)

    return chunks


# ------------------------- PROCESS INPUT -------------------------

def process_input(source: str) -> list:

    # Check whether input is a YouTube/online URL
    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL. Downloading audio..."
        )

        wav_path = download_youtube_audio(source)

    else:

        print(
            "Detected local file. Converting to WAV..."
        )

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(
        f"Audio ready — {len(chunks)} chunk(s) created."
    )

    return chunks