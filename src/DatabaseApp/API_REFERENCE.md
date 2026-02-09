# Dockerfile Database API Reference

## Quick Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required (add for production use)

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/stats` | Database statistics |
| GET | `/dockerfiles` | Get all Dockerfiles |
| GET | `/dockerfiles/dates` | Get all unique dates |
| GET | `/dockerfiles/by-date/{date}` | Get all Dockerfiles for a date |
| GET | `/dockerfiles/by-date/{date}/names` | Get Dockerfile names for a date |
| GET | `/dockerfiles/by-date/{date}/{name}` | Get specific Dockerfile |
| GET | `/dockerfiles/by-date/{date}/{name}/content` | Get Dockerfile content (plain text) |
| POST | `/dockerfiles` | Create new Dockerfile |
| DELETE | `/dockerfiles/{id}` | Delete Dockerfile by ID |

---

## Detailed Endpoint Documentation

### 1. Root Endpoint

**GET /** - Get API information

```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "Dockerfile Database API",
  "details": {
    "version": "1.0.0",
    "endpoints": {
      "docs": "/docs",
      "health": "/health",
      "stats": "/stats",
      "dockerfiles": "/dockerfiles"
    }
  }
}
```

---

### 2. Health Check

**GET /health** - Check API and database health

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "total_entries": 42
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Database health check failed: ..."
}
```

---

### 3. Statistics

**GET /stats** - Get database statistics

```http
GET /stats
```

**Response (200 OK):**
```json
{
  "total_dockerfiles": 42,
  "unique_dates": 7,
  "unique_names": 15
}
```

---

### 4. Get All Dockerfiles

**GET /dockerfiles** - Retrieve all Dockerfiles

```http
GET /dockerfiles
```

**Response (200 OK):**
```json
{
  "count": 2,
  "dockerfiles": [
    {
      "id": 1,
      "name": "Dockerfile.flask",
      "content": "FROM python:3.11-slim\nWORKDIR /app\n...",
      "created_date": "2026-02-08",
      "created_time": "14:30:00",
      "created_timestamp": "2026-02-08T14:30:00+00:00",
      "timezone": "UTC"
    },
    {
      "id": 2,
      "name": "Dockerfile.django",
      "content": "FROM python:3.11-slim\n...",
      "created_date": "2026-02-08",
      "created_time": "15:45:00",
      "created_timestamp": "2026-02-08T15:45:00+00:00",
      "timezone": "UTC"
    }
  ]
}
```

---

### 5. Get Unique Dates

**GET /dockerfiles/dates** - Get all dates with stored Dockerfiles

```http
GET /dockerfiles/dates
```

**Response (200 OK):**
```json
[
  "2026-02-08",
  "2026-02-07",
  "2026-02-06"
]
```

---

### 6. Get Dockerfiles by Date

**GET /dockerfiles/by-date/{date}** - Get all Dockerfiles for a specific date

**Parameters:**
- `date` (path) - Date in ISO format (YYYY-MM-DD)

```http
GET /dockerfiles/by-date/2026-02-08
```

**Response (200 OK):**
```json
{
  "count": 3,
  "dockerfiles": [
    {
      "id": 1,
      "name": "Dockerfile.flask",
      "content": "FROM python:3.11-slim\n...",
      "created_date": "2026-02-08",
      "created_time": "14:30:00",
      "created_timestamp": "2026-02-08T14:30:00+00:00",
      "timezone": "UTC"
    }
    // ... more dockerfiles
  ]
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

---

### 7. Get Dockerfile Names by Date

**GET /dockerfiles/by-date/{date}/names** - Get Dockerfile names for a date

**Parameters:**
- `date` (path) - Date in ISO format (YYYY-MM-DD)

```http
GET /dockerfiles/by-date/2026-02-08/names
```

**Response (200 OK):**
```json
[
  "Dockerfile.flask",
  "Dockerfile.django",
  "Dockerfile.fastapi"
]
```

---

### 8. Get Specific Dockerfile (JSON)

**GET /dockerfiles/by-date/{date}/{name}** - Get specific Dockerfile with metadata

**Parameters:**
- `date` (path) - Date in ISO format (YYYY-MM-DD)
- `name` (path) - Dockerfile name

```http
GET /dockerfiles/by-date/2026-02-08/Dockerfile.flask
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Dockerfile.flask",
  "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]",
  "created_date": "2026-02-08",
  "created_time": "14:30:00",
  "created_timestamp": "2026-02-08T14:30:00+00:00",
  "timezone": "UTC"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Dockerfile 'Dockerfile.flask' not found for date 2026-02-08"
}
```

---

### 9. Get Dockerfile Content (Plain Text)

**GET /dockerfiles/by-date/{date}/{name}/content** - Get only the content as plain text

**Parameters:**
- `date` (path) - Date in ISO format (YYYY-MM-DD)
- `name` (path) - Dockerfile name

```http
GET /dockerfiles/by-date/2026-02-08/Dockerfile.flask/content
```

**Response (200 OK):**
```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

