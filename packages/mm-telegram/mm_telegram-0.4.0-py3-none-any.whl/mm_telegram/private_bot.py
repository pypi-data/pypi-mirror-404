"""Private Telegram bot that only responds to allowed users."""

import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ApplicationHandlerStop,
    BaseHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

logger = logging.getLogger(__name__)


type TelegramHandler = BaseHandler[Any, ContextTypes.DEFAULT_TYPE, Any]
"""Type alias for python-telegram-bot handlers compatible with PrivateBot."""


async def _ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond with 'pong' to /ping command."""
    if update.effective_chat is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="pong")


async def _unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands with a default response."""
    if update.effective_chat is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


async def _check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Block users not in allowed_users list.

    Runs before all other handlers. Users not in the list receive "Who are you?"
    and are stopped from proceeding.
    """
    allowed_users: list[int] = context.bot_data.get("allowed_users", [])

    if update.effective_user is None or update.message is None:
        raise ApplicationHandlerStop

    if update.effective_user.id not in allowed_users:
        logger.warning("_check_access: blocked user", extra={"telegram_user_id": update.effective_user.id})
        await update.message.reply_text("Who are you?")
        raise ApplicationHandlerStop


class PrivateBot:
    """Telegram bot that only responds to allowed users.

    All messages from users not in the allowed_users list are blocked.

    Note:
        Only message-based handlers are supported (CommandHandler, MessageHandler).
        Handlers for non-message updates (CallbackQueryHandler, InlineQueryHandler,
        ChosenInlineResultHandler, etc.) will not receive responses because the
        access check cannot reply to these update types.

    """

    app: Application[Any, Any, Any, Any, Any, Any] | None

    def __init__(self, handlers: list[TelegramHandler], bot_data: dict[str, object]) -> None:
        """Initialize bot with custom handlers and initial bot data.

        Args:
            handlers: List of telegram handlers to register.
            bot_data: Initial data to populate app.bot_data.

        """
        self.handlers = handlers
        self.bot_data = bot_data
        self.app = None  # Set in start(), None when stopped

    async def start(self, token: str, allowed_users: list[int]) -> None:
        """Start the bot with given token and allowed users list.

        Raises ValueError if no allowed_users are provided.
        """
        if not allowed_users:
            raise ValueError("No allowed_users provided")
        logger.debug("Starting telegram bot...")
        app = ApplicationBuilder().token(token).build()
        for key, value in self.bot_data.items():
            app.bot_data[key] = value
        app.bot_data["allowed_users"] = allowed_users

        app.add_handler(TypeHandler(Update, _check_access), group=-1)

        for handler in self.handlers:
            app.add_handler(handler)

        app.add_handler(CommandHandler("ping", _ping))
        app.add_handler(MessageHandler(filters.COMMAND, _unknown_command))

        await app.initialize()
        await app.start()
        if app.updater is not None:
            await app.updater.start_polling()
            logger.debug("Telegram bot started.")

        self.app = app

    async def shutdown(self) -> None:
        """Stop the bot and clean up resources."""
        if self.app is not None:
            if self.app.updater is not None:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self.app = None
            logger.debug("Telegram bot stopped.")
