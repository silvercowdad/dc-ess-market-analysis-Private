# DC ESS Market Analysis Project

## 프로젝트 목적
데이터센터 전력 수요 증가가 ESS 시장에 미치는 영향 조사
SDI 배터리 사업 기회 발굴 목적

## 에이전트 구조
- Agent A: 시장 정의 (선행 단독 실행, 완료 후 사용자 승인 필요)
- Agent B~H: 병렬 실행
- Agent I: 시나리오 (후행, B~H 완료 후)
- Validator 1~2: 팩트/숫자 검증
- Agent J: SDI 전략 시사점

## 실행 원칙
- A 완료 후 반드시 사용자 승인 받고 다음 단계 진행
- 수치 충돌 시 자동 처리 금지, 사용자에게 질문
- 모든 중간 결과는 reports/ 폴더에 저장
- 최종 리포트는 한국어 C-Level 형식

## 폴더 구조
- data/raw/     ← 입력 문서
- reports/      ← 각 에이전트 결과
- final/        ← 최종 리포트
