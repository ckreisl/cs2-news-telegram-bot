<p align="center">
  <img alt="Logo" width="300px" height="300px" src="./images/logo.png" />
  <h1 align="center">Counter-Strike 2 Posts Telegram Bot</h1>
</p>

[![CI](https://github.com/ckreisl/cs2-posts-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ckreisl/cs2-posts-telegram-bot/actions/workflows/ci.yml)

This is a simple Telegram bot providing you the latest posts (news, updates, events) about Counter Strike 2. Stay up to date about the game by retrieving automatic update messages from the bot via Telegram.

The data is crawled from the official website of [Counter Strike 2](https://www.counter-strike.net/).


> [!IMPORTANT]
> The bot is not affiliated with Valve Corporation or Counter Strike 2. The bot is a private project and is not intended for commercial use.


## Features

* Get the latest news & updates about Counter Strike 2
* General Spam protection (chat based)
* Option command to retrieve only news or updates posts
* Data is crawled from the official website and checked every 15 minutes


## Usage

> [!NOTE]
> We have a bot already up and running for you which is compeltely free to use.
> Checkout: [@CS2PostsBot](https://t.me/CS2PostsBot)

To use [@CS2PostsBot](https://t.me/CS2PostsBot), simply start a chat with the bot on Telegram. Then just write `/start` to get started and `/help` to get a list of available commands.


### Commands

* `/start` - Start the bot
* `/stop` - Stop the bot
* `/help` - Get a list of available commands
* `/news` - Get the latest news posts
* `/updates` - Get the latest updates posts
* `/latest` - Get the latest post (news & updates)
* `/options` - Option to enable / disable news or updates posts (admin only)


### Adding the Bot to a Group

Adding the bot to a group is possible. The person adding the bot to the group will be the admin of the bot. Which means only the admin can use the `/options` command to enable / disable news or updates posts for the group chat.

To prevent spamming a spam protection is implemented. After 3 (default) strikes the chat will be banned and receives a timeout. This affects the whole chat not only the user who spammed.


### Single User Chats

Similar to group chats the spam protection is enabled. The `/options` is available for the user to enable / disable news or updates posts.


## Deploying the Bot

To deploy the bot as an own instance you need to create a Telegram Bot via the [@BotFather](https://t.me/BotFather) on Telegram. After creating the bot you will receive a **token**. Rename the `.env.example` to `.env` in the root directory and add the token to the file.

```env
TELEGRAM_TOKEN=<your_token>
```

Possible environment variables:
* `TELEGRAM_TOKEN`
* `CS2_UPDATE_CHECK_INTERVAL`(default: 900)
* `CHAT_SPAM_INTERVAL_MS` (default: 750)
* `CHAT_BAN_TIMEOUT_SECONDS` (default: 600)
* `CHAT_MAX_STRIKES` (default: 3)

for detailed information see `cs2posts/bot/settings.py`.


Create a docker image and run the bot. From the root folder exeucte the following commands:

```bash
docker build -t cs2-posts-bot .
docker run -d -v cs2posts/data:/app/cs2posts/data --env-file .env --name cs2-posts-bot cs2-posts-bot
```

To start the cron job checking for news & updates write `/start` in the chat of your bot.


## Contributing

Any contributions are **highly appreciated**.


## License

Distributed under the MIT License. See `LICENSE` for more information.
