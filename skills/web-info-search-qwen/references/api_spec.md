# Tongyi Web Search API Specifications

## Supported Search Engines

### Sogou (搜狗)
- Popular Chinese search engine
- Good for Chinese language content
- Access: https://www.sogou.com/web

### 360 Search (360搜索)
- Another popular Chinese search engine
- Access: https://www.so.com/s

### Bing
- International search engine
- Access: https://www.bing.com/search

## HTTP Client Specifications

### Headers
- `User-Agent`: Should mimic a real browser to avoid blocking
- `Accept-Language`: Set to preferred language (e.g., zh-CN,zh;q=0.9,en;q=0.8 for Chinese regions)
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

## Regional Access Considerations

### China and GFW (Great Firewall)
- Some international search services are restricted in mainland China
- Chinese search engines like Sogou and 360 Search work well in China
- Bing is generally accessible internationally

### Multi-Provider Strategy
- Primary: Sogou or 360 Search (Chinese-region optimized)
- Backup: Bing (accessible internationally)