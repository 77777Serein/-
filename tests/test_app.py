import unittest
from unittest.mock import Mock, patch

import requests

import app as weather_app


def valid_payload():
    return {"daily": {"time": ["2026-11-23"], "temperature_2m_max": [24.5],
                      "temperature_2m_min": [18.2], "weather_code": [2]}}


class WeatherAppTests(unittest.TestCase):
    def setUp(self):
        weather_app.app.config["TESTING"] = True
        self.client = weather_app.app.test_client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("天氣預測".encode(), response.data)
        self.assertIn(b"open-meteo.com/en/docs", response.data)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})

    @patch("app.requests.get")
    def test_success(self, get):
        get.return_value = Mock(status_code=200, json=Mock(return_value=valid_payload()))
        response = self.client.get("/api/天氣預報")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["source"], "Open-Meteo")
        self.assertEqual(response.get_json()["forecast"][0]["high"], 24.5)
        get.assert_called_once_with(weather_app.FORECAST_URL, params=weather_app.FORECAST_PARAMS,
                                    timeout=weather_app.REQUEST_TIMEOUT)

    @patch("app.requests.get", side_effect=requests.Timeout)
    def test_timeout(self, _get):
        self.assertEqual(self.client.get("/api/天氣預報").status_code, 504)

    @patch("app.requests.get")
    def test_rate_limited(self, get):
        get.return_value = Mock(status_code=429)
        self.assertEqual(self.client.get("/api/天氣預報").status_code, 503)

    @patch("app.requests.get")
    def test_invalid_json(self, get):
        get.return_value = Mock(status_code=200, json=Mock(side_effect=ValueError("bad json")))
        self.assertEqual(self.client.get("/api/天氣預報").status_code, 502)

    @patch("app.requests.get")
    def test_missing_required_field(self, get):
        payload = valid_payload()
        del payload["daily"]["temperature_2m_min"]
        get.return_value = Mock(status_code=200, json=Mock(return_value=payload))
        self.assertEqual(self.client.get("/api/天氣預報").status_code, 502)

    @patch("app.requests.get")
    def test_rejects_invalid_date(self, get):
        payload = valid_payload()
        payload["daily"]["time"] = ["javascript:1"]
        get.return_value = Mock(status_code=200, json=Mock(return_value=payload))
        self.assertEqual(self.client.get("/api/天氣預報").status_code, 502)

    @patch("app.requests.get")
    def test_upstream_url_is_fixed_https(self, get):
        get.return_value = Mock(status_code=200, json=Mock(return_value=valid_payload()))
        self.client.get("/api/天氣預報?url=http://example.invalid")
        self.assertEqual(weather_app.FORECAST_URL, "https://api.open-meteo.com/v1/forecast")
        self.assertEqual(get.call_args.args[0], weather_app.FORECAST_URL)


if __name__ == "__main__":
    unittest.main()
