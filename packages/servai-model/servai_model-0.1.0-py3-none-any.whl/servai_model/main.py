import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from fastapi.responses import JSONResponse

import librosa
import numpy as np
import tempfile
import os
import logging
from servai_model.utils.logger import setup_logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

from servai_model.utils.utils import load_and_process, list_wav_files
from servai_model.core.embedding import SpeakerEmbedding, centroid_L2
from servai_model.core.similarity import is_same_speaker
from servai_model.core.config import WHISPER_MODEL_NAME, get_active_model_config

from pyngrok import ngrok
os.environ["NGROK_UPDATE"] = "false"
os.environ["NGROK_DEBUG"] = "false"

REF_FOLDER = "resources/audio_source"
THRESHOLD = 0.60

app = FastAPI(title="Speaker Verification API")

# Whisper 백엔드 자동 감지 및 초기화
def init_whisper():
    # CUDA 확인
    try:
        import torch
        if torch.cuda.is_available():
            import whisper
            model = whisper.load_model(WHISPER_MODEL_NAME, device="cuda")
            logger.info(f"Whisper CUDA 백엔드 사용: {WHISPER_MODEL_NAME}")
            # CUDA용 래퍼: model 인자가 들어오면 제거
            return lambda path, **kwargs: {"text": model.transcribe(path, **{k:v for k,v in kwargs.items() if k != 'model'})["text"]}
    except (ImportError, Exception):
        pass
    
    # MPS (MLX) 확인
    try:
        import mlx.core as mx
        from whisper_mps.whisper.transcribe import transcribe, ModelHolder
        
        ModelHolder.get_model(WHISPER_MODEL_NAME, dtype=mx.float16)
        logger.info(f"Whisper MPS 백엔드 사용: {WHISPER_MODEL_NAME}")
        
        # MPS용 래퍼: model 인자가 없으면 "small"을 기본값으로 사용
        def mps_transcribe_wrapper(path, **kwargs):
            if "model" not in kwargs:
                kwargs["model"] = WHISPER_MODEL_NAME
            return transcribe(path, **kwargs)
            
        return mps_transcribe_wrapper
    except (ImportError, OSError, Exception):
        pass
    
    # CPU 기본값
    import whisper
    model = whisper.load_model(WHISPER_MODEL_NAME, device="cpu")
    logger.info(f"Whisper CPU 백엔드 사용: {WHISPER_MODEL_NAME}")
    # CUDA/CPU용 래퍼: model 인자가 들어오면 제거 (Whisper 모델 객체의 transcribe는 model 인자를 안 받음)
    return lambda path, **kwargs: {"text": model.transcribe(path, **{k:v for k,v in kwargs.items() if k != 'model'})["text"]}

transcribe_func = init_whisper()




