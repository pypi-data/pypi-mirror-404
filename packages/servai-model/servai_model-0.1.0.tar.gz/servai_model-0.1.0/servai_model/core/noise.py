import numpy as np
import noisereduce as nr

def reduce_noise_general(audio: np.ndarray, sr: int, prop_decrease: float = 0.5) -> np.ndarray:
    """
    audio: 입력 오디오, sr: 샘플레이트, prop_decrease: 노이즈 제거 강도
    """
    return nr.reduce_noise(
        y=audio,
        sr=sr,
        prop_decrease=prop_decrease,
        stationary=False
    )
