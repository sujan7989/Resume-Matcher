# Oracle Cloud Always Free VM — Full Deployment Guide

## What You'll Have When Done
- Python FastAPI backend running 24/7 on Oracle ARM VM (free forever)
- Nginx reverse proxy on port 80/443
- Auto-restart on crash via systemd
- Frontend on Vercel pointing to your Oracle backend

---

## Step 1 — Create Oracle Cloud Account & VM

1. Go to https://cloud.oracle.com and sign up (free, needs credit card for verification only — won't be charged)
2. After login, go to **Compute → Instances → Create Instance**
3. Configure:
   - **Name:** `resume-matcher-backend`
   - **Image:** Ubuntu 22.04 or 24.04
   - **Shape:** Change to `VM.Standard.A1.Flex` (ARM — Always Free)
     - Set **OCPUs: 2**, **Memory: 12 GB**
   - **Networking:** Create or use existing VCN, assign **public IP**
   - **SSH Keys:** Upload your public key (or generate one)
4. Click **Create**
5. Wait ~2 minutes for the VM to boot

---

## Step 2 — Open Firewall Ports in OCI Console

Oracle has TWO firewalls — you must open BOTH:

### OCI Security List (cloud-level firewall)
1. Go to **Networking → Virtual Cloud Networks → your VCN**
2. Click **Security Lists → Default Security List**
3. Add **Ingress Rules:**
   - Port **80** (HTTP) — Source: `0.0.0.0/0`, Protocol: TCP
   - Port **443** (HTTPS) — Source: `0.0.0.0/0`, Protocol: TCP

### VM-level iptables (Ubuntu blocks by default on Oracle)
SSH into your VM and run:
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 3 — SSH Into Your VM

```bash
ssh ubuntu@YOUR_VM_PUBLIC_IP
```

---

## Step 4 — Run the Setup Script

Copy `oracle-setup.sh` to your VM and run it:

```bash
# On your local machine, copy the script:
scp oracle-setup.sh ubuntu@YOUR_VM_IP:~/

# Then on the VM:
bash oracle-setup.sh
```

This will:
- Install Python 3.13, nginx, certbot
- Clone your Resume Matcher repo
- Set up a Python venv and install all dependencies
- Install Playwright + Chromium (for PDF generation)
- Create systemd service (auto-start on boot)
- Configure nginx reverse proxy
- Enable UFW firewall

---

## Step 5 — Configure Your .env

```bash
nano /opt/resume-matcher/apps/backend/.env
```

Set these values (use `oracle-env-template.env` as reference):
```
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-chat
LLM_API_KEY=your-actual-api-key
FRONTEND_BASE_URL=https://resume-matcher-zeta.vercel.app
CORS_ORIGINS=["https://resume-matcher-zeta.vercel.app"]
```

---

## Step 6 — Start the Backend

```bash
sudo systemctl start resume-matcher
sudo systemctl status resume-matcher
```

Test it works:
```bash
curl http://localhost:8000/api/v1/health
# Should return: {"status": "ok", ...}
```

Also test from outside:
```
http://YOUR_VM_IP/api/v1/health
```

---

## Step 7 — Update Vercel Frontend Env Var

1. Go to https://vercel.com/sujankumarreddy824-5492s-projects/resume-matcher/settings/environment-variables
2. Add:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `http://YOUR_VM_IP`  (or `https://yourdomain.com` if using HTTPS)
3. Click **Save**
4. Go to **Deployments** → click **Redeploy** on the latest deployment

---

## Step 8 — (Optional) Add HTTPS with a Free Domain

If you have a domain, run:
```bash
bash oracle-https-setup.sh yourdomain.com
```

For a free domain, use https://freedns.afraid.org or https://duckdns.org

---

## Useful Commands

```bash
# Check backend logs
sudo journalctl -u resume-matcher -f

# Restart backend
sudo systemctl restart resume-matcher

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Update code from GitHub
cd /opt/resume-matcher
git pull
cd apps/backend
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart resume-matcher
```

---

## Architecture

```
User Browser
     │
     ▼
Vercel (Next.js frontend)
https://resume-matcher-zeta.vercel.app
     │  NEXT_PUBLIC_API_URL
     ▼
Oracle Cloud VM (Always Free, ARM, 2 OCPU / 12GB RAM)
nginx :80/:443
     │
     ▼
uvicorn :8000 (FastAPI Python backend)
     │
     ▼
SQLite DB (/opt/resume-matcher/apps/backend/data/)
```
