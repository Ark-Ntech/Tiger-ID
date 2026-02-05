# External API Integration Guide

This document provides setup instructions and compliance information for external APIs integrated into the Tiger ID system.

## Overview

The Tiger ID system integrates with multiple external APIs to gather intelligence for investigations:
- **USDA**: Animal facility licensing and inspection data
- **CITES**: Trade records for endangered species
- **USFWS**: Federal wildlife permits and enforcement data
- **YouTube**: Video and channel information for social media intelligence
- **Meta/Facebook**: Page and post information for social media intelligence

## YouTube Data API v3

### Setup Instructions

1. **Obtain API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Create credentials (API Key)
   - Copy your API key

2. **Configure Environment**
   ```bash
   export YOUTUBE_API_KEY="your_api_key_here"
   ```

3. **Update Configuration**
   Edit `config/settings.yaml`:
   ```yaml
   external_apis:
     youtube:
       api_key: ${YOUTUBE_API_KEY}
       enabled: true
       base_url: https://www.googleapis.com/youtube/v3
       timeout: 30
   ```

4. **Quota Management**
   - YouTube API has daily quota limits (default: 10,000 units per day)
   - Video search: 100 units per request
   - Video details: 1 unit per request
   - Channel info: 1 unit per request
   - Monitor usage in Google Cloud Console

### Terms of Service Compliance

