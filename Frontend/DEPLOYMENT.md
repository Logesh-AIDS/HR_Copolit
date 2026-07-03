# TalentOS Stage 19 - Deployment Guide

## Quick Start

### Local Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Open http://localhost:3000
```

The app runs on port 3000 with hot reload enabled.

## Production Deployment

### Option 1: Vercel (Recommended)

#### Prerequisites
- GitHub account with repository
- Vercel account (free tier available)

#### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Stage 19: Complete frontend implementation"
   git push origin main
   ```

2. **Connect to Vercel**
   - Visit https://vercel.com/new
   - Import your repository
   - Framework: Next.js
   - Root Directory: ./
   - Build Command: `pnpm build`
   - Install Command: `pnpm install`

3. **Set Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Your app will be live at `your-project.vercel.app`

#### Custom Domain
- Go to Vercel Dashboard → Settings → Domains
- Add your custom domain
- Update DNS records as instructed

### Option 2: Docker

#### Dockerfile
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# Runtime stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["pnpm", "start"]
```

#### Build & Run
```bash
docker build -t talento-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com talento-frontend
```

### Option 3: Traditional Server (Node)

#### Prerequisites
- Node.js 18+ installed
- pnpm installed
- PM2 or similar process manager

#### Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/talento-frontend.git
cd talento-frontend

# Install dependencies
pnpm install

# Build for production
pnpm build

# Start with PM2
pm2 start pnpm --name "talento-frontend" -- start

# Make persistent
pm2 startup
pm2 save
```

#### Nginx Reverse Proxy
```nginx
upstream talento {
    server 127.0.0.1:3000;
}

server {
    listen 443 ssl http2;
    server_name app.talento.com;

    ssl_certificate /etc/letsencrypt/live/talento.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/talento.com/privkey.pem;

    location / {
        proxy_pass http://talento;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location /_next/static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /public {
        expires 30d;
        add_header Cache-Control "public";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name app.talento.com;
    return 301 https://$server_name$request_uri;
}
```

## Environment Configuration

### Development (.env.development.local)
```
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

### Production (.env.production.local)
```
NEXT_PUBLIC_API_URL=https://api.talento.com
```

### Available Variables
```
# API Configuration
NEXT_PUBLIC_API_URL          # Backend API base URL (required)

# Optional: Analytics & Monitoring
NEXT_PUBLIC_GA_ID            # Google Analytics ID
NEXT_PUBLIC_SENTRY_DSN       # Sentry error tracking

# Optional: Feature Flags
NEXT_PUBLIC_ENABLE_BETA      # Enable beta features
NEXT_PUBLIC_MAINTENANCE_MODE # Maintenance mode toggle
```

## Pre-Deployment Checklist

### Code Quality
- [ ] `pnpm run lint` passes
- [ ] No TypeScript errors: `pnpm run type-check`
- [ ] All dependencies up to date
- [ ] No console warnings in production build

### Testing
- [ ] Run through all main user flows manually
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)
- [ ] Test on mobile devices
- [ ] Verify all API endpoints respond

### Security
- [ ] Environment variables are secret
- [ ] HTTPS certificate is valid
- [ ] CORS configured correctly
- [ ] Input validation working
- [ ] XSS protections in place

### Performance
- [ ] Page load time < 3 seconds
- [ ] Core Web Vitals:
  - LCP < 2.5s
  - FID < 100ms
  - CLS < 0.1
- [ ] Bundle size reasonable (~150KB gzipped)

### Analytics & Monitoring
- [ ] Error tracking configured (Sentry)
- [ ] Analytics configured (Vercel Analytics)
- [ ] Log aggregation setup
- [ ] Performance monitoring active

### Database & APIs
- [ ] All backend API endpoints functional
- [ ] Database migrations complete
- [ ] WebSocket server running (if needed)
- [ ] Redis/cache configured (if needed)

## Monitoring & Logging

### Vercel Deployment Analytics
- **Dashboard**: https://vercel.com/dashboard
- **Analytics**: Built-in with Vercel
- **Logs**: Vercel → Project → Deployments → Logs

### Self-Hosted Monitoring

#### Error Tracking (Sentry)
```typescript
// In app/layout.tsx
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

