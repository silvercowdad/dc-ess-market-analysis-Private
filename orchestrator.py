"""
DC ESS 시장 분석 오케스트레이터

실행 순서:
  STEP 1  Agent A  단독 실행 → 사용자 승인 대기
  STEP 2  Agent B~H 병렬 실행
  STEP 3  Agent I  실행 (B~H 완료 후)
  STEP 4  Validator 1, 2 병렬 실행 → [FLAG] 항목 사용자 확인
  STEP 5  Agent J  실행 (검증 완료 후)
  STEP 6  최종 리포트 생성 → final/ 저장
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

import state
from agents import (
    AgentA, AgentB, AgentC, AgentD, AgentE,
    AgentF, AgentG, AgentH, AgentI, AgentJ,
    Validator1, Validator2,
)
from agents.base_agent import AgentResult


# ---------------------------------------------------------------------------
# 사용자 입력 유틸리티
# ---------------------------------------------------------------------------

async def _ask(prompt: str) -> str:
    """비동기 사용자 입력."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def _get_approval(question: str) -> bool:
    """y/n 승인 루프. q 입력 시 종료."""
    while True:
        answer = await _ask(
            f"\n{'='*60}\n{question}\n[y=승인  n=재실행  q=종료]: "
        )
        token = answer.strip().lower()
        if token in ("y", "yes", "예", "승인"):
            return True
        if token in ("n", "no", "아니오", "재실행"):
            return False
        if token in ("q", "quit", "종료"):
            print("실행을 종료합니다.")
            raise SystemExit(0)
        print("  y / n / q 중 하나를 입력하세요.")


# ---------------------------------------------------------------------------
# [FLAG] 처리
# ---------------------------------------------------------------------------

def _extract_flags(content: str) -> list[str]:
    return [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("[FLAG]")
    ]


async def _handle_flags(v1: AgentResult, v2: AgentResult) -> None:
    flags = _extract_flags(v1.content) + _extract_flags(v2.content)
    if not flags:
        print("  Validator: [FLAG] 항목 없음. 다음 단계로 진행합니다.")
        return

    print(f"\n{'='*60}")
    print(f"  [FLAG] 항목 {len(flags)}개 발견. 사용자 확인이 필요합니다.")
    for i, flag in enumerate(flags, 1):
        print(f"  {i}. {flag}")

    for flag in flags:
        answer = await _ask(
            f"\n{flag}\n→ 처리 방법을 입력하세요 (계속/수정 내용/삭제): "
        )
        print(f"   처리 확인: {answer.strip()}")


# ---------------------------------------------------------------------------
# 최종 리포트
# ---------------------------------------------------------------------------

async def _generate_final_report(all_results: list[AgentResult]) -> str:
    client = anthropic.AsyncAnthropic()

    # 각 에이전트 결과 요약 (파일 경로 목록)
    file_list = "\n".join(
        f"- {r.result_path}  [{r.agent_id}]" for r in all_results
    )
    combined_content = "\n\n".join(
        f"## [{r.agent_id}]\n{r.content}" for r in all_results
    )

    system = (
        "너는 한국어 경영 보고서 전문가야. Samsung SDI C-Level 임원을 위한 "
        "간결하고 명확한 보고서를 작성한다. "
        "핵심 인사이트를 먼저 제시하고, 데이터로 뒷받침하며, 실행 가능한 제안을 포함한다."
    )

    user = f"""다음 에이전트 분석 결과를 바탕으로 Samsung SDI 경영진을 위한 최종 보고서를 한국어로 작성해주세요.

{combined_content}

## 보고서 구조 (반드시 준수)

1. Executive Summary (핵심 요약, 1페이지 분량)
2. 시장 정의 및 세그먼트
3. 수요 전망 (2026-2030, MW/MWh/Revenue)
4. 주요 고객 및 유스케이스
5. 기술 아키텍처 현황
6. 경쟁사 분석
7. 정책 및 규제 환경
8. 공급망 분석
9. 경제성 분석
10. 리스크 및 시나리오
11. SDI 전략 시사점 및 권고사항
12. 의사결정 필요 항목 (경영진 판단 요구)

한국어로 작성. 수치에는 단위 명시. C-Level 보고 형식."""

    print("  최종 리포트 생성 중 (Opus)...")
    response = await client.messages.create(
        model="claude-opus-4-6",
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=16000,
    )

    content = "\n".join(
        block.text for block in response.content if hasattr(block, "text")
    )

    Path("final").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"final/DC_ESS_Market_Analysis_{timestamp}.md"
    Path(path).write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 메인 오케스트레이션
# ---------------------------------------------------------------------------

async def run() -> None:
    Path("reports").mkdir(exist_ok=True)
    Path("final").mkdir(exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  DC ESS 시장 분석 멀티에이전트 시스템")
    print("=" * 60)

    # ------------------------------------------------------------------ STEP 1
    print("\n[STEP 1] Agent A 실행 — 시장 정의 및 세그먼트")
    agent_a = AgentA()
    result_a = await agent_a.run()

    print(f"\n{'='*60}")
    print(result_a.content)

    while True:
        approved = await _get_approval("시장 정의와 세그먼트를 승인하시겠습니까?")
        if approved:
            break
        # 재실행 요청 시 체크포인트 초기화
        state.reset_agent("agent_a")
        result_a = await agent_a.run(force_rerun=True)
        print(f"\n{'='*60}")
        print(result_a.content)

    print("\n  [STEP 1] 승인 완료.")

    # ------------------------------------------------------------------ STEP 2
    print("\n[STEP 2] Agent B~H 병렬 실행 중...")

    agents_b_h = [
        AgentB([result_a]),
        AgentC([result_a]),
        AgentD([result_a]),
        AgentE([result_a]),
        AgentF([result_a]),
        AgentG([result_a]),
        AgentH([result_a]),
    ]

    raw_results = await asyncio.gather(
        *[a.run() for a in agents_b_h],
        return_exceptions=True,
    )

    results_b_h: list[AgentResult] = []
    for i, r in enumerate(raw_results):
        label = chr(ord("B") + i)
        if isinstance(r, Exception):
            print(f"  [경고] Agent {label} 실패: {r}")
        else:
            results_b_h.append(r)

    print(f"\n  [STEP 2] 완료. 성공 {len(results_b_h)}/7")

    # ------------------------------------------------------------------ STEP 3
    print("\n[STEP 3] Agent I 실행 — 시나리오 분석")
    agent_i = AgentI(results_b_h)
    result_i = await agent_i.run()
    print("  [STEP 3] 완료.")

    # ------------------------------------------------------------------ STEP 4
    print("\n[STEP 4] Validator 1, 2 병렬 실행 중...")
    all_until_i: list[AgentResult] = [result_a] + results_b_h + [result_i]
    v1_result, v2_result = await asyncio.gather(
        Validator1(all_until_i).run(),
        Validator2(all_until_i).run(),
    )
    print("  [STEP 4] 완료.")
    await _handle_flags(v1_result, v2_result)

    # ------------------------------------------------------------------ STEP 5
    print("\n[STEP 5] Agent J 실행 — SDI 전략 시사점")
    all_results = all_until_i + [v1_result, v2_result]
    agent_j = AgentJ(all_results)
    result_j = await agent_j.run()
    print("  [STEP 5] 완료.")

    # ------------------------------------------------------------------ STEP 6
    print("\n[STEP 6] 최종 리포트 생성 중...")
    final_path = await _generate_final_report(all_results + [result_j])

    print(f"\n{'='*60}")
    print(f"  분석 완료!")
    print(f"  최종 리포트 → {final_path}")
    print("=" * 60)
