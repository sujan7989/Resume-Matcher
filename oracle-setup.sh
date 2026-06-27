#!/bin/bash
# ============================================================
# Resume Matcher - Oracle Cloud Always Free VM Setup Script
# Run this as: bash oracle-setup.sh
# Tested on: Ubuntu 22.04 / 24.04 ARM (Ampere A1)
# ============================================================

set -e  # exit on any error

echo "============================================"
echo " Resume Matcher Backend - Oracle VM Setup"
echo "============================================"

# ── 1. System update ────────────────────────────
echo "[1/9] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# ── 2. Install dependencies ─────────────────────
echo "[2/9] Installing system dependencies..."

# Add deadsnakes PPA for Python 3.13 (not in Ubuntu 22.04 default repos)
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y

sudo apt-get install -y \
    python3.13 python3.13-venv python3.13-dev python3.13-distutils \
    python3-pip \
    nginx \
    certbot python3-certbot-nginx \
    git \
    curl \
    ufw \
    build-essential \
    libssl-dev \
    libffi-dev \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 \
    netfilter-persistent iptables-persistent

# Verify Python version
python3.13 --version

# ── 3. Clone the repo ───────────────────────────
echo "[3/9] Cloning Resume Matcher repo..."
cd /opt
sudo git clone https://github.com/sujan7989/Resume-Matcher.git resume-matcher
sudo chown -R $USER:$USER /opt/resume-matcher

# ── 4. Python venv + install deps ───────────────
echo "[4/9] Setting up Python virtual environment..."
cd /opt/resume-matcher/apps/backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers (needed for PDF generation)
echo "[4b] Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# ── 5. Create .env file ─────────────────────────
echo "[5/9] Creating .env config..."
if [ ! -f /opt/resume-matcher/apps/backend/.env ]; then
    cp /opt/resume-matcher/apps/backend/.env.sample \
       /opt/resume-matcher/apps/backend/.env
    echo ""
    echo "  ⚠️  IMPORTANT: Edit /opt/resume-matcher/apps/backend/.env"
    echo "  Set LLM_PROVIDER, LLM_API_KEY, FRONTEND_BASE_URL, CORS_ORIGINS"
    echo ""
fi

# ── 6. Create data directory ────────────────────
echo "[6/9] Creating data directory..."
mkdir -p /opt/resume-matcher/apps/backend/data
chmod 755 /opt/resume-matcher/apps/backend/data

# ── 7. Create systemd service ───────────────────
echo "[7/9] Creating systemd service..."
sudo tee /etc/systemd/system/resume-matcher.service > /dev/null <<EOF
[Unit]
Description=Resume Matcher FastAPI Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/resume-matcher/apps/backend
EnvironmentFile=/opt/resume-matcher/apps/backend/.env
ExecStart=/opt/resume-matcher/apps/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable resume-matcher

# ── 8. Configure nginx ──────────────────────────
echo "[8/9] Configuring nginx..."
sudo tee /etc/nginx/sites-available/resume-matcher > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # Allow large file uploads (resumes)
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Long timeout for AI operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 300s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/resume-matcher \
            /etc/nginx/sites-enabled/resume-matcher
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# ── 9. Firewall rules ───────────────────────────
echo "[9/9] Configuring UFW firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Oracle Cloud VMs also have iptables rules that block traffic by default
# These rules open ports 80 and 443 at the OS level
echo "Opening ports 80 and 443 in iptables (Oracle VM requirement)..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save

echo ""
echo "============================================"
echo " ✅ Setup complete!"
echo "============================================"
echo ""
echo " Next steps:"
echo ""
echo " 1. Edit the .env file with your real values:"
echo "    nano /opt/resume-matcher/apps/backend/.env"
echo ""
echo " 2. Start the backend service:"
echo "    sudo systemctl start resume-matcher"
echo "    sudo systemctl status resume-matcher"
echo ""
echo " 3. (Optional) Add HTTPS with Let's Encrypt:"
echo "    sudo certbot --nginx -d YOUR_DOMAIN"
echo ""
echo " 4. Open Oracle Cloud firewall ports 80 & 443"
echo "    in your OCI Console → VCN → Security Lists"
echo ""
echo " Your backend will be at: http://YOUR_VM_IP/api/v1"
echo "============================================"
