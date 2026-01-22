# GitHub Models Setup - FREE gpt-4o for KraftdIntel

## Status: ✅ CONFIGURATION COMPLETE (Cost: $0)

Your KraftdIntel workflow is now configured to use **GitHub Models (gpt-4o)** - completely free.

## What You Get

- **Model**: gpt-4o (latest, most capable)
- **Cost**: FREE ($0/month)
- **Rate Limit**: Rate-limited but sufficient for development/testing
- **Endpoint**: https://models.inference.ai.azure.com

## Setup Instructions

### Step 1: Create GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set permissions:
   - ✓ `repo` (Full control of private repositories)
   - ✓ `read:packages` (Read packages)
4. Generate token and **copy it** (you'll see it only once)

### Step 2: Add Token to .env

Replace `<your-github-token-here>` in `.env`:

```env
GITHUB_TOKEN=ghp_your_actual_token_here
MODEL_PROVIDER=github
MODEL_NAME=gpt-4o
```

### Step 3: Verify Setup

The following has been updated:
- ✅ `.env` - GitHub token configuration
- ✅ `backend/agent/kraft_agent.py` - Uses GitHub Models instead of Azure OpenAI
- ✅ Imports updated to use `azure.ai.inference`

### Step 4: Test Configuration

```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✓ GITHUB_TOKEN:', 'Set' if os.getenv('GITHUB_TOKEN') else 'Missing'); print('✓ MODEL_PROVIDER:', os.getenv('MODEL_PROVIDER')); print('✓ MODEL_NAME:', os.getenv('MODEL_NAME'))"
```

## Model Features

**gpt-4o (via GitHub Models):**
- Latest reasoning capabilities
- Vision/image understanding
- JSON mode support
- Function calling
- Excellent for:
  - Document analysis
  - Supplier data extraction
  - Risk signal detection
  - Conversational AI

## Rate Limits (GitHub Models Free Tier)

- **Requests**: Rate-limited
- **Tokens**: Adequate for development
- **Suitable for**: Dev, testing, prototyping
- **Not suitable for**: High-scale production (millions of requests/month)

**If you exceed free tier limits, you can:**
1. Switch to Azure OpenAI (paid, ~$0.15/1M tokens for gpt-4o-mini)
2. Wait for rate limit reset
3. Request GitHub Models enterprise access

## Files Modified

1. **backend/.env**
   - Removed Azure OpenAI config
   - Added GitHub token config

2. **backend/agent/kraft_agent.py**
   - Imports: Changed from `openai` to `azure.ai.inference`
   - Client: Now uses `ChatCompletionsClient` with GitHub endpoint
   - Removed Azure-specific authentication

## Architecture

```
User Input
    ↓
KraftdIntel Backend
    ↓
kraft_agent.py (Kraftd AI Agent)
    ↓
GitHub Models (gpt-4o)
    ↓
Response → Cosmos DB (learning storage)
    ↓
User Output
```

## Next Steps

1. **Add your GitHub token** to `.env`
2. **Restart backend**: `python main.py`
3. **Test upload** a document
4. **Monitor logs** for: "✓ Kraftd AI Agent initialized with GitHub Models: gpt-4o"

## Cost Comparison

| Provider | Model | Cost (per 1M input tokens) |
|----------|-------|---------------------------|
| **GitHub** | gpt-4o | **FREE** ✅ |
| Azure OpenAI | gpt-4o-mini | $0.15 |
| Azure OpenAI | gpt-4o | $15 |

## When to Upgrade to Azure OpenAI

- Production with high volume (>100K requests/month)
- Need guaranteed rate limits
- Require SLA/support
- Ready to budget $10-50+/month

## Troubleshooting

**Error: "GITHUB_TOKEN not configured"**
- Add `GITHUB_TOKEN=<your-token>` to `.env`

**Error: "ChatCompletionsClient not found"**
- Run: `pip install azure-ai-inference`

**Rate limit exceeded**
- GitHub free tier has rate limiting
- Wait or switch to Azure OpenAI (paid option)

**Token errors**
- Generate new token at https://github.com/settings/tokens
- Ensure it has `repo` permission

## Support

For GitHub Models issues:
- GitHub Support: https://support.github.com
- Azure AI Documentation: https://learn.microsoft.com/en-us/azure/ai-services/

For KraftdIntel issues:
- Check backend logs in Container Apps (UAE North)
- Review extraction workflow for errors
