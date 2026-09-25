# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0", "httpx>=0.25", "pydantic>=2.10.6"]
# ///
"""Turn a week of a Discord server's messages into an HTML newsletter, and post it where your readers are.

The script fetches the last seven days of messages from the channels you name, through Discord's API with a bot token,
shapes them into the input the cookbook's Discord newsletter method takes, runs the method by its address, and writes
the newsletter to newsletter.html. With `DIGEST_WEBHOOK_URL` set, it also posts the HTML there: an email service, a
CMS, or any endpoint that takes an HTML body.

    uv run digest.py <channel id>...     # needs DISCORD_BOT_TOKEN: a bot with the Message Content intent, invited with Read Message History
    uv run digest.py --sample            # the method's own sample week, no Discord needed

`PIPELEX_API_KEY` must be set; each newsletter is one run on the hosted API and spends credit.
"""

import argparse
import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from pipelex_sdk.client import PipelexAPIClient
from pydantic import BaseModel, TypeAdapter

from generated.discord_newsletter.models import Attachment, DiscordChannelUpdate, DiscordMessage, Embed, Text

METHOD_REF = "github.com/Pipelex/pipelex-cookbook/discord_newsletter@v0.18.0"
SAMPLE_INPUTS_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.18.0/methods/discord_newsletter/inputs.json"
DISCORD_API = "https://discord.com/api/v10"
DAYS = 7
TOO_MANY_REQUESTS = 429


# What Discord's API returns, cut down to what the newsletter reads.
class DiscordAuthor(BaseModel):
    username: str
    global_name: str | None = None


class DiscordAttachment(BaseModel):
    filename: str
    url: str


class DiscordEmbed(BaseModel):
    title: str | None = None
    description: str | None = None
    type: str | None = None


class DiscordApiMessage(BaseModel):
    id: str
    timestamp: datetime
    content: str
    author: DiscordAuthor
    attachments: list[DiscordAttachment] = []
    embeds: list[DiscordEmbed] = []


class DiscordChannel(BaseModel):
    id: str
    name: str
    guild_id: str


class RateLimited(BaseModel):
    """The body of Discord's 429: how many seconds to wait before asking again."""

    retry_after: float


MESSAGES = TypeAdapter(list[DiscordApiMessage])


async def discord_get(http: httpx.AsyncClient, path: str, *, params: dict[str, str | int] | None = None) -> httpx.Response:
    """GET from Discord's API, waiting out a rate limit as Discord asks rather than failing on it."""
    while True:
        response = await http.get(path, params=params)
        if response.status_code != TOO_MANY_REQUESTS:
            return response.raise_for_status()
        wait = RateLimited.model_validate(response.json()).retry_after
        print(f"rate limited by Discord, waiting {wait:.1f}s", file=sys.stderr)
        await asyncio.sleep(wait)


async def fetch_channel_update(http: httpx.AsyncClient, channel_id: str, *, position: int, since: datetime) -> DiscordChannelUpdate:
    """One channel's messages since `since`, oldest first, in the shape the method's `DiscordChannelUpdate` declares.

    `position` is where the channel's section goes in the newsletter, which the method orders its sections by.
    """
    channel = DiscordChannel.model_validate((await discord_get(http, f"/channels/{channel_id}")).json())
    messages: list[DiscordApiMessage] = []
    before: str | None = None
    while True:
        params: dict[str, str | int] = {"limit": 100} | ({"before": before} if before else {})
        page = MESSAGES.validate_python((await discord_get(http, f"/channels/{channel_id}/messages", params=params)).json())
        recent = [message for message in page if message.timestamp >= since]
        messages.extend(recent)
        if len(recent) < len(page) or len(page) < 100:
            break
        before = page[-1].id
    return DiscordChannelUpdate(
        name=channel.name,
        position=position,
        messages=[
            DiscordMessage(
                author=message.author.global_name or message.author.username,
                content=message.content,
                attachments=[Attachment(name=attachment.filename, url=attachment.url) for attachment in message.attachments],
                embeds=[Embed(title=embed.title or "", description=embed.description or "", type=embed.type or "") for embed in message.embeds],
                link=f"https://discord.com/channels/{channel.guild_id}/{channel.id}/{message.id}",
            )
            for message in reversed(messages)
        ],
    )


