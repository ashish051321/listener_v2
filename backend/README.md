# Conversation Recorder Backend

A FastAPI-based backend service for the conversation recorder application. This service handles audio file uploads from the Angular frontend, stores them locally, and generates conversation suggestions based on the audio files received.

## Features

- **Audio File Upload**: Accepts WebM audio files from the frontend
- **File Storage**: Saves uploaded files to local storage with unique naming
- **CORS Support**: Configured for Angular development server
- **File Management**: List and manage uploaded audio files
- **Health Monitoring**: Health check endpoint for monitoring
- **Input Validation**: Validates file types and sizes
- **Error Handling**: Comprehensive error handling and logging
- **Suggestion Generation**: Generates dummy conversation suggestions based on audio files received
- **Suggestion Queue**: Provides suggestions one by one with tracking of sent suggestions

## Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)

## Installation

1. **Install Poetry** (if not already installed):
   ```bash
   pip install poetry
   ```

2. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Running the Application

### Development Mode
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using uvicorn directly:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Base URL
- Development: `http://localhost:8000`
- Production: Configure as needed

### Available Endpoints

#### 1. Root Endpoint
- **GET** `/`
- Returns API information and available endpoints

#### 2. Health Check
- **GET** `/health`
- Returns service health status

#### 3. Audio Upload
- **POST** `/api/audio/upload`
- Accepts multipart form data with:
  - `audio`: Audio file (WebM format)
  - `timestamp`: ISO timestamp of recording
  - `duration`: Duration in seconds
- Automatically generates suggestions based on total audio files received

#### 4. List Audio Files
- **GET** `/api/audio/files`
- Returns list of all uploaded audio files

#### 5. Get Next Suggestion
- **GET** `/api/suggestions/next`
- Returns the next unsent suggestion from the queue
- Marks the suggestion as sent so it won't be returned again

#### 6. Get All Suggestions (Debug)
- **GET** `/api/suggestions/all`
- Returns all suggestions with their status (for debugging/testing)

#### 7. Reset Suggestions (Debug)
- **POST** `/api/suggestions/reset`
- Resets the suggestion system (for testing purposes)

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## File Storage

### Directory Structure
```
backend/
├── uploads/                    # Audio files storage
│   ├── conversation_20231201_143022_uuid1.webm
│   ├── conversation_20231201_143032_uuid2.webm
│   └── ...
├── app/
│   ├── main.py                # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── models.py              # Pydantic models
│   └── utils.py               # Utility functions
└── pyproject.toml             # Poetry configuration
```

### File Naming Convention
Files are saved with the format:
```
conversation_YYYYMMDD_HHMMSS_UUID.extension
```

Example: `conversation_20231201_143022_550e8400-e29b-41d4-a716-446655440000.webm`

## Suggestion System

### How It Works
1. **Audio Upload**: When an audio file is uploaded, the system counts total audio files
2. **Suggestion Generation**: Generates 1-3 dummy suggestions based on the audio count
3. **Suggestion Queue**: Suggestions are stored in memory with unique IDs
4. **Suggestion Retrieval**: Frontend can request suggestions one by one via `/api/suggestions/next`
5. **Tracking**: System tracks which suggestions have been sent to avoid duplicates

### Suggestion Response Format
```json
{
  "success": true,
  "suggestion": "Consider asking about their experience with similar projects",
  "timestamp": "2023-12-01T14:30:22.123Z",
  "suggestion_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Suggestion retrieved successfully"
}
```

### Dummy Suggestion Examples
- "Consider asking about their experience with similar projects"
- "You might want to explore the technical challenges they've faced"
- "Ask about their team dynamics and collaboration methods"
- "Discuss the timeline and milestones they've set"
- "Explore their approach to problem-solving"

## Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB in bytes
UPLOADS_DIR=uploads

# Security Configuration
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### Default Settings
- **Host**: `0.0.0.0`
- **Port**: `8000`
- **Max File Size**: 50MB
- **Allowed Origins**: `http://localhost:4200`
- **Upload Directory**: `uploads/`

## Integration with Frontend

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:4200` (Angular dev server)
- `http://127.0.0.1:4200`

### Expected Request Format
The frontend should send POST requests to `/api/audio/upload` with:
- `Content-Type: multipart/form-data`
- `audio`: Audio file blob
- `timestamp`: ISO timestamp string
- `duration`: Duration string

### Suggestion Retrieval
The frontend should:
1. Call `/api/suggestions/next` to get the next suggestion
2. Display the suggestion to the user
3. Store previous suggestions in an accordion or similar UI component
4. Continue calling the endpoint to get new suggestions as they become available

### Response Format
```json
{
  "success": true,
  "message": "Audio file uploaded successfully",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "conversation_20231201_143022_550e8400-e29b-41d4-a716-446655440000.webm",
  "file_size": 1024000,
  "timestamp": "2023-12-01T14:30:22.123Z",
  "duration": "10"
}
```

## Security Considerations

### File Validation
- Only audio files are accepted
- File size limits are enforced
- Unique filenames prevent conflicts

### Rate Limiting
- Configurable rate limiting (disabled by default in development)
- Prevents abuse of upload endpoints

### CORS
- Strict CORS configuration
- Only allows specified origins

## Monitoring and Logging

### Health Check
Monitor service health with:
```bash
curl http://localhost:8000/health
```

### File Management
List uploaded files:
```bash
curl http://localhost:8000/api/audio/files
```

### Suggestion Management
Get all suggestions (debug):
```bash
curl http://localhost:8000/api/suggestions/all
```

### Logs
The application logs to stdout/stderr. In production, consider:
- Structured logging
- Log aggregation
- File rotation

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill the process or change port in config
   ```

2. **Permission Denied**
   ```bash
   # Ensure uploads directory is writable
   chmod 755 uploads/
   ```

3. **CORS Errors**
   - Verify `ALLOWED_ORIGINS` includes your frontend URL
   - Check browser console for CORS details

4. **File Upload Fails**
   - Check file size limits
   - Verify file type is audio
   - Ensure uploads directory exists and is writable

### Debug Mode
Run with debug logging:
```bash
poetry run uvicorn app.main:app --log-level debug
```

## Production Deployment

### Using Gunicorn
```bash
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY app/ ./app/
RUN mkdir uploads

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

This project is licensed under the MIT License.
