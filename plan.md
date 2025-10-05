# Migration Plan for Note Taking App

## Step 1: Setup Supabase Integration

1. Create a new Supabase project at https://supabase.com
2. Set up the database schema using the schema.sql file
3. Create .env file with Supabase credentials
4. Add python-dotenv and supabase packages to requirements.txt

## Step 2: Database Migration

1. Create a new supabase_client.py for database connection
2. Update Note model to work with Supabase
3. Remove SQLAlchemy dependencies
4. Create migration script to move data from SQLite to Supabase (if needed)

## Step 3: Update API Routes

1. Refactor note routes to use Supabase client
2. Update CRUD operations to use Supabase methods
3. Update search functionality to use Supabase text search
4. Remove SQLAlchemy session management

## Step 4: Vercel Deployment Setup

1. Create vercel.json configuration file
2. Update main.py for serverless deployment
3. Configure environment variables in Vercel
4. Test deployment locally using vercel dev

## Step 5: Testing and Validation

1. Test all API endpoints with new Supabase backend
2. Verify data persistence
3. Test search functionality
4. Validate environment variable configuration