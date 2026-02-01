"""Count tokens, lines, words, characters, and bytes in text."""

import argparse
import json
import os
import sys
import traceback

# Disable HuggingFace progress bars
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

from huggingface_hub import hf_hub_download
from jinja2 import Template
from tokenizers import Tokenizer
import tiktoken

# Global verbose flag
verbose = False

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B"


class TokenizerWrapper:
    """Wrapper to provide consistent interface for both tiktoken and HF tokenizers."""

    def __init__(self, tokenizer, is_tiktoken: bool):
        self.tokenizer = tokenizer
        self.is_tiktoken = is_tiktoken

    def encode(self, text: str):
        if self.is_tiktoken:
            # tiktoken returns list[int] directly
            return TiktokenEncoding(self.tokenizer.encode(text))
        else:
            # HF tokenizer returns Encoding object with .ids
            return self.tokenizer.encode(text)


class TiktokenEncoding:
    """Wrapper for tiktoken encoding results to match HF interface."""

    def __init__(self, ids: list[int]):
        self.ids = ids


def load_tokenizer(model: str) -> tuple[TokenizerWrapper | None, str | None]:
    """Load tokenizer (try tiktoken first, then HuggingFace). Returns (tokenizer, error)."""
    # Try tiktoken first
    try:
        enc = tiktoken.get_encoding(model)
        return TokenizerWrapper(enc, is_tiktoken=True), None
    except Exception:
        pass  # Not a tiktoken encoding, try HuggingFace

    # Try HuggingFace
    try:
        path = hf_hub_download(model, "tokenizer.json")
        tokenizer = Tokenizer.from_file(path)
        return TokenizerWrapper(tokenizer, is_tiktoken=False), None
    except Exception as e:
        error_msg = f"Failed to load tokenizer: {e}"
        if verbose:
            error_msg += "\n" + traceback.format_exc()
        return None, error_msg


def load_chat_template(model: str) -> str | None:
    """Load chat template from model's tokenizer config."""
    try:
        path = hf_hub_download(model, "tokenizer_config.json")
        with open(path) as f:
            config = json.load(f)
        return config.get("chat_template")
    except Exception:
        return None


def apply_chat_template(template: str, messages: list[dict]) -> tuple[str | None, str | None]:
    """Apply Jinja2 chat template to messages. Returns (rendered, error_msg)."""
    try:
        jinja_template = Template(template)
        rendered = jinja_template.render(
            messages=messages,
            add_generation_prompt=True,
            bos_token="",
            eos_token="",
        )
        return rendered, None
    except Exception as e:
        error_msg = str(e)
        if verbose:
            error_msg += "\n" + traceback.format_exc()
        return None, error_msg


def parse_messages(text: str, wrap_input: str) -> tuple[list[dict] | None, bool, str | None]:
    """Parse input text into chat messages. Returns (messages, was_wrapped, error)."""
    if wrap_input == "no":
        try:
            return json.loads(text), False, None
        except json.JSONDecodeError:
            error_msg = "Input is not valid JSON, falling back to raw"
            if verbose:
                error_msg += "\n" + traceback.format_exc()
            return None, False, error_msg
    elif wrap_input == "yes":
        return [{"role": "user", "content": text}], True, None
    else:  # auto
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed, False, None
        except json.JSONDecodeError:
            pass
        return [{"role": "user", "content": text}], True, None


def count_tokens(text: str, tokenizer: TokenizerWrapper) -> int:
    return len(tokenizer.encode(text).ids)


