import os
import sys
import json
import datetime as dt
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.service.dest_recommend.place_tools import SearchPlaceId, GetDestinationPhotos
from app.service.dest_recommend.hashtag_catalog import HASHTAGS
from app.service.dest_recommend.dest_reco_chain import dest_reco_executor
from .prompts_and_scenarios import SCENARIOS

# ────────────────────────────────────────────────────────────────
# Ensure project root on path for imports
# ────────────────────────────────────────────────────────────────
SRC_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

load_dotenv()

# Constants
NUM_CARDS = 3
PHOTO_PER_CITY = 1

# ─────────────────────────────────────────────────────────────────────
# Base ChatExecutor for non-ReAct flows (Responses API)
# ─────────────────────────────────────────────────────────────────────
class ChatExecutor:
    def __init__(self, system_message: str, temperature: float = 0.0):
        # Use Responses API 
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            use_responses_api=True,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
        )
        self.system_message = system_message

    async def ainvoke(self, inputs: dict) -> dict:
        question = inputs["messages"][0]["content"]
        messages = [
            ("system", self.system_message),
            ("user", question),
        ]
        raw = self.llm.invoke(messages)
        return {"messages": [{"role": "assistant", "content": raw.content}]}

# ─────────────────────────────────────────────────────────────────────
# Executor factories: one per prompting technique
# ─────────────────────────────────────────────────────────────────────

def make_react_executor():
    return dest_reco_executor

def make_llm_config_executor():
    # Ensure the system message includes 'json' for Responses API
    sys_msg = "<no-op> Please output your recommendations as JSON."
    return ChatExecutor(system_message=sys_msg, temperature=0.1)

def make_zero_shot_executor():
    sys_msg = (
        "You are a travel assistant. Recommend TOP-3 destinations directly as JSON without examples."
    )
    return ChatExecutor(system_message=sys_msg)

def make_one_shot_executor():
    sys_msg = (
        "Example:\n"
        "Input: budget 120만·foodie·4/3–4/9\n"
        "Output: [1. Sapporo…, 2. Taipei…, 3. Busan…]\n"
        "Now, for the user request, follow the above format and output JSON."
    )
    return ChatExecutor(system_message=sys_msg)

def make_few_shot_executor():
    sys_msg = (
        "Examples:\n"
        "1) Input: … → Output: …\n"
        "2) Input: … → Output: …\n"
        "Based on the two examples, recommend TOP-3 as JSON."
    )
    return ChatExecutor(system_message=sys_msg)

def make_system_prompt_executor():
    sys_msg = "You are a professional travel consultant. Provide structured JSON recommendations."
    return ChatExecutor(system_message=sys_msg)

def make_contextual_prompt_executor():
    today = dt.date.today().isoformat()
    sys_msg = f"Today is {today} in Seoul. Provide JSON recommendations without ReAct."
    return ChatExecutor(system_message=sys_msg)

def make_role_prompt_executor():
    sys_msg = "You are a friendly customer service rep. Recommend travel in JSON format."
    return ChatExecutor(system_message=sys_msg)

def make_step_back_executor():
    sys_msg = "Before recommending, pause and think step by step, then output JSON."
    return ChatExecutor(system_message=sys_msg)

def make_cot_executor():
    sys_msg = "Think step by step and explain your reasoning, then output JSON recommendations."
    return ChatExecutor(system_message=sys_msg)

def make_self_consistency_executor():
   # Ensemble fallback: include 'json' in system prompt
    sys_msg = "<ensemble> Please output your final recommendations as JSON."
    return ChatExecutor(system_message=sys_msg, temperature=0.7)

# ─────────────────────────────────────────────────────────────────────
# Registry
 # "react": make_react_executor

# ─────────────────────────────────────────────────────────────────────
EXECUTORS = {
  #  "llm_config": make_llm_config_executor,
   # "zero_shot": make_zero_shot_executor,
   # "one_shot": make_one_shot_executor,
   # "few_shot": make_few_shot_executor,
   # "system_prompt": make_system_prompt_executor,
   # "contextual_prompt": make_contextual_prompt_executor,
   # "role_prompt": make_role_prompt_executor,
   # "step_back": make_step_back_executor,
    "cot": make_cot_executor,
    "self_consistency": make_self_consistency_executor,
}

# For manual testing
async def run_all_variants():
    from experiments.prompts_and_scenarios import SCENARIOS as LOCAL_SCENARIOS
    for scenario in LOCAL_SCENARIOS:
        print(f"\n=== Scenario {scenario['id']}: {scenario['question']} ===")
        for name, factory in EXECUTORS.items():
            executor = factory()
            if name == "react":
                res = await executor.ainvoke(
                    {"messages": [{"role": "user", "content": scenario['question']}]},
                    config={"max_rounds": 25, "recursion_limit": 60}
                )
            else:
                res = await executor.ainvoke(
                    {"messages": [{"role": "user", "content": scenario['question']}]}
                )
            raw = res['messages'][-1]['content']
            try:
                payload = json.loads(raw)
                print(f"[{name}] → {len(payload.get('cards', []))} cards")
            except:
                print(f"[{name}] → invalid JSON")

if __name__ == "__main__":
    asyncio.run(run_all_variants())
