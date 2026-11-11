from pydub import AudioSegment

def convert_webm_to_wav(input_path: str, output_path: str) -> str:
    """
    Chuyển đổi file âm thanh sang chuẩn wav (16kHz, mono) cho Azure Speech SDK.
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")
    return output_path