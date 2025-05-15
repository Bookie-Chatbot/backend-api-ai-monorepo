from langchain.prompts import ChatPromptTemplate

judge_prompt: ChatPromptTemplate = ChatPromptTemplate.from_template(
    """
You are an impartial **LLM-as-Judge**.

════════════════════════════════════
# Question
{question}

# Assistant response
{answer}

# External facts
{context}

# Pre-computed per-city scores  (list of dicts like
#   {{ "city": "파리", "budget_score": 8, "shopping_score": 7 }} )
{city_scores}
════════════════════════════════════

## Grading rubric (0–10 each)

1. **Accuracy** — Assistant response *전체* (설명·description 포함) 와 External facts를 비교.
    - Start **10**.  −2 per contradiction, −1 per unverifiable key fact (min 0).

2. **Budget Feasibility** — Let
  `B = mean(item["budget_score"] for item in city_scores)`   (0 – 10). \
   Use **B** directly.

3. **Shopping Appeal** — Let
   `S = mean(item["shopping_score"] for item in city_scores)`   (0 – 10). \
   Use **S** directly.

4. **Tone & Role Compliance** - `description` 문체가 “친근하고 전문적인 여행 가이드” 역할을 지켰는가?
   = 10 = perfect, 7 = minor drift, 4 = noticeable drift, 1 = off-tone.

### Final normalized score
`(Accuracy + B + S + ToneRole) / 40`  → three-decimal float.

### Output format (JSON only)


{{
"score": float // result of the below calculation
"calculation": string, // e.g. "Acc:8, Budget:9, Shop:6, Tone:7 → 30/40=0.75"
"justification": string // concise rationale
}}
"""
)

