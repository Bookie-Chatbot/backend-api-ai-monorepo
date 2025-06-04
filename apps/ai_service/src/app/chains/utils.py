from pydantic import BaseModel
from enum import Enum
from pydantic.json import pydantic_encoder
from chatbot_contents.intents import IntentOnly, Intent

def to_json(obj):
    # debug hook
    print(f"[to_json] {type(obj)} ➜", end=" ")

    if isinstance(obj, BaseModel):
        dumped = obj.model_dump(mode="json")
        print("BaseModel → dict")
        return dumped

    if isinstance(obj, IntentOnly):
        return obj.intent.value          # 또는 str(obj.intent)


    if isinstance(obj, Enum):
        print("Enum → value")
        return obj.value

    try:
        dumped = pydantic_encoder(obj)
        print("pydantic_encoder")
        return dumped
    except TypeError:
        print("fallback str")
        return str(obj)
