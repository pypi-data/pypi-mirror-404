from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any

from .config import (
    ConfigError,
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    config_path,
    detect_shell,
    load_config,
    redact_api_key,
    require_settings,
    resolve_settings,
    save_config,
)
from .llm import LLMError, generate_answer, generate_command, normalize_command
from .paste import paste_into_terminal


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argv, global_verbose = _extract_global_flags(argv)

    if not argv or argv[0] in {"-h", "--help"}:
        print(_main_help())
        return 0

    if argv[0] == "config":
        return _handle_config(argv[1:])
    if argv[0] == "init":
        return _handle_init(argv[1:])
    if _is_legacy_print_ask(argv):
        _warn_legacy_wrapper()
        return _handle_ask(argv[2:], global_verbose)
    if argv[0] == "do":
        return _handle_do(argv[1:], global_verbose)
    if argv[0] == "ask":
        return _handle_ask(argv[1:], global_verbose)

    # Backward compatible: treat bare prompt as `clanker do`.
    return _handle_do(argv, global_verbose)


def _main_help() -> str:
    return (
        "clanker - LLM shell helper\n\n"
        "Usage:\n"
        "  clanker do \"Describe the shell task\"\n"
        "  clanker ask \"Ask a question\"\n"
        "  clanker config\n"
        "  clanker config show\n"
        "  clanker config set --endpoint URL --model MODEL --api-key KEY\n"
        "  clanker init fish\n\n"
        "Options:\n"
        "  --print           Print the command instead of pasting it into the terminal\n"
        "  --endpoint URL    Override the OpenAI-compatible base endpoint\n"
        "  --model MODEL     Override the model name\n"
        "  --api-key KEY     Override the API key\n"
        "  --shell NAME      Override the target shell (default from $SHELL, fallback fish)\n"
        "  --temperature T   Override model temperature (default 0.2)\n"
        "  --max-tokens N    Override max tokens for the command response\n"
        "  -v, --verbose     Print verbose logs (request payload, response, steps)\n"
    )


def _handle_do(argv: list[str], global_verbose: bool) -> int:
    parser = argparse.ArgumentParser(prog="clanker do", add_help=True, exit_on_error=False)
    parser.add_argument("--print", dest="print_only", action="store_true", help="Print the command only")
    parser.add_argument("--endpoint", help="Override the OpenAI-compatible base endpoint")
    parser.add_argument("--model", help="Override the model name")
    parser.add_argument("--api-key", help="Override the API key")
    parser.add_argument("--shell", help="Override target shell")
    parser.add_argument("--temperature", type=float, help="Override model temperature")
    parser.add_argument("--max-tokens", type=int, help="Override max tokens for response")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("prompt", help="Prompt describing the task")

    if "-h" in argv or "--help" in argv:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except (argparse.ArgumentError, SystemExit):
        if _looks_like_legacy_ask(argv):
            _warn_legacy_wrapper()
        print(
            "clanker: prompt must be a single argument; wrap it in quotes",
            file=sys.stderr,
        )
        return 2

    log = _logger(args.verbose or global_verbose)
    log("Mode: do")
    prompt = args.prompt.strip()
    if not prompt:
        parser.error("Prompt required. Example: clanker do \"List files...\"")
    log(f"Prompt: {prompt}")

    log("Loading config")
    config = load_config()
    overrides = {
        "endpoint": args.endpoint,
        "api_key": args.api_key,
        "model": args.model,
        "shell": args.shell,
    }
    settings = resolve_settings(config, overrides)
    log(f"Endpoint: {settings.endpoint}")
    log(f"Model: {settings.model}")
    log(f"Shell: {settings.shell}")

    try:
        require_settings(settings)
    except ConfigError as exc:
        print(f"clanker: {exc}", file=sys.stderr)
        return 2

    try:
        log("Requesting command from LLM")
        command_text = generate_command(
            prompt=prompt,
            settings=settings,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            log=log if (args.verbose or global_verbose) else None,
        )
    except LLMError as exc:
        print(f"clanker: {exc}", file=sys.stderr)
        return 1

    command_text = normalize_command(command_text)
    log(f"Normalized command: {command_text}")

    if args.print_only:
        log("Print-only mode; skipping paste")
        print(command_text)
        return 0

    log("Attempting to paste into terminal")
    paste_result = paste_into_terminal(command_text)
    if not paste_result.ok:
        print(command_text)
        reason = paste_result.reason or "unknown error"
        print(f"clanker: unable to paste into the terminal; {reason}", file=sys.stderr)
        _print_paste_hints(settings.shell)
        return 1

    log("Paste successful")
    return 0


