"""Basic smoke tests for llmtokens."""

import io
import sys
import pytest

from llmtokens.cli import (
    load_tokenizer,
    count_tokens,
    parse_messages,
    apply_chat_template,
    main,
)


class TestTokenizerLoading:
    """Test loading tokenizers from different sources."""

    def test_load_tiktoken_tokenizer(self):
        """Test loading a tiktoken tokenizer."""
        tokenizer, error = load_tokenizer("cl100k_base")
        assert tokenizer is not None
        assert error is None
        assert tokenizer.is_tiktoken is True

    def test_load_hf_tokenizer(self):
        """Test loading a HuggingFace tokenizer."""
        tokenizer, error = load_tokenizer("gpt2")
        assert tokenizer is not None
        assert error is None
        # gpt2 exists in both tiktoken and HF, but tiktoken is tried first
        assert tokenizer.is_tiktoken is True

    def test_load_hf_only_tokenizer(self):
        """Test loading a HuggingFace-only tokenizer."""
        tokenizer, error = load_tokenizer("Qwen/Qwen2.5-0.5B")
        assert tokenizer is not None
        assert error is None
        assert tokenizer.is_tiktoken is False

    def test_load_invalid_tokenizer(self):
        """Test loading an invalid tokenizer returns error."""
        tokenizer, error = load_tokenizer("nonexistent-model-12345")
        assert tokenizer is None
        assert error is not None
        assert "Failed to load tokenizer" in error


class TestTokenCounting:
    """Test basic token counting functionality."""

    def test_count_tokens_tiktoken(self):
        """Test counting tokens with tiktoken."""
        tokenizer, _ = load_tokenizer("cl100k_base")
        assert tokenizer is not None

        count = count_tokens("hello world", tokenizer)
        assert count == 2

    def test_count_tokens_hf(self):
        """Test counting tokens with HuggingFace tokenizer."""
        tokenizer, _ = load_tokenizer("Qwen/Qwen2.5-0.5B")
        assert tokenizer is not None

        count = count_tokens("hello world", tokenizer)
        assert count == 2  # Qwen tokenizes this as 2 tokens


class TestMessageParsing:
    """Test message parsing with different wrap modes."""

    def test_parse_messages_auto_json(self):
        """Test auto mode with valid JSON."""
        json_input = '[{"role": "user", "content": "test"}]'
        messages, was_wrapped, error = parse_messages(json_input, "auto")

        assert messages == [{"role": "user", "content": "test"}]
        assert was_wrapped is False
        assert error is None

    def test_parse_messages_auto_text(self):
        """Test auto mode with plain text (should wrap)."""
        messages, was_wrapped, error = parse_messages("hello", "auto")

        assert messages == [{"role": "user", "content": "hello"}]
        assert was_wrapped is True
        assert error is None

    def test_parse_messages_yes(self):
        """Test yes mode (always wrap)."""
        messages, was_wrapped, error = parse_messages("test", "yes")

        assert messages == [{"role": "user", "content": "test"}]
        assert was_wrapped is True
        assert error is None

    def test_parse_messages_no_valid_json(self):
        """Test no mode with valid JSON."""
        json_input = '[{"role": "user", "content": "test"}]'
        messages, was_wrapped, error = parse_messages(json_input, "no")

        assert messages == [{"role": "user", "content": "test"}]
        assert was_wrapped is False
        assert error is None

    def test_parse_messages_no_invalid_json(self):
        """Test no mode with invalid JSON (should error)."""
        messages, was_wrapped, error = parse_messages("not json", "no")

        assert messages is None
        assert error is not None


class TestChatTemplate:
    """Test chat template functionality."""

    def test_apply_chat_template(self):
        """Test applying a simple chat template."""
        template = "{{ messages[0].content }}"
        messages = [{"role": "user", "content": "test"}]

        rendered, error = apply_chat_template(template, messages)

        assert rendered == "test"
        assert error is None

    def test_apply_invalid_template(self):
        """Test applying an invalid template."""
        template = "{{ invalid.syntax.here }"
        messages = [{"role": "user", "content": "test"}]

        rendered, error = apply_chat_template(template, messages)

        assert rendered is None
        assert error is not None


class TestCLI:
    """Test CLI end-to-end."""

    def test_main_tiktoken_raw_mode(self, monkeypatch, capsys):
        """Test main() with tiktoken tokenizer in raw mode."""
        # Mock stdin
        monkeypatch.setattr("sys.stdin", io.StringIO("hello world"))

        # Mock sys.argv
        monkeypatch.setattr("sys.argv", [
            "llmtokens",
            "-m", "cl100k_base",
            "--mode", "raw",
        ])

        # Run main
        main()

        # Check output
        captured = capsys.readouterr()
        assert "cl100k_base" in captured.out
        assert "raw" in captured.out
        assert "2" in captured.out  # 2 tokens for "hello world"

    def test_main_hf_raw_mode(self, monkeypatch, capsys):
        """Test main() with HF tokenizer in raw mode."""
        monkeypatch.setattr("sys.stdin", io.StringIO("hello world"))
        monkeypatch.setattr("sys.argv", [
            "llmtokens",
            "-m", "Qwen/Qwen2.5-0.5B",
            "--mode", "raw",
        ])

        main()

        captured = capsys.readouterr()
        assert "Qwen/Qwen2.5-0.5B" in captured.out
        assert "raw" in captured.out
        assert "2" in captured.out  # 2 tokens

    def test_main_template_mode(self, monkeypatch, capsys):
        """Test main() with template mode."""
        monkeypatch.setattr("sys.stdin", io.StringIO("What is 2+2?"))
        monkeypatch.setattr("sys.argv", [
            "llmtokens",
            "-m", "Qwen/Qwen2.5-0.5B",
            "--mode", "template",
        ])

        main()

        captured = capsys.readouterr()
        assert "Qwen/Qwen2.5-0.5B" in captured.out
        assert "template" in captured.out

    def test_main_multiple_models(self, monkeypatch, capsys):
        """Test main() with multiple models."""
        monkeypatch.setattr("sys.stdin", io.StringIO("test"))
        monkeypatch.setattr("sys.argv", [
            "llmtokens",
            "-m", "cl100k_base",
            "-m", "o200k_base",
            "--mode", "raw",
        ])

        main()

        captured = capsys.readouterr()
        assert "cl100k_base" in captured.out
        assert "o200k_base" in captured.out

    def test_main_invalid_model(self, monkeypatch, capsys):
        """Test main() with invalid model shows warning."""
        monkeypatch.setattr("sys.stdin", io.StringIO("test"))
        monkeypatch.setattr("sys.argv", [
            "llmtokens",
            "-m", "invalid-model-12345",
        ])

        # Should exit with error since no valid models
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No models could be loaded" in captured.err
