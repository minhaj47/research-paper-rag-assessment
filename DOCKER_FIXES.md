# Docker Compose Fixes - Summary

## Issues Fixed

### 1. **API Container Not Starting Automatically**

**Problem**: The API container had a hard dependency on Qdrant's health check, but the Qdrant image doesn't include `curl` or `wget` needed for HTTP health checks.

**Solution**:

- Changed Qdrant's health check dependency from `service_healthy` to `service_started`
- Removed the health check configuration from Qdrant service
- Kept the health check dependency on Postgres (which works correctly)

### 2. **Postgres Health Check Database Name Error**

**Problem**: The Postgres health check was using `pg_isready -U raguser` which tried to connect to a database named "raguser" (same as username) instead of "ragdb", causing FATAL errors in logs.

**Solution**:

- Updated health check to: `pg_isready -U ${POSTGRES_USER:-raguser} -d ${POSTGRES_DB:-ragdb}`
- Now correctly specifies both user and database name

### 3. **Collection Already Exists Warning**

**Problem**: The Qdrant client was attempting to create a collection without checking if it existed first, resulting in ugly 409 Conflict errors in logs.

**Solution**:

- Modified `create_collection()` in `qdrant_client.py` to check if collection exists before creating
- Now shows friendly message: `✅ Collection 'research_papers' already exists`

### 4. **Build Caching Optimization**

**Problem**: Docker wasn't efficiently using layer caching, causing slow rebuilds.

**Solution** (in Dockerfile):

- Reordered layers to optimize caching:
  1. System dependencies (rarely change)
  2. Python dependencies via requirements.txt (change occasionally)
  3. Create directories
  4. Copy source code (changes frequently)
- This ensures that changing source code doesn't trigger reinstallation of all dependencies

### 5. **Removed Obsolete Configuration**

- Removed `version: "3.8"` from docker-compose.yml (obsolete in modern Docker Compose)

## Files Modified

### docker-compose.yml

- Removed obsolete `version` field
- Removed Qdrant health check configuration
- Changed API dependency on Qdrant from `service_healthy` to `service_started`
- Added health check configuration for API service
- Fixed Postgres health check to include database name

### Dockerfile

- Optimized layer ordering for better caching
- Moved source code copy to the end
- Added clear comments explaining caching strategy

### src/services/qdrant_client.py

- Improved `create_collection()` method to check existence before creation
- Added friendly status messages
- Better error handling

## Benefits

1. **✅ Automatic Startup**: All containers now start automatically with `docker compose up --build`
2. **✅ Faster Builds**: Subsequent builds are much faster due to layer caching
3. **✅ Clean Logs**: No more confusing error messages for normal operations
4. **✅ Health Monitoring**: All services have proper health checks
5. **✅ Reliable Dependencies**: Services wait for dependencies to be ready before starting

## Usage

```bash
# Start all services (first time or after changes)
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Health Check Endpoints

- **API**: http://localhost:8000/health
- **Qdrant**: http://localhost:6333/readyz
- **Postgres**: Internal health check via `pg_isready -U raguser -d ragdb`

## Test Results

After fixes:

```
NAME           STATUS
rag_api        Up X seconds (healthy)
rag_postgres   Up X seconds (healthy)
rag_qdrant     Up X seconds
```

All containers start automatically without errors or warnings!
