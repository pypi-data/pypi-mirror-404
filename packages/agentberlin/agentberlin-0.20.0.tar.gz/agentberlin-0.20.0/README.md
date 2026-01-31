# Agent Berlin Python SDK

Official Python SDK for [Agent Berlin](https://agentberlin.ai) - AI-powered SEO and AEO automation.

## Installation

```bash
pip install agentberlin
```


## Configuration

```python
client = AgentBerlin()
```

## Error Handling

```python
from agentberlin import AgentBerlin
from agentberlin.exceptions import (
    AgentBerlinError,
    AgentBerlinAuthenticationError,
    AgentBerlinNotFoundError,
    AgentBerlinRateLimitError,
)

client = AgentBerlin()

try:
    analytics = client.analytics.get()
except AgentBerlinAuthenticationError:
    print("Invalid or missing API token")
except AgentBerlinNotFoundError:
    print("Domain not found")
except AgentBerlinRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except AgentBerlinError as e:
    print(f"API error: {e.message}")
```

---

# Workflow Script API Documentation

This section provides detailed API documentation for writing workflow scripts. When writing workflow scripts, you have access to the 'agentberlin' package which is pre-installed in the execution environment. But you need to initialize the client by calling AgentBerlin() class initialization.

## Important Notes for Script Writers

1. The project domain is automatically populated for all methods that require it
2. Optional input from the LLM is available as the 'INPUT' variable (may be None or a parsed JSON value)
3. Scripts should print their results or return values that can be captured
4. Use proper error handling with try/except blocks

## Available Resources and Methods

### 1. Analytics Resource
Get comprehensive analytics data for the project.

```python
# Get analytics for the project
analytics = client.analytics.get()

# Available fields:
# analytics.domain - The domain name
# analytics.domain_authority - Domain authority score (0-100)
# analytics.visibility.current_percentage - Current visibility percentage
# analytics.visibility.ranking_stability - Ranking stability score
# analytics.visibility.share_of_voice - Share of voice percentage
# analytics.visibility.history - List of VisibilityPoint(date, percentage)
# analytics.traffic.total_sessions - Total traffic sessions
# analytics.traffic.llm_sessions - Sessions from LLM sources
# analytics.traffic.channel_breakdown.direct - Direct traffic
# analytics.traffic.channel_breakdown.organic_search - Organic search traffic
# analytics.traffic.channel_breakdown.referral - Referral traffic
# analytics.traffic.channel_breakdown.organic_social - Social traffic
# analytics.traffic.channel_breakdown.llm - LLM-referred traffic
# analytics.traffic.daily_trend - List of DailyTraffic(date, sessions, llm_sessions)
# analytics.topics - List of TopicSummary(name, appearances, avg_position, topical_authority, trend)
# analytics.competitors - List of CompetitorSummary(name, visibility, share_of_voice)
# analytics.data_range.start - Data start date
# analytics.data_range.end - Data end date
# analytics.last_updated - Last update timestamp
```

### 2. Pages Resource
Search and get detailed information about pages.

```python
# Search for pages
pages = client.pages.search(
    query="SEO best practices",  # Semantic search query
    limit=10,                     # Max results (default: 10)
    domain=None,                  # Optional: filter by specific domain
    status_code=None,             # Optional: filter by HTTP status (200, 404, "error", "redirect", "success")
    topic=None,                   # Optional: filter by topic
    page_type=None                # Optional: "pillar" or "landing"
)
# Returns: PageSearchResponse with pages list and total count
# Each page has: url, title

# Get detailed page information
page = client.pages.get(
    url="https://example.com/blog/article",
    content_length=500  # Optional: include content preview (0 = no content)
)
# Returns PageDetailResponse with:
# page.url - Page URL
# page.title - Page title
# page.meta_description - Meta description
# page.h1 - H1 heading
# page.domain - Domain name
# page.links.inlinks - List of incoming links (PageLink objects)
# page.links.outlinks - List of outgoing links (PageLink objects)
# page.topic_info.topics - List of topic names
# page.topic_info.topic_scores - List of topic relevance scores
# page.topic_info.page_type - "pillar" or "landing"
# page.topic_info.assigned_topic - Primary assigned topic
# page.content_preview - Content preview (if content_length > 0)
# page.content_length - Total content length
```

### 3. Keywords Resource
Search for keywords with SEO metrics.

```python
# Search for keywords
keywords = client.keywords.search(
    query="digital marketing",  # Semantic search query
    limit=10                    # Max results (default: 10)
)
# Returns KeywordSearchResponse with keywords list and total count
# Each keyword has:
# keyword.keyword - The keyword text
# keyword.volume - Monthly search volume
# keyword.difficulty - Difficulty score (0-100)
# keyword.cpc - Cost per click
# keyword.intent - Search intent: "informational", "commercial", "transactional", "navigational"
```

### 4. Brand Resource
Get and update brand profile information.

```python
# Get brand profile
profile = client.brand.get_profile()
# Returns BrandProfileResponse with:
# profile.domain - Domain name
# profile.name - Brand name
# profile.context - Brand context/description
# profile.search_analysis_context - Search analysis context
# profile.domain_authority - Domain authority score
# profile.competitors - List of competitor domains
# profile.industries - List of industries
# profile.business_models - List of business models
# profile.company_size - Company size
# profile.target_customer_segments - Target segments
# profile.geographies - Target geographies
# profile.personas - Target personas
# profile.sitemaps - Sitemap URLs
# profile.profile_urls - Profile URLs

# Update brand profile
client.brand.update_profile(
    field="competitors",  # Field to update
    value="competitor.com",  # New value
    mode="add"  # "add" to append, "set" to replace
)
# Valid fields: name, context, competitors, industries, business_models,
#               company_size, target_segments, geographies, personas
```

### 5. Google Custom Search Resource
Simple, fast Google web searches using Google Custom Search Engine.

```python
# Search Google
results = client.google_cse.search(
    query="best seo tools",
    max_results=10,      # Max results (1-10, default: 10)
    country="us",        # Optional: ISO 3166-1 alpha-2 country code
    language="lang_en"   # Optional: ISO 639-1 with "lang_" prefix
)
# Returns GoogleCSEResponse with:
# results.query - The search query
# results.results - List of GoogleCSEResult objects
# results.total - Total results count
# Each result has: title, url, snippet
```

### 6. SerpApi Resource
Multi-engine search supporting Google and Bing with various search types.

**Parameters:**
- `query` (required): The search query
- `engine`: Search engine - `"google"` or `"bing"` (default: `"google"`)
- `search_type`: Type of search (default: `"web"`)
  - `"web"` - Standard web results
  - `"news"` - News articles (Google only)
  - `"images"` - Image results (Google only)
  - `"videos"` - Video results (Google only)
  - `"shopping"` - Shopping results (Google only)
- `device`: Device type - `"desktop"`, `"tablet"`, or `"mobile"` (optional)
- `country`: ISO 3166-1 alpha-2 country code, e.g., `"us"`, `"gb"`, `"de"` (optional)
- `language`: ISO 639-1 language code, e.g., `"en"`, `"de"`, `"fr"` (optional)
- `max_results`: Number of results, 1-100 (default: 10)

```python
# Bing web search
results = client.serpapi.search(
    query="best seo tools",
    engine="bing",
    country="us",
    max_results=10
)

# Google News search
results = client.serpapi.search(
    query="AI technology",
    search_type="news",
    country="us"
)

# Google Images search
results = client.serpapi.search(
    query="modern website design",
    search_type="images",
    max_results=20
)

# Google Shopping search
results = client.serpapi.search(
    query="wireless headphones",
    search_type="shopping",
    country="us"
)

# Returns SerpApiResponse with:
# results.query - The search query
# results.engine - Search engine used
# results.search_type - Type of search performed
# results.results - List of SerpApiResult objects
# results.total - Total results count
# results.search_metadata - Optional metadata (id, status, total_time_taken)
# Each result has: title, url, snippet, displayed_link, date, thumbnail
```

### 7. Files Resource
Upload files to cloud storage (auto-deleted after 30 days).

```python
# Upload from string content (must encode to bytes)
csv_content = "url,title\nhttps://example.com,Example"
result = client.files.upload(
    file_data=csv_content.encode(),  # Must be bytes, not string
    filename="report.csv"
)
# Returns FileUploadResponse with:
# result.file_id - Unique file identifier
# result.filename - The filename
# result.content_type - MIME type
# result.size - File size in bytes
# result.url - Download URL

# Upload from file path
result = client.files.upload(file_path="/path/to/file.csv")

# Upload with explicit content type
result = client.files.upload(
    file_data=b'{"key": "value"}',
    filename="data.json",
    content_type="application/json"
)
# Allowed content types: text/plain, text/csv, text/markdown, text/html,
# text/css, text/javascript, application/json, application/xml
```

### 8. GSC Resource (Google Search Console)
Access Google Search Console data through the Agent Berlin API.

```python
# Query search analytics data
result = client.gsc.query(
    start_date="2024-01-01",
    end_date="2024-01-31",
    dimensions=["query", "page"],  # Optional: "query", "page", "country", "device", "searchAppearance", "date"
    search_type="web",             # Optional: "web", "image", "video", "news", "discover", "googleNews"
    row_limit=100,                 # Optional: max rows (default 1000, max 25000)
    start_row=0,                   # Optional: pagination offset
    aggregation_type="auto",       # Optional: "auto", "byPage", "byProperty"
    data_state="final"             # Optional: "final", "all"
)
# Returns SearchAnalyticsResponse with:
# result.rows - List of SearchAnalyticsRow objects
# result.response_aggregation_type - How data was aggregated
# Each row has: keys (list), clicks, impressions, ctr, position

# Get site information
site = client.gsc.get_site()
# Returns SiteInfo with:
# site.site_url - The site URL
# site.permission_level - Permission level (e.g., "siteOwner")

# List all sitemaps
sitemaps = client.gsc.list_sitemaps()
# Returns SitemapListResponse with:
# sitemaps.sitemap - List of Sitemap objects
# Each sitemap has: path, last_submitted, is_pending, is_sitemaps_index,
#                   last_downloaded, warnings, errors, contents

# Get specific sitemap details
sitemap = client.gsc.get_sitemap("https://example.com/sitemap.xml")
# Returns Sitemap with full details

# Inspect a URL's index status
inspection = client.gsc.inspect_url(
    url="https://example.com/page",
    language_code="en-US"  # Optional: for localized results
)
# Returns UrlInspectionResponse with:
# inspection.inspection_result.inspection_result_link - Link to GSC
# inspection.inspection_result.index_status_result - Index status details
# inspection.inspection_result.mobile_usability_result - Mobile usability
# inspection.inspection_result.rich_results_result - Rich results info
```

#### Paginating Through All Results

The Search Console API returns a maximum of 25,000 rows per request. To retrieve all data for large result sets, use pagination with `row_limit` and `start_row`:

```python
from agentberlin import AgentBerlin

client = AgentBerlin()

def get_all_search_analytics(start_date: str, end_date: str, dimensions: list):
    """Fetch all search analytics data with automatic pagination."""
    all_rows = []
    start_row = 0
    row_limit = 25000  # Maximum allowed by the API

    while True:
        result = client.gsc.query(
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            row_limit=row_limit,
            start_row=start_row,
        )

        all_rows.extend(result.rows)

        # If we got fewer rows than requested, we've reached the end
        if len(result.rows) < row_limit:
            break

        start_row += row_limit

    return all_rows

# Example usage
all_queries = get_all_search_analytics(
    start_date="2024-01-01",
    end_date="2024-01-31",
    dimensions=["query"]
)
print(f"Total queries: {len(all_queries)}")
```

**Note:** The API has daily quota limits. For large datasets, consider reducing the date range, using fewer dimensions, or filtering with `dimension_filter_groups`.

## Example Script Patterns

### Pattern 1: Data Retrieval Script
```python
# Retrieves and formats analytics data
from agentberlin import AgentBerlin
import json

client = AgentBerlin()
analytics = client.analytics.get()

result = {
    "visibility": analytics.visibility.current_percentage,
    "traffic": analytics.traffic.total_sessions,
    "llm_traffic": analytics.traffic.llm_sessions,
    "top_topics": [
        {"name": t.name, "authority": t.topical_authority}
        for t in analytics.topics[:5]
    ]
}
print(json.dumps(result, indent=2))
```

### Pattern 2: Search and Analysis Script
```python
# Searches for content opportunities
from agentberlin import AgentBerlin
import json

client = AgentBerlin()
query = INPUT.get("query", "SEO tips") if INPUT else "SEO tips"
pages = client.pages.search(query=query, limit=20)
keywords = client.keywords.search(query=query, limit=20)

opportunities = []
for kw in keywords.keywords:
    if kw.difficulty and kw.difficulty < 50 and kw.volume and kw.volume > 100:
        opportunities.append({
            "keyword": kw.keyword,
            "volume": kw.volume,
            "difficulty": kw.difficulty
        })

print(json.dumps({"opportunities": opportunities}, indent=2))
```

### Pattern 3: Competitive Analysis Script
```python
# Analyzes competitors from SERP
from agentberlin import AgentBerlin
import json

client = AgentBerlin()
query = INPUT.get("query") if INPUT else "best seo software"
serp = client.google_cse.search(query=query, max_results=10)
profile = client.brand.get_profile()

competitor_presence = []
for result in serp.results:
    is_competitor = any(comp in result.url for comp in profile.competitors)
    is_own = profile.domain in result.url
    competitor_presence.append({
        "url": result.url,
        "title": result.title,
        "is_competitor": is_competitor,
        "is_own": is_own
    })

print(json.dumps(competitor_presence, indent=2))
```

### Pattern 4: Search Console Analytics Script
```python
# Retrieves and analyzes search performance data
from agentberlin import AgentBerlin
import json

client = AgentBerlin()

# Get search analytics for the last 30 days
result = client.gsc.query(
    start_date="2024-01-01",
    end_date="2024-01-31",
    dimensions=["query"],
    row_limit=50
)

# Find top performing queries
top_queries = []
for row in result.rows:
    if row.clicks > 10:
        top_queries.append({
            "query": row.keys[0],
            "clicks": row.clicks,
            "impressions": row.impressions,
            "ctr": round(row.ctr * 100, 2),
            "position": round(row.position, 1)
        })

# Sort by clicks
top_queries.sort(key=lambda x: x["clicks"], reverse=True)
print(json.dumps({"top_queries": top_queries[:10]}, indent=2))
```
