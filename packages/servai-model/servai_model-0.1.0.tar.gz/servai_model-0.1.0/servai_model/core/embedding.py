import os
import sys
import numpy as np
import torch
from speechbrain.inference.classifiers import EncoderClassifier
from huggingface_hub import hf_hub_download
from servai_model.core.config import get_active_model_config, MODEL_SAVE_ROOT

class SpeakerEmbedding:
    """
    ECAPA 모델을 로드하고 오디오에서 임베딩을 추출합니다.
    src/core/config.py의 설정을 따릅니다.
    """

    _model_instance = None
    _current_model_key = None

    def __init__(self):
        """
        초기화 시 인자를 받지 않고 src/core/config.py의 설정을 따릅니다.
        """
        # Config에서 현재 활성화된 모델 정보 가져오기
        config, model_key = get_active_model_config()
        
        # 싱글톤 패턴: 이미 로드된 모델이 있고, 활성 모델이 같으면 재사용
        if SpeakerEmbedding._model_instance is not None and SpeakerEmbedding._current_model_key == model_key:
            self.model = SpeakerEmbedding._model_instance
            return

        print(f"[Info] SpeakerEmbedding 초기화: '{model_key}' ({config['repo_id']}) 사용")

        # 1. 저장 경로 설정 및 생성 (Config의 ROOT 사용)
        save_path = os.path.join(MODEL_SAVE_ROOT, config['savedir_name'])
        if not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
            print(f"[Info] 모델 저장 폴더 생성: {save_path}")

        # 2. Device 설정
        run_opts = self._get_device_opts()

        # 3. 커스텀 다운로드 (튜닝 모델용)
        if config.get("custom", False):
            self._download_custom_files(config['repo_id'], save_path, config.get("files_to_download", []))
            
            # 커스텀 모듈 인식을 위해 sys.path 추가
            abs_save_path = os.path.abspath(save_path)
            if abs_save_path not in sys.path:
                sys.path.append(abs_save_path)

            self.model = EncoderClassifier.from_hparams(
                source=config['repo_id'],
                savedir=save_path,
                pymodule_file=config.get("pymodule_file"),
                hparams_file=config.get("hparams_file"),
                run_opts=run_opts
            )
        else:
            # 기본 모델 로딩
            self.model = EncoderClassifier.from_hparams(
                source=config['repo_id'],
                savedir=save_path,
                run_opts=run_opts
            )
            
        # 싱글톤 인스턴스 업데이트
        SpeakerEmbedding._model_instance = self.model
        SpeakerEmbedding._current_model_key = model_key

    def _get_device_opts(self):
        if torch.backends.mps.is_available():
            return {"device": "mps"}
        elif torch.cuda.is_available():
            return {"device": "cuda"}
        return None

    def _download_custom_files(self, repo_id, save_path, files):
        try:
            for filename in files:
                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=save_path,
                    force_download=False 
                )
        except Exception as e:
            print(f"[Warning] HuggingFace 다운로드 실패: {e}")


    def get_embedding(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        audio: 오디오 신호, sr: 샘플레이트
        """
        signal = torch.tensor(audio).float().unsqueeze(0)
        emb = (
            self.model.encode_batch(signal)
            .squeeze()
            .detach()
            .cpu()
            .numpy()
        )
        return emb

def centroid_L2(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    embeddings: L2 정규화 후 평균한 대표 임베딩
    """
    norms = [e / np.linalg.norm(e) for e in embeddings]
    centroid = np.mean(norms, axis=0)
    return centroid / np.linalg.norm(centroid)

def centroid_average(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    embeddings: 단순 평균 (가중합)
    """
    return np.mean(embeddings, axis=0)

def centroid_median(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    embeddings: 성분별 중앙값
    """
    return np.median(embeddings, axis=0)

def select_medoid(embeddings: list[np.ndarray]) -> np.ndarray:
    """
    embeddings: 가장 중심에 위치한 대표 임베딩 선택
    """
    from scipy.spatial.distance import cosine

    sims = []
    for emb in embeddings:
        total_sim = sum(1 - cosine(emb, other) for other in embeddings)
        sims.append(total_sim)

    return embeddings[np.argmax(sims)]