"""
Speaker Analysis Module
기능별 모듈화: 화자 수 측정, 화자 분리, 화자 식별
"""
import os
import torch
import torchaudio
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import SpectralClustering
import librosa
import logging
from .embedding import SpeakerEmbedding
from .vad import detect_voice_activity_silero
from .config import (
    NOISE_BETA, 
    VAD_THRESHOLD, 
    VAD_MIN_SPEECH_MS, 
    VAD_MIN_SILENCE_MS, 
    VAD_SPEECH_PAD_MS
)

logger = logging.getLogger(__name__)

# =============================================================================
# Helper Functions
# =============================================================================

def load_wav_as_tensor(path: str) -> Tuple[torch.Tensor, int]:
    """WAV 파일 로드 및 전처리 (torchaudio 사용)"""
    signal, sr = torchaudio.load(path)
    
    if signal.shape[0] > 1:
        signal = torch.mean(signal, dim=0, keepdim=True)
    
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        signal = resampler(signal)
        sr = 16000
    
    return signal.squeeze(0), sr

def _extract_embedding_direct(signal: torch.Tensor, embedder: SpeakerEmbedding) -> np.ndarray:
    """SpeakerEmbedding 클래스를 사용하여 텐서에서 임베딩 추출"""
    audio_np = signal.numpy()
    return embedder.get_embedding(audio_np, 16000)

def extract_noise_embedding(signal: torch.Tensor, sr: int, voice_segments: List[Tuple[float, float]], embedder: SpeakerEmbedding) -> np.ndarray:
    """
    음성이 없는 구간(Non-Speech)을 추출하여 노이즈 임베딩 생성
    """
    audio_np = signal.numpy()
    noise_audio = []
    current_pos = 0
    total_len = len(audio_np)
    
    # 음성 구간 사이의 간격을 노이즈로 수집
    for start_t, end_t in voice_segments:
        s_idx = int(start_t * sr)
        e_idx = int(end_t * sr)
        if s_idx > current_pos:
            gap = audio_np[current_pos:s_idx]
            if len(gap) > int(0.1 * sr): # 0.1초 이상의 간격만 수집
                noise_audio.append(gap)
        current_pos = e_idx
    
    if current_pos < total_len:
        gap = audio_np[current_pos:]
        if len(gap) > int(0.1 * sr):
            noise_audio.append(gap)
            
    if not noise_audio:
        logger.warning("[Noise] Non-Speech 구간이 없어 보정 생략")
        return np.zeros(192) # 기본 임베딩 크기
        
    noise_combined = np.concatenate(noise_audio)
    e_noise = embedder.get_embedding(noise_combined, sr)
    
    # L2 정규화 (방향성만 유지)
    norm = np.linalg.norm(e_noise)
    if norm > 0:
        e_noise = e_noise / norm
        
    logger.info(f"[Noise] 노이즈 임베딩 추출 완료 (구간 합계: {len(noise_combined)/sr:.2f}초)")
    return e_noise

# =============================================================================
# Modular Functions
# =============================================================================