async def fetch_week(channel_ids: list[str], *, token: str) -> list[DiscordChannelUpdate]:
    since = datetime.now(UTC) - timedelta(days=DAYS)
    async with httpx.AsyncClient(base_url=DISCORD_API, headers={"Authorization": f"Bot {token}"}) as http:
        return [await fetch_channel_update(http, channel_id, position=index, since=since) for index, channel_id in enumerate(channel_ids)]


async def fetch_sample_week() -> list[DiscordChannelUpdate]:
    """The method's sample week, from the inputs its cookbook page links to."""
    async with httpx.AsyncClient() as http:
        sample = (await http.get(SAMPLE_INPUTS_URL)).raise_for_status().json()
    return TypeAdapter(list[DiscordChannelUpdate]).validate_python(sample["discord_channel_updates"]["content"])


async def write_newsletter(updates: list[DiscordChannelUpdate]) -> str:
    async with PipelexAPIClient() as client:
        results = await client.start_and_wait(
            method_ref=METHOD_REF,
            inputs={
                "discord_channel_updates": {
                    "concept": "discord_newsletter.DiscordChannelUpdate",
                    "content": [update.model_dump(mode="json") for update in updates],
                }
            },
        )
    print(f"newsletter written by run {results.pipeline_run_id}", file=sys.stderr)
    # The method's HtmlNewsletter concept declares no fields of its own, so its content is a text holding the HTML.
    return Text.model_validate(results.main_stuff).text


async def post(html: str, *, webhook_url: str) -> None:
    """Post the newsletter to the webhook, never printing its URL: a webhook URL often carries its secret in its path."""
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(webhook_url, content=html, headers={"Content-Type": "text/html; charset=utf-8"})
    except httpx.HTTPError as exc:
        sys.exit(f"the webhook could not be reached ({type(exc).__name__}); the newsletter is saved all the same")
    if response.is_error:
        sys.exit(f"the webhook refused the newsletter (HTTP {response.status_code}); it is saved all the same")
    print(f"posted to DIGEST_WEBHOOK_URL (HTTP {response.status_code})", file=sys.stderr)


async def gather_and_write(channel_ids: list[str], *, sample: bool) -> str:
    if sample:
        updates = await fetch_sample_week()
    else:
        token = os.environ.get("DISCORD_BOT_TOKEN")
        if not token:
            sys.exit("DISCORD_BOT_TOKEN is not set: give the script a bot token, or try it with --sample")
        updates = await fetch_week(channel_ids, token=token)
    message_count = sum(len(update.messages or []) for update in updates)
    print(f"{message_count} message(s) from {len(updates)} channel(s)", file=sys.stderr)
    return await write_newsletter(updates)


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn a week of Discord messages into an HTML newsletter.")
    parser.add_argument("channel_ids", nargs="*", help="The ids of the channels to read, in the order they should appear")
    parser.add_argument("--sample", action="store_true", help="Use the method's sample week instead of reading Discord")
    parser.add_argument("--output", type=Path, default=Path("newsletter.html"), help="Where to write the HTML (default: newsletter.html)")
    arguments = parser.parse_args()
    if not arguments.sample and not arguments.channel_ids:
        parser.error("name at least one channel id, or pass --sample")
    html = asyncio.run(gather_and_write(arguments.channel_ids, sample=arguments.sample))
    # Saved before it is posted, so a webhook that refuses it loses nothing the run paid for.
    arguments.output.write_text(html, encoding="utf-8")
    print(arguments.output)
    if webhook_url := os.environ.get("DIGEST_WEBHOOK_URL"):
        asyncio.run(post(html, webhook_url=webhook_url))


if __name__ == "__main__":
    main()
