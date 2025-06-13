# MAIN

이 프로젝트는 INI 구성 파일을 편집하기 위한 Tkinter 기반 GUI를 제공합니다. 여러 INI 파일을 각각 탭으로 열 수 있으며 프로그램을 종료해도 창 크기와 열린 파일 목록이 저장되어 다음 실행 시 복원됩니다.

## 요구 사항
- Python 3.8 이상
- Tkinter (표준 Python 배포판에 포함)

추가 서드파티 패키지 설치는 필요하지 않습니다.

## 프로젝트 구조
- `gui/parameter_tab.py` – 토글 버튼과 편집 필드를 갖춘 동적 섹션/파라미터 UI
- `gui/parameter_manager.py` – 여러 파일 탭을 관리하고 `state_manager.py`를 사용해 창 상태를 `state.json`에 저장
- `state_manager.py` – JSON 상태 파일을 불러오고 저장하는 헬퍼
- `config_io.py` – INI 형식 파일을 읽고 쓰는 유틸리티
- `INI_EDIT.py` – GUI를 실행하는 진입점

## 사용법
레포지토리 루트에서 다음 명령으로 실행합니다.

```bash
python INI_EDIT.py
```

열린 INI 파일들은 탭 인터페이스에 표시됩니다. 창을 닫을 때 열린 파일 목록, 창 크기, 섹션 접힘 상태 등이 `gui/state.json`에 기록되며 다음 실행 시 그대로 복원됩니다.

메인 창 크기를 사용자가 조작하면 셀의 크기를 유지하면서 그리드가 재배치 됩니다.

## 기여 방법
- 코드 스타일은 [PEP 8](https://peps.python.org/pep-0008/)을 따릅니다.
- 변경 사항을 명확히 설명한 풀 리퀘스트를 보내 주세요.
- 새 모듈이나 기능을 추가할 경우 주석 및 이 README를 함께 업데이트해 주세요.
