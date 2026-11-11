import whisper

# Load the Whisper model once at startup for better performance.
# You can choose sizes: "tiny", "base", "small", "medium".
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Whisper model loaded successfully!")

def transcribe_audio_with_whisper(audio_file_path: str) -> str:
    """Use local Whisper to translate Chinese speech audio into text."""
    result = model.transcribe(audio_file_path, language="zh")
    return result["text"].strip()