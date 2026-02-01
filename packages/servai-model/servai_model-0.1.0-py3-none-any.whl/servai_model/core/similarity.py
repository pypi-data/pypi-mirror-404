import numpy as np
from scipy.spatial.distance import cosine

def similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    emb1/emb2: 두 화자 임베딩
    """
    return 1 - cosine(emb1, emb2)

def is_same_speaker(emb1: np.ndarray, emb2: np.ndarray, threshold: float = 0.65):
    """
    emb1/emb2: 임베딩, threshold: 동일 화자 판정 기준
    """
    sim = similarity(emb1, emb2)
    return sim, sim > threshold