def estimate_speaker_count(
    wav_path: str,
    embedder: SpeakerEmbedding,
    window_length: float = 1.5,
    window_shift: float = 0.75,
    similarity_threshold: float = 0.40,
    vad_threshold: float = 0.5
) -> Dict:
    """
    Step 1: 화자 수 측정
    """
    logger.info(f"[Count] 분석 시작: {wav_path}")
    signal, sr = load_wav_as_tensor(wav_path)
    
    # VAD
    voice_segments = detect_voice_activity_silero(
        signal, 
        sr, 
        threshold=VAD_THRESHOLD,
        min_speech_duration_ms=VAD_MIN_SPEECH_MS,
        min_silence_duration_ms=VAD_MIN_SILENCE_MS,
        speech_pad_ms=VAD_SPEECH_PAD_MS
    )
    
    if not voice_segments:
        logger.info("  → 음성 구간 없음")
        return {"speaker_count": 0, "avg_similarity": 0.0, "is_single_speaker": False}
    
    # 임베딩 추출
    window_samples = int(window_length * sr)
    shift_samples = int(window_shift * sr)
    embeddings = []
    
    for voice_start, voice_end in voice_segments:
        voice_start_sample = int(voice_start * sr)
        voice_end_sample = int(voice_end * sr)
        voice_duration = voice_end - voice_start
        
        if voice_duration < window_length:
            segment = signal[voice_start_sample:voice_end_sample]
            if len(segment) < sr * 0.5: continue
            if len(segment) < window_samples:
                padding = torch.zeros(window_samples - len(segment))
                segment = torch.cat([segment, padding])
            embeddings.append(_extract_embedding_direct(segment, embedder))
        else:
            for start_sample in range(voice_start_sample, voice_end_sample - window_samples + 1, shift_samples):
                end_sample = min(start_sample + window_samples, voice_end_sample)
                segment = signal[start_sample:end_sample]
                if len(segment) < window_samples * 0.5: continue
                if len(segment) < window_samples:
                    padding = torch.zeros(window_samples - len(segment))
                    segment = torch.cat([segment, padding])
                embeddings.append(_extract_embedding_direct(segment, embedder))
    
    if not embeddings:
        return {"speaker_count": 0, "avg_similarity": 0.0, "is_single_speaker": False}
    
    embeddings = np.array(embeddings)
    
    # 유사도 계산
    if len(embeddings) == 1:
        avg_similarity = 1.0
    else:
        similarity_matrix = cosine_similarity(embeddings)
        avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
    
    is_single = avg_similarity > similarity_threshold
    speaker_count = 1 if is_single else 2
    
    logger.info(f"  → 평균 유사도: {avg_similarity:.3f}, 추정 화자 수: {speaker_count}")
    
    return {
        "speaker_count": speaker_count,
        "avg_similarity": float(avg_similarity),
        "is_single_speaker": is_single
    }

def diarize_speakers(
    wav_path: str,
    num_speakers: int,
    embedder: SpeakerEmbedding,
    window_length: float = 1.5,
    window_shift: float = 0.75
) -> List[Dict]:
    """
    Step 2: 화자 분리 (Spectral Clustering)
    """
    logger.info(f"[Diarize] 화자 분리 시작 ({num_speakers}명)")
    signal, sr = load_wav_as_tensor(wav_path)
    
    window_samples = int(window_length * sr)
    shift_samples = int(window_shift * sr)
    
    embeddings = []
    timestamps = []
    
    # 전체 구간에 대해 윈도우 슬라이딩
    for start_sample in range(0, len(signal) - window_samples, shift_samples):
        end_sample = start_sample + window_samples
        segment = signal[start_sample:end_sample]
        
        embeddings.append(_extract_embedding_direct(segment, embedder))
        timestamps.append({
            "start": start_sample / sr,
            "end": end_sample / sr
        })
    
    if not embeddings:
        return []
    
    embeddings = np.array(embeddings)
    
    # Spectral Clustering
    similarity_matrix = cosine_similarity(embeddings)
    similarity_matrix = (similarity_matrix + 1) / 2
    
    clustering = SpectralClustering(
        n_clusters=num_speakers,
        affinity='precomputed',
        random_state=42
    )
    labels = clustering.fit_predict(similarity_matrix)
    
    # 세그먼트 병합
    segments = []
    current_speaker = labels[0]
    current_start = timestamps[0]["start"]
    
    for i in range(1, len(labels)):
        if labels[i] != current_speaker:
            segments.append({
                "speaker": f"SPEAKER_{current_speaker:02d}",
                "start": current_start,
                "end": timestamps[i-1]["end"]
            })
            current_speaker = labels[i]
            current_start = timestamps[i]["start"]
            
    segments.append({
        "speaker": f"SPEAKER_{current_speaker:02d}",
        "start": current_start,
        "end": timestamps[-1]["end"]
    })
    
    logger.info(f"  → {len(segments)}개 세그먼트로 분리됨")
    return segments

