<p align="center">
  <img alt="Logo" width="300px" height="300px" src="./images/logo.png" />
  <h1 align="center">Counter-Strike 2 News Telegram Bot</h1>
</p>

[![CI](https://github.com/ckreisl/cs2-posts-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ckreisl/cs2-posts-telegram-bot/actions/workflows/ci.yml)

This is a simple Telegram bot that provides the latest Counter-Strike 2 posts (news, updates, and events). Stay up to date by receiving automatic update messages via Telegram.

The data is crawled from the official Steam Web API (https://steamcommunity.com/dev).


> [!IMPORTANT]
> The bot is not affiliated with Valve Corporation or Counter Strike 2. The bot is a private project and is not intended for commercial use.


## Features

* Get the latest Counter-Strike 2 news and updates
* General chat-based spam protection
* Options command to receive only selected post types (news, updates, or external news)
* Data is crawled from the official Steam API and checked every few minutes (default: 15 minutes)


## Usage

> [!NOTE]
> We already have a bot running for you that is completely free to use.
> Check it out: [@CS2PostsBot](https://t.me/CS2PostsBot)

To use [@CS2PostsBot](https://t.me/CS2PostsBot), simply start a chat with the bot on Telegram. Then just write `/start` to get started and `/help` to get a list of available commands.


### Commands

* `/start` - Start the bot
* `/stop` - Stop the bot
* `/help` - Get a list of available commands
* `/news` - Get the latest news post
* `/update` - Get the latest update post
* `/external` - Sends the latest external post
* `/latest` - Get the latest post
* `/options` - Enable or disable news, update, and external posts (admin only)


### Adding the Bot to a Group

You can add the bot to a group. The person who adds the bot becomes the bot admin. This means only the admin can use `/options` to enable or disable news, update, or external news posts for that group.

Spam protection is enabled. After 3 strikes (default), the chat is banned for a timeout period. This affects the whole chat, not only the user who spammed.


### Single User Chats

As in group chats, spam protection is enabled. The `/options` command is available to enable or disable news, update, or external posts.


## Deploying the Bot

To deploy your own bot instance, create a Telegram bot via [@BotFather](https://t.me/BotFather). After creating the bot, you will receive a token. Rename .env.example to .env in the project root and add the token.

```env
TELEGRAM_TOKEN=<your_token>
```

Possible environment variables:
* `TELEGRAM_TOKEN`
* `CS2_UPDATE_CHECK_INTERVAL` (default: 900)
* `CHAT_SPAM_INTERVAL_MS` (default: 750)
* `CHAT_BAN_TIMEOUT_SECONDS` (default: 600)
* `CHAT_MAX_STRIKES` (default: 3)
* `CHAT_STRIKE_RECOVERY_MINUTES` (default: 60)

For detailed information, see `cs2posts/bot/settings.py`.


Create a Docker image and run the bot. From the project root, execute:

```bash
mkdir backups
mkdir database
docker build -t cs2-news-bot .
docker run -d -v backups:/app/backups/ -v database:/app/database --env-file .env --name cs2-news-bot cs2-news-bot
```

To start periodic checking for news and updates, send `/start` to your bot chat.


## Contributing

Any contributions are **highly appreciated**.


## License

Distributed under the MIT License. See `LICENSE` for more information.
