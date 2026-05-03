import logging
import time

import requests

logger = logging.getLogger(__name__)


class WebhookClient:
    _MAX_ATTEMPTS = 3
    _TIMEOUT = 5
    _INITIAL_BACKOFF = 1.0

    def __init__(self, url: str, secret: str):
        self._url = url
        self._secret = secret

    def notify_horn(self, event_id: str) -> None:
        payload = {"event_id": event_id}
        headers = {"X-Webhook-Secret": self._secret}

        backoff = self._INITIAL_BACKOFF
        for attempt in range(1, self._MAX_ATTEMPTS + 1):
            try:
                response = requests.post(
                    self._url,
                    json=payload,
                    headers=headers,
                    timeout=self._TIMEOUT,
                )
            except requests.RequestException as e:
                logger.warning(
                    "horn webhook attempt %d/%d failed: %s",
                    attempt,
                    self._MAX_ATTEMPTS,
                    e,
                )
            else:
                status = response.status_code
                if status == 202:
                    return
                if 400 <= status < 500:
                    logger.error(
                        "horn webhook returned %d (no retry): %s",
                        status,
                        response.text,
                    )
                    return
                logger.warning(
                    "horn webhook attempt %d/%d returned %d",
                    attempt,
                    self._MAX_ATTEMPTS,
                    status,
                )

            if attempt < self._MAX_ATTEMPTS:
                time.sleep(backoff)
                backoff *= 2
