from typing import List


class JasoJamoTokenizer:
    """한글 자소 분리기

    한글 음절을 초성, 중성, 종성으로 분리합니다.
    """

    def __init__(
        self,
        special_slang: List[str] = [
            "ㅇㅋ",
            "ㄱㅅ",
            "ㄳ",
            "ㄷㅊ",
            "ㅁㅊ",
            "ㅅㄱ",
            "ㅇㅈ",
            "ㅎㅇ",
            "ㅆㅅㅌㅊ",
            "ㄹㅇ",
        ],
    ):
        # 초성 19자
        self.CHO = [
            "ㄱ",
            "ㄲ",
            "ㄴ",
            "ㄷ",
            "ㄸ",
            "ㄹ",
            "ㅁ",
            "ㅂ",
            "ㅃ",
            "ㅅ",
            "ㅆ",
            "ㅇ",
            "ㅈ",
            "ㅉ",
            "ㅊ",
            "ㅋ",
            "ㅌ",
            "ㅍ",
            "ㅎ",
        ]
        # 중성 21자
        self.JUNG = [
            "ㅏ",
            "ㅐ",
            "ㅑ",
            "ㅒ",
            "ㅓ",
            "ㅔ",
            "ㅕ",
            "ㅖ",
            "ㅗ",
            "ㅘ",
            "ㅙ",
            "ㅚ",
            "ㅛ",
            "ㅜ",
            "ㅝ",
            "ㅞ",
            "ㅟ",
            "ㅠ",
            "ㅡ",
            "ㅢ",
            "ㅣ",
        ]
        # 종성 28자 (빈 종성 포함)
        self.JONG = [
            "",
            "ㄱ",
            "ㄲ",
            "ㄳ",
            "ㄴ",
            "ㄵ",
            "ㄶ",
            "ㄷ",
            "ㄹ",
            "ㄺ",
            "ㄻ",
            "ㄼ",
            "ㄽ",
            "ㄾ",
            "ㄿ",
            "ㅀ",
            "ㅁ",
            "ㅂ",
            "ㅄ",
            "ㅅ",
            "ㅆ",
            "ㅇ",
            "ㅈ",
            "ㅊ",
            "ㅋ",
            "ㅌ",
            "ㅍ",
            "ㅎ",
        ]
        if special_slang is None:
            special_slang = []
        self.SPECIAL_SLANG = special_slang

    def tokenize(self, text: str) -> List[str]:
        """텍스트를 자소 토큰으로 분리

        Args:
            text: 분리할 텍스트

        Returns:
            자소 토큰 리스트

        Security:
            - 입력 타입 검증
            - 최대 문자열 길이 제한으로 DoS 방지

        Example:
            >>> tokenizer = JasoJamoTokenizer()
            >>> tokenizer.tokenize("한글")
            ['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']
        """
        # 입력 검증
        if not isinstance(text, str):
            return []
        if not text:
            return []

        # DoS 방지: 최대 문자열 길이 제한 (100,000자)
        MAX_LENGTH = 100000
        if len(text) > MAX_LENGTH:
            text = text[:MAX_LENGTH]

        result = []
        try:
            for char in text:
                if self._is_hangeul(char):
                    jamos = self._decompose(char)
                    result.extend(jamos)
                else:
                    result.append(char)
        except (TypeError, ValueError, AttributeError):
            # 예외 발생 시 현재까지의 결과 반환
            pass

        return result

    def _is_hangeul(self, char: str) -> bool:
        """한글 음절인지 확인

        Security: 타입 및 범위 검증
        """
        if not isinstance(char, str):
            return False
        if len(char) != 1:
            return False
        try:
            code = ord(char)
            return 0xAC00 <= code <= 0xD7A3
        except (TypeError, ValueError):
            return False

    def _decompose(self, char: str) -> List[str]:
        """한글 음절을 자소로 분해

        Security:
            - 입력 검증 및 인덱스 범위 확인
            - 예외 처리로 안전성 보장
        """
        if not self._is_hangeul(char):
            return [char] if isinstance(char, str) else []

        try:
            code = ord(char) - 0xAC00

            # 범위 검증
            if code < 0 or code > 11171:  # 11172개 음절 (0~11171)
                return [char]

            jong_idx = code % 28
            jung_idx = ((code - jong_idx) // 28) % 21
            cho_idx = ((code - jong_idx) // 28) // 21

            # 인덱스 범위 검증 (보안)
            if not (0 <= cho_idx < len(self.CHO)):
                return [char]
            if not (0 <= jung_idx < len(self.JUNG)):
                return [char]
            if not (0 <= jong_idx < len(self.JONG)):
                return [char]

            jamos = [self.CHO[cho_idx], self.JUNG[jung_idx]]
            if jong_idx > 0:
                jamos.append(self.JONG[jong_idx])

            return jamos
        except (TypeError, ValueError, IndexError, KeyError):
            return [char] if isinstance(char, str) else []
