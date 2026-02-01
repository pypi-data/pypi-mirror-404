import os

# 모델 설정 레지스트리
# 키(Key)는 사용자가 식별하기 쉬운 이름(별칭)을 사용합니다.
MODEL_REGISTRY = {
    "spkrec-ecapa-voxceleb": {
        "repo_id": "speechbrain/spkrec-ecapa-voxceleb",
        "savedir_name": "spkrec-ecapa-voxceleb",
        "files_to_download": [],
        "custom": False,
        "similarity_threshold": 0.40  # 기본 모델용 임계값
    },
    "FT_voxceleb_0104": {
        "repo_id": "ai-AnIma/FT_voxceleb_0104",  # 예시 레포 ID
        "savedir_name": "FT_voxceleb_0104",
        "files_to_download": ["custom_model.py", "embedding_model.ckpt"],
        "custom": True,
        "pymodule_file": "custom_model.py",
        "hparams_file": "hyperparams.yaml",
        "similarity_threshold": 0.50  # 튜닝 모델용 임계값 (더 엄격하거나 완화된 값 적용 가능)
    }
}

# ★ 현재 사용할 모델 선택 ★
ACTIVE_MODEL_KEY = "FT_voxceleb_0104"
# ACTIVE_MODEL_KEY = "spkrec-ecapa-voxceleb"


# 모델이 저장될 로컬 루트 디렉토리
# 환경 변수 SERVAI_MODEL_PATH가 있으면 해당 경로를 사용하고, 없으면 사용자 홈 디렉토리의 캐시 폴더를 사용합니다.
MODEL_SAVE_ROOT = os.getenv(
    "SERVAI_MODEL_PATH", 
    os.path.expanduser("~/.cache/servai_model/models")
)

# Whisper 모델 설정 (예: 'tiny', 'base', 'small', 'medium', 'large', 'large-v3')
WHISPER_MODEL_NAME = "large"

# 노이즈 보정 설정 (Beta 감산 방식)
# e_speaker' = Norm(e_speaker - NOISE_BETA * e_noise)
NOISE_BETA = 0.2

# VAD 설정 (Silero VAD 기반)
VAD_THRESHOLD = 0.4            # 음성 판정 감도 (낮을수록 민감)
VAD_MIN_SPEECH_MS = 250        # 최소 음성 지속 시간 (ms)
VAD_MIN_SILENCE_MS = 500       # 최소 침묵 지속 시간 (ms, 문장 병합에 영향)
VAD_SPEECH_PAD_MS = 100        # 음성 구간 전후 여유 시간 (ms)

def get_active_model_config():
    """현재 활성화된 모델의 이름과 설정을 반환합니다."""
    if ACTIVE_MODEL_KEY not in MODEL_REGISTRY:
        raise ValueError(f"지정된 모델 키 '{ACTIVE_MODEL_KEY}'가 레지스트리에 없습니다. 가능한 키: {list(MODEL_REGISTRY.keys())}")
    
    return MODEL_REGISTRY[ACTIVE_MODEL_KEY], ACTIVE_MODEL_KEY
