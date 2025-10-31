# Backend Restart Required

## Issue

The backend server is still running the old code that expects a single `file` parameter, but we've updated it to accept `files: List[UploadFile]` for multiple file uploads.

## Solution

You need to restart the backend server to apply the changes:

### Option 1: Using Docker

```bash
docker-compose restart
```

### Option 2: Manual restart

1. Stop the current backend process (Ctrl+C in the terminal running it)
2. Restart it:

```bash
cd /Users/minhaj47/Desktop/Dev/research-paper-rag-assessment
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: If using the run script

```bash
./run.sh  # or whatever script you're using to start the backend
```

## Verification

After restarting, test the endpoint:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "files=@sample_papers/paper_1.pdf" \
  -v
```

You should see a 200 response instead of 422.

## What Changed

- **Before**: `/api/upload` accepted single `file: UploadFile`
- **After**: `/api/upload` accepts `files: List[UploadFile]` (one or more files)
- The endpoint now intelligently returns single result for 1 file, batch results for multiple files

## Frontend Compatibility

The frontend has been updated to work with the new endpoint format and will automatically handle both single and multiple file uploads.
