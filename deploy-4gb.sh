#!/bin/bash

# Deployment script for 4GB RAM server
# Optimized for minimal resource usage (2-3 CCU)

set -e

echo "========================================="
echo "  DNSE Insight - 4GB Server Deployment"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check system resources
print_info "Checking system resources..."
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
echo "   Total RAM: ${TOTAL_RAM}MB"

if [ "$TOTAL_RAM" -lt 3500 ]; then
    print_error "Not enough RAM! Need at least 4GB"
    exit 1
fi

if [ "$TOTAL_RAM" -lt 4500 ]; then
    print_warning "Running on minimal RAM (4GB). Some features will be disabled."
else
    print_success "RAM is sufficient"
fi

# Update system
print_info "Updating system..."
sudo apt-get update -qq

# Install dependencies
print_info "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv redis-server nginx git

# Setup project
print_info "Setting up project..."
cd /opt/dnse-insight || cd ~

# Create virtual environment
print_info "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install lightweight requirements
print_info "Installing Python packages (lightweight version)..."
pip install --upgrade pip
pip install -r requirements-lite.txt

print_success "Python packages installed"

# Setup environment
if [ ! -f .env ]; then
    print_info "Creating .env file..."
    cp .env.4gb-server .env
    print_warning "Please edit .env with your DNSE credentials!"
else
    print_info ".env already exists"
fi

# Configure Redis for 4GB server
print_info "Configuring Redis for minimal RAM..."
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""
appendonly no
EOF

sudo systemctl restart redis
print_success "Redis configured"

# Setup systemd service for backend
print_info "Setting up backend service..."
sudo tee /etc/systemd/system/dnse-backend.service > /dev/null <<EOF
[Unit]
Description=DNSE Trading Bot Backend
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python dashboard/backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable dnse-backend
print_success "Backend service created"

# Setup nginx for frontend
print_info "Setting up nginx..."
cd dashboard/frontend
npm install
npm run build
cd ../..

sudo tee /etc/nginx/sites-available/dnse-insight > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root $(pwd)/dashboard/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/dnse-insight /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
print_success "Nginx configured"

# Start services
print_info "Starting services..."
sudo systemctl start redis
sudo systemctl start dnse-backend

print_success "Services started"

# Display status
echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  ✅ Redis: Running on port 6379"
echo "  ✅ Backend: Running on port 8000"
echo "  ✅ Nginx: Running on port 80"
echo ""
echo "Access:"
echo "  🌐 Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  📊 API Docs: http://$(hostname -I | awk '{print $1}')/api/docs"
echo ""
echo "Management:"
echo "  sudo systemctl status dnse-backend"
echo "  sudo systemctl restart dnse-backend"
echo "  sudo journalctl -fu dnse-backend"
echo ""
print_warning "Remember to edit .env with your DNSE credentials!"
echo ""
