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
            print(f"--> Starting executor: {name}")
            executor = factory()
            try:
                # invoke
                print(f"    Invoking {name}.ainvoke...")
                # ReAct flow만 별도 config 전달
                if name == "react":
                    response = await executor.ainvoke(
                        {"messages": [{"role": "user", "content": scenario['question']} ]},
                        config={"max_rounds": 25, "recursion_limit": 60}
                    )
                else:
                    response = await executor.ainvoke(
                        {"messages": [{"role": "user", "content": scenario['question']}]}
                    )
                print(f"    Received response from {name}")
            except Exception as e:
                print(f"    ERROR invoking {name}: {e}")
                continue

            # Extract raw content
            try:
                last_msg = response['messages'][-1]
                raw = last_msg['content']
                print(f"    Raw content (type={type(raw)}): {raw}")
            except Exception as e:
                raw = response.content if hasattr(response, 'content') else str(response)
                print(f"    Fallback raw content: {raw} (error: {e})")

            # Normalize raw
            if isinstance(raw, (dict, list)):
                payload = raw if isinstance(raw, dict) else {'cards': raw}
                print(f"    Using raw directly as payload")
            else:
                try:
                    payload = json.loads(raw)
                    print(f"    Parsed JSON payload successfully")
                except (TypeError, json.JSONDecodeError) as e:
                    print(f"    JSON parse error: {e}, raw was: {raw}")
                    continue

            # Print card count
            cards = payload.get('cards', [])
            print(f"[{name}] → {len(cards)} cards")

if __name__ == "__main__":
    asyncio.run(run_all_variants())