def identify_owner(
    wav_path: str,
    segments: List[Dict],
    ref_emb: np.ndarray,
    embedder: SpeakerEmbedding
) -> Tuple[List[Dict], float]:
    """
    Step 3: 화자 식별 (OWNER/OTHER)
    Returns: (identified_segments, owner_similarity)
    """
    logger.info("[Identify] 화자 식별 시작")
    signal, sr = load_wav_as_tensor(wav_path)
    window_samples = int(1.5 * sr)
    
    # 화자별 임베딩 수집
    speaker_embeddings = {}
    
    for seg in segments:
        speaker = seg["speaker"]
        start_sample = int(seg["start"] * sr)
        end_sample = int(seg["end"] * sr)
        
        # 세그먼트 중간 1.5초 추출 (화자분리_테스트_1.py 로직)
        mid_point = (start_sample + end_sample) // 2
        seg_start = max(0, mid_point - window_samples // 2)
        seg_end = min(len(signal), seg_start + window_samples)
        
        segment = signal[seg_start:seg_end]
        if len(segment) < window_samples:
            padding = torch.zeros(window_samples - len(segment))
            segment = torch.cat([segment, padding])
        
        emb = _extract_embedding_direct(segment, embedder)
        
        if speaker not in speaker_embeddings:
            speaker_embeddings[speaker] = []
        speaker_embeddings[speaker].append(emb)
    
    # 노이즈 임베딩 추출 (보정용)
    voice_segments_for_noise = detect_voice_activity_silero(
        signal, 
        sr, 
        threshold=VAD_THRESHOLD,
        min_speech_duration_ms=VAD_MIN_SPEECH_MS,
        min_silence_duration_ms=VAD_MIN_SILENCE_MS,
        speech_pad_ms=VAD_SPEECH_PAD_MS
    )
    e_noise = extract_noise_embedding(signal, sr, voice_segments_for_noise, embedder)
    
    # 화자별 평균 임베딩 및 유사도 계산 (노이즈 보정 적용)
    speaker_similarities = {}
    for speaker, embs in speaker_embeddings.items():
        # 1. 원본 평균 임베딩
        avg_emb = np.mean(embs, axis=0)
        
        # 2. 노이즈 보정 적용: e' = Norm(e - Beta * e_noise)
        if np.any(e_noise):
            avg_emb = avg_emb - NOISE_BETA * e_noise
            norm = np.linalg.norm(avg_emb)
            if norm > 0:
                avg_emb = avg_emb / norm
        
        # 3. 보정된 임베딩으로 유사도 계산
        similarity = 1 - cosine(avg_emb, ref_emb)
        speaker_similarities[speaker] = similarity
        logger.info(f"  → {speaker} 유사도(보정후): {similarity:.3f}")
        
    if not speaker_similarities:
        return segments, 0.0
        
    owner_speaker = max(speaker_similarities, key=speaker_similarities.get)
    owner_similarity = speaker_similarities[owner_speaker]
    logger.info(f"  → OWNER 판정: {owner_speaker} (유사도: {owner_similarity:.3f})")
    for seg in segments:
        if seg["speaker"] == owner_speaker:
            logger.info(f"      - {seg['start']:.1f}s ~ {seg['end']:.1f}s")
    
    for spk, sim in speaker_similarities.items():
        if spk != owner_speaker:
            logger.info(f"  → OTHER 판정: {spk} (유사도: {sim:.3f})")
            for seg in segments:
                if seg["speaker"] == spk:
                    logger.info(f"      - {seg['start']:.1f}s ~ {seg['end']:.1f}s")
    
    identified_segments = []
    for seg in segments:
        new_seg = seg.copy()
        if seg["speaker"] == owner_speaker:
            new_seg["label"] = "OWNER"
        else:
            new_seg["label"] = "OTHER"
        
        new_seg["similarity"] = speaker_similarities.get(seg["speaker"], 0.0)
        identified_segments.append(new_seg)
        
    return identified_segments, owner_similarity

# Legacy support
def analyze_speaker(*args, **kwargs):
    pass
