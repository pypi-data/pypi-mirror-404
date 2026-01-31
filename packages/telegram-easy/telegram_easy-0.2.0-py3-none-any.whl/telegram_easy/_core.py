import os
from typing import Union, Tuple, Dict


BASE_URL = "https://api.telegram.org/bot"

def get_chat_id(
    chat_id: Union[str, None] = None,
) -> str:
    if chat_id is None:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if chat_id is None:
            raise ValueError("Either the 'chat_id' parameter or the TELEGRAM_CHAT_ID environment variable must be set")
    return chat_id

def get_token(
    token: Union[str, None] = None,
) -> str:
    if token is None:
        token = os.getenv("TELEGRAM_TOKEN")
        if token is None:
            raise ValueError("Either the 'token' parameter or the TELEGRAM_TOKEN environment variable must be set")
    return token

def prepare_send_text_message(
    message: str,
    chat_id: Union[str, None] = None,
    token: Union[str, None] = None,
) -> Tuple[str, Dict]:

    chat_id = get_chat_id(chat_id=chat_id)
    token = get_token(token=token)

    url = f"{BASE_URL}{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    return url, payload


def prepare_get_updates(
    token: Union[str, None] = None,
) -> str:

    token = get_token(token=token)

    url = f"{BASE_URL}{token}/getUpdates"

    return url
