# llmtokens

Count tokens and explore chat templates using HuggingFace tokenizers or OpenAI tiktoken.

## Installation

Run directly without installation:
```bash
uvx llmtokens --help
```

Or install as a persistent tool and run with just the tool name:
```bash
uv tool install llmtokens

llmtokens --help
```

## Quick Start

```bash
echo "hello world" | llmtokens
```

Output:
```
============================================================
                           STATS
============================================================
            model      mode  lines  words  chars  bytes  tokens
---------------------------------------------------------------
Qwen/Qwen2.5-0.5B       raw      1      2     12     12       3
Qwen/Qwen2.5-0.5B  template      6     11    120    120      22
```

By default, `llmtokens` shows both raw token counts and templated counts (with the model's chat template applied).

## Token Statistics

The tool prints token counts alongside standard text statistics (lines, words, characters, bytes). This makes it useful for comparing tokenizer efficiency across models and languages.

### Example: Comparing tokenizers across languages

**English** (*Pride and Prejudice*, Jane Austen):
```bash
echo "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife. However little known the feelings or views of such a man may be on his first entering a neighbourhood, this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of some one or other of their daughters." | llmtokens --mode raw -m Qwen/Qwen2.5-0.5B -m meta-llama/Llama-3.3-70B-Instruct -m mistralai/Mistral-7B-Instruct-v0.3
```

Output:
```
============================================================
                           STATS
============================================================
                             model  mode  lines  words  chars  bytes  tokens
----------------------------------------------------------------------------
                 Qwen/Qwen2.5-0.5B   raw      0     70    375    375      76
 meta-llama/Llama-3.3-70B-Instruct   raw      0     70    375    375      77
mistralai/Mistral-7B-Instruct-v0.3   raw      0     70    375    375      80
```

**Russian** (*Anna Karenina*, Leo Tolstoy):
```bash
echo "Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему. Все смешалось в доме Облонских. Жена узнала, что муж был в связи с бывшею в их доме француженкою-гувернанткой, и объявила мужу, что не может жить с ним в одном доме. Три дня после этого Степан Аркадьич Облонский — Стива, как его звали в свете, — не выходил из дома." | llmtokens --mode raw -m Qwen/Qwen2.5-0.5B -m meta-llama/Llama-3.3-70B-Instruct -m mistralai/Mistral-7B-Instruct-v0.3
```

Output:
```
============================================================
                           STATS
============================================================
                             model  mode  lines  words  chars  bytes  tokens
----------------------------------------------------------------------------
                 Qwen/Qwen2.5-0.5B   raw      0     61    357    644     138
 meta-llama/Llama-3.3-70B-Instruct   raw      0     61    357    644     123
mistralai/Mistral-7B-Instruct-v0.3   raw      0     61    357    644     150
```

**Chinese** (*Dream of the Red Chamber*, Cao Xueqin, 红楼梦):
```bash
echo "甄士隐梦幻识通灵，贾雨村风尘怀闺秀。此开卷第一回也。作者自云：因曾历过一番梦幻之后，故将真事隐去，而借"通灵"之说，撰此《石头记》一书也。故曰"甄士隐"云云。但书中所记何事何人？自又云：今风尘碌碌，一事无成，忽念及当日所有之女子，一一细考较去，觉其行止见识，皆出于我之上。何我堂堂须眉，诚不若彼裙钗哉？实愧则有余，悔又无益之大无可如何之日也！" | llmtokens --mode raw -m Qwen/Qwen2.5-0.5B -m meta-llama/Llama-3.3-70B-Instruct -m mistralai/Mistral-7B-Instruct-v0.3
```

Output:
```
============================================================
                           STATS
============================================================
                             model  mode  lines  words  chars  bytes  tokens
----------------------------------------------------------------------------
                 Qwen/Qwen2.5-0.5B   raw      0      1    171    505     153
 meta-llama/Llama-3.3-70B-Instruct   raw      0      1    171    505     172
mistralai/Mistral-7B-Instruct-v0.3   raw      0      1    171    505     217
```

## Chat Templates

The tool can access chat templates provided with HuggingFace models. Chat templates define how models expect input to be formatted, including special tokens, role markers, and system prompts.

### Example: viewing template details

```bash
echo "What is 2+2?" | llmtokens --show-original --show-template --show-rendered
```

Output:
```
============================================================
                           STATS
============================================================
            model      mode  lines  words  chars  bytes  tokens
---------------------------------------------------------------
Qwen/Qwen2.5-0.5B       raw      1      3     13     13       7
Qwen/Qwen2.5-0.5B  template      6     12    121    121      26

============================================================
                       ORIGINAL TEXT
============================================================
What is 2+2?


============================================================
              CHAT TEMPLATE: Qwen/Qwen2.5-0.5B
============================================================
{%- if tools %}
    {{- '<|im_start|>system\n' }}
    {%- if messages[0]['role'] == 'system' %}
        {{- messages[0]['content'] }}
    {%- else %}
        {{- 'You are a helpful assistant.' }}
    {%- endif %}
    {{- "\n\n# Tools\n\nYou may call one or more functions to assist with the user query.\n\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>" }}
    {%- for tool in tools %}
        {{- "\n" }}
        {{- tool | tojson }}
    {%- endfor %}
    {{- "\n</tools>\n\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\n<tool_call>\n{\"name\": <function-name>, \"arguments\": <args-json-object>}\n</tool_call><|im_end|>\n" }}
{%- else %}
    {%- if messages[0]['role'] == 'system' %}
        {{- '<|im_start|>system\n' + messages[0]['content'] + '<|im_end|>\n' }}
    {%- else %}
        {{- '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n' }}
    {%- endif %}
{%- endif %}
{%- for message in messages %}
    {%- if (message.role == "user") or (message.role == "system" and not loop.first) or (message.role == "assistant" and not message.tool_calls) %}
        {{- '<|im_start|>' + message.role + '\n' + message.content + '<|im_end|>' + '\n' }}
    {%- elif message.role == "assistant" %}
        {{- '<|im_start|>' + message.role }}
        {%- if message.content %}
            {{- '\n' + message.content }}
        {%- endif %}
        {%- for tool_call in message.tool_calls %}
            {%- if tool_call.function is defined %}
                {%- set tool_call = tool_call.function %}
            {%- endif %}
            {{- '\n<tool_call>\n{"name": "' }}
            {{- tool_call.name }}
            {{- '", "arguments": ' }}
            {{- tool_call.arguments | tojson }}
            {{- '}\n</tool_call>' }}
        {%- endfor %}
        {{- '<|im_end|>\n' }}
    {%- elif message.role == "tool" %}
        {%- if (loop.index0 == 0) or (messages[loop.index0 - 1].role != "tool") %}
            {{- '<|im_start|>user' }}
        {%- endif %}
        {{- '\n<tool_response>\n' }}
        {{- message.content }}
        {{- '\n</tool_response>' }}
        {%- if loop.last or (messages[loop.index0 + 1].role != "tool") %}
            {{- '<|im_end|>\n' }}
        {%- endif %}
    {%- endif %}
{%- endfor %}
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant\n' }}
{%- endif %}


============================================================
              RENDERED TEXT: Qwen/Qwen2.5-0.5B
============================================================
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
What is 2+2?
<|im_end|>
<|im_start|>assistant
```

The example shows the original input, the model's Jinja2 chat template, and the rendered text with special tokens and formatting applied.

### Raw vs template mode

Use `--mode` to control whether chat templates are applied:

```bash
# Raw mode: count tokens in the text as-is
echo "What is 2+2?" | llmtokens --mode raw
```

Output:
```
============================================================
                           STATS
============================================================
            model  mode  lines  words  chars  bytes  tokens
-----------------------------------------------------------
Qwen/Qwen2.5-0.5B   raw      1      3     13     13       7
```

```bash
# Template mode: apply chat template and count tokens
echo "What is 2+2?" | llmtokens --mode template
```

Output:
```
============================================================
                           STATS
============================================================
            model      mode  lines  words  chars  bytes  tokens
---------------------------------------------------------------
Qwen/Qwen2.5-0.5B  template      6     12    121    121      26
```

The default mode is `both-auto`, which shows both raw and templated counts when a template is available.

### JSON inputs

You can provide structured conversation inputs as JSON arrays:

```bash
echo '[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is 2+2?"}]' | llmtokens --wrap-input no
```

Control input wrapping with `--wrap-input`:
- `--wrap-input auto` (default): Try to parse as JSON; if that fails, wrap the text as a user message
- `--wrap-input yes`: Always wrap the input as a single user message
- `--wrap-input no`: Expect JSON array format; fail if input is not valid JSON

## Available Models

The tool uses the HuggingFace library and can access any model on HuggingFace Hub. For models in HuggingFace format, it downloads only the tokenizer files (small, typically a few MB), not the full model weights. Downloaded tokenizers are cached by HuggingFace and reused across runs.

Specify models with `-m`:
```bash
echo "test" | llmtokens -m gpt2 -m meta-llama/Llama-3.3-70B-Instruct
```

Default model: `Qwen/Qwen2.5-0.5B`

## All Options

### Model selection
- `-m MODEL` - Specify model (default: `Qwen/Qwen2.5-0.5B`)
- Multiple `-m` flags to compare models side-by-side

### Modes
- `--mode raw` - Count raw text only (no chat template)
- `--mode template` - Apply chat template (warn if missing)
- `--mode either` - Use template if available, otherwise raw
- `--mode both` - Show both raw and templated (warn if template missing)
- `--mode both-auto` - Show both if template available (default)

### Input wrapping
- `--wrap-input auto` - Parse as JSON messages if possible, otherwise wrap as user message (default)
- `--wrap-input yes` - Always wrap input as a user message
- `--wrap-input no` - Parse input as JSON messages array

### Display options
- `--show-original` - Show the original input text
- `--show-template` - Show the Jinja2 chat template
- `--show-rendered` - Show rendered text after applying template
- `--show-all` - Show all of the above

### Other
- `-v, --verbose` - Verbose output
- `file` - Read from file instead of stdin

### Help
```bash
llmtokens --help
```

## Gated Models

Some models (e.g., Llama) require HuggingFace authentication. Either set the `HF_TOKEN` environment variable or run:
```bash
huggingface-cli login
```