def _handle_ask(argv: list[str], global_verbose: bool) -> int:
    parser = argparse.ArgumentParser(prog="clanker ask", add_help=True, exit_on_error=False)
    parser.add_argument("--endpoint", help="Override the OpenAI-compatible base endpoint")
    parser.add_argument("--model", help="Override the model name")
    parser.add_argument("--api-key", help="Override the API key")
    parser.add_argument("--temperature", type=float, help="Override model temperature")
    parser.add_argument("--max-tokens", type=int, help="Override max tokens for response")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("prompt", help="Question to ask")

    if "-h" in argv or "--help" in argv:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(argv)
    except (argparse.ArgumentError, SystemExit):
        if _looks_like_legacy_ask(argv):
            _warn_legacy_wrapper()
        print(
            "clanker: prompt must be a single argument; wrap it in quotes",
            file=sys.stderr,
        )
        return 2

    log = _logger(args.verbose or global_verbose)
    log("Mode: ask")
    prompt = args.prompt.strip()
    if not prompt:
        parser.error("Prompt required. Example: clanker ask \"What is ...?\"")
    log(f"Prompt: {prompt}")

    log("Loading config")
    config = load_config()
    overrides = {
        "endpoint": args.endpoint,
        "api_key": args.api_key,
        "model": args.model,
    }
    settings = resolve_settings(config, overrides)
    log(f"Endpoint: {settings.endpoint}")
    log(f"Model: {settings.model}")

    try:
        require_settings(settings)
    except ConfigError as exc:
        print(f"clanker: {exc}", file=sys.stderr)
        return 2

    try:
        log("Requesting answer from LLM")
        answer_text = generate_answer(
            prompt=prompt,
            settings=settings,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            log=log if (args.verbose or global_verbose) else None,
        )
    except LLMError as exc:
        print(f"clanker: {exc}", file=sys.stderr)
        return 1

    print(answer_text.strip())
    log("Answer printed")
    return 0


def _handle_config(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="clanker config", add_help=True)
    subparsers = parser.add_subparsers(dest="subcommand")

    show_parser = subparsers.add_parser("show", help="Show current config")
    show_parser.add_argument("--show-key", action="store_true", help="Show API key in full")

    subparsers.add_parser("path", help="Print config path")

    set_parser = subparsers.add_parser("set", help="Set config values")
    set_parser.add_argument("--endpoint", help="OpenAI-compatible base endpoint")
    set_parser.add_argument("--model", help="Model name")
    set_parser.add_argument("--api-key", help="API key")
    set_parser.add_argument("--shell", help="Default shell")

    args = parser.parse_args(argv)

    if args.subcommand is None:
        return _run_config_wizard()

    if args.subcommand == "path":
        print(config_path())
        return 0

    if args.subcommand == "show":
        config = load_config()
        print(f"Config path: {config_path()}")
        if not config:
            print("Config is empty. Run `clanker config` to set values.")
            return 0
        api_key = config.get("api_key")
        if api_key and not args.show_key:
            api_key = redact_api_key(api_key)
        print(f"endpoint: {config.get('endpoint', '(not set)')}")
        print(f"model: {config.get('model', '(not set)')}")
        print(f"api_key: {api_key or '(not set)'}")
        print(f"shell: {config.get('shell', '(not set)')}")
        return 0

    if args.subcommand == "set":
        updates: dict[str, Any] = {}
        if args.endpoint:
            updates["endpoint"] = args.endpoint
        if args.model:
            updates["model"] = args.model
        if args.api_key:
            updates["api_key"] = args.api_key
        if args.shell:
            updates["shell"] = args.shell
        if not updates:
            print("No values provided. Use --endpoint/--model/--api-key/--shell.")
            return 1
        config = load_config()
        config.update(updates)
        save_config(config)
        print("Config updated.")
        return 0

    parser.error("Unknown config subcommand")
    return 1


def _run_config_wizard() -> int:
    print("Clanker configuration")
    print("Press enter to accept defaults.")

    config = load_config()

    endpoint_default = config.get("endpoint") or DEFAULT_ENDPOINT
    model_default = config.get("model") or DEFAULT_MODEL
    shell_default = config.get("shell") or detect_shell()

    endpoint = _prompt("OpenAI-compatible endpoint", endpoint_default)
    model = _prompt("Model", model_default)
    api_key = _prompt_secret("API key", config.get("api_key"))
    shell = _prompt("Shell", shell_default)

    data = {
        "endpoint": endpoint,
        "model": model,
        "api_key": api_key,
        "shell": shell,
    }

    if not api_key:
        print("API key is required. Config not saved.")
        return 1

    save_config(data)
    print(f"Saved config to {config_path()}")
    return 0


def _prompt(label: str, default: str | None = None) -> str:
    if default:
        prompt = f"{label} [{default}]: "
    else:
        prompt = f"{label}: "
    value = input(prompt).strip()
    if value:
        return value
    return default or ""


