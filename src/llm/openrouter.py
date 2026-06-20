from ..core.config import setting
from ..logger import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests


class OpenRouterAPI:
    def __init__(self) -> None:
        self.url = f"{setting.OPENROUTER_API_BASE_URL}/chat/completions"
        self.logger = get_logger("openrouter")

    def stream_openrouter_response(self, messages):
        session = requests.sessions.Session()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {setting.OPENROUTER_API_KEY}",
        }
        data = {"model": setting.OPENROUTER_MODEL, "messages": messages, "stream": True}

        with session.post(
            self.url, headers=headers, json=data, stream=True
        ) as response:
            for response_lines in response.iter_lines():
                yield response_lines

    def call_openrouter_api(self, messages):

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {setting.OPENROUTER_API_KEY}",
        }
        data = {"model": setting.OPENROUTER_MODEL, "messages": messages}
        self.logger.info(
            f"calling openrouter api with header : {headers}, data : {data}"
        )
        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        response = session.post(self.url, json=data, headers=headers, timeout=60)

        if response.status_code == 200:
            return response.json()
        else:
            self.logger.exception(
                f"OpenRouter API call failed with status code {response.status_code}: {response.text}"
            )
            raise Exception(
                f"OpenRouter API call failed with status code {response.status_code}: {response.text}"
            )
