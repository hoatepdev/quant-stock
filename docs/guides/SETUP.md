# Detailed Setup Guide

This guide provides comprehensive setup instructions for the Vietnam Quant Platform.

## System Requirements

### Minimum Requirements
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB free space
- OS: Linux, macOS, or Windows (with WSL2)

### Recommended Requirements
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Linux (Ubuntu 20.04+) or macOS

## Prerequisites Installation

### 1. Docker and Docker Compose

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Windows:**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Enable WSL2 backend

### 2. Python 3.10+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS:**
```bash
brew install python@3.10
```

## Platform Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd vnquant
```

### Step 2: Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
nano .env  # or use your preferred editor
```

3. Configure the following sections:

**Database Configuration:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vietnam_quant
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
```

**Redis Configuration:**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**API Keys:**

Register for SSI API access:
1. Visit https://iboard.ssi.com.vn/
2. Create an account
3. Navigate to API section
4. Generate API key and secret

```env
SSI_API_KEY=your_ssi_api_key
SSI_SECRET_KEY=your_ssi_secret_key
VNDIRECT_API_KEY=your_vndirect_key  # Optional
```

**Application Settings:**
```env
ENVIRONMENT=development  # or production
DEBUG=true  # false in production
LOG_LEVEL=INFO
API_PORT=8000
```

### Step 3: Docker Deployment

1. Build Docker images:
```bash
make docker-build
```

2. Start all services:
```bash
make docker-up
```

This starts:
- PostgreSQL with TimescaleDB (port 5432)
- Redis (port 6379)
- FastAPI application (port 8000)
- Celery worker
- pgAdmin (optional, port 5050)

3. Verify services are running:
```bash
make docker-ps
```

4. Check logs:
```bash
make docker-logs
```

### Step 4: Database Initialization

Initialize the database schema:

```bash
make init-db
```

This will:
- Create all database tables
- Enable TimescaleDB extension
- Create hypertables for time-series data
- Set up indexes
- Apply constraints

### Step 5: Data Backfill (Optional)

Load historical data:

```bash
make backfill-data
```

**Note:** This process:
- Takes 1-2 hours for full backfill
- Downloads 5 years of price data
- Fetches financial statements
- Calculates all factors
- Can be resumed if interrupted

To backfill specific tickers or date ranges:
```bash
python scripts/backfill_data.py --start-date 2023-01-01 --tickers VNM,HPG,VIC
```

### Step 6: Verify Installation

1. Check API health:
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "environment": "development",
  "database": "healthy"
}
```

2. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

3. Test stock screening:
```bash
curl -X POST "http://localhost:8000/api/v1/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "roe": {"min": 15}
    },
    "limit": 10
  }'
```

## Development Setup

For local development without Docker:

### 1. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
make install-dev
```

### 3. Set Up Local PostgreSQL

**Install PostgreSQL with TimescaleDB:**

```bash
# Ubuntu/Debian
sudo apt install postgresql-14 postgresql-contrib
sudo add-apt-repository ppa:timescale/timescaledb-ppa
sudo apt update
sudo apt install timescaledb-2-postgresql-14

# macOS
brew install postgresql@14 timescaledb
```

**Create Database:**

```bash
sudo -u postgres createdb vietnam_quant
sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vietnam_quant TO your_user;"
```

### 4. Set Up Local Redis

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis
```

### 5. Run Development Server

```bash
make run-api
```

API will be available at http://localhost:8000

## Configuration Options

### Logging Configuration

Edit `config/logging.yaml` to customize logging:

```yaml
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    level: INFO
  file:
    class: logging.FileHandler
    filename: logs/app.log
    formatter: default
    level: DEBUG
loggers:
  vietnam_quant:
    level: INFO
    handlers: [console, file]
```

### Rate Limiting

Adjust API rate limits in `.env`:

```env
SSI_RATE_LIMIT_REQUESTS=100  # Requests per period
SSI_RATE_LIMIT_PERIOD=60     # Period in seconds
API_RATE_LIMIT_REQUESTS=1000
API_RATE_LIMIT_PERIOD=60
```

### Cache Settings

Configure cache TTL in `.env`:

```env
CACHE_TTL_SECONDS=300         # General cache TTL
PRICE_DATA_CACHE_TTL=3600    # Price data cache (1 hour)
FACTOR_CACHE_TTL=1800         # Factor cache (30 minutes)
```

## Troubleshooting

### Docker Issues

**Problem:** Containers fail to start
```bash
# Check Docker logs
make docker-logs

# Restart services
make docker-down
make docker-up
```

**Problem:** Port conflicts
```bash
# Change ports in docker-compose.yml
# Edit docker/docker-compose.yml
ports:
  - "8001:8000"  # Change API port
```

### Database Issues

**Problem:** Database connection refused
```bash
# Check PostgreSQL is running
make docker-ps

# Verify connection settings in .env
# Check DATABASE_URL is correct
```

**Problem:** TimescaleDB extension error
```bash
# Connect to database
docker exec -it vietnam_quant_db psql -U postgres -d vietnam_quant

# Enable extension manually
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

### API Issues

**Problem:** API returns 500 errors
```bash
# Check API logs
docker logs vietnam_quant_api

# Verify database is initialized
make init-db
```

**Problem:** No data returned from endpoints
```bash
# Check if data has been loaded
curl http://localhost:8000/api/v1/tickers

# Run backfill if needed
make backfill-data
```

### Data Issues

**Problem:** Backfill fails
```bash
# Check SSI API credentials
# Verify API key in .env

# Run with verbose logging
LOG_LEVEL=DEBUG make backfill-data
```

## Production Deployment

### Security Hardening

1. **Change default passwords:**
```env
DB_PASSWORD=<strong-random-password>
API_SECRET_KEY=<cryptographically-secure-key>
```

2. **Disable debug mode:**
```env
DEBUG=false
ENVIRONMENT=production
```

3. **Configure HTTPS:**
- Use reverse proxy (nginx, Caddy)
- Obtain SSL certificate
- Update ALLOWED_ORIGINS

4. **Set up firewall:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Performance Tuning

1. **Database optimization:**
```sql
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Optimize work_mem
ALTER SYSTEM SET work_mem = '16MB';

-- Reload configuration
SELECT pg_reload_conf();
```

2. **API workers:**
```env
API_WORKERS=4  # Set to number of CPU cores
```

3. **Connection pooling:**
```python
# Adjust in src/database/connection.py
pool_size=20
max_overflow=40
```

### Monitoring Setup

1. **Health checks:**
```bash
# Add to cron
*/5 * * * * curl -f http://localhost:8000/api/v1/health || alert
```

2. **Log monitoring:**
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/vietnam-quant
```

3. **Database monitoring:**
```sql
-- Monitor query performance
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

## Backup and Recovery

### Database Backup

```bash
# Automated daily backup
docker exec vietnam_quant_db pg_dump -U postgres vietnam_quant > backup_$(date +%Y%m%d).sql

# Add to cron
0 2 * * * /path/to/backup-script.sh
```

### Restore from Backup

```bash
# Stop services
make docker-down

# Restore database
docker exec -i vietnam_quant_db psql -U postgres vietnam_quant < backup_20240115.sql

# Restart services
make docker-up
```

## Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild containers
make docker-down
make docker-build
make docker-up

# Run migrations if needed
# (Migrations will be automated in future releases)
```

### Daily Maintenance

Set up cron job for daily updates:

```bash
# Add to crontab
0 18 * * 1-5 cd /path/to/vnquant && python scripts/run_daily_update.py
```

## Getting Help

- Check logs: `make docker-logs`
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/docs
- Email: support@example.com
