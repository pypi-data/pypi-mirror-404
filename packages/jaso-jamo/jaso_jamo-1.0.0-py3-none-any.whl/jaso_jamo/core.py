from typing import List
from .JasoJamoTokenizer import JasoJamoTokenizer
from .JasoJamoDecoder import JasoJamoDecoder


def tokenize(text: str) -> List[str]:
    """텍스트를 자소로 분리"""
    tokenizer = JasoJamoTokenizer()
    return tokenizer.tokenize(text)


def detokenize(tokens: List[str], check_slang_mid=False) -> str:
    """자소를 한글로 복원
    
    Args:
        tokens: 자소 토큰 리스트
        check_slang_mid: 어절 중간 반복 자소 슬랭 처리 여부 (기본값: False)
    
    Returns:
        복원된 한글 텍스트
    """
    decoder = JasoJamoDecoder(check_slang_mid=check_slang_mid)
    return decoder.detokenize(tokens)
