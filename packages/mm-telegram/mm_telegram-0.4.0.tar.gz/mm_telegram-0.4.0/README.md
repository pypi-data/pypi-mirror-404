# mm-telegram

A Python library for building private Telegram bots that only respond to allowed users.

## Features

- **Private by default**: Only allowed users can interact with the bot
- **Type-safe**: Full type annotations with mypy strict mode support
- **Async/await**: Built on python-telegram-bot with modern async patterns
- **Message splitting**: Automatic handling of long messages (>4096 chars)
- **Simple API**: Minimal boilerplate for common bot operations

## Quick Start

### Basic Bot

```python
from mm_telegram import PrivateBot
from telegram.ext import CommandHandler

async def hello(update, context):
    await update.message.reply_text("Hello!")

bot = PrivateBot(
    handlers=[CommandHandler("hello", hello)],
    bot_data={}
)

await bot.start(token="YOUR_BOT_TOKEN", allowed_users=[YOUR_USER_ID])
```

### Send Messages

```python
from mm_telegram import send_text_message

result = await send_text_message(
    bot_token="YOUR_BOT_TOKEN",
    chat_id=123456789,
    text="Your message here"
)

if result.is_ok():
    message_ids = result.value
    print(f"Sent messages: {message_ids}")
```

## API Reference

### PrivateBot

Private bot wrapper that only responds to allowed users.

```python
bot = PrivateBot(handlers, bot_data)
await bot.start(token, allowed_users)
await bot.shutdown()
```

- `handlers`: List of telegram handlers (CommandHandler, MessageHandler, etc.)
- `bot_data`: Initial bot data dictionary
- `token`: Bot token from @BotFather
- `allowed_users`: List of user IDs allowed to use the bot

### send_text_message

Send text messages with automatic splitting for long text.

```python
result = await send_text_message(
    bot_token="token",
    chat_id=123,
    text="text",
    timeout=5,
    delay=3.0
)
```

Returns `Result[list[int]]` with message IDs on success.

### Built-in Handlers

- `/ping` - Responds with "pong"
- Unknown commands - "Sorry, I didn't understand that command."
