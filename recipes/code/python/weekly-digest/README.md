# A weekly digest: fetch in code, write with a method, post the HTML

A community lives on Discord, and most members never read a week of scrollback. This recipe reads the week's messages from the channels you name, has the cookbook's [Discord newsletter](https://github.com/Pipelex/pipelex-cookbook/tree/v0.18.0/methods/discord_newsletter) method write them up as an HTML newsletter, and posts it wherever your readers are.

It shows the split that suits a scheduled job:

- **Code does what code is good at.** Fetching from Discord's API, paging back seven days, and posting the result are plain HTTP, written in the script and typed with the method's generated models: each channel becomes a `DiscordChannelUpdate`, the method's own input type.
- **The method does the writing.** The newsletter's structure, its weekly summary, its sections per channel and its tone come from the method, run by its address, so the digest reads the same every week.
- **It runs anywhere a cron runs.** One command, no server: a scheduled GitHub Action, a cron job or a serverless function.

## What it needs

- [uv](https://docs.astral.sh/uv/), which reads the script's dependencies from its first lines and installs them.
- A Pipelex API key in `PIPELEX_API_KEY`, from [app.pipelex.com](https://app.pipelex.com). Each newsletter is one run on the hosted API and spends credit.
- To read your own server: a Discord bot token in `DISCORD_BOT_TOKEN`, for a bot [invited to the server](https://discord.com/developers/docs/topics/oauth2#bots) with the View Channels and Read Message History permissions, and the ids of the channels to read (with Developer Mode on, right-click a channel and copy its id). Turn on the bot's **Message Content Intent** in the Developer Portal, under Bot: it is a [privileged intent](https://discord.com/developers/docs/events/gateway#message-content-intent), and without it Discord hands the bot every message with its text, embeds and attachments empty, so the newsletter would have nothing to say.
- To post the newsletter: an endpoint in `DIGEST_WEBHOOK_URL` that takes an HTML body, such as your email service's or your CMS's. The script never prints it, since a webhook URL often carries its secret.

## Run it

Try it first on the method's sample week, with no Discord needed:

```bash
export PIPELEX_API_KEY=…
uv run digest.py --sample
```

Then on your own server, naming the channels in the order the newsletter should follow:

```bash
export PIPELEX_API_KEY=… DISCORD_BOT_TOKEN=…
uv run digest.py 1234567890123456789 2345678901234567890
```

## What you get

`newsletter.html`: a weekly summary of at most a few lines, a section per channel in the order you named them, with its highlights and links back to the messages, and the geographic hubs. The method writes its section welcoming new members only for a channel named exactly `Introduce-Yourself`, as in its sample week; a Discord text channel is normally named in lowercase, such as `introduce-yourself`, so on your server that channel is summarized like the others. With `DIGEST_WEBHOOK_URL` set, the same HTML is posted there once it is saved, so a webhook that refuses it loses nothing. The terminal shows how many messages were read and the run that wrote the newsletter.

## How it is built

- `digest.py` calls the method by its address, `github.com/Pipelex/pipelex-cookbook/discord_newsletter@v0.18.0`, pinned to a release tag so the method never changes under the types.
- `generated/discord_newsletter/` holds those types: `models.py`, generated from the method at that tag, and `codegen.lock`, which vouches for it. `sources.json` records the address and the target they come from. Never edit them by hand: in the cookbook, `make refresh` regenerates them, and in your own project `/pipelex-integrate` does.
- The newsletter comes back as a text holding the HTML, which the script reads through the generated `Text` model.
- The method orders its sections by each channel's `position`, which the script sets from the order of the channel ids you give it. A request Discord rate-limits is retried after the wait Discord asks for.
