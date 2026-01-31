import pytest

from telegram_easy import send_text_message
from utl_test import remove_env_vars

def test_send_text_message_error():
    remove_env_vars()

    with pytest.raises(ValueError):
        send_text_message(message="test")

    with pytest.raises(ValueError):
        send_text_message(message="test", token="123")

    with pytest.raises(ValueError):
        send_text_message(message="test", chat_id="123")



