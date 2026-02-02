"""
한글 자소 복원 라이브러리 (Jaso Jamo Decoder)
자음과 모음의 원리를 적용한 5단계 Fallback 방식

GitHub: https://github.com/yourusername/hangul-jamo
"""

from .core import (
    JasoJamoTokenizer,
    JasoJamoDecoder,
    tokenize,
    detokenize,
)

__version__ = "1.0.2"
__author__ = "김명환"
__all__ = [
    "JasoJamoTokenizer",
    "JasoJamoDecoder",
    "tokenize",
    "detokenize",
]
