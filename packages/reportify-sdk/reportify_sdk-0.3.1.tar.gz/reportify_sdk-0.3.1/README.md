# Reportify SDK for Python

Python SDK for Reportify API - Financial data and document search.

## Installation

```bash
pip install reportify-sdk
```

## Quick Start

```python
from reportify_sdk import Reportify

# Initialize client
client = Reportify(api_key="your-api-key")

# Search documents
docs = client.search("Tesla earnings", num=10)
for doc in docs:
    print(doc["title"])
```

## Features

### Document Search

```python
# General search across all categories
docs = client.search("revenue growth", num=10)

# Search specific document types
news = client.search_news("Apple iPhone", num=10)
reports = client.search_reports("semiconductor analysis", num=10)
filings = client.search_filings("10-K annual report", symbols=["US:AAPL"])
transcripts = client.search_transcripts("guidance", symbols=["US:TSLA"])
```

### Stock Data (returns pandas DataFrame)

```python
# Financial statements
income = client.stock.income_statement("US:AAPL", period="quarterly")
balance = client.stock.balance_sheet("US:AAPL")
cashflow = client.stock.cashflow_statement("US:AAPL")

# Price data
prices = client.stock.prices("US:AAPL", start_date="2024-01-01")

# Real-time quote
quote = client.stock.quote("US:AAPL")

# Company info
overview = client.stock.overview("US:AAPL")
shareholders = client.stock.shareholders("US:AAPL")

# Screening and calendar
stocks = client.stock.screener(country="US", market_cap_more_than=1e10)
earnings = client.stock.earnings_calendar(market="us", start_date="2024-01-01", end_date="2024-01-31")
```

### Timeline

```python
# Get timeline for followed entities
companies = client.timeline.companies(num=20)
topics = client.timeline.topics(num=20)
institutes = client.timeline.institutes(num=20)
public_media = client.timeline.public_media(num=20)
social_media = client.timeline.social_media(num=20)
```

### Knowledge Base

```python
# Search user's uploaded documents
chunks = client.kb.search("quarterly revenue", folder_ids=["folder_id"])
```

### Documents

```python
# Get document content
doc = client.docs.get("doc_id")
summary = client.docs.summary("doc_id")

# List and search documents
docs = client.docs.list(symbols=["US:AAPL"], page_size=10)
chunks = client.docs.search_chunks("revenue breakdown", num=5)

# Upload documents
result = client.docs.upload([
    {"url": "https://example.com/report.pdf", "name": "Annual Report"}
])
```

### Quant (Quantitative Analysis)

```python
# Compute technical indicators
df = client.quant.compute_indicators(["000001"], "RSI(14)")
df = client.quant.compute_indicators(["000001"], "MACD()")

# Screen stocks by formula
stocks = client.quant.screen(formula="RSI(14) < 30")
stocks = client.quant.screen(formula="CROSS(MA(5), MA(20))")

# Get OHLCV data
ohlcv = client.quant.ohlcv("000001", start_date="2024-01-01")
ohlcv_batch = client.quant.ohlcv_batch(["000001", "600519"])

# Backtest strategy
result = client.quant.backtest(
    start_date="2023-01-01",
    end_date="2024-01-01",
    symbol="000001",
    entry_formula="CROSS(MA(5), MA(20))",
    exit_formula="CROSSDOWN(MA(5), MA(20))"
)
print(f"Total Return: {result['total_return_pct']:.2%}")
```

### Concepts

```python
# Get latest concepts
concepts = client.concepts.latest()
for c in concepts:
    print(c["concept_name"])

# Get today's concept feeds
feeds = client.concepts.today()
```

### Channels

```python
# Search channels
result = client.channels.search("Goldman Sachs")

# Get followed channels
followings = client.channels.followings()

# Follow/unfollow a channel
client.channels.follow("channel_id")
client.channels.unfollow("channel_id")
```

### Chat

```python
# Chat completion based on documents
response = client.chat.completion(
    "What are Tesla's revenue projections?",
    symbols=["US:TSLA"],
    mode="comprehensive"  # concise, comprehensive, deepresearch
)
print(response["message"])
```

### Agent

```python
# Create agent conversation
conv = client.agent.create_conversation(agent_id=11887655289749510)

# Chat with agent
response = client.agent.chat(
    conversation_id=conv["id"],
    message="Analyze NVIDIA's latest earnings"
)

# Get agent-generated file
file_content = client.agent.get_file("file_id")
with open("output.xlsx", "wb") as f:
    f.write(file_content)
```

### User

```python
# Get followed companies
companies = client.user.followed_companies()
for company in companies:
    print(f"{company['symbol']}: {company['name']}")
```

## Error Handling

```python
from reportify_sdk import (
    Reportify,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIError,
)

try:
    docs = client.search("Tesla")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except NotFoundError:
    print("Resource not found")
except APIError as e:
    print(f"API error: {e.message}")
```

## Configuration

```python
client = Reportify(
    api_key="your-api-key",
    base_url="https://api.reportify.cn",  # Optional: custom API URL
    timeout=30.0,  # Optional: request timeout in seconds
)
```

## Context Manager

```python
with Reportify(api_key="your-api-key") as client:
    docs = client.search("Tesla")
    # Client will be closed automatically
```

## License

MIT License - see [LICENSE](LICENSE) for details.
