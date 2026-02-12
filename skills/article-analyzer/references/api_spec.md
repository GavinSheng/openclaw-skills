# Article Analysis API Specification

## Overview
The Article Analyzer skill provides detailed analysis of individual articles to generate suitable content for public account publishing.

## Endpoints

### GET /analyze
Analyzes a single article from a given URL.

**Request Parameters:**
- `url` (string, required): The URL of the article to analyze

**Response:**
```
{
  "success": boolean,
  "url": string,
  "title": string,
  "summary": string,
  "detail": string,
  "processing_duration": float,
  "model_used": string,
  "error": string (if success is false)
}
```

**Fields:**
- `success`: Whether the operation was successful
- `url`: The URL of the analyzed article
- `title`: The title of the article
- `summary`: A summary of the article (under 300 words)
- `detail`: Detailed analysis of the article, formatted for public account publishing
- `processing_duration`: Time taken to process the request in seconds
- `model_used`: The model used for analysis
- `error`: Error message if operation failed

## Error Handling

The skill handles various error conditions:
- Invalid URLs
- Unreachable articles
- Content parsing failures
- Model API errors