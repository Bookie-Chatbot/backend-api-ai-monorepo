import asyncio
import json
import os
import sys

SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from .executors import EXECUTORS
from experiments.prompts_and_scenarios import SCENARIOS

async def run_all_variants():
    """
    프롬프트 기법별로 각 시나리오를 실행하고 결과를 출력합니다.
    """
    for scenario in SCENARIOS:
        print(f"\n=== Scenario {scenario['id']}: {scenario['question']} ===")
        for name, factory in EXECUTORS.items():
            executor = factory()
            # ReAct flow만 별도 config 전달
            if name == "react":
                response = await executor.ainvoke(
                    {"messages": [{"role": "user", "content": scenario['question']}]},
                    config={"max_rounds": 25, "recursion_limit": 60}
                )
            else:
                response = await executor.ainvoke(
                    {"messages": [{"role": "user", "content": scenario['question']}]}
                )

            # Extract last message content
            try:
                last_msg = response['messages'][-1]
                raw = last_msg['content']
            except Exception:
                raw = response if not hasattr(response, 'content') else response.content

            # Normalize raw to a JSON-like object
            if isinstance(raw, (dict, list)):
                payload = raw if isinstance(raw, dict) else {'cards': raw}
            else:
                try:
                    payload = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    print(f"[{name}] → invalid JSON: {raw}")
                    continue

            # Print card count
            cards = payload.get('cards', [])
            print(f"[{name}] → {len(cards)} cards")

if __name__ == "__main__":
    asyncio.run(run_all_variants())
