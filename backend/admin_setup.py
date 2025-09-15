#!/usr/bin/env python3
"""
Admin Setup Script - Add admin role to users
Professional RBAC implementation for Vantage platform
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import User, Base
from database import DatabaseManager
from config import Config

def add_admin_columns():
    """Add admin role columns to existing users table"""
    try:
        # Use database URL from config
        database_url = Config.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if columns exist before adding them
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('role', 'is_admin')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'role' not in existing_columns:
                print("Adding 'role' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user' NOT NULL"))
                conn.commit()
                print("✅ Added 'role' column")
            else:
                print("✅ 'role' column already exists")
                
            if 'is_admin' not in existing_columns:
                print("Adding 'is_admin' column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL"))
                conn.commit()
                print("✅ Added 'is_admin' column")
            else:
                print("✅ 'is_admin' column already exists")
                
        print("Database schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False

def promote_user_to_admin(email: str, role: str = 'admin'):
    """Promote a user to admin role by email"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return False
                
            user.role = role
            user.is_admin = True
            session.commit()
            
            print(f"✅ Successfully promoted {email} to {role}")
            print(f"   User ID: {user.id}")
            print(f"   Name: {user.first_name} {user.last_name}")
            print(f"   Role: {user.role}")
            print(f"   Is Admin: {user.is_admin}")
            return True
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        return False

