# Social.vim - Terminal Social Network 🚀

A beautiful terminal-based social network with FastAPI backend and PostgreSQL database.

## 📁 Project Structure

```
test4/
├── backend/              # FastAPI backend server
│   ├── main.py          # API routes and FastAPI app
│   ├── database.py      # Database configuration
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database CRUD operations
│   ├── requirements.txt # Python dependencies
│   ├── railway.json     # Railway deployment config
│   ├── Procfile         # Process definition
│   ├── runtime.txt      # Python version
│   ├── init_db.py       # Database initialization script
│   └── README.md        # Backend documentation
│
├── database/            # Database schema and seed data
│   ├── schema.sql       # PostgreSQL database schema
│   └── seed_data.sql    # Demo data for development
│
├── RAILWAY_QUICKSTART.md  # Quick Railway deployment guide
├── LOCAL_SETUP.md         # Local development setup
└── README.md              # This file
```

## 🚀 Quick Start

### Option 1: Deploy to Railway (5 minutes)

Perfect for production deployment:

1. **Read the quick start guide**: [`RAILWAY_QUICKSTART.md`](RAILWAY_QUICKSTART.md)
2. **Create Railway account** at [railway.app](https://railway.app)
3. **Deploy PostgreSQL** with one click
4. **Deploy FastAPI backend** from GitHub
5. **Done!** Your API is live 🎉

### Option 2: Run Locally

Perfect for development:

1. **Read the setup guide**: [`LOCAL_SETUP.md`](LOCAL_SETUP.md)
2. **Install PostgreSQL** on your machine
3. **Create database** and run schema
4. **Start the server**: `uvicorn main:app --reload`
5. **Test at**: http://localhost:8000/docs

## 🌟 Features

### Backend API

- ✅ **User Management**: Profiles, settings, ASCII avatars
- ✅ **Posts**: Create, like, repost, comment
- ✅ **Timeline**: Personalized feed of posts
- ✅ **Discover**: Trending posts and users
- ✅ **Messages**: Direct messaging between users
- ✅ **Notifications**: Mentions, likes, reposts, follows
- ✅ **Comments**: Threaded discussions on posts

### Database

- PostgreSQL with proper indexes
- Relationships with foreign keys
- Seed data for demo/development
- Migration-ready schema

### Deployment

- Railway.app ready
- Docker compatible
- Environment-based configuration
- Auto-scaling support

## 📖 API Endpoints

### Users
- `GET /me` - Get current user profile
- `GET /settings` - Get user settings
- `PUT /settings` - Update user settings

### Posts
- `GET /timeline` - Get timeline feed
- `GET /discover` - Get trending posts
- `POST /posts` - Create a new post
- `POST /posts/{id}/like` - Toggle like
- `POST /posts/{id}/repost` - Toggle repost
- `GET /posts/{id}/comments` - Get comments
- `POST /posts/{id}/comments` - Add comment

### Messages
- `GET /conversations` - Get all conversations
- `GET /conversations/{id}/messages` - Get messages
- `POST /conversations/{id}/messages` - Send message
- `POST /dm` - Get or create DM conversation

### Notifications
- `GET /notifications` - Get notifications
- `POST /notifications/{id}/read` - Mark as read

### Other
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🔧 Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - SQL ORM
- Pydantic - Data validation
- uvicorn - ASGI server

**Database:**
- PostgreSQL 14+
- psycopg2 - PostgreSQL adapter

**Deployment:**
- Railway.app - Platform as a Service
- Docker - Containerization (optional)

## 📚 Documentation

- [`backend/README.md`](backend/README.md) - Full backend documentation
- [`RAILWAY_QUICKSTART.md`](RAILWAY_QUICKSTART.md) - Deploy to Railway in 5 minutes
- [`LOCAL_SETUP.md`](LOCAL_SETUP.md) - Local development setup

## 🛠️ Development

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- pip or pipenv

### Local Setup

```bash
# Clone repository
cd test4

# Install dependencies
cd backend
pip install -r requirements.txt

# Setup database
createdb socialvim
psql socialvim -f ../database/schema.sql
psql socialvim -f ../database/seed_data.sql

# Run server
uvicorn main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

### Database Schema

The database includes these tables:
- `users` - User profiles and stats
- `user_settings` - User preferences and OAuth connections
- `posts` - Social media posts
- `post_interactions` - Likes and reposts
- `comments` - Post comments
- `conversations` - DM conversations
- `messages` - Direct messages
- `notifications` - User notifications

## 🚢 Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

See [`RAILWAY_QUICKSTART.md`](RAILWAY_QUICKSTART.md) for detailed steps.

### Docker (Alternative)

```dockerfile
# Create Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t socialvim-backend .
docker run -p 8000:8000 -e DATABASE_URL=your_db_url socialvim-backend
```

## 🧪 Testing

### Interactive Testing
Visit http://localhost:8000/docs or your deployed URL + `/docs`

### curl Examples

```bash
# Health check
curl http://localhost:8000/health

# Get timeline
curl "http://localhost:8000/timeline?handle=yourname"

# Create post
curl -X POST "http://localhost:8000/posts?handle=yourname" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world!"}'

# Like a post
curl -X POST "http://localhost:8000/posts/1/like?handle=yourname"
```

## 🔐 Security Notes

This is a **demo application** without authentication for simplicity. For production:

- Add JWT authentication
- Implement rate limiting
- Use HTTPS only
- Validate all inputs
- Add CORS restrictions
- Use environment variables for secrets

## 🤝 Contributing

This is a demo project, but feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Use as a learning resource

## 📄 License

Open source - use however you like!

## 🆘 Support

- **Backend Issues**: See `backend/README.md`
- **Railway Deployment**: See `RAILWAY_QUICKSTART.md`
- **Local Setup**: See `LOCAL_SETUP.md`
- **Database**: Check `database/schema.sql`

## 🎯 Next Steps

1. ✅ **Deploy to Railway** - Get your backend live in 5 minutes
2. 🎨 **Customize the API** - Add features in `backend/main.py`
3. 📱 **Build a client** - Connect your TUI, web, or mobile app
4. 🔐 **Add authentication** - Implement JWT or OAuth
5. 🚀 **Scale up** - Add caching, CDN, load balancing

---

**Made with ❤️ for terminal enthusiasts and vim lovers**

Ready to deploy? Start with [`RAILWAY_QUICKSTART.md`](RAILWAY_QUICKSTART.md)! 🚂

