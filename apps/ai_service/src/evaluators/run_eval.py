
"""
executor → 답변 생성 → 컨텍스트 생성 → LangSmith LLM-Judge 점수 업로드
──────────────────────────────────────────────────────────────
ReAct / Step-Back / Self-Consistency 모두 동일 평가 루프에 연결
"""

from __future__ import annotations
import os, sys, asyncio, datetime as dt
from uuid import uuid4
from typing import Dict, Any, Callable
import json
import random

# ── 경로 & .env ─────────────────────────────────────────────
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from dotenv import load_dotenv
load_dotenv()

# ── LangSmith 로깅 ──────────────────────────────────────────
from langchain_teddynote import logging as ls_logging
PROJECT_NAME = "bookie"
ls_logging.langsmith(PROJECT_NAME)

# ── 외부 / 내부 모듈 ────────────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langsmith.evaluation import aevaluate
from langsmith.schemas import Example, Run

from experiments.executors import EXECUTORS
from .context_answer_dest import context_answer_dest
from .judge_prompt         import judge_prompt

# ── LLM-Judge 체인 ─────────────────────────────────────────
llm_judge = (
    judge_prompt
    | ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    | StrOutputParser()
)

def make_custom_evaluator(executor_name: str):
    async def _eval(run: Run, _: Example) -> dict:

         # 1) 모델 호출
        raw_output: str = llm_judge.invoke({
            "question": run.outputs["question"],
            "answer":   run.outputs["answer"],
            "context":  run.outputs["context"],
            "city_scores": run.outputs["city_scores"],
        })
        print("[DEBUG] judge raw:", raw_output)
        # 2) JSON 파싱
        result = json.loads(raw_output)

        return {
            f"{executor_name}_score":         result["score"],
            f"{executor_name}_calculation":  result["calculation"],
            f"{executor_name}_justification":result["justification"],
        }
    return _eval

# ── 공통 질문 & 데이터셋 ────────────────────────────────────
QUESTION   = (
"예산 120만 원, 2박3일 동안 와인과 치즈 테이스팅을 중심으로 즐길 수 있는 도시를 알려 주세요."
  # "학생이라 예산 5만 원, 3박4일 일정으로 가장 알뜰하게 다녀올 수 있는 서유럽 해외 여행지를 추천해 주세요."
  #  "부모님 모시고 7박8일간 예산 1,000만 원으로 최상의 서비스를 누릴 수 있는 고급 여행지를 추천해 주세요."
  # "할머니 할아버지 모시고 4박5일 동안 예산 3000만 원 무리 없이 편안하게 다닐 수 있는 치안이 좋고 바다 근처의 안전한 여행지를 추천해 주세요."
  #  "대학교 동기들끼리 놀러갈 건데, 제한된 예산 내에서라도 스릴 넘치는 어드벤처 코스를 즐길 수 있는 여행지를 알려 주세요."
   # "예산 100만 원, 4박5일 일정으로 한적한 해변에서 휴양할 수 있는 여행지를 추천해 주세요."
    #"예산 100만 원, 4박5일 동안 활기찬 나이트라이프와 파티를 즐길 수 있는 여행지를 추천해 주세요."
   # "예산 200만 원, 5박6일 일정으로 쇼핑도 하고 역사·문화유산도 둘러볼 수 있는 여행지를 추천해 주세요."
   # "나 예산 2000만원 있어. 이번에 로또에 당첨되어서 4일 동안 명품 쇼핑하러 해외에 가려고 해 유명 브랜드 가방들이랑, 시계 사러 가고 싶어. 추천해줘."
  # "예산 100만원 있는데, 이번에 학교 2일 휴강이여서 친구랑  우리나라 근처면서 저가 쇼핑도 많이 할 수 있는 해외 여행하려고 해. 추천해줘."
)
DATASET_ID = "d7ebde55-b668-47fb-9b34-d2eea49bf3c4"

# ── executor 실행 + 컨텍스트 생성 함수 ─────────────────────
async def execute_one(
    inputs: Dict[str, Any],
    factory: Callable[[], Any],
    name: str,
) -> Dict[str, Any]:
    executor = factory()

    # 1) LLM 응답 얻기
    if name == "react":
        answer_dict = await executor.ainvoke(
            {"messages": [{"role": "user", "content": inputs["question"]}]},
            config={"max_rounds": 25, "recursion_limit": 60},
        )
    else:
        answer_dict = await executor.ainvoke(
            {"messages": [{"role": "user", "content": inputs["question"]}]}
        )

    answer_content = answer_dict["messages"][-1]["content"]

    # 2) 실제 평가 데이터  컨텍스트 부여
    return await context_answer_dest(
        {"question": inputs["question"], "answer": answer_content}
    )

# ── main 루틴 ───────────────────────────────────────────────
async def main() -> None:
    # Example 하나만 만들어 모든 executor에 재사용
    base_example = Example(
        id=str(uuid4()),
        dataset_id=DATASET_ID,
        inputs={"question": QUESTION},
    )

    for name, factory in EXECUTORS.items():
        print(f"\n▶︎ {dt.datetime.now().isoformat(timespec='seconds')}  {name.upper()} experiment upload")

        # 비동기 래퍼 (aevaluate 가 await 할 수 있도록)
        async def run_wrapper(
            inp: Dict[str, Any],
            _f: Callable[[], Any] = factory,
            _n: str               = name,
        ) -> Dict[str, Any]:
            return await execute_one(inp, _f, _n)

        await aevaluate(
            run_wrapper,
            data=[base_example],
            evaluators=[make_custom_evaluator(name)],
            experiment_prefix=f"{name}-DEST-EVAL-{random.randint(0, 9999)}={dt.datetime.now().isoformat(timespec='seconds')}",
            metadata={"prompt_variant": name},
            upload_results=True,
        )

# ── entrypoint ─────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())