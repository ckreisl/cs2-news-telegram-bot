<p align="center">
  <img alt="Logo" width="300px" height="300px" src="./images/logo.png" />
  <h1 align="center">Counter-Strike 2 News Telegram Bot</h1>
</p>

[![CI](https://github.com/ckreisl/cs2-news-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ckreisl/cs2-news-telegram-bot/actions/workflows/ci.yml)

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

| Variable | Default | Purpose |
| --- | --- | --- |
| `TELEGRAM_TOKEN` | *required* | Bot token from @BotFather |
| `CS2_UPDATE_CHECK_INTERVAL` | `900` | Seconds between crawls |
| `CHAT_SPAM_INTERVAL_MS` | `750` | Minimum gap between commands |
| `CHAT_BAN_TIMEOUT_SECONDS` | `600` | Ban length after the last strike |
| `CHAT_MAX_STRIKES` | `3` | Strikes before a ban |
| `CHAT_STRIKE_RECOVERY_MINUTES` | `60` | Inactivity that clears one strike |
| `CHAT_DB_FILEPATH` | `database/sqlite.db` | Chat storage |
| `POST_DB_FILEPATH` | `database/sqlite.db` | Post storage |
| `CHAT_DB_BACKUP_FILEPATH` | `backups/backup.db` | Backup target |
| `CHAT_DB_BACKUP_INTERVAL` | `86400` | Seconds between backups |
| `CHAT_DB_BACKUP_COUNT` | `5` | Timestamped backups to keep |
| `HEARTBEAT_FILEPATH` | `/app/bot.heartbeat` | Liveness file for the healthcheck |
| `IMPORT_CHATS_FROM_JSON` | *unset* | One-off import from the legacy format |
| `IMPORT_POSTS_FROM_JSON` | *unset* | One-off import from the legacy format |

Values are read, validated and frozen once at startup in `cs2posts/settings.py`;
a missing token or a non-numeric interval fails immediately with a clear message
rather than part-way through the first crawl.


Create a Docker image and run the bot. From the project root, execute:

```bash
mkdir backups
mkdir database
docker build -t cs2-news-bot .
docker run -d -v backups:/app/backups/ -v database:/app/database --env-file .env --name cs2-news-bot cs2-news-bot
```

To start periodic checking for news and updates, send `/start` to your bot chat.


## Development

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install it, then set up the environment:

```bash
uv sync
```

This creates `.venv` from `uv.lock` with the runtime and development dependencies. Common tasks are wrapped in the `Makefile`:

```bash
make test        # run the test suite
make lint        # ruff lint + format check
make format      # apply ruff fixes and formatting
make typecheck   # mypy
make check       # lint + test
make run         # run the bot locally
```

Anything else can be run through `uv run <command>`. To change dependencies, edit `[project.dependencies]` or the `dev` group in `pyproject.toml`, then run `make lock` (or `make upgrade` to move locked versions forward).


### Layout

```
cs2posts/
  settings.py     Validated configuration, built once at startup
  clock.py        Clock protocol, so time-dependent code stays testable
  exceptions.py   Error hierarchy; callers catch these, not bare Exception
  crawler.py      Steam Web API client
  feed.py         One crawl response, as PostFeed
  http.py         Shared pooled HTTP client and timeout
  utils.py        URL validation and resolution
  bot/
    cs2.py        Telegram wiring and command handlers
    notifier.py   Crawl -> diff -> broadcast
    messenger.py  Delivery, and the chat lifecycle a failure implies
    bootstrap.py  Startup: storage, legacy imports, seeding
    options.py    /options and its inline keyboard
    spam.py       Per-chat rate limiting
    backup.py     Timestamped chat-database backups
  db/
    repository.py ChatRepository / PostRepository protocols
    sqlite.py     The sqlite file and shared query helpers
    chats.py      SqliteChatRepository
    posts.py      SqlitePostRepository
  dto/            Post and Chat
  parser/         Steam bbcode/HTML -> Telegram HTML (stateless)
  content/        Splitting a post body into text, images, video, carousels
  msg/            Rendering and sending a post
```

The bot depends on the repository *protocols*, not on sqlite, so the suite
substitutes in-memory doubles (`tests/fakes.py`) rather than mocks.


## Contributing

Any contributions are **highly appreciated**.


## License

Distributed under the MIT License. See `LICENSE` for more information.
