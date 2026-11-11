import os
import shutil
import uuid
import difflib
import whisper
import av  # Use av to read audio without relying on ffmpeg being installed separately
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Pronunciation Check API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading Whisper model...")
model = whisper.load_model("base")
print("Whisper model loaded successfully!")

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def load_audio_with_av(file_path: str, sample_rate: int = 16000) -> np.ndarray:
    """Đọc file audio bằng thư viện av và chuyển về định dạng chuẩn 16kHz mono cho Whisper"""
    # Sử dụng 'with' để tự động đóng file container và giải phóng khóa file ngay khi đọc xong
    with av.open(file_path) as container:
        stream = container.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format='s16',
            layout='mono',
            rate=sample_rate
        )
        
        frames = []
        for frame in container.decode(stream):
            resampled_frames = resampler.resample(frame)
            for rf in resampled_frames:
                frames.append(rf.to_ndarray())
                
    if not frames:
        return np.array([], dtype=np.float32)
        
    audio_data = np.concatenate(frames, axis=1)
    audio_float = audio_data.astype(np.float32) / 32768.0
    return audio_float.flatten()

def compare_texts(reference: str, recognized: str) -> dict:
    ref_clean = reference.replace(" ", "")
    rec_clean = recognized.replace(" ", "")

    matcher = difflib.SequenceMatcher(None, ref_clean, rec_clean)
    similarity_score = matcher.ratio() * 100

    detailed_diff = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        ref_segment = ref_clean[i1:i2]
        rec_segment = rec_clean[j1:j2]
        
        if tag == 'equal':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "correct"})
        elif tag == 'replace':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "incorrect", "recognized_as": rec_segment})
        elif tag == 'delete':
            for char in ref_segment:
                detailed_diff.append({"char": char, "status": "missing"})
        elif tag == 'insert':
            for char in rec_segment:
                detailed_diff.append({"char": char, "status": "extra"})

    return {
        "similarity_score": round(similarity_score, 2),
        "is_perfect_match": (ref_clean == rec_clean),
        "detailed_diff": detailed_diff
    }

@app.get("/")
def read_root():
    return {"message": "API Check Lỗi Phát Âm Tiếng Trung (Whisper + PyAV) đang hoạt động!"}

@app.post("/api/v1/check-pronunciation")
async def check_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...)
):
    temp_input = None
    try:
        file_ext = os.path.splitext(audio.filename)[1] or ".webm"
        temp_input = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{file_ext}")

        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # Sử dụng hàm load_audio_with_av để đọc file qua thư viện av (Không cần ffmpeg.exe)
        audio_np = load_audio_with_av(temp_input)

        # Truyền mảng numpy trực tiếp vào model.transcribe
        result = model.transcribe(audio_np, language="zh")
        recognized_text = result["text"].strip()

        comparison = compare_texts(reference_text, recognized_text)

        return {
            "status": "success",
            "reference_text": reference_text,
            "recognized_text": recognized_text,
            "similarity_score": comparison["similarity_score"],
            "is_match": comparison["is_perfect_match"],
            "detailed_diff": comparison["detailed_diff"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )