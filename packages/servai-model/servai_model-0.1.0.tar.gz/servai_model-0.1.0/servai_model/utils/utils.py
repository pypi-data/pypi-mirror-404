from typing import List
import os
import numpy as np
import librosa
import noisereduce as nr
import webrtcvad

def reduce_noise_general(audio, sr):
    """일반 생활 소음 제거"""
    return nr.reduce_noise(
        y=audio,
        sr=sr,
        prop_decrease=0.5,
        stationary=False
    )

def apply_vad(audio, sr, frame_ms=20):
    """음성 구간만 추출 (WebRTC VAD)"""
    vad = webrtcvad.Vad(1)
    frame_len = int(sr * frame_ms / 1000)
    
    audio_int16 = (audio * 32767).astype(np.int16)
    voiced_frames = []

    for i in range(0, len(audio_int16), frame_len):
        frame = audio_int16[i:i+frame_len]
        if len(frame) < frame_len:
            break
        if vad.is_speech(frame.tobytes(), sr):
            voiced_frames.append(frame.astype(np.float32) / 32767.0)

    if len(voiced_frames) == 0:
        return audio  # 음성 검출 실패 시 원본 반환

    return np.concatenate(voiced_frames)

def load_and_process(path: str):
    """파일 로드 → 노이즈 제거 → VAD로 음성만 추출"""
    audio, sr = librosa.load(path, sr=16000)

    noise_reduced = reduce_noise_general(audio, sr)
    voiced = apply_vad(noise_reduced, sr)

    return voiced, sr


def list_wav_files(directory: str) -> List[str]:
    """
    directory: 폴더 경로
    """
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".wav")
    ]