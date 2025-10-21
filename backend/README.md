# Social.vim Backend - Railway Deployment Guide

This guide will help you deploy the FastAPI backend and PostgreSQL database to Railway.

## Prerequisites

- A [Railway](https://railway.app) account (free tier available)
- Railway CLI installed (optional): `npm i -g @railway/cli`

## Deployment Steps

### Option 1: Deploy via Railway Dashboard (Recommended)

#### Step 1: Create a New Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy PostgreSQL" first

#### Step 2: Set Up PostgreSQL Database

1. Railway will automatically create a PostgreSQL database
2. Click on the PostgreSQL service
3. Go to "Variables" tab and note these variables:
   - `DATABASE_URL` (or `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`)
4. Keep this tab open - you'll need the database URL

#### Step 3: Initialize Database Schema

You have two options to initialize the database:

**Option A: Using Railway CLI (Recommended)**
```bash
# Install Railway CLI if you haven't
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Connect to PostgreSQL and run schema
railway run psql $DATABASE_URL -f database/schema.sql
railway run psql $DATABASE_URL -f database/seed_data.sql
```

**Option B: Using local psql**
```bash
# Copy the DATABASE_URL from Railway dashboard
# Replace YOUR_DATABASE_URL with the actual URL
psql YOUR_DATABASE_URL -f database/schema.sql
psql YOUR_DATABASE_URL -f database/seed_data.sql
```

**Option C: Using a Python script**
Create a file `init_db.py` in the backend folder and run it once:
```python
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Read and execute schema
with open('../database/schema.sql', 'r') as f:
    cur.execute(f.read())

# Read and execute seed data
with open('../database/seed_data.sql', 'r') as f:
    cur.execute(f.read())

conn.commit()
cur.close()
conn.close()
print("Database initialized!")
```

#### Step 4: Deploy FastAPI Backend

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" (or "Empty Service" if deploying manually)
3. If using GitHub:
   - Connect your GitHub account
   - Select your repository
   - Railway will auto-detect the Python app
4. Configure the service:
   - Set **Root Directory**: `backend`
   - Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Step 5: Set Environment Variables

1. Click on your FastAPI service
2. Go to "Variables" tab
3. Click "Add Reference" and select the PostgreSQL database
4. Railway will automatically add `DATABASE_URL`
5. Add any custom variables if needed:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

#### Step 6: Deploy

1. Railway will automatically deploy your service
2. Once deployed, go to "Settings" tab
3. Click "Generate Domain" to get a public URL
4. Your API will be available at: `https://your-service.railway.app`

### Option 2: Deploy via Railway CLI

```bash
# Login to Railway
railway login

# Create new project
railway init

# Add PostgreSQL
railway add

# Select PostgreSQL from the list

# Link your project
railway link

# Initialize database
railway run psql $DATABASE_URL -f database/schema.sql
railway run psql $DATABASE_URL -f database/seed_data.sql

# Deploy backend
cd backend
railway up
```

## Configuration Files

The following files are included for Railway deployment:

- `railway.json` - Railway configuration
- `Procfile` - Process configuration (alternative)
- `runtime.txt` - Python version specification

## Environment Variables

Railway automatically sets these variables:

- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Port to run the server on

## Database Connection

The `database.py` file automatically reads `DATABASE_URL` from environment variables:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/socialvim")
```

## Verifying Deployment

1. Check your service logs in Railway dashboard
2. Visit your API docs: `https://your-service.railway.app/docs`
3. Test the health endpoint: `https://your-service.railway.app/health`

## Updating Your Application

### Via GitHub (Automatic)
- Push changes to your repository
- Railway automatically redeploys

### Via Railway CLI
```bash
railway up
```

## Database Migrations

When you update the schema:

```bash
# Connect to production database
railway run psql $DATABASE_URL

# Or run migration scripts
railway run psql $DATABASE_URL -f database/migrations/001_add_new_column.sql
```

## Troubleshooting

### Issue: "Connection refused" or database errors

**Solution**: Make sure DATABASE_URL is properly set:
```bash
railway variables
```

### Issue: "Module not found"

**Solution**: Ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Issue: Build fails

**Solution**: Check the build logs and ensure:
- Python version is compatible (3.9+)
- All dependencies install successfully
- No syntax errors in code

### Issue: Database schema not initialized

**Solution**: Run the SQL scripts manually:
```bash
railway run psql $DATABASE_URL -f database/schema.sql
railway run psql $DATABASE_URL -f database/seed_data.sql
```

## Monitoring

- View logs: Railway Dashboard → Your Service → Logs
- View metrics: Railway Dashboard → Your Service → Metrics
- Database queries: Railway Dashboard → PostgreSQL → Metrics

## Costs

Railway free tier includes:
- $5 of usage per month
- 512 MB RAM per service
- Shared CPU
- 1 GB disk per database

This is sufficient for development and small projects.

## Local Development

To run locally with Railway database:

```bash
# Get the DATABASE_URL
railway variables

# Set it locally
export DATABASE_URL="your_database_url_here"

# Run the app
cd backend
uvicorn main:app --reload
```

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

If you encounter issues:
1. Check Railway status: [status.railway.app](https://status.railway.app)
2. Check service logs in Railway dashboard
3. Verify environment variables are set correctly

