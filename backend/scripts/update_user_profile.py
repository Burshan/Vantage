#!/usr/bin/env python3
"""Update user profile with missing Clerk data"""

from database import DatabaseManager
from config import Config

db_manager = DatabaseManager(Config.DATABASE_URL)

print("🔧 UPDATING USER PROFILE FROM CLERK")
print("=" * 50)

# Get current user data
user = db_manager.get_user_by_id(1)
print(f"Current user data:")
print(f"  Clerk ID: {user['clerk_user_id']}")
print(f"  Email: {user.get('email', 'None')}")
print(f"  First Name: {user.get('first_name', 'None')}")
print(f"  Last Name: {user.get('last_name', 'None')}")
print()

# For now, let's manually update with reasonable defaults
# In a real scenario, you'd fetch this from Clerk API
print("🔄 Updating user profile...")

with db_manager.get_session() as session:
    from models import User
    from sqlalchemy.sql import func
    
    user_record = session.query(User).filter_by(id=1).first()
    if user_record:
        # Update with default values - you can change these
        user_record.email = "user@example.com"  # Replace with actual email
        user_record.first_name = "User"  # Replace with actual first name
        user_record.last_name = "Demo"   # Replace with actual last name
        user_record.updated_at = func.now()
        
        session.commit()
        print("✅ User profile updated successfully!")
        
        print(f"New user data:")
        print(f"  Email: {user_record.email}")
        print(f"  First Name: {user_record.first_name}")  
        print(f"  Last Name: {user_record.last_name}")
    else:
        print("❌ User not found")

print()
print("💡 To get real Clerk data, you need to:")
print("   1. Make a fresh API call to authenticate")
print("   2. Or manually update the database with your real info")