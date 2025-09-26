# ReguChain Watch - Deployment Guide

## Deployment Options

1. **Render** (Backend) + **Vercel** (Frontend) - Recommended
2. **Docker** (Self-hosted)
3. **Railway** (Full-stack)
4. **AWS/GCP/Azure** (Enterprise)

## 🚀 Option 1: Render + Vercel (Recommended)

### Backend Deployment (Render)

1. **Prepare GitHub Repository:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/reguchain-watch.git
git push -u origin main
```

2. **Deploy to Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Name**: `reguchain-watch-api`
     - **Root Directory**: `backend`
     - **Environment**: `Docker`
     - **Build Command**: (auto-detected from Dockerfile)
     - **Start Command**: (auto-detected from Dockerfile)

3. **Set Environment Variables in Render:**
```env
GOOGLE_API_KEY=AIzaSyB92bGbdLvhhw9ykm5mEJlmNzpEjXZuHxc
NEWSAPI_KEY=pub_95bfb272640345c19abd536a1ab7c96f
DATABASE_URL=sqlite:///app/data/reguchain.db
FAISS_INDEX_PATH=/app/faiss_index/index
```

4. **Add Persistent Disk:**
   - Go to service settings
   - Add disk: `/app/data` (1GB)

### Frontend Deployment (Vercel)

1. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Import GitHub repository
   - Configure:
     - **Framework Preset**: Next.js
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build`
     - **Output Directory**: `.next`

2. **Set Environment Variables in Vercel:**
```env
NEXT_PUBLIC_API_URL=https://reguchain-watch-api.onrender.com
```

3. **Configure Domain (Optional):**
   - Add custom domain in Vercel settings
   - Update CORS in backend if needed

## 🐳 Option 2: Docker Deployment

### Single Server Deployment

1. **Clone repository on server:**
```bash
git clone https://github.com/yourusername/reguchain-watch.git
cd reguchain-watch
```

2. **Configure environment:**
```bash
cp .env.production .env
# Edit .env with your production values
nano .env
```

3. **Build and run:**
```bash
docker-compose up -d --build
```

4. **Setup reverse proxy (nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **Setup SSL with Let's Encrypt:**
```bash
sudo certbot --nginx -d your-domain.com
```

### Docker Swarm Deployment

```yaml
# docker-stack.yml
version: '3.8'

services:
  backend:
    image: reguchain-backend:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    networks:
      - reguchain-net

  frontend:
    image: reguchain-frontend:latest
    deploy:
      replicas: 2
    networks:
      - reguchain-net

networks:
  reguchain-net:
    driver: overlay
```

Deploy:
```bash
docker stack deploy -c docker-stack.yml reguchain
```

## 🚂 Option 3: Railway Deployment

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Deploy:**
```bash
railway login
railway init
railway up
```

3. **Configure in Railway Dashboard:**
   - Add environment variables
   - Set up custom domain
   - Configure health checks

## ☁️ Option 4: Cloud Platforms

### AWS Deployment

1. **Using AWS App Runner:**
```bash
# Install AWS CLI
aws configure

# Create App Runner service
aws apprunner create-service \
  --service-name "reguchain-watch" \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/yourusername/reguchain-watch",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      }
    }
  }'
```

2. **Using ECS Fargate:**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker build -t reguchain-backend ./backend
docker tag reguchain-backend:latest $ECR_URI/reguchain-backend:latest
docker push $ECR_URI/reguchain-backend:latest

# Deploy with ECS
aws ecs create-service \
  --cluster default \
  --service-name reguchain \
  --task-definition reguchain-task \
  --desired-count 2
```

### Google Cloud Platform

```bash
# Deploy to Cloud Run
gcloud run deploy reguchain-backend \
  --source ./backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group reguchain-rg \
  --name reguchain-backend \
  --image reguchain-backend:latest \
  --dns-name-label reguchain \
  --ports 8000
```

## 📊 Production Checklist

### Security
- [ ] Use HTTPS everywhere
- [ ] Set secure CORS origins
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerting

### Performance
- [ ] Enable caching (Redis/Memcached)
- [ ] Use CDN for static assets
- [ ] Optimize Docker images
- [ ] Set up horizontal scaling

### Monitoring
- [ ] Application logs (Datadog/New Relic)
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring (UptimeRobot)
- [ ] Performance metrics (Prometheus/Grafana)

### Backup
- [ ] Database backups
- [ ] FAISS index backups
- [ ] Configuration backups

## 🔧 Environment Variables

### Required for Production
```env
# API Keys
GOOGLE_API_KEY=your_production_key
NEWSAPI_KEY=your_production_key

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Storage
FAISS_INDEX_PATH=/persistent/storage/path

# Security
CORS_ORIGINS=https://your-frontend-domain.com
API_KEY_HEADER=X-API-Key
RATE_LIMIT=100
```

### Optional Enhancements
```env
# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key

# Caching
REDIS_URL=redis://localhost:6379

# Advanced
ENABLE_METRICS=true
LOG_LEVEL=info
WORKER_COUNT=4
```

## 🚨 Troubleshooting

### Render Issues
```bash
# Check logs
render logs --tail

# Restart service
render restart
```

### Vercel Issues
```bash
# Check build logs
vercel logs

# Redeploy
vercel --prod
```

### Docker Issues
```bash
# Check container logs
docker-compose logs -f backend

# Restart containers
docker-compose restart

# Clean rebuild
docker-compose down -v
docker-compose up --build
```

## 📈 Scaling Strategies

### Horizontal Scaling
- Add more container replicas
- Use load balancer (nginx/HAProxy)
- Implement session affinity if needed

### Vertical Scaling
- Increase container resources
- Optimize memory usage
- Use connection pooling

### Database Scaling
- Switch from SQLite to PostgreSQL
- Implement read replicas
- Use connection pooling

### Vector Store Scaling
- Distribute FAISS index shards
- Use approximate algorithms
- Implement caching layer

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Docker Documentation](https://docs.docker.com)
- [Railway Documentation](https://docs.railway.app)

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test API endpoints
4. Review error messages

---

**Production Ready!** Your ReguChain Watch instance is now deployed! 🎉