def promote_user_by_id(user_id: int, role: str = 'admin'):
    """Promote a user to admin role by user ID"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"❌ User with ID '{user_id}' not found")
                return False
                
            user.role = role
            user.is_admin = True
            session.commit()
            
            print(f"✅ Successfully promoted User ID {user_id} to {role}")
            print(f"   Email: {user.email or 'Not set'}")
            print(f"   Name: {user.first_name or 'Unknown'} {user.last_name or ''}")
            print(f"   Clerk ID: {user.clerk_user_id}")
            print(f"   Role: {user.role}")
            print(f"   Is Admin: {user.is_admin}")
            return True
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        return False

def update_user_info(user_id: int, email: str = None, first_name: str = None, last_name: str = None):
    """Update user information manually"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"❌ User with ID '{user_id}' not found")
                return False
                
            if email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
                
            session.commit()
            
            print(f"✅ Successfully updated User ID {user_id}")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.first_name} {user.last_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return False

def list_admin_users():
    """List all admin users"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            admin_users = session.query(User).filter(User.is_admin == True).all()
            
            if not admin_users:
                print("No admin users found")
                return
                
            print(f"\n📋 Admin Users ({len(admin_users)}):")
            print("-" * 80)
            for user in admin_users:
                print(f"  • {user.email} ({user.first_name} {user.last_name})")
                print(f"    Role: {user.role} | ID: {user.id} | Tokens: {user.tokens_remaining}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing admin users: {e}")

def list_all_users():
    """List all users to help debug"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            all_users = session.query(User).all()
            
            if not all_users:
                print("No users found in database")
                return
                
            print(f"\n👥 All Users ({len(all_users)}):")
            print("-" * 80)
            for user in all_users:
                admin_status = "✅ ADMIN" if getattr(user, 'is_admin', False) else "👤 USER"
                role = getattr(user, 'role', 'user')
                print(f"  • {user.email} ({user.first_name} {user.last_name}) [{admin_status}]")
                print(f"    Role: {role} | ID: {user.id} | Clerk ID: {user.clerk_user_id}")
                print(f"    Tokens: {user.tokens_remaining} | Created: {user.created_at}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def search_user(search_term: str):
    """Search for users by email or name"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            users = session.query(User).filter(
                (User.email.ilike(f'%{search_term}%')) |
                (User.first_name.ilike(f'%{search_term}%')) |
                (User.last_name.ilike(f'%{search_term}%'))
            ).all()
            
            if not users:
                print(f"No users found matching '{search_term}'")
                return
                
            print(f"\n🔍 Search Results for '{search_term}' ({len(users)}):")
            print("-" * 80)
            for user in users:
                admin_status = "✅ ADMIN" if getattr(user, 'is_admin', False) else "👤 USER"
                role = getattr(user, 'role', 'user')
                print(f"  • {user.email} ({user.first_name} {user.last_name}) [{admin_status}]")
                print(f"    Role: {role} | ID: {user.id}")
                print()
                
    except Exception as e:
        print(f"❌ Error searching users: {e}")

def revoke_admin(email: str):
    """Revoke admin privileges from a user"""
    try:
        db_manager = DatabaseManager(Config.DATABASE_URL)
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return False
                
            user.role = 'user'
            user.is_admin = False
            session.commit()
            
            print(f"✅ Successfully revoked admin privileges from {email}")
            return True
            
    except Exception as e:
        print(f"❌ Error revoking admin: {e}")
        return False

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("""
🛡️  Vantage Admin Management Tool

Usage:
  python admin_setup.py setup                      - Add admin columns to database
  python admin_setup.py promote <email> [role]     - Promote user to admin (default: admin)
  python admin_setup.py promote-id <user_id> [role] - Promote user by ID (for empty emails)
  python admin_setup.py update-user <id> <email> <first> [last] - Update user info
  python admin_setup.py list                       - List all admin users  
  python admin_setup.py users                      - List ALL users (debug)
  python admin_setup.py search <term>              - Search users by email/name
  python admin_setup.py revoke <email>             - Revoke admin privileges
  python admin_setup.py quick-setup <email>        - Setup database + promote user

Examples:
  python admin_setup.py setup
  python admin_setup.py users                      - See all users first
  python admin_setup.py promote-id 2 admin         - Promote User ID 2 to admin
  python admin_setup.py update-user 2 omer.burshan1@gmail.com Omer Burshan
        """)
        return
        
    command = sys.argv[1]
    
    if command == 'setup':
        add_admin_columns()
        
    elif command == 'promote':
        if len(sys.argv) < 3:
            print("❌ Email required. Usage: python admin_setup.py promote <email> [role]")
            return
        email = sys.argv[2]
        role = sys.argv[3] if len(sys.argv) > 3 else 'admin'
        
        if role not in ['admin', 'super_admin']:
            print("❌ Invalid role. Use 'admin' or 'super_admin'")
            return
            
        promote_user_to_admin(email, role)
        
    elif command == 'promote-id':
        if len(sys.argv) < 3:
            print("❌ User ID required. Usage: python admin_setup.py promote-id <user_id> [role]")
            return
        try:
            user_id = int(sys.argv[2])
        except ValueError:
            print("❌ User ID must be a number")
            return
        role = sys.argv[3] if len(sys.argv) > 3 else 'admin'
        
        if role not in ['admin', 'super_admin']:
            print("❌ Invalid role. Use 'admin' or 'super_admin'")
            return
            
        promote_user_by_id(user_id, role)
        
    elif command == 'update-user':
        if len(sys.argv) < 5:
            print("❌ Usage: python admin_setup.py update-user <user_id> <email> <first_name> [last_name]")
            return
        try:
            user_id = int(sys.argv[2])
        except ValueError:
            print("❌ User ID must be a number")
            return
        email = sys.argv[3]
        first_name = sys.argv[4]
        last_name = sys.argv[5] if len(sys.argv) > 5 else None
        
        update_user_info(user_id, email, first_name, last_name)
        
    elif command == 'list':
        list_admin_users()
        
    elif command == 'users':
        list_all_users()
        
    elif command == 'search':
        if len(sys.argv) < 3:
            print("❌ Search term required. Usage: python admin_setup.py search <term>")
            return
        search_term = sys.argv[2]
        search_user(search_term)
        
    elif command == 'revoke':
        if len(sys.argv) < 3:
            print("❌ Email required. Usage: python admin_setup.py revoke <email>")
            return
        email = sys.argv[2]
        revoke_admin(email)
        
    elif command == 'quick-setup':
        if len(sys.argv) < 3:
            print("❌ Email required. Usage: python admin_setup.py quick-setup <email>")
            return
        email = sys.argv[2]
        
        print("🚀 Running quick setup...")
        if add_admin_columns():
            promote_user_to_admin(email, 'admin')
            print("\n🎉 Quick setup completed!")
        
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()