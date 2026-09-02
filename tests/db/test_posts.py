from __future__ import annotations

import json

import pytest
import pytest_asyncio

from cs2posts.db import SqlitePostRepository
from cs2posts.dto.post import PostType


@pytest_asyncio.fixture
async def repository(tmp_path):
    repository = SqlitePostRepository.at(tmp_path / "posts.db")
    await repository.setup()
    return repository


@pytest.fixture
def news(make_post):
    return make_post(gid="news-1", title="News", date=1000)


@pytest.fixture
def update(make_post):
    return make_post(gid="update-1", title="Release Notes", date=2000)


@pytest.fixture
def external(make_post):
    return make_post(gid="external-1", title="Elsewhere", date=3000, feed_type=0)


@pytest_asyncio.fixture
async def populated(repository, news, update, external):
    for post in (news, update, external):
        await repository.save(post)
    return repository


@pytest.mark.asyncio
async def test_a_new_repository_is_empty(repository):
    assert await repository.is_empty()
    assert await repository.latest() is None


@pytest.mark.asyncio
async def test_saved_posts_round_trip(repository, news):
    await repository.save(news)

    assert not await repository.is_empty()
    assert await repository.get_by_gid("news-1") == news


@pytest.mark.asyncio
async def test_tags_survive_the_round_trip(repository, make_post):
    post = make_post(gid="tagged", tags=["patchnotes", "cs2"])

    await repository.save(post)

    stored = await repository.get_by_gid("tagged")
    assert stored is not None
    assert stored.tags == ["patchnotes", "cs2"]


@pytest.mark.asyncio
async def test_latest_without_a_type_returns_the_newest_post(populated, external):
    assert await populated.latest() == external


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("post_type", "fixture_name"),
    [
        (PostType.NEWS, "news"),
        (PostType.UPDATE, "update"),
        (PostType.EXTERNAL, "external"),
    ],
)
async def test_latest_of_a_type_returns_that_type(
    populated, request, post_type, fixture_name
):
    assert await populated.latest(post_type) == request.getfixturevalue(fixture_name)


@pytest.mark.asyncio
async def test_latest_of_a_type_returns_none_when_absent(repository, news):
    await repository.save(news)

    assert await repository.latest(PostType.EXTERNAL) is None


@pytest.mark.asyncio
async def test_latest_prefers_the_newest_of_several(repository, make_post):
    older = make_post(gid="a", date=1000)
    newer = make_post(gid="b", date=2000)
    await repository.save(older)
    await repository.save(newer)

    assert await repository.latest(PostType.NEWS) == newer


@pytest.mark.asyncio
async def test_saving_the_same_gid_twice_updates_in_place(repository, make_post):
    await repository.save(make_post(gid="same", title="First"))
    await repository.save(make_post(gid="same", title="Second"))

    assert len(await repository.load()) == 1
    stored = await repository.get_by_gid("same")
    assert stored is not None
    assert stored.title == "Second"


@pytest.mark.asyncio
async def test_get_by_gid_returns_none_when_unknown(populated):
    assert await populated.get_by_gid("nope") is None


@pytest.mark.asyncio
async def test_import_from_json_accepts_the_legacy_keyed_format(
    repository, tmp_path, news, update, external
):
    payload = {
        "news": news.to_dict(),
        "update": update.to_dict(),
        "external": external.to_dict(),
    }
    json_file = tmp_path / "posts.json"
    json_file.write_text(json.dumps(payload), encoding="utf-8")

    await repository.import_from_json(json_file)

    assert len(await repository.load()) == 3
    assert await repository.latest(PostType.UPDATE) == update


@pytest.mark.asyncio
async def test_import_from_json_ignores_absent_keys(repository, tmp_path, news):
    json_file = tmp_path / "posts.json"
    json_file.write_text(json.dumps({"news": news.to_dict()}), encoding="utf-8")

    await repository.import_from_json(json_file)

    assert len(await repository.load()) == 1


@pytest.mark.asyncio
async def test_import_from_json_rejects_a_non_object_payload(repository, tmp_path):
    """Regression: a list-shaped snapshot raised AttributeError from ``.get``,
    which bootstrap does not catch, so it took the whole bot down instead of
    being logged and skipped."""
    json_file = tmp_path / "posts.json"
    json_file.write_text(json.dumps([{"gid": "1"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a JSON object"):
        await repository.import_from_json(json_file)
