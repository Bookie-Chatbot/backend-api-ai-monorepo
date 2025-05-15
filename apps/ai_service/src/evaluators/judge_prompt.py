from langchain.prompts import ChatPromptTemplate

judge_prompt = ChatPromptTemplate.from_template(
    """
You are an impartial LLM-as-Judge.

════════════════════════════════════
# Question
{question}

# Assistant response
{answer}

# External context (real-world data)
{context}
════════════════════════════════════

## Grading rubric (0-10 each)

1. **Accuracy** — Does the response contradict or faithfully reflect the context?
2. **Budget Feasibility** — For a 3-night trip, sum of daily cost × 3:
   · ≤ ₩500 000 → 10 · ≤ ₩600 000 → 7 · ≤ ₩750 000 → 4 · > ₩750 000 → 0
3. **Shopping Appeal** — Number of shopping POIs in the city:
   · ≥ 300 → 10 · ≥ 150 → 7 · ≥ 50 → 4 · < 50 → 0

### Final normalized score
`(Accuracy + Budget Feasibility + Shopping Appeal) ÷ 30` → 0 – 1 float.

**출력 포맷**
반드시 **유효한 JSON**로, 다음 필드를 포함하세요:
이 밖의 필드는 포함하지 마세요.

```
{{
  "score": float,           // 0.0–1.0 사이
  "calculation": string,    // 예: "Accuracy:10, Budget:7, Shopping:4; (10+7+4)/30=0.7"
  "justification": string   // 한두 문장 분량의 근거 설명
}}
"""
)

