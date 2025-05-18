from langchain.prompts import ChatPromptTemplate

judge_prompt = ChatPromptTemplate.from_template(
    """
You are an impartial **LLM-as-Judge**.

════════════════════════════════════
# Question
{question}

# Assistant response
{answer}

# External facts
{context}
## 도시별 예산 점수, 쇼핑 점수
city_en,country_en,daily_usd,shopping_poi
Paris,France,110,480
London,United Kingdom,130,520
Barcelona,Spain,90,340
Berlin,Germany,85,310
Rome,Italy,95,290
Amsterdam,Netherlands,105,330
Lisbon,Portugal,70,220
Prague,Czechia,60,200
Vienna,Austria,100,250
Munich,Germany,120,350

# Pre-computed per-city scores
{city_scores}
════════════════════════════════════

## Grading rubric (0–10 each, sum / 40)

1. **Accuracy** — Assistant response 전체(설명· answer 포함)와 External facts 비교.
   • 시작점 10 → 모순 당 −2, 확인 불가 −1, 최소 0.

2. **Budget Feasibility** —
   `B = mean(item["budget_score"] for item in city_scores)`
   (0–10)

3. **Shopping Appeal** —
   `S = mean(item["shopping_score"] for item in city_scores)`
   (0–10)

4. **Tone & Role Compliance** —
   `T =` “친근하고 전문적인 여행 가이드” 역할대로 `description` 문체가 지켜졌는가?
   • 완벽 10, 약간 이탈 7, 명백 불일치 3, 완전 실패 0.

### 최종 normalized score
(Accuracy + B + S + T) / 40 → 소수 둘째 자리까지

### 출력 형식 (JSON only)

{{
"score": float, // 0.00–1.00
"calculation": string, // e.g. "Acc:8.0, B:7.5, S:4.3, T:10.0 => (8.0+7.5+4.3+10.0)/40=0.74"
"justification": string // 한두 문장 분량, 정확도와 tone, role compliance가 각각 10점에서 감점이 있었다면 왜 그렇게  평가했는지 구체적으로 설명(만점이 아니라, 약간의 감점이 있었으면 왜 그런지도 설명 포함)
}}

"""
)