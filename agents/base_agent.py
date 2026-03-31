"""
BaseAgent: 모든 에이전트의 공통 기반.

각 에이전트는 다음 도구를 가짐:
  - web_search  : Tavily로 최신 데이터 검색
  - read_file   : 선행 에이전트 결과 파일 참조

실행 흐름:
  1. 체크포인트 확인 → 이미 완료된 경우 결과 파일에서 복원
  2. 선행 결과 파일 경로를 초기 메시지에 포함
  3. tool_use 루프 실행 (검색·파일 읽기 반복)
  4. 최종 텍스트 추출 → reports/ 에 저장 → 체크포인트 갱신
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

import state
from tools.search import tavily_search

# 동시 API 호출 제한 (rate limit 대응)
_SEM: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    global _SEM
    if _SEM is None:
        _SEM = asyncio.Semaphore(3)
    return _SEM


WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "웹에서 최신 시장 데이터, 뉴스, 연구자료를 검색합니다. "
        "최신 수치나 특정 기업/정책 정보가 필요할 때 사용하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색 쿼리 (영어 검색 권장, 구체적일수록 좋음)",
            }
        },
        "required": ["query"],
    },
}

READ_FILE_TOOL = {
    "name": "read_file",
    "description": (
        "파일을 읽어 내용을 반환합니다. "
        "선행 에이전트 결과 파일(reports/ 폴더)을 참조할 때 사용하세요."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "읽을 파일의 경로 (예: reports/agent_a_20250101_120000.md)",
            }
        },
        "required": ["path"],
    },
}


@dataclass
class AgentResult:
    agent_id: str
    content: str
    result_path: str


class BaseAgent:
    AGENT_ID: str = ""
    MODEL: str = "claude-sonnet-4-6"
    PROMPT_FILE: str = ""
    MAX_TOKENS: int = 8096
    MAX_TOOL_CALLS: int = 20  # 무한 루프 방지

    def __init__(self, input_results: Optional[list[AgentResult]] = None):
        self.input_results: list[AgentResult] = input_results or []
        self.client = anthropic.AsyncAnthropic()
        self._system_prompt = self._load_prompt()

    # ------------------------------------------------------------------
    # 공개 메서드
    # ------------------------------------------------------------------

    async def run(
        self,
        force_rerun: bool = False,
        feedback: Optional[str] = None,
    ) -> AgentResult:
        """에이전트 실행. force_rerun=True면 체크포인트 무시.

        Args:
            force_rerun: True면 이미 완료된 경우에도 재실행.
            feedback: 재실행 시 사용자 수정 요청 메모.
                      초기 메시지 맨 앞에 포함되어 에이전트에 전달된다.
        """
        if not force_rerun and state.is_completed(self.AGENT_ID):
            path = state.get_result_path(self.AGENT_ID)
            content = Path(path).read_text(encoding="utf-8")
            print(f"  [{self.AGENT_ID}] 체크포인트에서 복원 ({path})")
            return AgentResult(self.AGENT_ID, content, path)

        print(f"  [{self.AGENT_ID}] 실행 시작...")
        content = await self._run_tool_loop(feedback=feedback)
        result_path = self._save_result(content)
        state.mark_completed(self.AGENT_ID, result_path)
        print(f"  [{self.AGENT_ID}] 완료 → {result_path}")
        return AgentResult(self.AGENT_ID, content, result_path)

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _load_prompt(self) -> str:
        path = Path(self.PROMPT_FILE)
        if not path.exists():
            raise FileNotFoundError(f"프롬프트 파일 없음: {self.PROMPT_FILE}")
        return path.read_text(encoding="utf-8")

    def _build_initial_message(self, feedback: Optional[str] = None) -> str:
        """초기 사용자 메시지 구성.

        선행 결과가 있으면 파일 경로 목록을 포함하고,
        에이전트가 read_file 도구로 직접 읽도록 지시한다.
        feedback이 있으면 맨 앞에 사용자 수정 요청으로 포함한다.
        """
        parts = []

        if feedback:
            parts.append(
                f"## 사용자 수정 요청 (최우선 반영)\n{feedback}\n\n"
                "위 수정 요청을 반드시 반영하여 분석을 다시 수행하세요.\n\n"
            )

        parts.append(
            "분석을 시작하세요. "
            "web_search 도구로 최신 데이터를 수집하고 심층 분석을 수행해주세요.\n"
        )

        if self.input_results:
            parts.append("\n## 선행 에이전트 결과 파일 (read_file 도구로 읽으세요)\n")
            for r in self.input_results:
                parts.append(f"- `{r.result_path}`  ← [{r.agent_id}]\n")
            parts.append(
                "\n위 파일들을 read_file 도구로 읽은 후 내용을 참고하여 분석하세요. "
                "선행 에이전트의 정의/수치를 벗어나지 마세요.\n"
            )

        parts.append(
            "\n분석이 완료되면 전체 결과를 마크다운 형식으로 최종 출력하세요. "
            "출처·가정·수치 단위를 명확히 표시하세요."
        )
        return "".join(parts)

    async def _run_tool_loop(self, feedback: Optional[str] = None) -> str:
        messages = [{"role": "user", "content": self._build_initial_message(feedback=feedback)}]
        tools = [WEB_SEARCH_TOOL, READ_FILE_TOOL]
        tool_call_count = 0

        async with _get_semaphore():
            while True:
                # 도구 호출 한도 초과 시 도구 제거해 최종 답변 유도
                active_tools = tools if tool_call_count < self.MAX_TOOL_CALLS else []

                response = await self.client.messages.create(
                    model=self.MODEL,
                    system=self._system_prompt,
                    messages=messages,
                    tools=active_tools,
                    max_tokens=self.MAX_TOKENS,
                )

                if response.stop_reason == "end_turn":
                    return self._extract_text(response)

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type != "tool_use":
                            continue
                        tool_call_count += 1
                        result = await self._dispatch_tool(block)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            }
                        )
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # 예상치 못한 stop_reason
                    return self._extract_text(response)

    async def _dispatch_tool(self, block) -> str:
        if block.name == "web_search":
            query = block.input.get("query", "")
            print(f"    [{self.AGENT_ID}] 검색: {query[:70]}")
            return await tavily_search(query)

        if block.name == "read_file":
            path_str = block.input.get("path", "")
            print(f"    [{self.AGENT_ID}] 파일 읽기: {path_str}")
            try:
                return Path(path_str).read_text(encoding="utf-8")
            except Exception as e:
                return f"[파일 읽기 오류: {e}]"

        return f"[알 수 없는 도구: {block.name}]"

    @staticmethod
    def _extract_text(response) -> str:
        return "\n".join(
            block.text for block in response.content if hasattr(block, "text")
        )

    def _save_result(self, content: str) -> str:
        Path("reports").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"reports/{self.AGENT_ID}_{timestamp}.md"
        Path(path).write_text(content, encoding="utf-8")
        return path
