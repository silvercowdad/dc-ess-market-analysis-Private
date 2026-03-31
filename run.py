"""
DC ESS 시장 분석 실행 진입점

사용법:
  python run.py             # 처음 실행 / 이어서 실행 (체크포인트 자동 복원)
  python run.py --reset     # 체크포인트 초기화 후 처음부터 재실행

환경변수 (필수):
  ANTHROPIC_API_KEY
  TAVILY_API_KEY
"""

import asyncio
import os
import sys


def check_env() -> None:
    missing = [k for k in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY") if not os.getenv(k)]
    if missing:
        print("[오류] 다음 환경변수가 설정되지 않았습니다:")
        for m in missing:
            print(f"  export {m}=your_key_here")
        sys.exit(1)


def main() -> None:
    check_env()

    if "--reset" in sys.argv:
        import state as _state
        _state.reset_all()
        print("[초기화] 체크포인트가 삭제되었습니다. 처음부터 실행합니다.")

    from orchestrator import run
    asyncio.run(run())


if __name__ == "__main__":
    main()
