# langchain-cloro

This package contains the LangChain integration for [cloro.dev](https://cloro.dev/) - a unified API for monitoring multiple AI providers including Google Search, ChatGPT, Gemini, Perplexity, Grok, and Microsoft Copilot.

## Installation

```bash
pip install langchain-cloro
```

## Setup

You'll need a cloro API key. Get one at [https://cloro.dev](https://cloro.dev/).

Set the API key as an environment variable:

```bash
export CLORO_API_KEY="your-api-key-here"
```

Or pass it directly when initializing:

```python
from langchain_cloro import CloroGoogleSearch

tool = CloroGoogleSearch(cloro_api_key="your-api-key-here")
```

## Available Tools

### CloroGoogleSearch

Extract structured data from Google Search results, including organic results, People Also Ask questions, related searches, and optional AI Overview data.

```python
from langchain_cloro import CloroGoogleSearch

tool = CloroGoogleSearch()

# Basic search
results = tool.invoke({"query": "best laptops for programming"})

# With AI Overview
results = tool.invoke({
    "query": "best laptops for programming",
    "include_aioverview": True,
    "aioverview_markdown": True
})

# Multiple pages
results = tool.invoke({
    "query": "python tutorials",
    "pages": 3,
    "country": "US",
    "device": "desktop"
})
```

**Parameters:**
- `query` (str, required): The search query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `device` (str): "desktop" or "mobile". Default: "desktop"
- `pages` (int): Number of pages to scrape (1-20). Default: 1
- `include_aioverview` (bool): Include Google AI Overview. Default: False
- `aioverview_markdown` (bool): Format AI Overview as markdown. Default: False
- `include_html` (bool): Include raw HTML response. Default: False

### CloroChatGPT

Extract structured data from ChatGPT with shopping cards, entity extraction, and advanced features for monitoring products, prices, and brand mentions.

```python
from langchain_cloro import CloroChatGPT

tool = CloroChatGPT()

# Basic query
results = tool.invoke({"prompt": "What are the best sneakers under $100?"})

# With shopping card data
results = tool.invoke({
    "prompt": "best running shoes",
    "include_raw_response": True,
    "include_search_queries": True
})
```

**Parameters:**
- `prompt` (str, required): The prompt/query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `include_raw_response` (bool): Include raw streaming response events. Default: False
- `include_search_queries` (bool): Include search fan-out queries. Default: False
- `include_html` (bool): Include HTML response. Default: False
- `include_markdown` (bool): Include markdown response. Default: False

### CloroGemini

Extract structured data from Google's Gemini AI with source citations, confidence levels, and multiple output formats.

```python
from langchain_cloro import CloroGemini

tool = CloroGemini()

results = tool.invoke({"prompt": "Explain quantum entanglement"})
```

**Parameters:**
- `prompt` (str, required): The prompt/query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `include_html` (bool): Include HTML response. Default: False
- `include_markdown` (bool): Include markdown response. Default: False

### CloroPerplexity

Extract comprehensive structured data from Perplexity AI with real-time web sources, shopping products, media content, and travel information.

```python
from langchain_cloro import CloroPerplexity

tool = CloroPerplexity()

# Travel query
results = tool.invoke({"prompt": "Best hotels in San Francisco"})

# Shopping query
results = tool.invoke({"prompt": "best noise-cancelling headphones"})
```

**Parameters:**
- `prompt` (str, required): The prompt/query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `include_html` (bool): Include HTML response. Default: False
- `include_markdown` (bool): Include markdown response. Default: False

### CloroGrok

Extract comprehensive structured data from Grok with real-time web sources and enhanced source metadata including preview text, creator details, and images.

```python
from langchain_cloro import CloroGrok

tool = CloroGrok()

results = tool.invoke({"prompt": "Latest news about AI"})
```

**Parameters:**
- `prompt` (str, required): The prompt/query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `include_html` (bool): Include HTML response. Default: False
- `include_markdown` (bool): Include markdown response. Default: False

### CloroCopilot

Extract structured data from Microsoft Copilot with source citations.

```python
from langchain_cloro import CloroCopilot

tool = CloroCopilot()

results = tool.invoke({"prompt": "What is the capital of France?"})
```

**Parameters:**
- `prompt` (str, required): The prompt/query
- `country` (str): ISO 3166-1 alpha-2 country code. Default: "US"
- `include_html` (bool): Include HTML response. Default: False
- `include_markdown` (bool): Include markdown response. Default: False

### get_countries Utility

Get list of supported country codes for specific AI providers.

```python
from langchain_cloro import get_countries

# Get all countries
all_countries = get_countries()

# Get countries for specific model
chatgpt_countries = get_countries(model="chatgpt")
google_countries = get_countries(model="google")
```

## Usage with LangChain Agents

### With an Agent

```python
from langchain.agents import initialize_agent, AgentType
from langchain_openai import OpenAI
from langchain_cloro import CloroGoogleSearch, CloroChatGPT

llm = OpenAI(temperature=0)
tools = [CloroGoogleSearch(), CloroChatGPT()]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

agent.run("What are the latest developments in AI?")
```

### With LCEL

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_cloro import CloroChatGPT

chatgpt = CloroChatGPT()

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based on the AI's response:\n\n{response}"),
    ("user", "{question}")
])

chain = {
    "response": lambda x: chatgpt.invoke({"prompt": x["question"]}),
    "question": lambda x: x["question"]
} | prompt | ChatOpenAI() | StrOutputParser()

response = chain.invoke({"question": "What is LangChain?"})
print(response)
```

### Multiple Tools Example

```python
from langchain_cloro import (
    CloroGoogleSearch,
    CloroChatGPT,
    CloroGemini,
    CloroPerplexity,
    CloroGrok,
    CloroCopilot
)

tools = [
    CloroGoogleSearch(),  # For search queries
    CloroChatGPT(),      # For shopping/product queries
    CloroGemini(),       # For general AI queries
    CloroPerplexity(),   # For research with citations
    CloroGrok(),         # For real-time news
    CloroCopilot(),      # For general queries
]
```

## Supported Country Codes

Use the `get_countries()` utility to fetch supported countries:

```python
from langchain_cloro import get_countries

# Check which countries are available for each model
models = ["google", "chatgpt", "gemini", "perplexity", "grok", "copilot"]

for model in models:
    countries = get_countries(model=model)
    print(f"{model}: {len(countries)} countries")
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit_tests -v

# Linting
ruff check .
ruff format .

# Type checking
mypy langchain_cloro
```

## API Reference

For detailed API documentation, see [https://docs.cloro.dev](https://docs.cloro.dev/).

## License

MIT

## Links

- Documentation: [https://docs.cloro.dev](https://docs.cloro.dev/)
- Source: [https://github.com/cloro-dev/langchain-cloro](https://github.com/cloro-dev/langchain-cloro)
- cloro API: [https://cloro.dev](https://cloro.dev/)