@app.post("/verify")
async def verify_speaker(audio_stream: UploadFile = File(...), ref_embedding_vector: str = Form(...)):
    """
    업로드된 음성이 제공된 기준 화자 임베딩(ref_embedding_vector)과 동일한지 판정 + Whisper STT
    (화자 분리 로직 적용: 모듈화된 함수 사용)
    """
    try:
        from servai_model.core.speaker_analysis import estimate_speaker_count, diarize_speakers, identify_owner
        import soundfile as sf
        from scipy.spatial.distance import cosine
        import json

        # 0) 기준 임베딩 파싱 (JSON String -> Numpy Array)
        try:
            emb_list = json.loads(ref_embedding_vector)
            ref_emb = np.array(emb_list)
        except Exception as e:
            logger.error(f"JSON String -> Numpy Array 임베딩 파싱 실패: {e}")
            return JSONResponse(status_code=400, content={"error": "Invalid ref_embedding format"})

        # 임시 파일 저장
        _, temp_path = tempfile.mkstemp(suffix=".wav")
        contents = await audio_stream.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        # -----------------------------
        # 1) 화자 분석 (Orchestration)
        # -----------------------------
        embedder = SpeakerEmbedding() # 모델 로드 (캐싱됨)
        
        # 현재 활성 모델의 설정 가져오기 (임계값 등)
        model_config, _ = get_active_model_config()
        current_similarity_threshold = model_config.get("similarity_threshold", 0.40) # 기본값 0.40

        # Step 1: 화자 수 측정
        count_result = estimate_speaker_count(
            wav_path=temp_path,
            embedder=embedder,
            similarity_threshold=current_similarity_threshold,
            vad_threshold=0.5
        )
        speaker_count = count_result["speaker_count"]
        
        segments = []
        similarity = 0.0
        
        # Step 2: 화자가 검출되지 않았을 때
        if speaker_count == 0:
            os.remove(temp_path)  # 임시 파일 정리
            return []

        elif speaker_count >= 2:
            # Step 2: 화자 분리 (다중 화자)
            diarized_segments = diarize_speakers(
                wav_path=temp_path,
                num_speakers=speaker_count,
                embedder=embedder
            )
            
            # Step 3: 화자 식별
            segments, similarity = identify_owner(
                wav_path=temp_path,
                segments=diarized_segments,
                ref_emb=ref_emb,
                embedder=embedder
            )
            
        else:
            # 단일 화자 처리
            # 전체 오디오 임베딩 추출하여 유사도 계산
            audio, sr = load_and_process(temp_path)
            emb = embedder.get_embedding(audio, sr)
            similarity = 1 - cosine(emb, ref_emb)
            
            total_duration = len(audio) / sr
            segments = [{
                "start": 0.0,
                "end": total_duration,
                "label": "OWNER", # 단일 화자는 일단 OWNER로 가정하고 유사도 반환
                "speaker": "SPEAKER_00",
                "similarity": similarity
            }]
            logger.info(f"단일 화자 유사도: {similarity:.3f}")

        # -----------------------------
        # 2) 전체 구간 STT (화자별 구분) 및 결과 구성
        # -----------------------------
        audio_data, sr = sf.read(temp_path)
        response_list = []
        
        for seg in segments:
            start_s = int(seg["start"] * sr)
            end_s = int(seg["end"] * sr)
            segment_audio = audio_data[start_s:end_s]
            
            if len(segment_audio) == 0:
                continue
                
            # STT용 임시 파일
            _, stt_temp_path = tempfile.mkstemp(suffix=".wav")
            sf.write(stt_temp_path, segment_audio, sr)
            
            seg_text = ""
            try:
                transcription = transcribe_func(stt_temp_path, verbose=False)
                seg_text = transcription["text"].strip()
            except Exception as e:
                logger.error(f"STT Error ({seg['label']}): {e}")
            finally:
                os.remove(stt_temp_path)
            
            if seg_text:
                # 결과 리스트에 추가
                response_list.append({
                    "similarity": float(f"{seg['similarity']:.4f}"),
                    "text": f"{seg_text}"
                })

        # 임시파일 삭제
        os.remove(temp_path)

        return response_list

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/register")
async def register_speaker(reference_audio: List[UploadFile] = File(...)):
    """
    여러 개의 음성 파일을 받아 화자 임베딩 벡터의 평균(Centroid) 리스트를 반환합니다.
    """
    try:
        embedder = SpeakerEmbedding()
        embeddings = []
        
        for file in reference_audio:
            # 임시 파일 저장
            _, temp_path = tempfile.mkstemp(suffix=".wav")
            try:
                contents = await file.read()
                with open(temp_path, "wb") as f:
                    f.write(contents)
                
                # 임베딩 추출
                audio, sr = load_and_process(temp_path)
                emb = embedder.get_embedding(audio, sr)
                embeddings.append(emb)
            
            except Exception as e:
                logger.error(f"파일 처리 중 오류 발생 ({file.filename}): {e}")
                continue
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if not embeddings:
            return JSONResponse(status_code=400, content={"error": "유효한 오디오 파일이 없습니다."})

        # Centroid 계산
        final_emb = centroid_L2(embeddings)

        # 저장 없이 바로 벡터 리스트 반환
        return final_emb.tolist()

    except Exception as e:
        logger.error(f"Register endpoint error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/test")
async def test_mock_endpoint(audio_stream: UploadFile = File(...)):
    """
    테스트용 목업 엔드포인트
    음성 파일을 받지만 실제 분석 없이 고정된 대화 데이터를 반환합니다.
    """
    return [
        {
            "text": "이번 프로젝트 마감 언제였지? 나 금요일로 알고 있는데",
            "similarity": 0.612
        },
        {
            "text": "아니야 다음 주 수요일까지야 아직 시간 좀 있어",
            "similarity": 0.154
        },
        {
            "text": "아 진짜? 다행이다 그럼 우리 다음주 금요일에 회식하는 거 어때?",
            "similarity": 0.589
        },
        {
            "text": "오 좋은데? 강남역 삼겹살집 가자 6시쯤?",
            "similarity": 0.121
        },
        {
            "text": "그래 좋아 안 그래도 고기 먹고 싶었는데",
            "similarity": 0.605
        },
        {
            "text": "다음주 금요일 오후 6시에 강남역 회식 일정 등록해줘",
            "similarity": 0.642
        }
    ]


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    PORT = 8000

    try:
        public_url = ngrok.connect(PORT, bind_tls=True)
        logger.info(f"ngrok 외부 접속 URL: {public_url.public_url}")
    except Exception as e:
        logger.error(f"ngrok 연결 실패: {e}")
        logger.info("로컬에서만 접속 가능합니다.")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
