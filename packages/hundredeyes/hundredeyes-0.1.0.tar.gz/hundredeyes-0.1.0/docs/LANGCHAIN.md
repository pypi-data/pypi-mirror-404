# LangChain Integration

Argus provides seamless integration with LangChain through callback handlers.

## Quick Start

```python
from argus.integrations import ArgusCallbackHandler
from langchain.llms import OpenAI

# Create Argus callback
callback = ArgusCallbackHandler(
    agent_name="my-bot",
    tags=["langchain", "production"]
)

# Add to LLM
llm = OpenAI(callbacks=[callback])

# All calls automatically tracked!
response = llm("Hello world")
```

## Features

### Automatic Tracking

Argus automatically tracks:
- ✅ **All LLM calls** - OpenAI, Anthropic, Cohere, etc.
- ✅ **Token usage** - Input and output tokens
- ✅ **Cost calculation** - Automatic based on model pricing
- ✅ **Latency** - Response time for each call
- ✅ **Errors** - Failed calls with error messages
- ✅ **Chain execution** - Track entire chain runs

### Zero Code Changes

No need to modify your existing LangChain code - just add the callback!

```python
# Before
llm = OpenAI()

# After
from argus.integrations import ArgusCallbackHandler
llm = OpenAI(callbacks=[ArgusCallbackHandler()])
```

## Usage Examples

### Basic LLM

```python
from langchain.llms import OpenAI
from argus.integrations import ArgusCallbackHandler

callback = ArgusCallbackHandler(agent_name="openai-bot")
llm = OpenAI(callbacks=[callback])

response = llm("Explain quantum computing")
```

### Chat Models

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from argus.integrations import ArgusCallbackHandler

callback = ArgusCallbackHandler(agent_name="chat-bot")
chat = ChatOpenAI(callbacks=[callback])

messages = [HumanMessage(content="Hello!")]
response = chat(messages)
```

### Chains

```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from argus.integrations import ArgusCallbackHandler

callback = ArgusCallbackHandler(agent_name="chain-bot")

llm = OpenAI()
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for {product}?"
)

chain = LLMChain(
    llm=llm,
    prompt=prompt,
    callbacks=[callback]  # Track entire chain
)

response = chain.run("AI code review tool")
```

### Multiple Agents

Track different LangChain agents separately:

```python
from argus.integrations import ArgusCallbackHandler

# Production bot
prod_callback = ArgusCallbackHandler(
    agent_name="prod-bot",
    tags=["production", "gpt-4"]
)
prod_llm = OpenAI(model="gpt-4", callbacks=[prod_callback])

# Development bot
dev_callback = ArgusCallbackHandler(
    agent_name="dev-bot",
    tags=["development", "gpt-3.5"]
)
dev_llm = OpenAI(model="gpt-3.5-turbo", callbacks=[dev_callback])

# Each tracked separately in dashboard!
```

### Anthropic Claude

```python
from langchain.chat_models import ChatAnthropic
from argus.integrations import ArgusCallbackHandler

callback = ArgusCallbackHandler(agent_name="claude-bot")
chat = ChatAnthropic(
    model="claude-3-opus-20240229",
    callbacks=[callback]
)

response = chat([HumanMessage(content="Hello Claude!")])
```

## Configuration

### ArgusCallbackHandler Parameters

```python
ArgusCallbackHandler(
    agent_name: str = "langchain-agent",  # Name in dashboard
    tags: List[str] = None,               # Tags for filtering
    db_path: str = "argus.db"             # Database path
)
```

### Example with Custom Config

```python
callback = ArgusCallbackHandler(
    agent_name="my-custom-bot",
    tags=["production", "customer-support", "gpt-4"],
    db_path="/path/to/custom/argus.db"
)
```

## Cost Tracking

Argus automatically calculates costs for LangChain calls:

```python
from argus.integrations import ArgusCallbackHandler
from langchain.llms import OpenAI

