import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.whisper_service import transcribe_audio_with_whisper
from app.services.comparison_service import compare_texts

router = APIRouter(prefix="/api/v1", tags=["Pronunciation"])

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/check-pronunciation")
async def check_pronunciation(
    audio: UploadFile = File(...),
    reference_text: str = Form(...)
):
    temp_input = None
    try:
        # 1. Lưu file audio tạm thời do client gửi lên
        file_ext = os.path.splitext(audio.filename)[1] or ".webm"
        temp_input = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{file_ext}")

        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 2. Gọi Whisper local để dịch âm thanh tiếng Trung thành text
        recognized_text = transcribe_audio_with_whisper(temp_input)

        # 3. So sánh chi tiết từng ký tự giữa câu gốc và câu đọc
        comparison_result = compare_texts(reference_text, recognized_text)

        # 4. Trả kết quả JSON về cho Frontend hiển thị
        return {
            "status": "success",
            "reference_text": reference_text,
            "recognized_text": recognized_text,
            "similarity_score": comparison_result["similarity_score"],
            "is_match": comparison_result["is_perfect_match"],
            "detailed_diff": comparison_result["detailed_diff"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 5. Dọn dẹp file tạm
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)