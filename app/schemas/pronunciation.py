from pydantic import BaseModel
from typing import List, Optional

class PhonemeResult(BaseModel):
    phoneme: str
    accuracy_score: float

class SyllableResult(BaseModel):
    syllable: str
    accuracy_score: float
    gop: Optional[float] = None

class WordResult(BaseModel):
    word: str
    accuracy_score: float
    error_type: str
    syllables: List[SyllableResult] = []
    phonemes: List[PhonemeResult] = []

class PronunciationResponse(BaseModel):
    status: str
    reference_text: str
    pronunciation_score: float
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    raw_json: dict