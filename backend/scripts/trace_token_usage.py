#!/usr/bin/env python3
from database import DatabaseManager
from config import Config
from datetime import datetime, timedelta

db_manager = DatabaseManager(Config.DATABASE_URL)

print("🕵️ TRACING TOKEN USAGE FOR USER 1")
print("=" * 80)

# Get current user status
user = db_manager.get_user_by_id(1)
print(f"Current Status:")
print(f"  Tokens Remaining: {user['tokens_remaining']}")
print(f"  Total Used: {user['total_tokens_used']}")
print(f"  Started with: 100 tokens")
print(f"  Consumed: {100 - user['tokens_remaining']} tokens")
print()

# Get all transactions 
print("💰 TOKEN TRANSACTIONS:")
print("=" * 80)
transactions = db_manager.get_user_token_transactions(user_id=1, limit=50)

if transactions:
    print(f"{'Date/Time':<20} {'Type':<15} {'Amount':<8} {'Before':<8} {'After':<8} {'Note'}")
    print("-" * 80)
    
    total_granted = 0
    total_used = 0
    
    for tx in transactions:
        date = tx['created_at'][:19] if tx['created_at'] else 'N/A'
        tx_type = tx['transaction_type']
        amount = tx['amount']
        before = tx['balance_before']
        after = tx['balance_after']
        note = (tx.get('admin_note') or tx.get('reference_id') or '')[:25]
        
        if amount > 0:
            total_granted += amount
        else:
            total_used += abs(amount)
        
        print(f"{date:<20} {tx_type:<15} {amount:>8} {before:>8} {after:>8} {note}")
    
    print("-" * 80)
    print(f"Total Granted: +{total_granted}")
    print(f"Total Used (via transactions): -{total_used}")
    print(f"Net from transactions: {total_granted - total_used}")

else:
    print("No token transactions found")

print()

# Get analysis history from last 2 hours
print("🛰️ RECENT ANALYSIS ACTIVITY:")
print("=" * 80)
two_hours_ago = datetime.now() - timedelta(hours=2)

analyses = db_manager.get_user_history(user_id=1, limit=100)

# Filter to last 2 hours
recent_analyses = []
for analysis in analyses:
    if analysis.get('analysis_timestamp'):
        analysis_time = datetime.fromisoformat(analysis['analysis_timestamp'].replace('Z', ''))
        if analysis_time >= two_hours_ago:
            recent_analyses.append(analysis)

if recent_analyses:
    print(f"Found {len(recent_analyses)} analyses in the last 2 hours:")
    print(f"{'Time':<20} {'Operation':<25} {'AOI':<5} {'Tokens':<7} {'Type'}")
    print("-" * 80)
    
    analysis_tokens = 0
    for analysis in recent_analyses:
        time = analysis.get('analysis_timestamp', 'N/A')[:19]
        operation = analysis.get('operation_name', 'N/A')[:24]
        aoi_id = analysis.get('aoi_id', 'N/A')
        tokens = analysis.get('tokens_used', 0)
        analysis_type = "Scheduled" if "SCHEDULED" in str(operation) else "Manual"
        
        analysis_tokens += tokens
        print(f"{time:<20} {operation:<25} {aoi_id:<5} {tokens:<7} {analysis_type}")
    
    print("-" * 80)
    print(f"Total tokens recorded in recent analyses: {analysis_tokens}")

else:
    print("No analyses found in the last 2 hours")

print()
print("🔍 DISCREPANCY ANALYSIS:")
print("=" * 80)
print(f"Tokens consumed according to user.total_tokens_used: {user['total_tokens_used']}")
print(f"Tokens consumed according to transactions: {total_used if 'total_used' in locals() else 0}")
print(f"Tokens consumed according to recent analyses: {analysis_tokens if 'analysis_tokens' in locals() else 0}")

discrepancy = user['total_tokens_used'] - (total_used if 'total_used' in locals() else 0)
print(f"DISCREPANCY (missing from transactions): {discrepancy}")

if discrepancy > 0:
    print(f"⚠️  {discrepancy} tokens were consumed but NOT recorded in transactions!")
    print("This suggests the token consumption happened outside the transaction system.")