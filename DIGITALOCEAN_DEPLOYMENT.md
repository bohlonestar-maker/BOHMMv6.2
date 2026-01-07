# DigitalOcean App Platform Deployment Guide

## Prerequisites
- GitHub repository with your code
- DigitalOcean account
- MongoDB running on your Droplet (104.248.71.87)

## Step 1: Connect GitHub to DigitalOcean

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click **"Create App"**
3. Select **"GitHub"** as source
4. Authorize DigitalOcean to access your GitHub
5. Select your repository and branch (usually `main`)

## Step 2: Configure the App

### Backend Service
- **Source Directory**: `/backend`
- **Type**: Web Service
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: 8001
- **Routes**: `/api`, `/health`

### Frontend Service  
- **Source Directory**: `/frontend`
- **Type**: Web Service
- **Dockerfile Path**: `frontend/Dockerfile`
- **HTTP Port**: 80
- **Routes**: `/`

## Step 3: Environment Variables

### Backend Environment Variables

| Variable | Value | Type |
|----------|-------|------|
| MONGO_URL | `mongodb://bohAdmin:BOH2158SecurePass!@104.248.71.87:27017/test_database?authSource=admin` | Secret |
| DB_NAME | `test_database` | Plain |
| JWT_SECRET | (generate a random string) | Secret |
| CORS_ORIGINS | `https://bohhub.com,https://www.bohhub.com` | Plain |
| SMTP_HOST | `smtp.zoho.com` | Plain |
| SMTP_PORT | `465` | Plain |
| SMTP_EMAIL | `support@boh2158.org` | Secret |
| SMTP_PASSWORD | (your Zoho app password) | Secret |
| SQUARE_ACCESS_TOKEN | (your Square token) | Secret |
| SQUARE_ENVIRONMENT | `production` | Plain |
| DISCORD_BOT_TOKEN | (your Discord bot token) | Secret |

### Frontend Environment Variables

| Variable | Value |
|----------|-------|
| REACT_APP_BACKEND_URL | `https://bohhub.com` |

## Step 4: Configure Domain

1. In App Settings, go to **Domains**
2. Add `bohhub.com` as primary domain
3. Add `www.bohhub.com` as alias
4. Update Cloudflare DNS:
   - Remove old A/CNAME records for bohhub.com
   - Add CNAME record pointing to your App Platform URL

## Step 5: MongoDB Firewall

Make sure your MongoDB Droplet (104.248.71.87) allows connections from DigitalOcean App Platform:

```bash
# SSH into your MongoDB droplet
ssh root@104.248.71.87

# Allow connections from DigitalOcean App Platform IP ranges
# Or temporarily allow all (less secure):
ufw allow 27017/tcp
```

## Step 6: Deploy

1. Click **"Create Resources"**
2. Wait for build and deployment (5-10 minutes)
3. Test your app at the provided URL
4. Once working, update Cloudflare DNS

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `systemctl status mongod`
- Check firewall allows App Platform IPs
- Verify credentials are correct

### Build Failures
- Check build logs in DigitalOcean dashboard
- Ensure all dependencies are in requirements.txt / package.json

### Frontend Can't Reach Backend
- Verify REACT_APP_BACKEND_URL is set correctly
- Check CORS_ORIGINS includes your domain

## Estimated Costs

- Backend (basic-xxs): ~$5/month
- Frontend (basic-xxs): ~$5/month
- **Total**: ~$10-12/month

## Benefits Over Emergent Deployment

✅ No cold starts - always running
✅ Faster response times
✅ Full control over scaling
✅ Direct GitHub integration
