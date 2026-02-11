# Web Search API Specifications

## DuckDuckGo API

### Endpoint
```
GET https://api.duckduckgo.com/
```

### Parameters
- `q` (required): Search query
- `format`: Response format (json, xml)
- `no_redirect`: Prevent redirects (1 or 0)
- `skip_disambig`: Skip disambiguation (1 or 0)

### Response Format
```json
{
  "Heading": "Search Query",
  "Results": [...],
  "RelatedTopics": [...],
  "Definition": "...",
  "Abstract": "..."
}
```

### Rate Limits
- No formal rate limit for unauthenticated requests
- Heavy usage may be throttled

## Bing Search

### Endpoint
```
GET https://www.bing.com/search
```

### Parameters
- `q`: Search query
- `count`: Number of results to return
- `first`: Index of first result to return

## Baidu Search

### Endpoint
```
GET https://www.baidu.com/s
```

### Parameters
- `wd`: Search query
- `rn`: Number of results to return
- `ie`: Input encoding

## HTTP Client Specifications

### Headers
- `User-Agent`: Should mimic a real browser to avoid blocking
- `Accept-Language`: Set to preferred language (e.g., en-US,en;q=0.9)
- `Accept-Encoding`: gzip, deflate for efficient transfer
- Timeout: Should be set appropriately to avoid hanging requests

### Response Processing
- Status codes other than 200 indicate failure
- Content-Type header indicates response type
- Large responses should be processed efficiently

## Proxy Configuration

### Environment Variables
- `HTTPS_PROXY`: HTTPS proxy server (e.g., `http://proxy.example.com:8080`)
- `HTTP_PROXY`: HTTP proxy server (e.g., `http://proxy.example.com:8080`)

### Proxy Support
- The script automatically detects and uses proxy settings from environment variables
- To configure a proxy: `export HTTPS_PROXY=http://proxy-server:port`
- Proxy configuration is essential for users behind corporate firewalls or in restricted regions
- Proxies are applied per-request based on URL scheme (HTTP or HTTPS)

## Regional Access Considerations

### China and GFW (Great Firewall)
- Many international search services are blocked in mainland China
- Services like Google are inaccessible, but Bing and Baidu may work
- Consider using regional alternatives like Baidu, Sogou, or 360 Search
- Users in China may need to use a VPN or proxy to access international services

### Multi-Provider Strategy
- Primary: DuckDuckGo (works well internationally)
- Backup: Bing (accessible internationally)
- Alternative: Baidu (better accessibility in China)