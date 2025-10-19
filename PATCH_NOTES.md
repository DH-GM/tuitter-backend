# SQLAlchemy 2.0 Compatibility and Database Model Fixes

## Issue Description

The backend API is returning 500 errors due to two main issues:

1. **String Length Errors**: UUIDs and some string fields exceed the database column size limits
   - Error message: `value too long for type character varying(32)` 
   - UUIDs are 36 characters but columns were defined without explicit length

2. **SQLAlchemy 2.0 Compatibility**: Raw SQL strings need to use `text()` function
   - Error message: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`

## Changes Required

1. **In db_models.py**:
   
   - Update all ID fields to use String(36) for UUIDs
   - Set appropriate lengths for other string columns
   - Add proper connection pool settings for cloud deployment
   - Fix database connection validation to use text()
   ```python
   def get_session():
       """Create a new database session with validation and error handling."""
       from sqlalchemy import text
       session = SessionLocal()
       try:
           # Validate that the connection is working with a simple query using text()
           session.execute(text("SELECT 1"))
           return session
       except Exception as e:
           session.close()
           print(f"Database connection error: {str(e)}")
           raise
   ```

2. **In api.py**:
   
   - Fix all SQL expressions to use text()
   - In health endpoint:
   ```python
   # Add database connection test if requested
   if db_test:
       try:
           from sqlalchemy import text
           with get_session() as db:
               # Simple query to test connection using text()
               db.execute(text("SELECT 1")).scalar()
               response["database"] = "connected"
   ```
   
   - In db_diagnostics endpoint:
   ```python
   # Get table counts using text() function
   from sqlalchemy import text
   tables = ["users", "posts", "follows", "conversations",
             "conversation_participants", "messages", "notifications"]

   for table in tables:
       try:
           count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
           diagnostics["table_counts"][table] = count
       except Exception as e:
           diagnostics["table_counts"][table] = f"Error: {str(e)}"
   ```
   
   - And for show_tables:
   ```python
   if show_tables and debug:
       try:
           from sqlalchemy import text
           with get_session() as db:
               tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).scalars().all()
               response["tables"] = list(tables)
   ```

3. **In db_repo.py**:
   
   - Add validation for string lengths in create_user function
   ```python
   def create_user(handle: str, display_name: str, bio: str = "") -> User:
       """
       Create a new user with validation to prevent database errors.
       """
       # Validate inputs
       if not handle:
           raise ValueError("Handle cannot be empty")
           
       # Ensure lengths are within database limits
       if len(handle) > 32:
           handle = handle[:32]
       if len(display_name) > 100:
           display_name = display_name[:100]
   ```

## Expected Results After Fix

1. Database connections should work properly
2. Health endpoint should return "database": "connected"  
3. All endpoints should work, including those that create users and posts
4. The notifications endpoint should work correctly

Once these changes are deployed to the Render.com server, the backend should function properly and connect successfully to the PostgreSQL database.