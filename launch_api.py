# launch_api.py
import subprocess
import sys

def main():
    # 현재 가상환경의 파이썬과 uvicorn 모듈을 사용
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--app-dir", "apps/api_server/workspace/fastapi-project",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    subprocess.run(cmd, check=True)
if __name__ == "__main__":
    main()
