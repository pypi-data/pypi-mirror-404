# simple-utils

날짜/시간, 문자열, 파일, 데코레이터 등 다양한 Python 유틸리티 모음입니다.

## 설치

```bash
pip install simple-utils
```

### 선택적 의존성

```bash
# Iceberg 지원
pip install simple-utils[iceberg]
```

## 모듈

- **datetime_utils** - 날짜 및 시간 연산
- **string_utils** - 문자열 변환 및 조작
- **file_utils** - 파일 및 경로 작업
- **decorators** - 유용한 함수 데코레이터
- **storage** - 객체 저장소 유틸리티
- **platform** - 플랫폼 연동 (Iceberg, DuckDB)

## 사용법

### DateTime Utilities

```python
from simple_utils import datetime_utils

# 현재 날짜/시간
now = datetime_utils.now()
today = datetime_utils.today()

# 타임스탬프
ts = datetime_utils.now_timestamp()
ts_ms = datetime_utils.now_timestamp_ms()

# 파싱 및 포맷
date = datetime_utils.parse_date("2024-01-15")
dt = datetime_utils.parse_datetime("2024-01-15 10:30:00")
formatted = datetime_utils.format_date(date, "%Y/%m/%d")

# 날짜 연산
dates = datetime_utils.date_range("2024-01-01", "2024-01-10")
days = datetime_utils.days_between("2024-01-01", "2024-01-10")
new_date = datetime_utils.add_days("2024-01-01", 7)

# 하루의 시작/끝
start = datetime_utils.start_of_day()
end = datetime_utils.end_of_day()

# 주말 확인
is_weekend = datetime_utils.is_weekend("2024-01-13")  # True (토요일)

# 타임스탬프 변환
dt = datetime_utils.timestamp_to_datetime(1705312200)
ts = datetime_utils.datetime_to_timestamp(dt)
```

### String Utilities

```python
from simple_utils import string_utils

# 케이스 변환
string_utils.to_snake_case("HelloWorld")      # "hello_world"
string_utils.to_camel_case("hello_world")     # "helloWorld"
string_utils.to_pascal_case("hello_world")    # "HelloWorld"
string_utils.to_kebab_case("HelloWorld")      # "hello-world"

# 문자열 연산
string_utils.truncate("Hello World", 8)        # "Hello..."
string_utils.slugify("Hello World!")           # "hello-world"
string_utils.reverse("hello")                  # "olleh"

# 랜덤 문자열
string_utils.random_string(16)                 # "aB3xKm9pQr2sT5vW"
string_utils.random_hex(8)                     # "a1b2c3d4"

# 검사
string_utils.is_empty("")                      # True
string_utils.is_not_empty("hello")             # True
string_utils.contains_any("hello", ["he", "x"]) # True
string_utils.contains_all("hello", ["he", "lo"]) # True

# 접두사/접미사 제거
string_utils.remove_prefix("prefix_text", "prefix_")  # "text"
string_utils.remove_suffix("text_suffix", "_suffix")  # "text"

# 마스킹
string_utils.mask("1234567890", 2, 2)          # "12******90"

# 추출
string_utils.extract_numbers("abc123def456")   # ["123", "456"]
string_utils.split_words("helloWorld")         # ["hello", "world"]
```

### File Utilities

```python
from simple_utils import file_utils

# 텍스트 파일
content = file_utils.read_text("file.txt")
file_utils.write_text("file.txt", "content")

lines = file_utils.read_lines("file.txt")
file_utils.write_lines("file.txt", ["line1", "line2"])

# JSON 파일
data = file_utils.read_json("data.json")
file_utils.write_json("data.json", {"key": "value"})

# 바이너리 파일
bytes_data = file_utils.read_bytes("file.bin")
file_utils.write_bytes("file.bin", b"binary data")

# 디렉토리 작업
file_utils.ensure_dir("path/to/dir")
file_utils.ensure_parent_dir("path/to/file.txt")
files = file_utils.list_files("dir", "*.py", recursive=True)

# 파일 정보
file_utils.exists("file.txt")
file_utils.is_file("file.txt")
file_utils.is_dir("directory")
file_utils.get_extension("file.txt")     # ".txt"
file_utils.get_stem("file.txt")          # "file"
file_utils.get_name("path/to/file.txt")  # "file.txt"
file_utils.get_parent("path/to/file.txt") # Path("path/to")
file_utils.get_size("file.txt")          # 바이트 크기
file_utils.get_size_human("file.txt")    # "1.5 MB"

# 파일 작업
file_utils.copy_file("src.txt", "dst.txt")
file_utils.move_file("src.txt", "dst.txt")
file_utils.delete_file("file.txt")
file_utils.delete_dir("directory")

# 경로 유틸리티
path = file_utils.join_path("path", "to", "file.txt")
abs_path = file_utils.resolve_path("./file.txt")
```

### Decorators

```python
from simple_utils import decorators

# 지수 백오프 재시도
@decorators.retry(max_attempts=3, delay=1.0, backoff=2.0)
def unstable_function():
    ...

# 실행 시간 측정
@decorators.timing
def slow_function():
    ...

# 결과 캐싱
@decorators.memoize
def expensive_function(x):
    ...

# 지원 중단 표시
@decorators.deprecated(message="new_func을 사용하세요", version="2.0")
def old_function():
    ...

# 싱글톤 패턴
@decorators.singleton
class Database:
    ...

# 호출 제한
@decorators.throttle(interval=1.0)  # 초당 최대 1회
def rate_limited_function():
    ...

@decorators.debounce(wait=0.5)      # 마지막 호출 후 0.5초 대기
def debounced_function():
    ...

# 로깅
@decorators.log_calls(log_args=True, log_result=True)
def logged_function(x, y):
    ...

# 에러 처리
@decorators.catch_exceptions(default=None, exceptions=(ValueError,))
def safe_function():
    ...

# 1회만 실행
@decorators.run_once
def initialize():
    ...

# 인자 검증
@decorators.validate_args(x=lambda x: x > 0, name=lambda s: len(s) > 0)
def validated_function(x, name):
    ...
```

### Object Storage

```python
from simple_utils.storage import ObjectStorage

# 스토리지 초기화
storage = ObjectStorage("/path/to/storage")

# 데이터 쓰기
storage.write("config.json", {"key": "value"})
storage.write("data.txt", "텍스트 내용")
storage.write("binary.bin", b"바이너리 데이터")

# 데이터 읽기
data = storage.read("config.json")       # JSON 자동 파싱
text = storage.read_text("data.txt")
binary = storage.read_bytes("binary.bin")

# 확인 및 목록
storage.exists("config.json")            # True
storage.list_keys()                       # ["config.json", "data.txt", ...]
storage.list_keys(prefix="config")        # ["config.json"]
storage.list_dirs()                       # 하위 디렉토리 목록

# 삭제
storage.delete("config.json")
```

### Platform 연동

- [Iceberg 사용 가이드](docs/iceberg.md) - Apache Iceberg 카탈로그 연동
- [DuckDB 사용 가이드](docs/duckdb.md) - Iceberg 지원 DuckDB 연동

## 요구사항

- Python >= 3.8

## 라이선스

MIT