def main():
    parser = argparse.ArgumentParser(
        description="Count tokens and text statistics",
        epilog="For gated models (e.g. Llama), set HF_TOKEN env var or run `huggingface-cli login`",
    )
    parser.add_argument(
        "-m", "--model",
        action="append",
        dest="models",
        metavar="MODEL",
        help=f"Tokenizer name: tiktoken encoding (e.g., cl100k_base, o200k_base) or HuggingFace model (repeatable, default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--mode",
        choices=["raw", "template", "either", "both", "both-auto"],
        default="both-auto",
        help="raw: no template; template: apply template (warn+fallback if missing); either: template if available; both: raw+template (warn if missing); both-auto: raw+template if available",
    )
    parser.add_argument(
        "--wrap-input",
        choices=["yes", "no", "auto"],
        default="auto",
        help="Wrap input as user message: yes (always wrap), no (parse as JSON messages), auto (default, try JSON then wrap)",
    )
    parser.add_argument("--show-original", action="store_true", help="Show original input text")
    parser.add_argument("--show-template", action="store_true", help="Show chat template")
    parser.add_argument("--show-rendered", action="store_true", help="Show rendered text after template")
    parser.add_argument("--show-all", action="store_true", help="Show original, template, and rendered")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full stacktrace on errors")
    parser.add_argument("file", nargs="?", help="Input file (reads stdin if not provided)")
    args = parser.parse_args()

    if args.show_all:
        args.show_original = args.show_template = args.show_rendered = True

    global verbose
    verbose = args.verbose

    models = sorted(args.models or [DEFAULT_MODEL])

    if args.file:
        with open(args.file) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    # Parse messages if needed (for template modes)
    messages = None
    was_wrapped = None
    parse_error = None
    if args.mode != "raw":
        messages, was_wrapped, parse_error = parse_messages(text, args.wrap_input)

    # 1. Wrap-input message (if auto and verbose) or parse error warning
    if parse_error and args.mode != "raw":
        print(f"Warning: {parse_error}", file=sys.stderr)
        args.mode = "raw"  # Force raw mode since we can't do templating
    elif verbose and args.wrap_input == "auto" and args.mode != "raw":
        if was_wrapped:
            print("Input: wrapped as user message")
        else:
            print("Input: parsed as JSON messages")

    # 2. Process models (prints warnings), collect results
    results = []  # (model, mode, lines, words, chars, bytes, tokens)
    model_data = []  # (model, template, rendered)

    def calc_stats(t: str, tokenizer: TokenizerWrapper) -> tuple:
        return (t.count("\n"), len(t.split()), len(t), len(t.encode("utf-8")), count_tokens(t, tokenizer))

    models.sort()

    for model in models:
        tokenizer, tok_err = load_tokenizer(model)
        if tokenizer is None:
            print(f"Warning: {model}: {tok_err}", file=sys.stderr)
            continue
        template = load_chat_template(model)

        if args.mode == "raw":
            stats = calc_stats(text, tokenizer)
            results.append((model, "raw", *stats))
            model_data.append((model, None, None))

        elif args.mode == "template":
            if messages is None:
                # JSON parse failed, fall back to raw
                stats = calc_stats(text, tokenizer)
                results.append((model, "raw", *stats))
                model_data.append((model, None, None))
            elif template:
                rendered, err = apply_chat_template(template, messages)
                if rendered is not None:
                    stats = calc_stats(rendered, tokenizer)
                    results.append((model, "template", *stats))
                    model_data.append((model, template, rendered))
                else:
                    print(f"Warning: {model} template failed to render: {err}", file=sys.stderr)
                    stats = calc_stats(text, tokenizer)
                    results.append((model, "raw", *stats))
                    model_data.append((model, None, None))
            else:
                print(f"Warning: {model} has no chat template, falling back to raw", file=sys.stderr)
                stats = calc_stats(text, tokenizer)
                results.append((model, "raw", *stats))
                model_data.append((model, None, None))

        elif args.mode == "either":
            if messages is None:
                # JSON parse failed, fall back to raw
                stats = calc_stats(text, tokenizer)
                results.append((model, "raw", *stats))
                model_data.append((model, None, None))
            elif template:
                rendered, err = apply_chat_template(template, messages)
                if rendered is not None:
                    stats = calc_stats(rendered, tokenizer)
                    results.append((model, "template", *stats))
                    model_data.append((model, template, rendered))
                else:
                    stats = calc_stats(text, tokenizer)
                    results.append((model, "raw", *stats))
                    model_data.append((model, None, None))
            else:
                stats = calc_stats(text, tokenizer)
                results.append((model, "raw", *stats))
                model_data.append((model, None, None))

        elif args.mode == "both":
            stats_raw = calc_stats(text, tokenizer)
            results.append((model, "raw", *stats_raw))
            if messages is None:
                # JSON parse failed, skip template
                model_data.append((model, None, None))
            elif template:
                rendered, err = apply_chat_template(template, messages)
                if rendered is not None:
                    stats_tpl = calc_stats(rendered, tokenizer)
                    results.append((model, "template", *stats_tpl))
                    model_data.append((model, template, rendered))
                else:
                    print(f"Warning: {model} template failed to render: {err}", file=sys.stderr)
                    model_data.append((model, None, None))
            else:
                print(f"Warning: {model} has no chat template", file=sys.stderr)
                model_data.append((model, None, None))

        elif args.mode == "both-auto":
            stats_raw = calc_stats(text, tokenizer)
            results.append((model, "raw", *stats_raw))
            if messages is None:
                # JSON parse failed, skip template
                model_data.append((model, None, None))
            elif template:
                rendered, err = apply_chat_template(template, messages)
                if rendered is not None:
                    stats_tpl = calc_stats(rendered, tokenizer)
                    results.append((model, "template", *stats_tpl))
                    model_data.append((model, template, rendered))
                else:
                    model_data.append((model, None, None))
            else:
                model_data.append((model, None, None))

    # 3. Stats table
    if not results:
        print("Error: No models could be loaded", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("STATS".center(60))
    print("=" * 60)

    # Calculate column widths: model, mode, lines, words, chars, bytes, tokens
    headers = ["model", "mode", "lines", "words", "chars", "bytes", "tokens"]
    col_widths = [
        max(len(headers[0]), max(len(r[0]) for r in results)),
        max(len(headers[1]), max(len(r[1]) for r in results)),
    ]
    for i in range(2, 7):
        col_widths.append(max(len(headers[i]), max(len(str(r[i])) for r in results)))

    # Print header
    header_row = "  ".join(h.rjust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * len(header_row))

    # Print rows
    for row in results:
        print("  ".join(str(v).rjust(w) for v, w in zip(row, col_widths)))

    # 4. Original (if needed)
    if args.show_original:
        print("\n" + "=" * 60)
        print("ORIGINAL TEXT".center(60))
        print("=" * 60)
        print(text)

    # 5. Templates and rendered per model
    for model, template, rendered in model_data:
        if args.show_template and template:
            print("\n" + "=" * 60)
            print(f"CHAT TEMPLATE: {model}".center(60))
            print("=" * 60)
            print(template)
        if args.show_rendered and rendered:
            print("\n" + "=" * 60)
            print(f"RENDERED TEXT: {model}".center(60))
            print("=" * 60)
            print(rendered)


if __name__ == "__main__":
    main()
