import os
import whisper

# FFmpeg PATH
FFMPEG_PATH = r"C:\Users\Shivansh jha\Downloads\ffmpeg-9.0.2-essentials_build\bin"
os.environ["PATH"] += os.pathsep + FFMPEG_PATH

# Whisper model
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None


def load_model():
    global _model

    if _model is None:
        print("Loading Whisper model...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded successfully.")

    return _model


def transcribe_chunk(
    chunk_path: str,
    translate: bool = False,
    language: str = None
) -> str:

    model = load_model()

    task = "translate" if translate else "transcribe"

    result = model.transcribe(
        chunk_path,
        task=task,
        language=language
    )

    return result["text"].strip()


def transcribe_all(
    chunks: list,
    translate: bool = False,
    language: str = None
) -> str:

    full_transcript = []

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        text = transcribe_chunk(
            chunk_path=chunk,
            translate=translate,
            language=language
        )

        full_transcript.append(text)

    print("Transcription completed.")

    return " ".join(full_transcript)