#### Performance Monitoring
```bash
# Install package
pnpm add web-vitals

# Track in app
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

## Scaling Strategy

### For 1,000 Concurrent Users
- Single Vercel deployment
- Standard Next.js caching
- CDN for static assets (automatic with Vercel)

### For 10,000 Concurrent Users
- Load balancer (Vercel automatic)
- Redis for session storage
- Optimized API caching
- CDN edge caching

### For 100,000+ Concurrent Users
- Multi-region deployment
- Separate API server cluster
- WebSocket server farm
- Database read replicas
- Full CDN strategy

## Rollback Procedure

### Vercel
```
1. Go to Vercel Dashboard
2. Project → Deployments
3. Click on previous stable version
4. Click "Redeploy"
```

### Docker
```bash
# Save current image
docker tag talento-frontend:latest talento-frontend:backup

# Rollback to previous
docker run -p 3000:3000 talento-frontend:previous
```

### Manual Server
```bash
# Stash current changes
git stash

# Checkout previous commit
git checkout <previous-commit-hash>

# Rebuild and restart
pnpm build
pm2 restart talento-frontend
```

## Maintenance

### Weekly Tasks
- [ ] Review error logs
- [ ] Monitor performance metrics
- [ ] Check for dependency updates

### Monthly Tasks
- [ ] Update npm dependencies: `pnpm update`
- [ ] Run security audit: `pnpm audit`
- [ ] Review API usage & costs
- [ ] Backup configuration

### Quarterly Tasks
- [ ] Major dependency updates
- [ ] Performance optimization review
- [ ] Security audit & penetration testing
- [ ] Update documentation

## Troubleshooting

### Build Failures

```bash
# Clear cache
rm -rf .next
rm -rf node_modules
pnpm install
pnpm build

# Check for TypeScript errors
pnpm run type-check

# Check Node version
node --version  # Should be 18+
```

### Runtime Errors

```bash
# Check logs
pm2 logs talento-frontend

# Restart service
pm2 restart talento-frontend

# Clear session/cache
redis-cli FLUSHALL  # If using Redis
```

### API Connection Issues

```bash
# Verify API URL
echo $NEXT_PUBLIC_API_URL

# Test connectivity
curl -X GET https://api.talento.com/auth/me

# Check CORS headers
curl -I -X OPTIONS https://api.talento.com
```

## Performance Optimization

### Image Optimization
```typescript
import Image from 'next/image';

export function OptimizedImage() {
  return (
    <Image
      src="/image.jpg"
      alt="Description"
      width={1920}
      height={1080}
      priority  // For LCP images
    />
  );
}
```

### Code Splitting
```typescript
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => <p>Loading editor...</p>,
});
```

### Caching Strategy
```typescript
// Cache production builds
export const revalidate = 3600; // 1 hour
```

## Support & Escalation

### Deployment Issues
1. Check Vercel/server logs
2. Verify environment variables
3. Test API connectivity
4. Review recent code changes

### Performance Issues
1. Profile with DevTools
2. Check Core Web Vitals
3. Optimize critical paths
4. Review database queries

### Security Issues
1. Update dependencies immediately
2. Review access logs
3. Notify users if needed
4. Implement hotfix

## Contact & Resources

**Deployment Support**: deployment@talento.com  
**Incident Response**: incidents@talento.com  
**Documentation**: https://docs.talento.com  

## Post-Deployment Tasks

1. **Smoke Testing**
   - Login/signup flow
   - Dashboard load
   - Interview room initialization
   - API connectivity

2. **Analytics Verification**
   - User sessions tracked
   - Page views recorded
   - Error tracking active
   - Performance metrics visible

3. **Communication**
   - Notify stakeholders of deployment
   - Update status page if applicable
   - Document any issues encountered

4. **Documentation**
   - Update deployment notes
   - Record configuration changes
   - Document any custom modifications

---

**Last Updated**: 2024-07-03  
**Version**: 1.0.0  
**Status**: Ready for Production Deployment
