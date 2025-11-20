# FinChat API Setup

## Quick Start

### Environment Variables

**No environment variables are required!** The system works out of the box with defaults.

Optional environment variables:

```bash
# Optional: Override default API URL
export FINCHAT_API_URL=https://finchat-api.adgo.io

# Optional: API token (not required - FinChat API doesn't require authentication)
export FINCHAT_API_TOKEN=your-bearer-token-here
```

### Default Configuration

- **API URL**: Defaults to `https://finchat-api.adgo.io` if not specified
- **API Token**: Not required - FinChat API doesn't require authentication

## Configuration in Backtest

Use the following strategy configuration:

```json
{
  "strategy": {
    "entryPromptType": "finchat-slug",
    "entryFinChatSlug": "conditional-stock-purchase",
    "exitPromptType": "finchat-slug",
    "exitFinChatSlug": "conditional-stock-sell-trigger",
    "positionSizingMethod": "portfolio-percent",
    "portfolioPercent": 100.0,
    "maxPositions": 1,
    "eligibleSymbols": "IBM"
  }
}
```

## Testing the Connection

You can test the FinChat connection by running:

```python
from backend.finchat_client import FinChatClient

# No token required!
client = FinChatClient()
session_id = await client.create_session()
print(f"Session created: {session_id}")
```

## COT Slugs

- **Entry COT**: `conditional-stock-purchase`
- **Exit COT**: `conditional-stock-sell-trigger`

## API Endpoints

The FinChat API base URL is: `https://finchat-api.adgo.io`

Key endpoints:
- `POST /api/v1/sessions/` - Create session
- `POST /api/v1/chats/` - Run COT prompt
- `GET /api/v1/chats/` - Poll for completion
- `GET /api/v1/results/{id}/` - Get results

See `HOW_TO_RUN_COT_API.md` for detailed API documentation.

