# 🚂 Railway Deployment Checklist

Use this checklist to deploy your Social.vim backend to Railway step by step.

## ☁️ Railway Setup

### 1. Create Account
- [ ] Go to [railway.app](https://railway.app)
- [ ] Sign up with GitHub (free)
- [ ] Verify email

### 2. Deploy PostgreSQL
- [ ] Click "New Project"
- [ ] Select "Deploy PostgreSQL"
- [ ] Wait for provisioning (1-2 minutes)
- [ ] ✅ Database is ready!

### 3. Note Database Credentials
- [ ] Click on PostgreSQL service
- [ ] Go to "Variables" tab
- [ ] Copy `DATABASE_URL` (you'll need this)

## 🗄️ Database Initialization

### Option A: Using Railway CLI (Recommended)

- [ ] Install Railway CLI: `npm i -g @railway/cli`
- [ ] Login: `railway login`
- [ ] Link project: `railway link`
- [ ] Run init script: `railway run python backend/init_db.py`
- [ ] ✅ Database initialized!

### Option B: Using psql

- [ ] Copy DATABASE_URL from Railway
- [ ] Run: `psql YOUR_DATABASE_URL -f database/schema.sql`
- [ ] Run: `psql YOUR_DATABASE_URL -f database/seed_data.sql`
- [ ] ✅ Database initialized!

### Verify Database
- [ ] Click on PostgreSQL service
- [ ] Go to "Data" tab
- [ ] Confirm tables exist: users, posts, messages, etc.

## 🚀 Backend Deployment

### 4. Deploy FastAPI App

- [ ] In Railway project, click "New Service"
- [ ] Select "GitHub Repo"
- [ ] Connect your GitHub account
- [ ] Select your repository
- [ ] Railway detects Python app automatically

### 5. Configure Deployment

- [ ] Click on your new service
- [ ] Go to "Settings" tab
- [ ] Set **Root Directory**: `backend`
- [ ] Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Save changes

### 6. Connect Database

- [ ] Click on your backend service
- [ ] Go to "Variables" tab
- [ ] Click "New Variable" → "Add Reference"
- [ ] Select your PostgreSQL service
- [ ] Select variable: `DATABASE_URL`
- [ ] ✅ Database connected!

### 7. Deploy

- [ ] Railway automatically builds and deploys
- [ ] Check "Deployments" tab for progress
- [ ] Wait for "Success" status (2-5 minutes)

### 8. Get Your API URL

- [ ] Go to "Settings" tab
- [ ] Click "Generate Domain"
- [ ] Copy your URL: `https://your-service.railway.app`
- [ ] ✅ API is live!

## ✅ Testing

### 9. Verify Deployment

- [ ] Health check: `curl https://your-service.railway.app/health`
- [ ] Open API docs: `https://your-service.railway.app/docs`
- [ ] Test timeline: `https://your-service.railway.app/timeline?handle=yourname`

### 10. Test Core Features

- [ ] Get user profile: `/me?handle=yourname`
- [ ] Get timeline: `/timeline?handle=yourname`
- [ ] Get discover: `/discover?handle=yourname`
- [ ] Get conversations: `/conversations?handle=yourname`
- [ ] Get notifications: `/notifications?handle=yourname`

## 🎯 Update Your Client

### 11. Configure API URL

Update your client application to use the Railway URL:

```python
# In your api_interface.py or similar
api = RealAPI(base_url="https://your-service.railway.app")
```

- [ ] Update API base URL in your code
- [ ] Test connection from client
- [ ] ✅ Client connected to Railway backend!

## 📊 Monitoring

### 12. Set Up Monitoring

- [ ] Check "Metrics" tab for usage
- [ ] Enable "Deployments" notifications
- [ ] Monitor "Logs" for errors
- [ ] Set up alerts (optional)

## 🔄 Future Updates

### When You Make Changes:

**Auto-Deploy (GitHub):**
- [ ] Push to GitHub: `git push`
- [ ] Railway auto-deploys
- [ ] Check "Deployments" for status

**Manual Deploy (CLI):**
- [ ] Run: `railway up`
- [ ] Wait for deployment

### Database Migrations:

- [ ] Create migration SQL file
- [ ] Run: `railway run psql $DATABASE_URL -f migration.sql`

## 💰 Usage & Limits

### Free Tier Checklist

- [ ] Check current usage in Railway dashboard
- [ ] Monitor included: $5/month
- [ ] RAM per service: 512 MB
- [ ] Database storage: 1 GB

### Upgrade If Needed

- [ ] Hobby Plan: $5/month
- [ ] Pro Plan: $20/month
- [ ] Scale as needed

## 🐛 Troubleshooting

### If Something Goes Wrong:

**Build Failed?**
- [ ] Check "Logs" tab
- [ ] Verify requirements.txt is complete
- [ ] Check Python version in runtime.txt

**Database Connection Error?**
- [ ] Verify DATABASE_URL is set
- [ ] Check database service is running
- [ ] Verify tables exist (run init script)

**500 Errors?**
- [ ] Check application logs
- [ ] Test endpoints locally first
- [ ] Verify all dependencies installed

**Deploy Taking Forever?**
- [ ] Check Railway status: [status.railway.app](https://status.railway.app)
- [ ] Try redeploying
- [ ] Contact Railway support

## 📝 Documentation

- [ ] Save your API URL somewhere safe
- [ ] Document environment variables
- [ ] Share API docs URL with team
- [ ] Update README with production URL

## 🎉 Success Checklist

You're done when:
- ✅ PostgreSQL database is running
- ✅ Database schema initialized
- ✅ Backend service is deployed
- ✅ API docs accessible
- ✅ All endpoints working
- ✅ Client can connect
- ✅ No errors in logs

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

## Quick Reference

**Your Railway URLs:**
```
API: https://your-service.railway.app
Docs: https://your-service.railway.app/docs
Health: https://your-service.railway.app/health
```

**Important Commands:**
```bash
railway login          # Login to Railway
railway link           # Link to project
railway status         # Check deployment status
railway logs           # View logs
railway run CMD        # Run command in Railway environment
railway up             # Deploy changes
```

**Database Connection:**
```bash
# Connect to production database
railway run psql $DATABASE_URL

# Run migrations
railway run psql $DATABASE_URL -f migration.sql

# Initialize database
railway run python backend/init_db.py
```

---

**Need help?** Check `RAILWAY_QUICKSTART.md` for detailed instructions!

🎉 **Congratulations on deploying to production!** 🎉

