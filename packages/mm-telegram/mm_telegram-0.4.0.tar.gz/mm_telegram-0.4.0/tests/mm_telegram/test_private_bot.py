"""Tests for PrivateBot class."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ApplicationHandlerStop

from mm_telegram.private_bot import PrivateBot, _check_access, _ping, _unknown_command


def make_message(chat: Chat | None = None, user: User | None = None) -> Message:
    """Create a Message object for testing."""
    return Message(
        message_id=1,
        date=datetime.now(tz=UTC),
        chat=chat or Chat(id=1, type="private"),
        from_user=user,
    )


def make_update(user: User | None = None, message: Message | None = None, chat: Chat | None = None) -> Update:
    """Create an Update object for testing."""
    if message is None and (user is not None or chat is not None):
        message = make_message(chat=chat, user=user)
    return Update(update_id=1, message=message)


def make_context(allowed_users: list[int] | None = None) -> MagicMock:
    """Create a mock context with bot_data."""
    context = MagicMock()
    context.bot_data = {"allowed_users": allowed_users or []}
    context.bot.send_message = AsyncMock()
    return context


class TestPrivateBotInit:
    """Tests for PrivateBot initialization."""

    def test_stores_handlers(self) -> None:
        """Handlers list is stored on instance."""
        handlers: list[object] = []
        bot = PrivateBot(handlers=[], bot_data={})
        assert bot.handlers == handlers

    def test_stores_bot_data(self) -> None:
        """Bot data dict is stored on instance."""
        bot_data: dict[str, object] = {"key": "value"}
        bot = PrivateBot(handlers=[], bot_data=bot_data)
        assert bot.bot_data is bot_data

    def test_app_is_none_initially(self) -> None:
        """App attribute is None before start() is called."""
        bot = PrivateBot(handlers=[], bot_data={})
        assert bot.app is None


class TestPrivateBotValidation:
    """Tests for PrivateBot validation logic."""

    @pytest.mark.asyncio
    async def test_start_raises_on_empty_allowed_users(self) -> None:
        """Start raises ValueError when allowed_users is empty."""
        bot = PrivateBot(handlers=[], bot_data={})
        with pytest.raises(ValueError, match="No allowed_users provided"):
            await bot.start(token="dummy_token", allowed_users=[])


class TestCheckAccess:
    """Tests for _check_access handler using real telegram objects."""

    @pytest.mark.asyncio
    async def test_blocks_unauthorized_user(self) -> None:
        """Raises ApplicationHandlerStop for user not in allowed list."""
        update = make_update(user=User(id=999, first_name="Test", is_bot=False))
        context = make_context(allowed_users=[123, 456])

        # Patch at class level since Message objects are frozen
        with patch.object(Message, "reply_text", new_callable=AsyncMock) as mock_reply:
            with pytest.raises(ApplicationHandlerStop):
                await _check_access(update, context)
            mock_reply.assert_called_once_with("Who are you?")

    @pytest.mark.asyncio
    async def test_allows_authorized_user(self) -> None:
        """Returns normally for user in allowed list."""
        update = make_update(user=User(id=123, first_name="Test", is_bot=False))
        context = make_context(allowed_users=[123, 456])

        await _check_access(update, context)

    @pytest.mark.asyncio
    async def test_blocks_when_no_effective_user(self) -> None:
        """Raises ApplicationHandlerStop when effective_user is None."""
        update = make_update(message=make_message(user=None))
        context = make_context(allowed_users=[123])

        with pytest.raises(ApplicationHandlerStop):
            await _check_access(update, context)

    @pytest.mark.asyncio
    async def test_blocks_when_no_message(self) -> None:
        """Raises ApplicationHandlerStop when message is None."""
        update = Update(update_id=1, message=None)
        context = make_context(allowed_users=[123])

        with pytest.raises(ApplicationHandlerStop):
            await _check_access(update, context)


class TestPingHandler:
    """Tests for _ping handler."""

    @pytest.mark.asyncio
    async def test_sends_pong(self) -> None:
        """Sends 'pong' message to effective chat."""
        update = make_update(chat=Chat(id=12345, type="private"))
        context = make_context()

        await _ping(update, context)

        context.bot.send_message.assert_called_once_with(chat_id=12345, text="pong")

    @pytest.mark.asyncio
    async def test_no_send_when_no_chat(self) -> None:
        """Does nothing when effective_chat is None."""
        update = Update(update_id=1, message=None)
        context = make_context()

        await _ping(update, context)

        context.bot.send_message.assert_not_called()


class TestUnknownCommandHandler:
    """Tests for _unknown_command handler."""

    @pytest.mark.asyncio
    async def test_sends_error_message(self) -> None:
        """Sends error message to effective chat."""
        update = make_update(chat=Chat(id=12345, type="private"))
        context = make_context()

        await _unknown_command(update, context)

        context.bot.send_message.assert_called_once_with(chat_id=12345, text="Sorry, I didn't understand that command.")

    @pytest.mark.asyncio
    async def test_no_send_when_no_chat(self) -> None:
        """Does nothing when effective_chat is None."""
        update = Update(update_id=1, message=None)
        context = make_context()

        await _unknown_command(update, context)

        context.bot.send_message.assert_not_called()


class TestPrivateBotIntegration:
    """Integration tests using real Telegram API."""

    @pytest.mark.asyncio
    async def test_lifecycle(self, telegram_token: str, telegram_chat_id: int) -> None:
        """Start creates app, shutdown cleans up."""
        bot = PrivateBot(handlers=[], bot_data={"custom_key": "custom_value"})

        assert bot.app is None

        await bot.start(token=telegram_token, allowed_users=[telegram_chat_id])

        assert bot.app is not None
        assert bot.app.bot_data["allowed_users"] == [telegram_chat_id]
        assert bot.app.bot_data["custom_key"] == "custom_value"

        await bot.shutdown()

        assert bot.app is None
