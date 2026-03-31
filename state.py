"""체크포인트 상태 관리 - 재시작 시 완료된 에이전트는 건너뜀."""
import json
import os
from pathlib import Path

STATE_FILE = "state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def mark_completed(agent_id: str, result_path: str):
    state = load_state()
    state[agent_id] = {"status": "completed", "result_path": result_path}
    save_state(state)


def is_completed(agent_id: str) -> bool:
    return load_state().get(agent_id, {}).get("status") == "completed"


def get_result_path(agent_id: str) -> str | None:
    return load_state().get(agent_id, {}).get("result_path")


def reset_agent(agent_id: str):
    state = load_state()
    state.pop(agent_id, None)
    save_state(state)


def reset_all():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