def _prompt_secret(label: str, existing: str | None = None) -> str:
    import getpass

    if existing:
        prompt = f"{label} [stored]: "
    else:
        prompt = f"{label}: "
    value = getpass.getpass(prompt).strip()
    if value:
        return value
    return existing or ""


def _handle_init(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="clanker init", add_help=True)
    parser.add_argument(
        "shell",
        nargs="?",
        default="fish",
        choices=["fish"],
        help="Shell to generate integration for (default: fish)",
    )
    parser.add_argument(
        "--print",
        dest="print_only",
        action="store_true",
        help="Print the integration script instead of writing it",
    )
    args = parser.parse_args(argv)

    if args.shell == "fish":
        script = _fish_init_script()
        path = _fish_function_path()
        if args.print_only:
            print(script, end="" if script.endswith("\n") else "\n")
            return 0

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script, encoding="utf-8")
        print(f"Installed fish function at {path}")

        source_cmd = f"source {path}"
        if os.getenv("FISH_VERSION"):
            paste_result = paste_into_terminal(source_cmd)
            if paste_result.ok:
                print("Pasted: source command into your prompt (press Enter to run it).")
                return 0

        print(f"Run: {source_cmd}")
        return 0

    parser.error("Unsupported shell")
    return 1


def _fish_init_script() -> str:
    return (
        "function clanker\n"
        "    if test (count $argv) -eq 0\n"
        "        command clanker\n"
        "        return $status\n"
        "    end\n"
        "    set args $argv\n"
        "    set args_no_v\n"
        "    set saw_end 0\n"
        "    for a in $args\n"
        "        if test $saw_end -eq 0 -a \"$a\" = \"--\"\n"
        "            set saw_end 1\n"
        "            break\n"
        "        end\n"
        "        if test \"$a\" = \"-v\" -o \"$a\" = \"--verbose\"\n"
        "            continue\n"
        "        end\n"
        "        set -a args_no_v $a\n"
        "    end\n"
        "    set sub \"\"\n"
        "    if test (count $args_no_v) -ge 1\n"
        "        set sub $args_no_v[1]\n"
        "    end\n"
        "    set cmd \"\"\n"
        "    switch $sub\n"
        "        case config init help --help -h --version ask\n"
        "            command clanker $args\n"
        "            return $status\n"
        "        case do\n"
        "            set out\n"
        "            set inserted 0\n"
        "            for a in $args\n"
        "                if test $inserted -eq 0 -a \"$a\" = \"do\"\n"
        "                    set -a out $a\n"
        "                    set -a out --print\n"
        "                    set inserted 1\n"
        "                else\n"
        "                    set -a out $a\n"
        "                end\n"
        "            end\n"
        "            set cmd (command clanker $out)\n"
        "        case '*'\n"
        "            set cmd (command clanker --print $args)\n"
        "    end\n"
        "    set status_code $status\n"
        "    if test $status_code -ne 0\n"
        "        return $status_code\n"
        "    end\n"
        "    if test -n \"$cmd\"\n"
        "        commandline -i -- $cmd\n"
        "    end\n"
        "end\n"
    )


def _print_paste_hints(shell: str | None) -> None:
    if shell == "fish":
        fish_path = _fish_function_path()
        print(
            "clanker: for fish, run `clanker init fish` and then "
            f"`source {fish_path}` (or restart fish)",
            file=sys.stderr,
        )


def _extract_global_flags(argv: list[str]) -> tuple[list[str], bool]:
    verbose = False
    remaining: list[str] = []
    stop = False
    for arg in argv:
        if arg == "--":
            stop = True
            remaining.append(arg)
            continue
        if not stop and arg in {"-v", "--verbose"}:
            verbose = True
            continue
        remaining.append(arg)
    return remaining, verbose


def _is_legacy_print_ask(argv: list[str]) -> bool:
    return len(argv) >= 2 and argv[0] == "--print" and argv[1] == "ask"


def _looks_like_legacy_ask(argv: list[str]) -> bool:
    return "--print" in argv and "ask" in argv


def _warn_legacy_wrapper() -> None:
    print(
        "clanker: detected legacy fish wrapper; run `clanker init fish` to update",
        file=sys.stderr,
    )


def _logger(enabled: bool):
    def log(message: str) -> None:
        if not enabled:
            return
        if not message:
            return
        for line in str(message).splitlines():
            print(f"[clanker] {line}", file=sys.stderr)

    return log


def _fish_function_path() -> Path:
    base = os.getenv("XDG_CONFIG_HOME")
    if base:
        base_path = Path(base)
    else:
        base_path = Path.home() / ".config"
    return base_path / "fish" / "functions" / "clanker.fish"


if __name__ == "__main__":
    raise SystemExit(main())
