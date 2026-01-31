import argparse
import asyncio
import json
import sys
from telegram_easy import __version__ as telegram_easy_version

from .aio import send_text_message, get_updates


def main():
    parser = argparse.ArgumentParser(description=f"Telegram Easy CLI {telegram_easy_version}")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand send_text_message
    send_parser = subparsers.add_parser("send_text_message", help="Send a text message")
    send_parser.add_argument("text", help="Text of the message to send")
    send_parser.add_argument("--token", required=False, help="Telegram bot token", default=None)
    send_parser.add_argument("--chat_id", required=False, help="Chat ID", default=None)

    # Subcommand get_updates
    updates_parser = subparsers.add_parser("get_updates", help="Get updates")
    updates_parser.add_argument("--token", required=False, help="Telegram bot token", default=None)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "send_text_message":
        result = asyncio.run(
            send_text_message(
                message=args.text,
                token=args.token,
                chat_id=args.chat_id
            )
        )
    elif args.command == "get_updates":
        result = asyncio.run(
            get_updates(token=args.token)
        )
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()