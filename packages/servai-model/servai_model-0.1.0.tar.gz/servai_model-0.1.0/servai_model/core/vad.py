import numpy as np
import webrtcvad
import torch
from typing import List, Tuple
import logging


# Silero VAD 추가
_silero_vad_model = None
_silero_vad_utils = None

logger = logging.getLogger(__name__)


def apply_vad(audio: np.ndarray, sr: int, frame_ms: int = 20, level: int = 1) -> np.ndarray:
    """
    audio: 입력 오디오, sr: 샘플레이트, frame_ms: 프레임 크기, level: VAD 민감도
    """
    vad = webrtcvad.Vad(level)

    frame_len = int(sr * frame_ms / 1000)
    audio_int16 = (audio * 32767).astype(np.int16)

    voiced_frames = []
    for i in range(0, len(audio_int16), frame_len):
        frame = audio_int16[i:i+frame_len]
        if len(frame) < frame_len:
            break
        if vad.is_speech(frame.tobytes(), sr):
            voiced_frames.append(frame.astype(np.float32) / 32767.0)

    return np.concatenate(voiced_frames) if voiced_frames else audio



def load_silero_vad():
    """Silero VAD 모델 로드 (싱글톤)"""
    global _silero_vad_model, _silero_vad_utils
    
    if _silero_vad_model is not None:
        return _silero_vad_model, _silero_vad_utils
    
    logger.info("[VAD] Silero VAD 모델 로딩 중...")
    _silero_vad_model, _silero_vad_utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False,
        onnx=False,
        verbose=False
    )
    logger.info("[VAD] 로딩 완료!")
    return _silero_vad_model, _silero_vad_utils


def detect_voice_activity_silero(
    signal: torch.Tensor,
    sr: int = 16000,
    threshold: float = 0.5,
    min_speech_duration_ms: int = 250,
    min_silence_duration_ms: int = 100,
    speech_pad_ms: int = 30
) -> List[Tuple[float, float]]:
    """
    Silero VAD로 음성 구간 탐지
    
    Args:
        signal: 오디오 신호 (torch.Tensor)
        sr: 샘플레이트
        threshold: VAD 임계값 (0.0~1.0)
        min_speech_duration_ms: 최소 음성 지속 시간 (ms)
        min_silence_duration_ms: 최소 침묵 지속 시간 (ms)
        speech_pad_ms: 음성 구간 전후 여유 시간 (ms)
    
    Returns:
        List of (start_time, end_time) in seconds
    """
    model, utils = load_silero_vad()
    (get_speech_timestamps, _, _, _, _) = utils
    
    speech_timestamps = get_speech_timestamps(
        signal,
        model,
        threshold=threshold,
        sampling_rate=sr,
        min_speech_duration_ms=min_speech_duration_ms,
        min_silence_duration_ms=min_silence_duration_ms,
        speech_pad_ms=speech_pad_ms
    )
    
    voice_segments = [
        (ts['start'] / sr, ts['end'] / sr)
        for ts in speech_timestamps
    ]
    
    return voice_segments
