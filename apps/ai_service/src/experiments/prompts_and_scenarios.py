SCENARIOS = [
    {
        "id": 1,
        "question": "예산 50만원 이하로 5월에 갈 만한 해변 휴양지 추천해줘",
        # — 테스트 시뮬레이션용 정답 메트릭 (ground truth)
        "reference_turns": 6,                    # 목표 턴 수
        "reference_flow_breaks": [False] * 6,     # 각 턴의 flow-break 여부
        "reference_sus": 85,                     # 사용자 SUS 점수
    },
    {
        "id": 2,
        "question": "가족 여행으로 유럽 추천지 알려줘",
        "reference_turns": 7,
        "reference_flow_breaks": [False, False, True, False, False, False, False],
        "reference_sus": 78,
    },
]