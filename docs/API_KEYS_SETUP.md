# External API Keys Setup Guide

This document explains how to obtain and configure API keys for external services used by the Tiger ID application.

## Required API Keys

### 1. Firecrawl API (Web Scraping) - Recommended

**Purpose:** Web scraping and search functionality

**How to Get:**
1. Visit: https://firecrawl.dev
2. Sign up for an account
3. Navigate to API Keys section
4. Copy your API key

**Configuration:**
```env
FIRECRAWL_API_KEY=your_api_key_here
FIRECRAWL_SEARCH_ENABLED=true
```

**Alternative Providers:**
- **Serper API** (Google Search): https://serper.dev
  ```env
  SERPER_API_KEY=your_api_key_here
  WEB_SEARCH_PROVIDER=serper
  ```

- **Tavily API**: https://tavily.com
  ```env
  TAVILY_API_KEY=your_api_key_here
  WEB_SEARCH_PROVIDER=tavily
  ```

- **Perplexity API**: https://www.perplexity.ai
  ```env
  PERPLEXITY_API_KEY=your_api_key_here
  WEB_SEARCH_PROVIDER=perplexity
  ```

### 2. YouTube Data API (Optional)

**Purpose:** Video search and monitoring

**How to Get:**
1. Visit: https://console.cloud.google.com
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Copy the API key

**Configuration:**
```env
YOUTUBE_API_KEY=your_api_key_here
```

**Note:** YouTube API has quota limits. Free tier: 10,000 units/day

### 3. Meta/Facebook Graph API (Optional)

**Purpose:** Social media search and monitoring

**How to Get:**
1. Visit: https://developers.facebook.com
2. Create a new app
3. Get App ID and App Secret
4. Generate Access Token

**Configuration:**
```env
META_ACCESS_TOKEN=your_access_token_here
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_ENABLED=true
```

**Note:** Requires Facebook Developer account and app approval for production use

### 4. OmniVinci API (Optional - NVIDIA)

**Purpose:** Advanced AI model for multimodal analysis

**How to Get:**
1. Visit: https://www.nvidia.com/en-us/ai-data-science/products/omnivinci/
2. Sign up for NVIDIA API access
3. Get API key from dashboard

**Configuration:**
```env
OMNIVINCI_API_KEY=your_api_key_here
```

**Alternative:** Use local model (requires GPU)
```env
OMNIVINCI_USE_LOCAL=true
OMNIVINCI_MODEL_PATH=./data/models/omnivinci/omnivinci
```

### 5. Government APIs (Optional)

#### USDA API
**Purpose:** Facility data synchronization

**How to Get:**
1. Visit: https://www.aphis.usda.gov/aphis/ourfocus/animalwelfare
2. Contact USDA for API access
3. Obtain API key

**Configuration:**
```env
USDA_API_KEY=your_api_key_here
USDA_ENABLED=true
```

#### CITES API
**Purpose:** Trade records synchronization

**How to Get:**
1. Visit: https://trade.cites.org
2. Contact CITES for API access
3. Obtain API key

**Configuration:**
```env
CITES_API_KEY=your_api_key_here
CITES_ENABLED=true
```

#### USFWS API
**Purpose:** Permit data synchronization

**How to Get:**
1. Visit: https://www.fws.gov
2. Contact USFWS for API access
3. Obtain API key

**Configuration:**
```env
USFWS_API_KEY=your_api_key_here
USFWS_ENABLED=true
```

## Priority Order

1. **Firecrawl API** - Most important for web search functionality
2. **YouTube API** - Useful for video monitoring
3. **Meta API** - Useful for social media monitoring
4. **Government APIs** - Optional, for data synchronization
5. **OmniVinci API** - Optional, for advanced AI features

## Testing API Keys

After adding API keys to your `.env` file:

1. Restart the backend server
2. Check health endpoint: `GET /health`
3. Test web search: Use the Web Search tab in Launch Investigation
4. Check logs for any authentication errors

## Security Notes

- **Never commit API keys to version control**
- Use `.env` file (already in `.gitignore`)
- Rotate keys regularly
- Use environment-specific keys (dev/staging/prod)
- Monitor API usage to avoid unexpected charges

## Troubleshooting

### "API key invalid" errors
- Verify key is copied correctly (no extra spaces)
- Check if key has expired
- Verify API is enabled in provider dashboard

### "Quota exceeded" errors
- Check usage limits in provider dashboard
- Upgrade plan if needed
- Implement rate limiting

### "Permission denied" errors
- Verify API permissions/scopes are correct
- Check if API needs to be enabled in provider console

