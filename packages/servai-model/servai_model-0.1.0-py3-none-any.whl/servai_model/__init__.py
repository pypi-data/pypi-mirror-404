from .core.embedding import SpeakerEmbedding, centroid_L2
from .core.speaker_analysis import estimate_speaker_count, diarize_speakers, identify_owner
from .core.config import NOISE_BETA, VAD_THRESHOLD

__version__ = "0.1.0"
__all__ = [
    "SpeakerEmbedding",
    "centroid_L2",
    "estimate_speaker_count",
    "diarize_speakers",
    "identify_owner",
    "NOISE_BETA",
    "VAD_THRESHOLD"
]
