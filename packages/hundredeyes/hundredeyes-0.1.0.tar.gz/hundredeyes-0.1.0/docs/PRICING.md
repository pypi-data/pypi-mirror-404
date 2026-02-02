# Automatic Cost Calculation

Argus automatically calculates costs for major LLM providers.

## Supported Providers

### OpenAI

Argus supports all OpenAI models with automatic cost calculation:

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| GPT-4 Turbo | $0.01 | $0.03 |
| GPT-4 | $0.03 | $0.06 |
| GPT-4 32K | $0.06 | $0.12 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| GPT-4o | $0.005 | $0.015 |
| GPT-4o Mini | $0.00015 | $0.0006 |

### Anthropic Claude

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| Claude 3 Opus | $0.015 | $0.075 |
| Claude 3 Sonnet | $0.003 | $0.015 |
| Claude 3 Haiku | $0.00025 | $0.00125 |
| Claude 2.1 | $0.008 | $0.024 |
| Claude Instant | $0.0008 | $0.0024 |

### Cohere

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| Command | $0.001 | $0.002 |
| Command Light | $0.0003 | $0.0006 |

## Usage

### Automatic Cost Calculation

```python
from argus import watch
from openai import OpenAI

client = OpenAI()

@watch.agent(
    name="gpt-bot",
    provider="openai",  # Specify provider
    model="gpt-4"       # Specify model
)
def ask_gpt(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response  # Cost calculated automatically!
```

Argus will:
1. Extract token usage from the response
2. Look up pricing for the model
3. Calculate cost automatically
4. Log everything to the dashboard

### Manual Cost Override

If you're using a custom model or want to set cost manually:

```python
@watch.agent(
    name="custom-model",
    cost_per_call=0.05  # Manual cost
)
def custom_llm(prompt: str):
    # Your custom logic
    return response
```

### Cost from Response

You can also return cost in the response:

```python
@watch.agent(name="my-agent")
def my_function():
    # Your logic
    cost = calculate_my_cost()
    return {"result": "...", "cost": cost}
```

## Cost Comparison

Example costs for 1000 input tokens + 500 output tokens:

| Provider | Model | Cost |
|----------|-------|------|
| OpenAI | GPT-4 | $0.060 |
| OpenAI | GPT-3.5 Turbo | $0.0013 |
| OpenAI | GPT-4o Mini | $0.00045 |
| Anthropic | Claude 3 Opus | $0.0525 |
| Anthropic | Claude 3 Haiku | $0.00088 |
| Cohere | Command | $0.002 |

**Tip**: Use cheaper models (GPT-3.5, Claude Haiku) for simple tasks!

## Pricing Updates

Pricing data is updated regularly. Current as of January 2025.

If you notice outdated pricing, please:
1. Open an issue on GitHub
2. Submit a PR with updated prices in `argus/pricing.py`

## Custom Pricing

To add custom pricing for your own models:

```python
from argus.pricing import OPENAI_PRICING

# Add your custom model
OPENAI_PRICING["my-custom-model"] = {
    "input": 0.01 / 1000,
    "output": 0.02 / 1000
}
```

## API Reference

### `calculate_cost(provider, model, input_tokens, output_tokens)`

Calculate cost for any provider.

**Parameters:**
- `provider` (str): "openai", "anthropic", or "cohere"
- `model` (str): Model name
- `input_tokens` (int): Number of input tokens
- `output_tokens` (int): Number of output tokens

**Returns:** Cost in USD (float)

**Example:**
```python
from argus.pricing import calculate_cost

cost = calculate_cost("openai", "gpt-4", 1000, 500)
print(f"Cost: ${cost:.4f}")  # Cost: $0.0600
```

### `calculate_openai_cost(model, input_tokens, output_tokens)`

Calculate cost specifically for OpenAI models.

### `calculate_anthropic_cost(model, input_tokens, output_tokens)`

Calculate cost specifically for Anthropic models.

### `extract_openai_usage(response)`

Extract token usage from OpenAI API response.

**Returns:** Dict with `input_tokens`, `output_tokens`, `total_tokens`

### `extract_anthropic_usage(response)`

Extract token usage from Anthropic API response.

## See Also

- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [Cohere Pricing](https://cohere.com/pricing)
