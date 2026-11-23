"""無狀態 Flask 天氣預報代理，適用於本機與 Vercel。"""

from math import isfinite

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_PARAMS = {
    "latitude": 25.0330,
    "longitude": 121.5654,
    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
    "forecast_days": 5,
    "timezone": "Asia/Taipei",
}
REQUEST_TIMEOUT = (3.05, 8)


class ForecastError(Exception):
    """可安全回傳給前端的上游錯誤。"""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def _parse_forecast(payload):
    """檢查上游必要欄位及值，避免把不可信資料直接送到瀏覽器。"""
    if not isinstance(payload, dict) or not isinstance(payload.get("daily"), dict):
        raise ForecastError("天氣服務回傳的資料格式不正確。")

    daily = payload["daily"]
    dates = daily.get("time")
    highs = daily.get("temperature_2m_max")
    lows = daily.get("temperature_2m_min")
    codes = daily.get("weather_code")
    if not all(isinstance(values, list) for values in (dates, highs, lows, codes)):
        raise ForecastError("天氣服務缺少必要的預報欄位。")
    if not dates or not (len(dates) == len(highs) == len(lows) == len(codes)):
        raise ForecastError("天氣服務回傳的預報欄位不完整。")

    forecast = []
    for date, high, low, code in zip(dates, highs, lows, codes):
        if (not isinstance(date, str) or len(date) != 10 or date[4:5] != "-" or date[7:8] != "-"
                or not isinstance(code, int) or isinstance(code, bool) or code < 0 or code > 99):
            raise ForecastError("天氣服務回傳了無效的預報資料。")
        if not _valid_number(high) or not _valid_number(low):
            raise ForecastError("天氣服務回傳了無效的溫度資料。")
        forecast.append({"date": date, "high": high, "low": low, "code": code})
    return forecast


def _valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify(ok=True)


@app.get("/api/天氣預報")
def weather_forecast():
    try:
        response = requests.get(FORECAST_URL, params=FORECAST_PARAMS, timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        return jsonify(ok=False, error="連線逾時，請稍後再試。"), 504
    except requests.RequestException:
        return jsonify(ok=False, error="目前無法連接天氣服務，請稍後再試。"), 502

    if response.status_code == 429:
        return jsonify(ok=False, error="天氣服務目前流量較大，請稍後再試。"), 503
    if not 200 <= response.status_code < 300:
        return jsonify(ok=False, error="天氣服務暫時無法提供資料。"), 502
    try:
        payload = response.json()
    except (ValueError, requests.JSONDecodeError):
        return jsonify(ok=False, error="天氣服務回傳了無法讀取的資料。"), 502

    try:
        forecast = _parse_forecast(payload)
    except ForecastError as error:
        return jsonify(ok=False, error=str(error)), error.status
    return jsonify(ok=True, location="臺北市", forecast=forecast, source="Open-Meteo")


if __name__ == "__main__":
    app.run(debug=True)
