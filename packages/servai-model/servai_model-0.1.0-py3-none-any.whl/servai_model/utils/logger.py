import logging

def setup_logging():
    """
    로깅 설정 초기화
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 불필요한 외부 라이브러리 로그 억제
    loggers_to_silence = [
        "speechbrain",
        "pyngrok",
        "urllib3",
        "multipart",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "httpcore",
        "httpx"
    ]
    
    for logger_name in loggers_to_silence:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
        
    # SpeechBrain의 경우 별도의 핸들러가 있을 수 있으므로 전파 방지
    logging.getLogger("speechbrain").propagate = False
