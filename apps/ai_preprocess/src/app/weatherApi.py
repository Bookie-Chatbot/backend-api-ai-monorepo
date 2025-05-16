from fastmcp import FastMCP
import requests
import json
from dotenv import load_dotenv
import os
    # url = f"http://api.openweathermap.org/data/2.5/\
    #     weather?q={city}&appid={api_key}&units=metric"
    
    # response = requests.get(url)
    # if response.status_code != 200:
    #     return f"날씨 정보를 가져오지 못했습니다. 오류 코드: {response.status_code}"
    # data = response.json()
    # description = data['weather'][0]['description']
    # temp = data['main']['temp']
    # humidity = data['main']['humidity']
    # wind_speed = data['wind']['speed']
    # return (f"현재 {city}의 날씨는 '{description}', 온도는 {temp}°C, "
    #         f"습도는 {humidity}%, 풍속은 {wind_speed}m/s입니다.")
city=input()
lang = "kr"
load_dotenv()

weather_key = os.getenv("WEATHERMAPAPI_KEY")
api = f"""http://api.openweathermap.org/data/2.5/\
weather?q={city}&appid={weather_key}&lang={lang}&units=metric"""

result = requests.get(api)

data = json.loads(result.text)

print(data["name"],"의 날씨입니다.")
print("날씨는 ",data["weather"][0]["description"],"입니다.")
print("현재 온도는 ",data["main"]["temp"],"입니다.")
print("체감 온도는 ",data["main"]["feels_like"],"입니다.")
print("최고 기온은 ",data["main"]["temp_max"],"입니다.")
print("최저 기온은 ",data["main"]["temp_min"],"입니다.")
