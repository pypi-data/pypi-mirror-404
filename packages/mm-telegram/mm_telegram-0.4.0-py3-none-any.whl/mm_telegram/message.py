"""Telegram message sending utilities."""

import asyncio

from mm_http import http_request
from mm_result import Result


async def send_text_message(
    bot_token: str,
    chat_id: int,
    text: str,
    timeout: float = 5,
    delay: float = 3.0,
) -> Result[list[int]]:
    """Send a message to a Telegram chat.

    If the message exceeds the Telegram character limit (4096),
    it will be split into multiple messages and sent sequentially
    with a delay between each part.

    Args:
        bot_token: The Telegram bot token.
        chat_id: The target chat ID.
        text: The message text to send.
        timeout: The HTTP request timeout in seconds. Defaults to 5.
        delay: The delay in seconds between sending parts of a long message. Defaults to 3.0.

    Returns:
        A Result object containing a list of message IDs for the sent messages
        on success, or an error details on failure. The 'extra' field in the
        Result contains the raw responses from the Telegram API.

    """
    parts = _split_string(text, 4096)
    responses = []
    result_message_ids = []
    for i, text_part in enumerate(parts):
        params = {"chat_id": chat_id, "text": text_part}
        res = await http_request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage", method="post", json=params, timeout=timeout
        )
        responses.append(res.model_dump)
        if res.is_err():
            return Result.err(res.error_message or "error sending message", context={"responses": responses})

        message_id = res.json_body_or_none("result.message_id")
        if message_id is not None:
            result_message_ids.append(message_id)
        else:
            return Result.err("unknown_response_structure", context={"responses": responses})

        if i < len(parts) - 1:
            await asyncio.sleep(delay)
    return Result.ok(result_message_ids, context={"responses": responses})


def _split_string(text: str, chars_per_string: int) -> list[str]:
    """Split a string into a list of strings, each with a maximum length."""
    return [text[i : i + chars_per_string] for i in range(0, len(text), chars_per_string)]
