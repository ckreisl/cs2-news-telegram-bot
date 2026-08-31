from __future__ import annotations


class CS2PostsError(Exception):
    """Base class for every error raised by this package.

    Callers can catch this instead of bare ``Exception`` and still let
    programming errors (``TypeError``, ``AttributeError``, ...) propagate.
    """


class ConfigurationError(CS2PostsError):
    """The environment does not describe a runnable bot."""


class CrawlerError(CS2PostsError):
    """The Steam news API could not be queried."""


class SteamApiUnavailable(CrawlerError):
    """Steam answered, but not with a usable response."""


class InvalidSteamResponse(CrawlerError):
    """Steam answered with a body that is not the expected JSON."""


class UnsupportedPostError(CS2PostsError):
    """A post cannot be rendered into a Telegram message."""
