# 🚂 Railway Deployment - Quick Start Guide

Deploy your Social.vim backend to Railway in 5 minutes!

## 🎯 Quick Steps

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub (free tier: $5/month credit)

### 2. Deploy PostgreSQL Database

1. **Create New Project** → Click "Deploy PostgreSQL"
2. Railway automatically provisions a PostgreSQL database
3. **Done!** Your database is ready

### 3. Initialize Database Schema

**Option A: Using Railway CLI** (Recommended)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Initialize database
railway run python backend/init_db.py
```

**Option B: Manual SQL Execution**
```bash
# Get DATABASE_URL from Railway dashboard (PostgreSQL → Variables)
# Then run:
psql YOUR_DATABASE_URL -f database/schema.sql
psql YOUR_DATABASE_URL -f database/seed_data.sql
```

### 4. Deploy FastAPI Backend

**In your Railway project:**

1. Click **"New Service"** → **"GitHub Repo"**
2. Connect your GitHub account and select your repository
3. Configure deployment:
   - **Root Directory**: `backend`
   - **Build Command**: (auto-detected)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Database Connection**:
   - Go to service **"Variables"** tab
   - Click **"Reference"** → Select your PostgreSQL service
   - Railway automatically adds `DATABASE_URL`

5. **Generate Domain**:
   - Go to **"Settings"** → **"Generate Domain"**
   - Your API is now live! 🎉

### 5. Test Your API

```bash
# Health check
curl https://your-service.railway.app/health

# API docs
open https://your-service.railway.app/docs

# Get timeline
curl https://your-service.railway.app/timeline?handle=yourname
```

## 📁 Project Structure

```
test4/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── requirements.txt     # Python dependencies
│   ├── railway.json         # Railway configuration
│   ├── Procfile             # Process definition
│   ├── runtime.txt          # Python version
│   ├── init_db.py           # Database init script
│   └── README.md            # Full documentation
└── database/
    ├── schema.sql           # Database schema
    └── seed_data.sql        # Demo data
```

## 🔧 Configuration Files Explained

### `railway.json`
Tells Railway how to build and run your app:
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT"
  }
}
```

### `Procfile`
Alternative process definition:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### `runtime.txt`
Specifies Python version:
```
python-3.11
```

## 🔐 Environment Variables

Railway automatically sets:
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Port number for your service

No manual configuration needed! ✨

## 🚀 Deployment Methods

### Method 1: GitHub Auto-Deploy (Recommended)
- Push to GitHub → Railway auto-deploys
- Perfect for continuous deployment

### Method 2: Railway CLI
```bash
cd backend
railway up
```

### Method 3: Railway Dashboard
- Upload files directly
- Good for testing

## 📊 Monitoring

**View Logs:**
```bash
railway logs
```

**Or in dashboard:**
- Railway Dashboard → Your Service → Logs

**Check Metrics:**
- Railway Dashboard → Your Service → Metrics
- CPU, Memory, Network usage

## 🐛 Common Issues & Solutions

### ❌ "Connection refused"
**Fix:** Link database to backend service
```bash
# In backend service variables, add reference to PostgreSQL
```

### ❌ "Module not found"
**Fix:** Ensure all dependencies in requirements.txt
```bash
pip freeze > requirements.txt
git commit -am "Update dependencies"
git push
```

### ❌ "Port already in use"
**Fix:** Railway automatically sets $PORT, use it:
```python
# In main.py
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

### ❌ "Database tables don't exist"
**Fix:** Run initialization script
```bash
railway run python backend/init_db.py
```

## 💰 Pricing

**Free Tier:**
- $5 usage credit/month
- 512 MB RAM per service
- Shared CPU
- 1 GB database storage

**Enough for:**
- Development
- Small projects
- Testing
- Demos

## 🎓 Next Steps

1. ✅ Deploy to Railway
2. 📱 Update your TUI app to use Railway API URL
3. 🔐 Add authentication (optional)
4. 🌍 Share your app!

## 📚 Full Documentation

See `backend/README.md` for comprehensive documentation including:
- Detailed deployment options
- Database migrations
- Troubleshooting guide
- Production best practices

## 🆘 Need Help?

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [FastAPI Docs](https://fastapi.tiangolo.com)

---

**Ready to deploy?** Start with step 1! 🚀

