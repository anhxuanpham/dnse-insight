# DNSE Insight - Production Deployment Guide

Complete guide for deploying DNSE Insight trading system to production.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB SSD
- Network: Stable connection with low latency

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- (Optional) Kubernetes for cluster deployment

---

## 🚀 Quick Start with Docker

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/dnse-insight.git
cd dnse-insight
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Required Configuration:**
```bash
# DNSE API Credentials (from https://hdsd.dnse.com.vn)
DNSE_API_BASE_URL=https://api.dnse.com.vn
DNSE_API_KEY=your_api_key_here
DNSE_API_SECRET=your_api_secret_here
DNSE_ACCOUNT_ID=your_account_id_here

# MQTT Credentials
MQTT_BROKER=mqtt.dnse.com.vn
MQTT_PORT=1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# Trading Mode
TRADING_MODE=paper  # or 'live' for real trading

# Database Password
DB_PASSWORD=your_secure_password_here

# Telegram (Optional but recommended)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f backend

# Access services
# - Frontend Dashboard: http://localhost:3000
# - Backend API: http://localhost:8000
# - Grafana: http://localhost:3001 (admin/admin)
# - Flower (Celery): http://localhost:5555
```

---

## 🏭 Production Deployment

### Option 1: Single Server Deployment

#### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app directory
sudo mkdir -p /opt/dnse-insight
sudo chown $USER:$USER /opt/dnse-insight
cd /opt/dnse-insight
```

#### 2. Clone and Configure

```bash
git clone https://github.com/yourusername/dnse-insight.git .
cp .env.example .env
nano .env  # Configure production settings
```

#### 3. Setup SSL (Optional but recommended)

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Update docker-compose.yml to use SSL
# Add volumes for certificates
```

#### 4. Deploy

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 5. Setup Systemd Service

Create `/etc/systemd/system/dnse-insight.service`:

```ini
[Unit]
Description=DNSE Insight Trading System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dnse-insight
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable dnse-insight
sudo systemctl start dnse-insight
```

### Option 2: Kubernetes Deployment

#### 1. Create Kubernetes Manifests

See `k8s/` directory for complete manifests.

#### 2. Deploy to Cluster

```bash
# Create namespace
kubectl create namespace dnse-insight

# Apply secrets
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/

# Check status
kubectl get pods -n dnse-insight
```

---

## ⚙️ Configuration

### Environment Variables

#### Core Settings

```bash
# Application
TRADING_MODE=paper|live          # Trading mode
LOG_LEVEL=INFO|DEBUG|WARNING    # Log level
LOG_FILE=logs/trading_bot.log   # Log file path
```

#### DNSE API

```bash
DNSE_API_BASE_URL=https://api.dnse.com.vn
DNSE_API_KEY=your_key
DNSE_API_SECRET=your_secret
DNSE_ACCOUNT_ID=your_account_id

# MQTT for real-time data
MQTT_BROKER=mqtt.dnse.com.vn
MQTT_PORT=1883
MQTT_USERNAME=username
MQTT_PASSWORD=password
```

#### Trading Parameters

```bash
MAX_POSITION_SIZE=100000000      # Max position size (VND)
MAX_POSITIONS=10                 # Max concurrent positions
RISK_PER_TRADE=0.02             # Risk per trade (2%)
DEFAULT_STOP_LOSS_PCT=0.03      # Default stop loss (3%)
VOLATILITY_THRESHOLD=0.05       # Volatility cutloss threshold
```

#### Database

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

#### Notifications

```bash
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=true

# Discord webhook (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Email (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_password
EMAIL_TO=recipient@example.com
```

---

## 📊 Monitoring

### Prometheus Metrics

Access Prometheus at `http://localhost:9091`

**Key Metrics:**
- `trading_orders_total` - Total orders placed
- `trading_orders_pnl` - P&L distribution
- `portfolio_total_value` - Portfolio value
- `active_positions_count` - Number of positions
- `api_requests_total` - API requests
- `cache_hits_total` - Cache performance

### Grafana Dashboards

Access Grafana at `http://localhost:3001` (admin/admin)

**Pre-configured Dashboards:**
1. Trading Performance
2. System Health
3. API Performance
4. Database Metrics

### Logging

**View Logs:**
```bash
# Backend logs
docker-compose logs -f backend

# All services
docker-compose logs -f

# Specific time range
docker-compose logs --since 30m backend
```

**Log Files:**
- `logs/trading_bot.log` - Main application log
- `logs/error.log` - Error logs
- `logs/trading.log` - Trade execution log (365 days retention)

---

## 💾 Backup & Recovery

### Database Backup

```bash
# Backup TimescaleDB
docker exec dnse-timescaledb pg_dump -U trader dnse_trading > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i dnse-timescaledb psql -U trader dnse_trading < backup_20240101.sql
```

### Configuration Backup

```bash
# Backup .env and configs
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker/
```

### Automated Backups

Add to crontab:
```bash
# Daily database backup at 2 AM
0 2 * * * /opt/dnse-insight/scripts/backup.sh

# Weekly full backup
0 3 * * 0 /opt/dnse-insight/scripts/full_backup.sh
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Containers Won't Start

```bash
# Check logs
docker-compose logs backend

# Check system resources
docker stats

# Restart services
docker-compose restart
```

#### 2. MQTT Connection Failed

```bash
# Verify credentials
docker-compose exec backend python -c "from core.price_stream import price_stream_manager; price_stream_manager.connect()"

# Check network
docker-compose exec backend ping mqtt.dnse.com.vn
```

#### 3. High Memory Usage

```bash
# Check memory
docker stats

# Adjust memory limits in docker-compose.yml
services:
  backend:
    mem_limit: 2g
    memswap_limit: 2g
```

#### 4. Database Performance

```bash
# Check connections
docker exec dnse-timescaledb psql -U trader -d dnse_trading -c "SELECT count(*) FROM pg_stat_activity;"

# Vacuum database
docker exec dnse-timescaledb psql -U trader -d dnse_trading -c "VACUUM ANALYZE;"
```

### Health Checks

```bash
# Check all services health
curl http://localhost:8000/api/v1/health

# Check specific service
docker-compose ps
docker inspect dnse-backend | grep -i health
```

### Performance Tuning

**Optimize Redis:**
```bash
# In docker-compose.yml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

**Optimize TimescaleDB:**
```sql
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';

-- Reload config
SELECT pg_reload_conf();
```

---

## 🔐 Security Best Practices

1. **Change Default Passwords**
   - Grafana admin password
   - Database passwords
   - Redis password (if enabled)

2. **Use SSL/TLS**
   - Enable HTTPS for frontend
   - Use SSL for database connections

3. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

4. **API Rate Limiting**
   - Enabled by default in `utils/security.py`
   - Adjust limits in environment variables

5. **Regular Updates**
   ```bash
   # Update containers
   docker-compose pull
   docker-compose up -d

   # Update system
   sudo apt update && sudo apt upgrade
   ```

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale celery workers
docker-compose up -d --scale celery-worker=3

# Scale backend instances (with load balancer)
docker-compose up -d --scale backend=3
```

### Kubernetes Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/dnse-insight/issues
- Documentation: README.md, ROADMAP.md
- Email: support@example.com

---

**Last Updated:** 2024-01-15
