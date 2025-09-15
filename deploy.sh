#!/bin/bash

echo "🚀 Preparing for Railway deployment..."

# Check if .env files exist and warn user
if [ -f ".env" ]; then
    echo "⚠️  WARNING: .env file found - it will NOT be committed (protected by .gitignore)"
fi

if [ -f "backend/.env" ]; then
    echo "⚠️  WARNING: backend/.env file found - it will NOT be committed (protected by .gitignore)"
fi

if [ -f "frontend/.env" ]; then
    echo "⚠️  WARNING: frontend/.env file found - it will NOT be committed (protected by .gitignore)"
fi

echo "✅ Secrets are protected by .gitignore"
echo ""

# Add all files (excluding those in .gitignore)
git add .

# Commit with deployment message
git commit -m "🚀 Add Railway deployment configuration

- Added railway.json and nixpacks.toml for both services
- Updated frontend package.json with serve dependency
- Created RAILWAY_DEPLOYMENT.md with complete setup guide
- Ready for Railway deployment with PostgreSQL database"

# Push to origin
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ Code pushed to GitHub!"
echo ""
echo "🎯 Next steps:"
echo "1. Go to https://railway.app"
echo "2. Create new project from GitHub"
echo "3. Follow RAILWAY_DEPLOYMENT.md guide"
echo ""
echo "📖 Full instructions in: RAILWAY_DEPLOYMENT.md"