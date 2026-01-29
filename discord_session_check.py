#!/usr/bin/env python3
"""
Discord Session State Checker
============================

This script checks for active Discord voice sessions that might not have been
completed yet, which could explain why HAB Goat Roper's activity isn't showing
in the database even though the logs show the bot detected the activity.
"""

import requests
import urllib3
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_discord_sessions():
    print("🔍 Discord Session State Investigation")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('/app/backend/.env')
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    # Connect to database
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    # Login to API
    login_response = requests.post(
        'https://attendance-mgr-4.preview.emergentagent.com/api/auth/login',
        json={'username': 'testadmin', 'password': 'testpass123'},
        verify=False
    )
    
    if login_response.status_code != 200:
        print("❌ Failed to login")
        return
    
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n📊 Current Database State:")
    
    # Check current voice activity records
    voice_records = list(db.discord_voice_activity.find().sort('joined_at', -1))
    print(f"Total voice records: {len(voice_records)}")
    
    # Check for incomplete sessions (no left_at or duration_seconds)
    incomplete_sessions = [r for r in voice_records if r.get('left_at') is None or r.get('duration_seconds') is None]
    print(f"Incomplete voice sessions: {len(incomplete_sessions)}")
    
    if incomplete_sessions:
        print("⚠️  Found incomplete voice sessions:")
        for session in incomplete_sessions:
            print(f"   User: {session.get('discord_user_id')} - Channel: {session.get('channel_name')} - Joined: {session.get('joined_at')}")
    
    # Check recent activity for target users
    target_users = {
        '1288662056748191766': '⭐NSEC Lonestar⭐',
        '127638717115400192': 'HAB Goat Roper'
    }
    
    print(f"\n👤 Target User Activity:")
    for user_id, display_name in target_users.items():
        voice_count = db.discord_voice_activity.count_documents({'discord_user_id': user_id})
        text_count = db.discord_text_activity.count_documents({'discord_user_id': user_id})
        print(f"   {display_name} ({user_id}):")
        print(f"     Voice records: {voice_count}")
        print(f"     Text records: {text_count}")
        
        # Check most recent activity
        recent_voice = list(db.discord_voice_activity.find({'discord_user_id': user_id}).sort('joined_at', -1).limit(1))
        recent_text = list(db.discord_text_activity.find({'discord_user_id': user_id}).sort('last_message_at', -1).limit(1))
        
        if recent_voice:
            rv = recent_voice[0]
            print(f"     Last voice: {rv.get('joined_at')} - {rv.get('channel_name')} - Duration: {rv.get('duration_seconds', 'N/A')}s")
        
        if recent_text:
            rt = recent_text[0]
            print(f"     Last text: {rt.get('last_message_at')} - {rt.get('channel_name')} - Messages: {rt.get('message_count', 0)}")
    
    print(f"\n🤖 Discord Bot Status:")
    
    # Get bot status
    bot_response = requests.get(
        'https://attendance-mgr-4.preview.emergentagent.com/api/discord/test-activity',
        headers=headers,
        verify=False
    )
    
    if bot_response.status_code == 200:
        bot_data = bot_response.json()
        print(f"   Bot Status: {bot_data.get('bot_status', 'Unknown')}")
        print(f"   Total Voice Records: {bot_data.get('total_voice_records', 0)}")
        print(f"   Total Text Records: {bot_data.get('total_text_records', 0)}")
        print(f"   Recent Voice Activity: {bot_data.get('recent_voice_activity', 0)}")
        print(f"   Recent Text Activity: {bot_data.get('recent_text_activity', 0)}")
    else:
        print(f"   ❌ Failed to get bot status: {bot_response.status_code}")
    
    print(f"\n📈 Analytics API Response:")
    
    # Get analytics
    analytics_response = requests.get(
        'https://attendance-mgr-4.preview.emergentagent.com/api/discord/analytics',
        headers=headers,
        verify=False
    )
    
    if analytics_response.status_code == 200:
        analytics_data = analytics_response.json()
        print(f"   Total Members: {analytics_data.get('total_members', 0)}")
        
        voice_stats = analytics_data.get('voice_stats', {})
        text_stats = analytics_data.get('text_stats', {})
        
        print(f"   Voice Stats:")
        print(f"     Total Sessions: {voice_stats.get('total_sessions', 0)}")
        top_voice = voice_stats.get('top_users', [])
        print(f"     Top Voice Users: {len(top_voice)}")
        for i, user in enumerate(top_voice[:3]):
            print(f"       {i+1}. {user.get('username', 'Unknown')} - {user.get('total_duration', 0)}s")
        
        print(f"   Text Stats:")
        print(f"     Total Messages: {text_stats.get('total_messages', 0)}")
        top_text = text_stats.get('top_users', [])
        print(f"     Top Text Users: {len(top_text)}")
        for i, user in enumerate(top_text[:3]):
            print(f"       {i+1}. {user.get('username', 'Unknown')} - {user.get('total_messages', 0)} messages")
    else:
        print(f"   ❌ Failed to get analytics: {analytics_response.status_code}")
    
    print(f"\n🔍 Root Cause Analysis:")
    
    # Analyze the discrepancy
    issues = []
    
    # Check if HAB Goat Roper has any activity at all
    goat_roper_voice = db.discord_voice_activity.count_documents({'discord_user_id': '127638717115400192'})
    goat_roper_text = db.discord_text_activity.count_documents({'discord_user_id': '127638717115400192'})
    
    if goat_roper_voice == 0 and goat_roper_text == 0:
        issues.append("HAB Goat Roper has NO activity records in database despite bot logs showing activity detection")
        
        # This suggests either:
        # 1. The user is still in a voice channel (session not completed)
        # 2. There's an issue with the bot's session tracking
        # 3. The user left before the bot could save the session
        
        print("   ⚠️  CRITICAL ISSUE: HAB Goat Roper activity missing from database")
        print("   Possible causes:")
        print("     1. User is still in voice channel (session not completed)")
        print("     2. Bot session tracking issue")
        print("     3. User left before bot could save session")
        print("     4. Database write failure")
    
    # Check if Lonestar data is consistent
    lonestar_voice = db.discord_voice_activity.count_documents({'discord_user_id': '1288662056748191766'})
    lonestar_text = db.discord_text_activity.count_documents({'discord_user_id': '1288662056748191766'})
    
    if lonestar_voice > 0 or lonestar_text > 0:
        print("   ✅ Lonestar data is present - bot is working for some users")
    
    # Check for timing issues
    now = datetime.now(timezone.utc)
    recent_cutoff = now.replace(hour=now.hour-1)  # Last hour
    
    recent_voice = db.discord_voice_activity.count_documents({
        'joined_at': {'$gte': recent_cutoff}
    })
    
    recent_text = db.discord_text_activity.count_documents({
        'last_message_at': {'$gte': recent_cutoff}
    })
    
    print(f"\n   📊 Recent Activity (last hour):")
    print(f"     Voice records: {recent_voice}")
    print(f"     Text records: {recent_text}")
    
    if issues:
        print(f"\n❌ Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"\n✅ No critical issues detected")
    
    print(f"\n" + "=" * 50)

if __name__ == "__main__":
    check_discord_sessions()