from typing import List
from .JasoJamoTokenizer import JasoJamoTokenizer


class JasoJamoDecoder:
    """한글 자소 복원기 (5단계 Fallback 방식)

    자음과 모음의 특성을 기반으로 자소 토큰을 한글 음절로 복원합니다.

    알고리즘 원리:
        1. 안전장치(Safety Guard) 기반 반복 자소 슬랭 처리 (Lookahead 5)
           - 옵션: 문장 중간 반복 자소 슬랭 처리 여부 (check_slang_mid)
        2. 문맥 인식 선행 탐색 (Lookahead 4)
        3. 패턴 매칭 (3자 → 2자)
        4. 패턴 매칭 (2자)
        5. 실패 시 개별 토큰 유지

    Example:
        >>> decoder = JasoJamoDecoder()
        >>> tokens = ['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']
        >>> decoder.detokenize(tokens)
        '한글'
    """

    def __init__(self, check_slang_mid=False):
        """
        Args:
            check_slang_mid (bool): 문장 중간에 위치한 반복 자소 슬랭 처리 여부.
                                    True면 "바다ㄱㄱ네요"의 'ㄱㄱ'를 반복 자소 슬랭으로 처리.
                                    False면 오타(예: 학ㄴ교) 오탐지를 방지하기 위해 처리하지 않음 (기본값).
        """
        self.tokenizer = JasoJamoTokenizer()
        self.CHO = set(self.tokenizer.CHO)
        self.JUNG = set(self.tokenizer.JUNG)
        self.JONG = set(self.tokenizer.JONG[1:])  # 빈 종성 제외

        # 빠른 조회를 위한 딕셔너리
        self.CHO_MAP = {ch: i for i, ch in enumerate(self.tokenizer.CHO)}
        self.JUNG_MAP = {ch: i for i, ch in enumerate(self.tokenizer.JUNG)}
        self.JONG_MAP = {ch: i for i, ch in enumerate(self.tokenizer.JONG)}

        self.CONSONANTS = self.JONG | self.CHO  # 모든 자음
        self.check_slang_mid = check_slang_mid

    def detokenize(self, tokens: List[str]) -> str:
        """자소 토큰을 한글 텍스트로 복원"""
        # 입력 검증
        if not isinstance(tokens, (list, tuple)):
            return ""
        if not tokens:
            return ""

        # DoS 방지: 최대 토큰 수 제한
        MAX_TOKENS = 1000000
        if len(tokens) > MAX_TOKENS:
            tokens = tokens[:MAX_TOKENS]

        result = []
        i = 0
        n = len(tokens)
        word_eos = self._get_word_eos(tokens, i)

        while i < n:
            # 현재 토큰이 자소가 아니면 바로 추가
            if not self._is_jaso(tokens[i]):
                result.append(tokens[i])
                i += 1
                continue

            # [초음 종음]으로 시작하지 않으면 개별 토큰 (모음 단독 등)
            if not self._is_consonant(tokens[i]):
                result.append(tokens[i])
                i += 1
                continue
            
            if i > word_eos:
                word_eos = self._get_word_eos(tokens, i)
            
            # =================================================================
            # 1단계: 5개 패턴 확인 (반복 자소 슬랭 처리 + 안전장치)
            # =================================================================
            if i + 4 < word_eos:
                t0, t1, t2, t3, t4 = tokens[i:i+5]

                # [안전장치 1] 뒤따르는 3개 토큰(t2, t3, t4)이 모두 자음이고 자소여야 함
                # 목적: "학교(ㅎㅏㄱㄱㅕ)" 같은 정상 단어를 반복 자소 슬랭으로 오판하는 것 방지
                # 추가: "바다ㄱㄱ!가요" 같이 반복 자소 슬랭 뒤 비자소 문자가 있는 경우 반복 자소 슬랭으로 인식
                if (self._is_consonant(t0) and self._is_vowel(t1) and 
                    self._is_consonant(t2) and 
                    self._is_consonant(t3) and 
                    self._is_consonant(t4)):
                    
                    # [안전장치 2] 반복 자소 슬랭 처리 위치 결정 (연구 목적 옵션)
                    # check_slang_mid=False(기본): 문장/어절 끝에서만 반복 자소 슬랭 처리 (오타 방지)
                    # check_slang_mid=True: 중간 반복 자소 슬랭도 처리 (오타 위험 감수)
                    check_slang_mid = self.check_slang_mid
                    
                    # 자소5개 글자가 단어의 끝인지 확인
                    last_word = (i + 5 == word_eos)

                    if check_slang_mid or last_word:
                        # 1. 반복 자음 우선 처리 (예: 가요ㅋㅋ)
                        if t2 == t3 == t4: # 3개 반복
                            char = self._compose_jamos([t0, t1])
                            result.append(char)
                            i += 2 # t0, t1 처리. t2부터 슬랭 시작
                            continue
                
                        # 사전 반복 자소 슬랭은 유행어의 발전에 따라 달라 질 수 있다.
                        # 2. 3글자 사전 반복 자소 슬랭 (예: 가ㄱㄴㄹ)
                        if "".join(tokens[i+2 : i+5]) in self.tokenizer.SPECIAL_SLANG:
                            char = self._compose_jamos([t0, t1])
                            result.append(char)
                            i += 2 # t0, t1 처리. t2부터 반복 자소 슬랭 시작
                            continue

                        # 3. 자모자 + 2글자 사전 반복 자소 슬랭 (예: 각ㅁㅅ)
                        # t2를 종성으로 사용하고, t3부터 반복 자소 슬랭
                        if "".join(tokens[i+3 : i+5]) in self.tokenizer.SPECIAL_SLANG:
                            char = self._compose_jamos([t0, t1, t2])
                            result.append(char)
                            i += 3 # t0, t1, t2 처리. t3부터 반복 자소 슬랭 시작
                            continue
                        
                        # [주의] "자모 + 2글자 반복 자소 슬랭(t2~t3)" 케이스는 의도적으로 제외함
                        # 이유: "학ㄴ교" 같은 오타 케이스가 "하+ㄱㄴ+교"로 오복원되는 것을 방지

            # =================================================================
            # 2단계: 4개 패턴 확인 (선행 탐색 Lookahead - 표준 복원)
            # =================================================================
            if i + 3 < word_eos:
                t0, t1, t2, t3 = tokens[i:i+4]
                
                # 자소4개 글자가 단어의 끝인지 확인
                # 오타 복원 방지용 주석 처리
                #last_word = (i + 4 == word_eos)
                
                # 자솆4개 글자가 문장/어절의 끝인지 확인
                # 2글자 반복 자소 슬랭은 문장의 끝만 확인
                last_word = (i + 4 == n)

                if self._is_consonant(t0) and self._is_vowel(t1) and self._is_consonant(t2):
                    # 패턴: 자모자자 (t3가 자음 → t2는 종성)
                    # 오타 자동 복원 효과: 단어 중간에 자음이 끼어있을 때 종성으로 붙여버림
                    if self._is_consonant(t3):
                        # [안전장치] 반복 자음 (t2==t3)이면 반복 자소 슬랭 가능성이 있으므로 종성으로 붙이지 않음
                        # 예: "바다ㄱㄱ" → "바닥ㄱ"이 아니라 "바다" + "ㄱㄱ"으로 처리되도록
                        if last_word and t2 == t3:
                            # t2, t3가 같은 자음 → 2자모 조합만 수행하고 넘어감
                            char = self._compose_jamos([t0, t1])
                            result.append(char)
                            i += 2
                            continue
                        
                        # 일반적인 종성 처리 (t2 != t3)
                        char = self._compose_jamos([t0, t1, t2])
                        result.append(char)
                        i += 3
                        continue
                    
                    # 패턴: 자모자모 (t3가 모음 → t2는 다음 음절 초성)
                    if self._is_vowel(t3):
                        char = self._compose_jamos([t0, t1])
                        result.append(char)
                        i += 2
                        continue

            # =================================================================
            # 3단계: 3개 패턴 확인 (자모자 - 종성 조합)
            # =================================================================
            if i + 2 < word_eos:
                t0, t1, t2 = tokens[i:i+3]
                if self._is_consonant(t0) and self._is_vowel(t1) and self._is_consonant(t2):
                    char = self._compose_jamos([t0, t1, t2])
                    result.append(char)
                    i += 3
                    continue

            # =================================================================
            # 4단계: 2개 패턴 확인 (자모 - 초성+중성 조합)
            # =================================================================
            if i + 1 < word_eos:
                t0, t1 = tokens[i:i+2]
                if self._is_consonant(t0) and self._is_vowel(t1):
                    char = self._compose_jamos([t0, t1])
                    result.append(char)
                    i += 2
                    continue

            # 5단계: 개별 토큰 유지 (조합 불가)
            result.append(tokens[i])
            i += 1

        return "".join(result)

    def _get_word_eos(self, tokens: List[str], start: int) -> int:
        """단어의 끝 인덱스 찾기 (비자소 토큰 또는 리스트 끝)"""
        def check_eos(tok):
            if not isinstance(tok, str) or len(tok) != 1:
                return False
            return not self._is_jaso(tok)
        word_eos = next((j for j, tok in enumerate(tokens[start:], start=start) if check_eos(tok)), len(tokens))
        return word_eos

    def _is_consonant(self, token):
        if not isinstance(token, str): return False
        return token in self.CONSONANTS

    def _is_vowel(self, token):
        if not isinstance(token, str): return False
        return token in self.JUNG
    
    def _is_jaso(self, token):
        """자소 범위 확인 (0x3131-0x318E)"""
        if not isinstance(token, str) or len(token) != 1: return False
        return 0x3131 <= ord(token) <= 0x318E
    
    def _compose_jamos(self, jamos: List[str]) -> str:
        """자소를 음절로 조합 (Security & Validation)"""
        if not isinstance(jamos, (list, tuple)): return ""
        
        try:
            cho = jamos[0] if len(jamos) > 0 else ""
            jung = jamos[1] if len(jamos) > 1 else ""
            jong = jamos[2] if len(jamos) > 2 else ""

            cho_idx = self.CHO_MAP.get(cho)
            jung_idx = self.JUNG_MAP.get(jung)
            # 종성이 없거나 매핑되지 않으면 0 (종성 없음)
            jong_idx = self.JONG_MAP.get(jong, 0)

            if cho_idx is None or jung_idx is None:
                return "".join(jamos)

            code = 0xAC00 + (cho_idx * 21 + jung_idx) * 28 + jong_idx

            if 0xAC00 <= code <= 0xD7A3:
                return chr(code)
            else:
                return "".join(jamos)
        except Exception:
            return "".join(jamos)


