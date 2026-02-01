# clanker

LLM-powered shell helper that generates a command and pastes it into your terminal input so you can edit or run it.

## Install

Use uv:

```bash
uv tool install clanker
```

## Quick start

Configure the endpoint, model, and API key once:

```bash
clanker config
```

Then ask for a command:

```bash
clanker do "List all the files with the extension .pyc in this directory recursively and sum up their sizes"
```

Ask a question (no command insertion):

```bash
clanker ask "What does the -print0 flag do in find?"
```

By default, clanker will attempt to paste the generated command into your active terminal input (no auto-enter). If pasting fails, the command is printed so you can copy it manually.

You can also omit the `do` subcommand; `clanker "..."` is treated as `clanker do "..."`.
Prompts should be provided as a single quoted string.

Verbose mode (prints request payload, response, and step logs to stderr). Use `-v` or `--verbose`, and it can appear anywhere in the command:

```bash
clanker -v do "List all .py files"
```

## Fish integration (recommended)

Many Linux distros disable tty injection. If you use fish, the best UX is to install the fish wrapper so the command is inserted via `commandline -i`:

```bash
clanker init fish
```

If you want the script printed instead of written, run `clanker init fish --print`.

Restart fish (or run the `source ...` command that `clanker init` prints) and then run `clanker "..."` as usual.

## Configuration

Interactive wizard:

```bash
clanker config
```

Show config:

```bash
clanker config show
```

Set values directly:

```bash
clanker config set --endpoint https://api.openai.com/v1 --model gpt-4o-mini --api-key sk-...
```

Config file location:

```bash
clanker config path
```

Environment overrides:

- `CLANKER_ENDPOINT`
- `CLANKER_MODEL`
- `CLANKER_API_KEY`
- `CLANKER_SHELL`
- `CLANKER_CONFIG` (full path to config file)

## Notes on pasting

Clanker uses a Linux tty injection (`TIOCSTI`) to paste the command into the current terminal input buffer. Some systems disable this for security (for example `dev.tty.legacy_tiocsti=0`). If it is blocked, clanker prints the command instead. You can also force printing with:

```bash
clanker --print "..."
```
