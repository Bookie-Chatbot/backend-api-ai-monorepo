import os
import json
from app import config

def load_json_file(filename: str):
    """
    지정한 JSON 파일을 로드
    """
    file_path = os.path.join(config.VIRTUAL_DB_DIR, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_virtual_db():
    """
    여러 JSON 파일을 로드하여 가상 DB 데이터를 병합
    """
    db = {}
    db["User"] = load_json_file("user.json")
    db["Hotel"] = load_json_file("hotel.json")
    db["Flight"] = load_json_file("flight.json")
    db["Reservation"] = load_json_file("reservation.json")
    db["QueryLog"] = load_json_file("querylog.json")
    db["AdminSettings"] = load_json_file("adminsettings.json")
    return db
