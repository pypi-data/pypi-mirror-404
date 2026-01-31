import sys
from unittest.mock import patch, AsyncMock

import pytest

from telegram_easy.cli import main


class TestCliHelp:
    """Tests for CLI help."""

    def test_help_no_arguments(self, capsys):
        """Shows help if no arguments are passed."""
        with patch.object(sys, "argv", ["telegram-easy"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Telegram Easy CLI" in captured.out
        assert "send_text_message" in captured.out
        assert "get_updates" in captured.out

    def test_help_flag(self, capsys):
        """Shows help with --help flag."""
        with patch.object(sys, "argv", ["telegram-easy", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "Telegram Easy CLI" in captured.out

    def test_unknown_command(self, capsys):
        """Shows help if the command does not exist."""
        with patch.object(sys, "argv", ["telegram-easy", "unknown_command"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0


class TestCliSendTextMessage:
    """Tests for send_text_message command."""

    def test_send_text_message_success(self, capsys):
        """Sends a message successfully."""
        mock_response = {"ok": True, "result": {"message_id": 123}}

        with patch.object(sys, "argv", [
            "telegram-easy", "send_text_message", "Hi!",
            "--token", "xxx", "--chat_id", "123"
        ]):
            with patch(
                "telegram_easy.cli.send_text_message",
                new_callable=AsyncMock,
                return_value=mock_response
            ) as mock_send:
                main()
                mock_send.assert_called_once_with(
                    message="Hi",
                    token="xxx",
                    chat_id="123"
                )

        captured = capsys.readouterr()
        assert '"ok": true' in captured.out
        assert '"message_id": 123' in captured.out

    def test_send_text_message_missing_token(self):
        """Error if token is missing."""
        with patch.object(sys, "argv", [
            "telegram-easy", "send_text_message", "Hola!",
            "--chat_id", "123"
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_send_text_message_missing_chat_id(self):
        """Error if chat_id is missing."""
        with patch.object(sys, "argv", [
            "telegram-easy", "send_text_message", "Hola!",
            "--token", "xxx"
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_send_text_message_missing_text(self):
        """Error if text is missing."""
        with patch.object(sys, "argv", [
            "telegram-easy", "send_text_message",
            "--token", "xxx", "--chat_id", "123"
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0


class TestCliGetUpdates:
    """Tests for get_updates command."""

    def test_get_updates_success(self, capsys):
        """Gets updates successfully."""
        mock_response = {"ok": True, "result": []}

        with patch.object(sys, "argv", [
            "telegram-easy", "get_updates", "--token", "xxx"
        ]):
            with patch(
                "telegram_easy.cli.get_updates",
                new_callable=AsyncMock,
                return_value=mock_response
            ) as mock_updates:
                main()
                mock_updates.assert_called_once_with(token="xxx")

        captured = capsys.readouterr()
        assert '"ok": true' in captured.out
        assert '"result": []' in captured.out

    def test_get_updates_missing_token(self):
        """Error if token is missing."""
        with patch.object(sys, "argv", ["telegram-easy", "get_updates"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0