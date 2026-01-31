import httpx
from typing import Union
from ._core import prepare_send_text_message, prepare_get_updates


def send_text_message(
    message: str,
    chat_id: Union[str, None] = None,
    token: Union[str, None] = None,
    raise_for_status: bool = False,
) -> dict:
    """
    Send a text message to a Telegram chat.

    :param message: The text message to send.
    :param chat_id: The ID of the chat to send the message to. If None, the default chat ID is used.
    :param token: The Telegram bot token. If None, the default token is used.
    :param raise_for_status: Whether to raise an exception if the HTTP response status code is not 200.
    :return: The JSON response from the Telegram API.
    """
    url, payload = prepare_send_text_message(
        message=message,
        chat_id=chat_id,
        token=token
    )

    response = httpx.post(url=url, json=payload)

    if raise_for_status:
        response.raise_for_status()

    return response.json()

def get_updates(
    token: Union[str, None] = None,
    raise_for_status: bool = False,
) -> dict:
    """
    Fetches and returns the latest updates from a specified endpoint.

    :param token: The Telegram bot token. If None, the default token is used.
    :param raise_for_status: Whether to raise an exception if the HTTP response status code is not 200.
    :return: The JSON response from the Telegram API.
    """
    url = prepare_get_updates(token=token)
    response = httpx.get(url=url)

    if raise_for_status:
        response.raise_for_status()

    return response.json()
