# setup.py
from setuptools import setup, find_packages


'''
mcp-server      # MCP 서버 기동
mcp-client      # MCP 클라이언트 호출
mcp-test        # 통합 테스트 스크립트 실행
preprocess      # apps.ai_service.src.main_preprocess 실행
"bookie-chat = apps.ai_service.src.main_service:main"
api-server      # FastAPI(Uvicorn) 서버 기동


'''



setup(
      name="bookie",
    version="0.1.0",

    # ── 여기에 쓸 최상위 패키지를 전부 나열 ──
    packages=[
      *find_packages(where="."),
        "root",  # 루트 패키지
        "mcp",
        "app_preprocess",
        "service",
        "chains",
        "database",
        "app_service",
        "app_service.service",
        "api_server",
        "api_server.routers",
        "chatbot_contents",
        "core_backend",
        "test",
    ],

    # “싱글 파일 모듈”은 find_packages 로 잡히지 않으므로 명시 필요
     py_modules=[
          "launch_api",       # launch_api.py 을 bookie 패키지에 포함
    ],

    # ── 그 패키지들이 실제로 어디 폴더에 있는지 1:1 맵핑 ──
    package_dir={
        # 원래 일반 패키지들 인식될 수 있게끔 루트도 포함
        "": ".",
        "root":                 "",
        "mcp":                  "apps/ai_preprocess/src/mcp",
        "app_preprocess":       "apps/ai_preprocess/src/app",
        "service":              "apps/ai_service/src",
        "app_service":          "apps/ai_service/src/app",
        "app_service.service":  "apps/ai_service/src/app/service",
        "chains":               "apps/ai_service/src/app/chains",
        "database":             "apps/api-server/workspace/fastapi-project/database",
        "api_server":           "apps/api-server/workspace/fastapi-project",
        "api_server.routers":   "apps/api-server/workspace/fastapi-project/routers",
        "chatbot_contents":     "packages/chatbot_contents",
        "core_backend":         "packages/core_backend",
        "test":                 "runs/test",


    },
    py_directories=["apps/ai_service/src"],

    # 4) console_scripts 엔트리포인트
    entry_points={
        "console_scripts": [
            # MCP 서버·클라이언트·테스트
            "mcp-server    = mcp.mcp_server:main",
            "mcp-client    = mcp.mcp_client:main",
            "mcp-test      = runs.test.mcp:main",
            "mcp-test2    = runs.test.mcp2:main",

            # 의도 분류 테스트
            "intent-test   = runs.test.intent:main",
            "main = runs.main:main",

            # AI 서비스 전처리 & 메인 서비스
            "preprocess    = app_preprocess.main_preprocess:main",
            "bookie-chat  = service.main_service:main",

            # FastAPI 서버 실행 (uvicorn wrapper)
            "api-server    = launch_api:main",
        ],
    },
)