**Required Reading:**
- [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service)
- [Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- [YouTube Terms of Service](https://www.youtube.com/terms)

**Key Requirements:**
1. **Data Usage**: Only use API data for investigation purposes. Do not store, cache, or redistribute video content.
2. **Rate Limiting**: Implement proper rate limiting to respect API quotas and avoid excessive requests.
3. **Attribution**: When displaying YouTube content, properly attribute to YouTube and content creators.
4. **Privacy**: Respect user privacy. Do not use API data to identify or contact individual users.
5. **Content Policies**: Ensure usage complies with YouTube's Community Guidelines.

**Compliance Checklist:**
- [ ] API key stored securely (environment variables, not in code)
- [ ] Rate limiting implemented
- [ ] Quota monitoring in place
- [ ] Data retention policies documented
- [ ] Terms of Service reviewed and understood
- [ ] Privacy policy updated to reflect YouTube data usage

### Available MCP Tools

The YouTube API is exposed via MCP tools accessible through the orchestrator:
- `youtube_search_videos`: Search for videos by query
- `youtube_get_channel`: Get channel information
- `youtube_get_channel_videos`: Get videos from a channel
- `youtube_search_channels`: Search for channels
- `youtube_get_video_details`: Get detailed video information
- `youtube_get_comments`: Get video comments

## Meta/Facebook Graph API

### Setup Instructions

1. **Create Facebook App**
   - Go to [Facebook Developers](https://developers.facebook.com/)
   - Create a new app or select an existing one
   - Note your App ID and App Secret

2. **Obtain Access Token**
   - For page access: Use Page Access Token
   - For app access: Generate App Access Token (App ID + App Secret)
   - For user access: Implement OAuth flow (if needed)
   - Long-lived tokens recommended for production

3. **Configure Environment**
   ```bash
   export META_ACCESS_TOKEN="your_access_token_here"
   export META_APP_ID="your_app_id_here"
   export META_APP_SECRET="your_app_secret_here"
   ```

4. **Update Configuration**
   Edit `config/settings.yaml`:
   ```yaml
   external_apis:
     meta:
       access_token: ${META_ACCESS_TOKEN}
       app_id: ${META_APP_ID}
       app_secret: ${META_APP_SECRET}
       enabled: true
       base_url: https://graph.facebook.com/v19.0
       timeout: 30
       api_version: v19.0
   ```

5. **Data Use Checkup (DUC)**
   - Complete Data Use Checkup for your app in Facebook App Dashboard
   - Required for apps that access user data or public content
   - Must be completed before production use

### Terms of Service Compliance

**Required Reading:**
- [Meta Platform Terms](https://developers.facebook.com/terms/dfc_platform_terms/)
- [Developer Data Use Policy](https://developers.meta.com/horizon/policy/data-use/)
- [Data Use Checkup Information](https://developers.meta.com/horizon/resources/publish-data-use/)

**Key Requirements:**
1. **Data Use Policy**: Must comply with Meta's Data Use Policy. Use data only for approved purposes.
2. **Privacy**: Respect user privacy. Only access publicly available data or data with proper permissions.
3. **Data Retention**: Do not store user data longer than necessary. Implement data retention policies.
4. **Rate Limiting**: Respect API rate limits (typically 200 requests per hour per user)
5. **Attribution**: Properly attribute content to Facebook and page owners when displaying.
6. **Platform Policy**: Ensure usage complies with Facebook Community Standards.

**Compliance Checklist:**
- [ ] Access token stored securely (environment variables, not in code)
- [ ] Data Use Checkup completed
- [ ] Rate limiting implemented
- [ ] Data retention policies documented
- [ ] Privacy policy updated to reflect Facebook data usage
- [ ] Terms of Service reviewed and understood
- [ ] App permissions configured correctly

### Available MCP Tools

The Meta Graph API is exposed via MCP tools accessible through the orchestrator:
- `meta_get_page`: Get page information
- `meta_search_pages`: Search for Facebook pages
- `meta_get_page_posts`: Get posts from a page
- `meta_get_post_details`: Get detailed post information
- `meta_get_comments`: Get post comments
- `meta_search_posts`: Search public posts (limited availability)

## General Best Practices

### Security
- **Never commit API keys or tokens to version control**
- Use environment variables or secure secret management
- Rotate credentials periodically
- Monitor API usage for suspicious activity

### Per-Domain Rate Limiting

Tiger ID implements a sophisticated per-domain rate limiter in `facility_crawler_service.py`:

```python
from backend.services.facility_crawler_service import RateLimiter

rate_limiter = RateLimiter(
    requests_per_second=0.5,  # 2-second base interval
    max_backoff=60.0          # Maximum 60-second wait
)

# Before each request
await rate_limiter.wait_for_slot(url)

# After request completes
if response.status == 200:
    rate_limiter.report_success(url)
else:
    rate_limiter.report_error(url, response.status)
```

**Key Features:**
- Per-domain tracking (different sites have different rate limits)
- Automatic domain extraction from URLs
- Thread-safe for async operations

### Exponential Backoff Strategy

The rate limiter implements exponential backoff with gradual recovery:

| Event | Backoff Change | Rationale |
|-------|----------------|-----------|
| Success | × 0.9 | Gradually return to normal |
| HTTP 429 | × 2.0 | Rate limited, back off |
| HTTP 503 | × 2.0 | Service unavailable |
| HTTP 520-524 | × 2.0 | Cloudflare errors |
| HTTP 5xx | × 1.5 | Server errors (less aggressive) |

**Backoff Bounds:**
- Minimum: 1.0 (no backoff = base interval)
- Maximum: Capped so total wait ≤ `max_backoff`

### Monitoring Backoff State

```python
stats = rate_limiter.get_stats()
# Returns:
# {
#     "domains_tracked": 15,
#     "total_requests": 142,
#     "domains_with_backoff": {
#         "example.com": 4.0,    # 4x backoff = 8 seconds
#         "slow-site.org": 16.0  # 16x backoff = 32 seconds
#     }
# }
```

### Rate Limiting
- Implement client-side rate limiting (built into discovery system)
- Respect API quotas and limits
- Implement exponential backoff for retries (automatic in RateLimiter)
- Monitor usage and set up alerts for quota limits

### Error Handling
- Handle API errors gracefully
- Log errors for debugging without exposing sensitive information
- Implement fallback mechanisms when APIs are unavailable
- Provide meaningful error messages to users

### Data Management
- Only request data that is needed
- Implement caching where appropriate (respecting API terms)
- Delete or anonymize data after retention period
- Document data retention policies

### Monitoring
- Track API usage and costs
- Monitor for quota exhaustion
- Set up alerts for API failures
- Log API calls for audit purposes

## Troubleshooting

### YouTube API Issues

**Quota Exceeded:**
- Check daily quota in Google Cloud Console
- Reduce request frequency
- Implement better caching
- Request quota increase if needed

**Authentication Errors:**
- Verify API key is correct
- Check API key restrictions in Google Cloud Console
- Ensure YouTube Data API v3 is enabled

### Meta API Issues

**Access Token Expired:**
- Generate new long-lived token
- Implement token refresh logic
- Check token permissions in App Dashboard

**Rate Limit Exceeded:**
- Implement exponential backoff
- Reduce request frequency
- Use batch requests where possible

**Data Use Checkup Required:**
- Complete DUC in Facebook App Dashboard
- Ensure app is in approved status
- Review and update app permissions

## Support and Resources

### YouTube API
- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [API Quotas and Limits](https://developers.google.com/youtube/v3/getting-started#quota)
- [Support Forum](https://support.google.com/youtube/thread/2489758)

### Meta Graph API
- [Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [API Versioning Guide](https://developers.facebook.com/docs/graph-api/changelog)
- [Support Portal](https://developers.facebook.com/support/)

## Legal Compliance Summary

### YouTube API
- Comply with YouTube API Services Terms of Service
- Follow Developer Policies
- Respect YouTube Community Guidelines
- Do not store or redistribute video content without permission

### Meta Graph API
- Comply with Meta Platform Terms
- Follow Developer Data Use Policy
- Complete Data Use Checkup (DUC)
- Respect Facebook Community Standards
- Implement proper data retention and deletion

Both APIs require:
- Secure credential storage
- Rate limiting compliance
- Privacy policy updates
- Data retention documentation
- Regular ToS review

## Notes

- **Langgraph**: Implemented as optional workflow engine. Enable via `USE_LANGGRAPH=true` environment variable. The system defaults to custom OrchestratorAgent pattern but can use Langgraph StateGraph workflow when enabled. Langgraph provides structured state management and conditional routing between investigation phases.
- **MCP Implementation**: All MCP servers follow consistent patterns defined in `MCPServerBase`. New servers (YouTube, Meta) follow the same structure as existing servers (Firecrawl, Database, TigerID).

