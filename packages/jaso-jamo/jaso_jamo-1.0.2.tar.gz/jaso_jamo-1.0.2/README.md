# jaso-jamo

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/jaso-jamo.svg)](https://pypi.org/project/jaso-jamo/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

한글 자소 분리 및 복원 라이브러리 (5단계 Fallback 방식)

## 개요

`jaso-jamo`는 한글을 자소(초성, 중성, 종성)로 분리한 이후 다시 완벽하게 복원하기 위한 Python 라이브러리입니다.

## 특징

- **높은 정확도**: 자음/모음 특성 기반 복원 알고리즘
- **실용적 성능**: O(1) 딕셔너리 조회 최적화
- **간단한 API**: 2개의 메인 함수로 모든 기능 제공
- **의존성 없음**: 순수 Python 구현
- **유니코드 표준**: 완벽한 한글 유니코드 지원
- **반복 자소 슬랭 처리**: "ㅋㅋㅋ", "ㅎㅎㅎ" 등 실제 채팅 언어 대응

## 설치

```bash
pip install jaso-jamo
```

또는 개발 모드로 설치:

```bash
git clone https://github.com/c0z0c/jaso-jamo.git
cd jaso-jamo
pip install -e .
```

### 기본 사용

```python
from jaso_jamo import tokenize, detokenize

# 자소 분리
text = "안녕하세요"
tokens = tokenize(text)
print(tokens)
# ['ㅇ', 'ㅏ', 'ㄴ', 'ㄴ', 'ㅕ', 'ㅇ', 'ㅎ', 'ㅏ', 'ㅅ', 'ㅔ', 'ㅇ', 'ㅛ']

# 자소 복원
restored = detokenize(tokens)
print(restored)  # "안녕하세요"
```

## 사용 예시

### 예시 1: 기본 단어

```python
from jaso_jamo import tokenize, detokenize

text = "한글"
tokens = tokenize(text)      # ['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']
restored = detokenize(tokens) # "한글"
```

### 예시 2: 반복 자소 슬랭 처리 (핵심 차별화 기능)

```python
text = "가요ㅋㅋㅋ"
tokens = tokenize(text)      # ['ㄱ', 'ㅏ', 'ㅇ', 'ㅛ', 'ㅋ', 'ㅋ', 'ㅋ']
restored = detokenize(tokens) # "가요ㅋㅋㅋ"
```

### 예시 3: 한영 혼용

```python
text = "Python으로 개발했어요"
tokens = tokenize(text)
restored = detokenize(tokens) # "Python으로 개발했어요"
```

## API 문서

### 함수

#### `tokenize(text: str) -> List[str]`

한글 텍스트를 자소로 분리합니다.

```python
>>> from jaso_jamo import tokenize
>>> tokenize("한글")
['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ']
```

#### `detokenize(tokens: List[str]) -> str`

자소 토큰을 한글 텍스트로 복원합니다.

```python
>>> from jaso_jamo import detokenize
>>> detokenize(['ㅎ', 'ㅏ', 'ㄴ', 'ㄱ', 'ㅡ', 'ㄹ'])
'한글'
```

## 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

### 기여 방법

1. 저장소를 Fork합니다
2. Feature 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push합니다 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성합니다

### 기여 가이드라인

- 코드 스타일: PEP 8 준수 (Black, isort 사용)
- 테스트: 새 기능에는 테스트 추가
- 문서: 변경사항은 README에 반영
- 커밋 메시지: 명확하고 간결하게 작성

---

## 📝 라이센스

### 코드 라이센스

MIT License - 본 프로젝트의 코드는 자유롭게 사용하실 수 있습니다.

### 데이터 라이센스

본 프로젝트에서 사용된 벤치마크 및 테스트 데이터는 **AI허브 - 일상생활 및 구체어 말뭉치 데이터**를 활용하였습니다.

- **제공기관**: 한국지능정보사회진흥원 (NIA)
- **출처**: [AI허브 (aihub.or.kr)](https://www.aihub.or.kr/)
- **이용약관**: AI허브 이용약관 준수 필요

```text
본 프로젝트는 과학기술정보통신부 및 한국지능정보사회진흥원의
'AI허브 - 일상생활 및 구체어 말뭉치 데이터'를 활용하였습니다.
```

자세한 데이터 라이센스 정보는 [DATA_LICENSE.md](DATA_LICENSE.md)를 참조하세요.

## 개발 배경

한글을 자소 분리한 이후 다시 복원하기 위한 로직입니다.
많은 사람들이 편하게 사용하였으면 좋겠습니다.
자음과 모음의 원리를 적용하여 개발하였습니다.

개발일: 2025년 10월 17일

## 참고 자료

- [한글 유니코드 표준](https://www.unicode.org/charts/PDF/UAC00.pdf)
- [한글 자모 이해하기](https://ko.wikipedia.org/wiki/한글_자모)

