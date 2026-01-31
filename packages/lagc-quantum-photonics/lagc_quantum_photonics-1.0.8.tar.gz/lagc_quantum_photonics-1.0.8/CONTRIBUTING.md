# Contributing to LAGC

먼저, LAGC에 기여해 주셔서 감사합니다! 🎉

## 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/quantum-dev/lagc.git
cd lagc

# 개발 의존성 설치
pip install -e ".[dev]"

# pre-commit 훅 설정
pre-commit install
```

## 코드 스타일

- Python 코드는 [Black](https://black.readthedocs.io/) 포매터를 사용합니다
- import 정렬은 [isort](https://pycqa.github.io/isort/)를 사용합니다
- 타입 힌트를 필수로 사용합니다

```bash
# 포매팅
black lagc/
isort lagc/

# 타입 체크
mypy lagc/

# 린팅
flake8 lagc/
```

## 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=lagc --cov-report=html

# 특정 테스트
pytest tests/test_core.py -v
```

## Pull Request 가이드라인

1. **Fork** 후 feature 브랜치 생성
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **변경사항 커밋** (명확한 커밋 메시지)
   ```bash
   git commit -m "Add: 새로운 토폴로지 지원"
   ```

3. **테스트 통과 확인**
   ```bash
   pytest tests/ -v
   ```

4. **브랜치 푸시 및 PR 생성**
   ```bash
   git push origin feature/amazing-feature
   ```

## 커밋 메시지 규칙

```
<타입>: <설명>

[선택적 본문]
```

타입:
- `Add`: 새 기능 추가
- `Fix`: 버그 수정
- `Docs`: 문서 변경
- `Style`: 코드 스타일 변경 (포매팅 등)
- `Refactor`: 리팩토링
- `Test`: 테스트 추가/수정
- `Chore`: 빌드/의존성 변경

## 이슈 리포트

버그나 기능 요청은 [GitHub Issues](https://github.com/quantum-dev/lagc/issues)에 등록해 주세요.

### 버그 리포트 포함 사항

- Python 버전
- LAGC 버전 (`lagc.__version__`)
- 재현 가능한 최소 코드
- 예상 동작 vs 실제 동작
- 전체 에러 메시지

## 질문

- [GitHub Discussions](https://github.com/quantum-dev/lagc/discussions)

감사합니다! 🚀
