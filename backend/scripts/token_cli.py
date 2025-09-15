#!/usr/bin/env python3
"""Interactive Token Management CLI"""
import sys
import os
import argparse
from typing import Optional
from database import DatabaseManager
from config import Config
from models import User

class TokenCLI:
    def __init__(self):
        self.db_manager = DatabaseManager(Config.DATABASE_URL)
    
    def find_user(self, identifier: str) -> Optional[dict]:
        """Find user by ID or email"""
        # Try as user ID first
        if identifier.isdigit():
            user = self.db_manager.get_user_by_id(int(identifier))
            if user:
                return user
        
        # Try as email
        user = self.db_manager.get_user_by_email(identifier)
        return user
    
    def add_tokens_interactive(self):
        """Interactive token addition"""
        print("\n🎯 Add Tokens to User")
        print("=" * 30)
        
        # Get user
        while True:
            identifier = input("Enter User ID or Email: ").strip()
            if not identifier:
                print("❌ Please enter a valid identifier")
                continue
                
            user = self.find_user(identifier)
            if user:
                print(f"✅ Found user: {user['email']} (ID: {user['id']})")
                print(f"   Current tokens: {user['tokens_remaining']}")
                break
            else:
                print(f"❌ User '{identifier}' not found")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return
        
        # Get token amount
        while True:
            try:
                amount = int(input("Enter token amount to add: "))
                if amount <= 0:
                    print("❌ Amount must be positive")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Get admin note
        note = input("Admin note (optional): ").strip() or f"CLI: Added {amount} tokens"
        
        # Confirm
        print(f"\n📋 Summary:")
        print(f"   User: {user['email']} (ID: {user['id']})")
        print(f"   Current tokens: {user['tokens_remaining']}")
        print(f"   Adding: {amount} tokens")
        print(f"   New balance: {user['tokens_remaining'] + amount}")
        print(f"   Note: {note}")
        
        confirm = input("\nProceed? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
        
        # Execute
        result = self.db_manager.add_tokens_to_user(
            user_id=user['id'],
            amount=amount,
            transaction_type='admin_grant',
            admin_note=note
        )
        
        if result['success']:
            print(f"✅ Success! Added {amount} tokens")
            print(f"   Transaction ID: {result['transaction_id']}")
            print(f"   New balance: {result['balance_after']}")
        else:
            print(f"❌ Error: {result['message']}")
    
    def view_user_interactive(self):
        """Interactive user viewing"""
        print("\n👤 View User Info")
        print("=" * 20)
        
        identifier = input("Enter User ID or Email: ").strip()
        if not identifier:
            print("❌ Please enter a valid identifier")
            return
            
        user = self.find_user(identifier)
        if not user:
            print(f"❌ User '{identifier}' not found")
            return
        
        print(f"\n📊 User Details:")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user.get('first_name', '')} {user.get('last_name', '')}")
        print(f"   Tokens Remaining: {user['tokens_remaining']}")
        print(f"   Total Tokens Used: {user['total_tokens_used']}")
        print(f"   Created: {user['created_at']}")
        
        # Show recent transactions
        show_tx = input("\nShow recent transactions? (y/n): ").lower()
        if show_tx == 'y':
            transactions = self.db_manager.get_user_token_transactions(user['id'], limit=10)
            if transactions:
                print(f"\n📈 Recent Transactions:")
                for tx in transactions[:5]:
                    amount_str = f"+{tx['amount']}" if tx['amount'] > 0 else str(tx['amount'])
                    print(f"   {tx['created_at'][:19]} | {tx['transaction_type']:12} | {amount_str:6} tokens | Balance: {tx['balance_after']}")
            else:
                print("   No transactions found")
    
    def list_users_interactive(self):
        """List all users with pagination"""
        print("\n📋 All Users")
        print("=" * 15)
        
        total_users = self.db_manager.get_user_count()
        print(f"Total users: {total_users}")
        
        page = 0
        page_size = 10
        
        while True:
            offset = page * page_size
            users = self.db_manager.list_all_users(limit=page_size, offset=offset)
            
            if not users:
                print("No more users to display")
                break
            
            print(f"\nPage {page + 1} (showing {offset + 1}-{offset + len(users)} of {total_users})")
            print("-" * 80)
            print(f"{'ID':<5} {'Email':<30} {'Tokens':<8} {'Used':<8} {'Created':<12}")
            print("-" * 80)
            
            for user in users:
                created_date = user['created_at'][:10] if user['created_at'] else 'N/A'
                print(f"{user['id']:<5} {user['email'][:29]:<30} {user['tokens_remaining']:<8} {user['total_tokens_used']:<8} {created_date:<12}")
            
            if len(users) < page_size:
                print("\n(End of list)")
                break
            
            action = input(f"\n[n]ext page, [p]revious page, [q]uit: ").lower()
            if action == 'n':
                page += 1
            elif action == 'p' and page > 0:
                page -= 1
            elif action == 'q':
                break
    
    def interactive_menu(self):
        """Main interactive menu"""
        while True:
            print("\n" + "="*50)
            print("🎮 TOKEN MANAGEMENT CLI")
            print("="*50)
            print("1. Add tokens to user")
            print("2. View user info")
            print("3. List all users")
            print("4. Exit")
            print("-"*50)
            
            choice = input("Choose option (1-4): ").strip()
            
            if choice == '1':
                self.add_tokens_interactive()
            elif choice == '2':
                self.view_user_interactive()
            elif choice == '3':
                self.list_users_interactive()
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")

def main():
    parser = argparse.ArgumentParser(description='Token Management CLI')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    
    # Command line arguments for non-interactive use
    parser.add_argument('--add-tokens', action='store_true', help='Add tokens to user')
    parser.add_argument('--user-id', type=int, help='User ID')
    parser.add_argument('--email', help='User email')
    parser.add_argument('--amount', type=int, help='Token amount')
    parser.add_argument('--note', help='Admin note')
    parser.add_argument('--view-user', action='store_true', help='View user info')
    
    args = parser.parse_args()
    
    cli = TokenCLI()
    
    # Interactive mode
    if args.interactive or len(sys.argv) == 1:
        cli.interactive_menu()
        return
    
    # Command line mode
    if args.add_tokens:
        if not args.amount:
            print("❌ --amount is required for adding tokens")
            return
            
        identifier = args.email or args.user_id
        if not identifier:
            print("❌ Either --user-id or --email is required")
            return
            
        user = cli.find_user(str(identifier))
        if not user:
            print(f"❌ User '{identifier}' not found")
            return
            
        result = cli.db_manager.add_tokens_to_user(
            user_id=user['id'],
            amount=args.amount,
            admin_note=args.note or f"CLI: Added {args.amount} tokens"
        )
        
        if result['success']:
            print(f"✅ Added {args.amount} tokens to {user['email']}")
            print(f"   New balance: {result['balance_after']}")
        else:
            print(f"❌ Error: {result['message']}")
    
    elif args.view_user:
        identifier = args.email or args.user_id
        if not identifier:
            print("❌ Either --user-id or --email is required")
            return
            
        user = cli.find_user(str(identifier))
        if user:
            print(f"User: {user['email']} | Tokens: {user['tokens_remaining']}")
        else:
            print(f"❌ User '{identifier}' not found")

if __name__ == '__main__':
    main()