callback = ArgusCallbackHandler(agent_name="cost-tracker")
llm = OpenAI(model="gpt-4", callbacks=[callback])

# Make some calls
for i in range(10):
    llm(f"Question {i}")

# Check total cost
from argus import watch
stats = watch.stats(agent_name="cost-tracker")
print(f"Total cost: ${stats['total_cost']:.4f}")
```

## Error Tracking

Failed LangChain calls are automatically logged:

```python
from argus.integrations import ArgusCallbackHandler
from langchain.llms import OpenAI

callback = ArgusCallbackHandler(agent_name="error-tracker")

# Invalid API key
llm = OpenAI(
    openai_api_key="invalid-key",
    callbacks=[callback]
)

try:
    llm("This will fail")
except Exception as e:
    pass  # Error logged in Argus!

# View errors in dashboard
```

## Dashboard

All LangChain calls appear in the Argus dashboard:

```bash
argus dashboard
```

Open http://localhost:3000 to see:
- Total calls per agent
- Cost breakdown
- Error rates
- Performance metrics
- Recent activity

## Advanced Usage

### Custom Database Path

```python
callback = ArgusCallbackHandler(
    agent_name="my-bot",
    db_path="/custom/path/argus.db"
)
```

### Multiple Callbacks

Combine Argus with other LangChain callbacks:

```python
from langchain.callbacks import StdOutCallbackHandler
from argus.integrations import ArgusCallbackHandler

callbacks = [
    StdOutCallbackHandler(),      # Print to console
    ArgusCallbackHandler()         # Track in Argus
]

llm = OpenAI(callbacks=callbacks)
```

### Conditional Tracking

Track only in production:

```python
import os
from argus.integrations import ArgusCallbackHandler

callbacks = []
if os.getenv("ENV") == "production":
    callbacks.append(ArgusCallbackHandler(
        agent_name="prod-bot",
        tags=["production"]
    ))

llm = OpenAI(callbacks=callbacks)
```

## Supported LangChain Components

### LLMs
- ✅ OpenAI
- ✅ Anthropic
- ✅ Cohere
- ✅ HuggingFace
- ✅ All other LangChain LLMs

### Chat Models
- ✅ ChatOpenAI
- ✅ ChatAnthropic
- ✅ All other chat models

### Chains
- ✅ LLMChain
- ✅ SequentialChain
- ✅ All other chains

### Agents
- ✅ All LangChain agents

## Troubleshooting

### Callback Not Working

Make sure LangChain is installed:
```bash
pip install langchain
```

### Costs Not Calculated

Ensure you're using a supported model:
- OpenAI: gpt-4, gpt-3.5-turbo, etc.
- Anthropic: claude-3-opus, claude-3-sonnet, etc.

### Database Not Found

Check the database path:
```python
callback = ArgusCallbackHandler(db_path="./argus.db")
```

## Examples

See [`examples/langchain_example.py`](../examples/langchain_example.py) for complete examples.

## API Reference

### ArgusCallbackHandler

```python
class ArgusCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler for Argus observability"""
    
    def __init__(
        self,
        agent_name: str = "langchain-agent",
        tags: Optional[List[str]] = None,
        db_path: str = "argus.db"
    ):
        """
        Initialize Argus callback handler
        
        Args:
            agent_name: Name for this agent in Argus dashboard
            tags: Optional tags for categorization
            db_path: Path to Argus database
        """
```

### create_callback

```python
def create_callback(
    agent_name: str = "langchain-agent",
    tags: Optional[List[str]] = None
) -> ArgusCallbackHandler:
    """
    Convenience function to create Argus callback
    
    Args:
        agent_name: Name for this agent
        tags: Optional tags
    
    Returns:
        ArgusCallbackHandler instance
    """
```

## See Also

- [LangChain Documentation](https://python.langchain.com/)
- [Argus Pricing](PRICING.md)
- [Examples](../examples/)
