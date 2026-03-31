from .base_agent import BaseAgent


class Validator1(BaseAgent):
    AGENT_ID = "validator_1"
    MODEL = "claude-sonnet-4-6"
    PROMPT_FILE = "prompts/validator_1.txt"

    def _build_initial_message(self) -> str:
        parts = [
            "다음 에이전트 결과 파일들을 read_file 도구로 모두 읽고 팩트체크를 수행하세요.\n\n"
            "## 검증 대상 파일\n"
        ]
        for r in self.input_results:
            parts.append(f"- `{r.result_path}`  ← [{r.agent_id}]\n")
        parts.append(
            "\n파일을 읽은 후 시스템 프롬프트의 형식([BLOCK]/[FLAG]/[WARN]/[PASS])으로 검증 결과를 출력하세요. "
            "[FLAG] 항목은 반드시 별도로 목록화하세요."
        )
        return "".join(parts)
