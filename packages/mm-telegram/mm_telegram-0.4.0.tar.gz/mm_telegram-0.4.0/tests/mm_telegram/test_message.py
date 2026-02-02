"""Tests for message sending utilities."""

import pytest

from mm_telegram.message import _split_string, send_text_message


class TestSplitString:
    """Tests for _split_string helper function."""

    def test_empty_string(self) -> None:
        """Empty string returns empty list."""
        result = _split_string("", 10)
        assert result == []

    def test_shorter_than_limit(self) -> None:
        """String shorter than limit returns single chunk."""
        result = _split_string("hello", 10)
        assert result == ["hello"]

    def test_exactly_at_limit(self) -> None:
        """String exactly at limit returns single chunk."""
        result = _split_string("1234567890", 10)
        assert result == ["1234567890"]

    def test_longer_than_limit(self) -> None:
        """String longer than limit splits into multiple chunks."""
        result = _split_string("12345678901234567890", 10)
        assert result == ["1234567890", "1234567890"]

    def test_uneven_split(self) -> None:
        """String with uneven split has smaller final chunk."""
        result = _split_string("12345678901234", 10)
        assert result == ["1234567890", "1234"]


class TestSendTextMessage:
    """Integration tests for send_text_message using real Telegram API."""

    @pytest.mark.asyncio
    async def test_send_short_message(self, telegram_token: str, telegram_chat_id: int) -> None:
        """Send short message returns ok with single message_id."""
        result = await send_text_message(telegram_token, telegram_chat_id, "Test message from pytest")

        assert result.is_ok()
        message_ids = result.unwrap()
        assert len(message_ids) == 1
        assert isinstance(message_ids[0], int)

    @pytest.mark.asyncio
    async def test_send_long_message(self, telegram_token: str, telegram_chat_id: int) -> None:
        """Send message over 4096 chars returns multiple message_ids."""
        long_text = "A" * 5000
        result = await send_text_message(telegram_token, telegram_chat_id, long_text, delay=0.5)

        assert result.is_ok()
        message_ids = result.unwrap()
        assert len(message_ids) == 2
        assert all(isinstance(mid, int) for mid in message_ids)

    @pytest.mark.asyncio
    async def test_invalid_token(self, telegram_chat_id: int) -> None:
        """Invalid token returns error result."""
        result = await send_text_message("invalid_token", telegram_chat_id, "Test")

        assert result.is_err()
