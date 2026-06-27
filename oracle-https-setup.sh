#!/bin/bash
# ============================================================
# Resume Matcher - Add HTTPS with Let's Encrypt
# Run AFTER oracle-setup.sh AND after pointing a domain to VM IP
# Usage: bash oracle-https-setup.sh yourdomain.com
# ============================================================

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Usage: bash oracle-https-setup.sh yourdomain.com"
    echo ""
    echo "If you don't have a domain, skip this and use the IP directly."
    echo "Your Vercel frontend env var would be: http://YOUR_VM_IP"
    exit 1
fi

echo "Setting up HTTPS for: $DOMAIN"

# Update nginx server_name
sudo sed -i "s/server_name _;/server_name $DOMAIN;/" \
    /etc/nginx/sites-available/resume-matcher
sudo nginx -t
sudo systemctl reload nginx

# Get SSL cert from Let's Encrypt
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

echo ""
echo "✅ HTTPS enabled!"
echo "Your backend API is now at: https://$DOMAIN/api/v1"
echo ""
echo "Update your Vercel env var:"
echo "  NEXT_PUBLIC_API_URL=https://$DOMAIN"
