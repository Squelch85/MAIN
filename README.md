# MAIN

이 프로젝트는 INI 구성 파일을 편집하기 위한 Tkinter 기반 GUI를 제공합니다.
여러 INI 파일을 개별 탭에서 열 수 있으며 창 상태를 세션 간 유지합니다.

## Requirements
- Python 3.8 이상
- Tkinter(표준 Python 배포판에 포함)

추가 서드파티 패키지는 필요하지 않습니다.

## Project Structure
- `gui/parameter_tab.py` – 토글 버튼과 편집 가능한 필드를 갖춘 동적 섹션/파라미터 UI
- `gui/parameter_manager.py` – 여러 파일을 위한 탭을 관리하고 `state_manager.py`를 사용해 창 크기와 열려 있는 파일 정보를 `state.json`에 저장
- `state_manager.py` – JSON 상태 파일을 로드하고 저장하는 헬퍼
- `config_io.py` – INI 형식 파일을 읽고 쓰기 위한 유틸리티
- `INI_EDIT.py` – GUI를 실행하는 시작 지점

## Usage
저장소 루트에서 다음과 같이 실행합니다:

```bash
python INI_EDIT.py
```

열린 INI 파일들은 탭 인터페이스에 표시됩니다. 프로그램을 종료하면 열린 파일 목록, 창 크기, 파일별 UI 상태(접힘 상태와 사용자 지정 순서)가 `gui/state.json`에 저장되며 다음 실행 시 그대로 복원됩니다.

## Contributing
- 코드 스타일은 [PEP 8](https://peps.python.org/pep-0008/)을 따르세요.
- 변경 사항에 대한 명확한 설명과 함께 풀 리퀘스트를 제출하세요.
- 새로운 모듈이나 기능을 추가할 경우 docstring을 작성하고 이 README도 갱신하세요.