# 편의 함수
def detokenize(tokens: List[str], check_slang_mid=False) -> str:
    """자소 토큰을 한글 텍스트로 복원하는 편의 함수

    Args:
        tokens: 자소 토큰 리스트

    Returns:
        복원된 한글 텍스트

    Example:
        >>> detokenize(['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ'])
        '한글'
    """    
    decoder = JasoJamoDecoder(check_slang_mid=check_slang_mid)
    return decoder.detokenize(tokens)

# 편의 함수들
def tokenize(text: str) -> List[str]:
    """한글 텍스트를 자소로 분리하는 편의 함수

    Args:
        text: 분리할 텍스트

    Returns:
        자소 토큰 리스트

    Example:
        >>> tokenize("한글")
        ['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']
    """
    tokenizer = JasoJamoTokenizer()
    return tokenizer.tokenize(text)


if __name__ == "__main__":
    # 사용 예시
    print("=" * 60)
    print("한글 자소 복원 라이브러리 테스트")
    print("=" * 60)

    # 예시 1: 기본 사용
    text = "안녕하세요"
    tokens = tokenize(text)
    restored = detokenize(tokens)

    print(f"\n원본: {text}")
    print(f"자소: {' '.join(tokens)}")
    print(f"복원: {restored}")
    print(f"일치: {text == restored}")

    # 예시 2: 클래스 사용
    print("\n" + "=" * 60)
    decoder = JasoJamoDecoder()

    examples = [
        # "한글",
        "자소복원",
        "자소복구ㅋㅋㅋ잘한다",
        # "네ㅇㅋ",
        # "넵ㅇㅋ",
        # "냉캄사",
        # "ㅋㅋㅋ 재밌다",
        # "사랑해ㅋㅋㅋㅋㅋㅋ",
        # "사랑해ㅋㅋ",
        # "사랑행ㅋㅋ",
        # "사랑해ㅇㅋ",
        # "ㅇㅋ좋아",
        # "좋아ㅇㅋ",
        # "Python과 한글",
        # "복잡한 문장도 잘 처리됩니다!",
        # "값을깎다",
        # "꽃이없다",
        # "뿔이없다",
        # "쌀이짜다",
        # "짧쌀",
        # "핥쓰다"
    ]

    for example in examples:
        tokens = tokenize(example)
        restored = detokenize(tokens)
        match = "o" if example == restored else "x"
        print(f"\n{match} {example}")
        print(f"   → {restored}")