**Content-Type:** `text/plain`

---

### 10. Create Dockerfile

**POST /dockerfiles** - Add a new Dockerfile to the database

**Request Body:**
```json
{
  "name": "Dockerfile.custom",
  "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]"
}
```

**Response (201 Created):**
```json
{
  "id": 5,
  "name": "Dockerfile.custom",
  "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]",
  "created_date": "2026-02-08",
  "created_time": "16:20:00",
  "created_timestamp": "2026-02-08T16:20:00+00:00",
  "timezone": "UTC"
}
```

**Error Response (409 Conflict):**
```json
{
  "detail": "Dockerfile 'Dockerfile.custom' already exists at this timestamp"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": "Failed to create Dockerfile: ..."
}
```

---

### 11. Delete Dockerfile

**DELETE /dockerfiles/{id}** - Delete a Dockerfile by its ID

**Parameters:**
- `id` (path) - Dockerfile ID (integer)

```http
DELETE /dockerfiles/5
```

**Response (200 OK):**
```json
{
  "message": "Dockerfile with ID 5 deleted successfully"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Dockerfile with ID 5 not found"
}
```

---

## Common Use Cases

### Use Case 1: Store Generated Dockerfile

```bash
# Generate Dockerfile
python dockerfile_generator_v2.py app.py

# Read the content
CONTENT=$(cat Dockerfile)

# Store via API
curl -X POST http://localhost:8000/dockerfiles \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Dockerfile.app\", \"content\": \"$CONTENT\"}"
```

### Use Case 2: Retrieve Today's Dockerfiles

```bash
# Get today's date
TODAY=$(date +%Y-%m-%d)

# Fetch Dockerfiles
curl http://localhost:8000/dockerfiles/by-date/$TODAY
```

### Use Case 3: Download Specific Dockerfile

```bash
# Download as plain text
curl http://localhost:8000/dockerfiles/by-date/2026-02-08/Dockerfile.flask/content \
  -o Dockerfile.flask
```

### Use Case 4: Monitor Database

```bash
# Watch statistics
watch -n 5 'curl -s http://localhost:8000/stats | jq .'
```

---

## Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid date format, malformed JSON |
| 404 | Not Found | Dockerfile or date not found |
| 409 | Conflict | Duplicate Dockerfile entry |
| 500 | Internal Server Error | Database error, unexpected failure |
| 503 | Service Unavailable | Database not connected |

---

## Rate Limiting

Currently no rate limiting implemented. For production:
- Implement rate limiting per IP
- Add authentication
- Monitor API usage

---

## Data Models

### DockerfileCreate (Request)

```typescript
{
  name: string        // Required: Dockerfile name
  content: string     // Required: Full Dockerfile content
}
```

### DockerfileResponse (Response)

```typescript
{
  id: integer                 // Database ID
  name: string               // Dockerfile name
  content: string            // Full content
  created_date: string       // ISO date (YYYY-MM-DD)
  created_time: string       // ISO time (HH:MM:SS)
  created_timestamp: string  // Full ISO 8601 timestamp
  timezone: string           // Timezone used (e.g., "UTC")
}
```

---

## Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Interactive API testing
- Request/response examples
- Schema documentation
- Try-it-out functionality

---

## Security Best Practices

For production deployment:

1. **Add Authentication**
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @app.get("/dockerfiles", dependencies=[Depends(security)])
   async def get_dockerfiles():
       ...
   ```

2. **Use HTTPS**
   ```bash
   uvicorn dockerfile_api:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

3. **Add CORS if needed**
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

4. **Input Validation**
   - Already implemented via Pydantic
   - Add custom validators as needed

5. **Rate Limiting**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

---

## Performance Tips

1. **Use HTTP/2** for better performance
2. **Enable response compression**
3. **Add caching** for frequently accessed dates
4. **Use connection pooling** for database
5. **Monitor with metrics** (Prometheus, etc.)

---

## Examples with Different Languages

### Python (requests)
```python
import requests

response = requests.get("http://localhost:8000/dockerfiles/by-date/2026-02-08")
data = response.json()
```

### JavaScript (fetch)
```javascript
fetch('http://localhost:8000/dockerfiles/by-date/2026-02-08')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Go
```go
resp, err := http.Get("http://localhost:8000/dockerfiles/by-date/2026-02-08")
defer resp.Body.Close()
body, _ := ioutil.ReadAll(resp.Body)
```

### curl (bash)
```bash
curl -X GET "http://localhost:8000/dockerfiles/by-date/2026-02-08" \
  -H "accept: application/json"
```
