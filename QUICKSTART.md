# Quick Start Guide

Get the Vietnam Quant Platform up and running in 10 minutes!

## Prerequisites Checklist

- [x] Docker and Docker Compose installed
- [x] 4GB+ RAM available
- [x] 20GB+ disk space
- [ ] SSI API credentials (OPTIONAL - only if using SSI as data source)

## 5-Step Setup

### 1. Configure Environment (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Minimum required settings:**

```env
# Database (can keep defaults for development)
DB_PASSWORD=postgres

# Data Source (vnstock is default and FREE - no API key needed!)
DATA_SOURCE=vnstock

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO

# Optional: Only needed if you want to use SSI instead of vnstock
# SSI_API_KEY=your_actual_key_here
# SSI_SECRET_KEY=your_actual_secret_here
```

**Note:** The platform now uses **vnstock** as the default data source, which is:
- ✅ **FREE** - No API registration or keys required
- ✅ **FAST** - Better performance than SSI
- ✅ **RELIABLE** - Built-in corporate action adjustments
- ✅ **COMPLETE** - Covers HOSE, HNX, and UPCoM exchanges

You can optionally switch to SSI by setting `DATA_SOURCE=ssi` in `.env`

### 2. Start Services (2 minutes)

```bash
# Build and start all services
make docker-up

# Wait for services to be ready (~30 seconds)
# Check status
make docker-ps
```

### 3. Initialize Database (1 minute)

```bash
# Create tables and indexes
make init-db
```

### 4. Verify Installation (1 minute)

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Access API documentation
open http://localhost:8000/docs
```

### 5. Load Sample Data (Optional - 5 minutes)

```bash
# Quick test with a few stocks
python scripts/backfill_data.py --tickers VNM,HPG,VIC --start-date 2024-01-01
```

## Test Your Setup

### Test 1: Get Available Tickers

```bash
curl http://localhost:8000/api/v1/tickers | jq
```

### Test 2: Screen Stocks

```bash
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "roe": {"min": 15}
    },
    "limit": 5
  }' | jq
```

### Test 3: Get Stock Factors

```bash
curl http://localhost:8000/api/v1/factors/VNM | jq
```

## Common Issues & Solutions

### Issue: Docker containers won't start

**Solution:**

```bash
# Check Docker is running
docker ps

# If not, start Docker Desktop
# Then retry
make docker-down
make docker-up
```

### Issue: "Connection refused" errors

**Solution:**

```bash
# Wait for services to fully start (can take 30-60 seconds)
sleep 30

# Check logs
make docker-logs
```

### Issue: No data returned from API

**Solution:**

```bash
# Make sure database is initialized
make init-db

# Load some data
python scripts/backfill_data.py --tickers VNM --start-date 2024-01-01
```

### Issue: Data source errors

**Solution:**

**If using vnstock (default):**
- No API keys needed
- Check internet connection
- Verify vnstock is installed: `pip install vnstock==0.3.2`

**If using SSI:**
1. Verify your API credentials are correct in `.env`
2. Check you have API access enabled on SSI iBoard
3. Ensure you haven't exceeded rate limits (100 requests/minute)
4. Set `DATA_SOURCE=ssi` in `.env`

## Next Steps

Once everything is running:

1. **Load More Data** - Run full backfill:

   ```bash
   make backfill-data
   ```

   ⚠️ This takes 1-2 hours for all stocks

2. **Explore the API** - Visit http://localhost:8000/docs

   - Try different screening criteria
   - Get factor history
   - Test filtering and sorting

3. **Set Up Daily Updates** - Add to cron:

   ```bash
   0 18 * * 1-5 cd /path/to/vnquant && python scripts/run_daily_update.py
   ```

4. **Read Full Documentation**:
   - [README.md](README.md) - Feature overview
   - [docs/SETUP.md](docs/SETUP.md) - Detailed setup guide
   - [docs/API.md](docs/API.md) - API documentation

## Development Workflow

### Run Tests

```bash
make run-tests
```

### Format Code

```bash
make format
```

### View Logs

```bash
# All services
make docker-logs

# Specific service
docker logs vietnam_quant_api -f
```

### Stop Services

```bash
make docker-down
```

### Access Database

```bash
# Using psql
docker exec -it vietnam_quant_db psql -U postgres -d vietnam_quant

# Or use pgAdmin at http://localhost:5050
# (if running with dev profile: docker-compose --profile dev up)
```

## Production Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure HTTPS/SSL
- [ ] Set up automated backups
- [ ] Configure monitoring
- [ ] Review and adjust rate limits
- [ ] Set up log aggregation
- [ ] Configure firewall rules
- [ ] Test disaster recovery procedures

## Getting Help

**Documentation:**

- README.md - Overview and features
- docs/SETUP.md - Detailed setup instructions
- docs/API.md - API reference
- docs/ARCHITECTURE.md - System architecture

**Support:**

- GitHub Issues: Report bugs and request features
- Logs: Check `logs/app.log` and `logs/error.log`
- Docker logs: `make docker-logs`

## Quick Reference

### Makefile Commands

```bash
make help              # Show all available commands
make docker-up         # Start services
make docker-down       # Stop services
make docker-logs       # View logs
make init-db           # Initialize database
make backfill-data     # Load historical data
make run-tests         # Run tests
make format            # Format code
make lint              # Run linters
make clean             # Clean temporary files
```

### API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/tickers` - List tickers
- `POST /api/v1/screen` - Screen stocks
- `GET /api/v1/factors/{ticker}` - Get stock factors
- `GET /api/v1/factors/available` - List available factors

### Default Ports

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050 (dev profile)

---

**You're all set!** 🚀

Start exploring Vietnamese stocks with quantitative analysis!
