import sys
import os

# Critical: Write to stderr immediately to test if module is loading
sys.stderr.write("🚀 [INIT] Starting server.py module import...\n")
sys.stderr.flush()

# Also try writing to a file as a fallback
try:
    with open('/tmp/server_import.log', 'w') as f:
        f.write("server.py module is being imported\n")
except:
    pass

sys.stderr.write("  [INIT] Importing FastAPI...\n")
sys.stderr.flush()
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Response, UploadFile, File, Request
sys.stderr.write("  [INIT] Importing security...\n")
sys.stderr.flush()
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
sys.stderr.write("  [INIT] Importing dotenv...\n")
sys.stderr.flush()
from dotenv import load_dotenv
sys.stderr.write("  [INIT] Importing CORS...\n")
sys.stderr.flush()
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
sys.stderr.write("  [INIT] Importing Motor (MongoDB async)...\n")
sys.stderr.flush()
from motor.motor_asyncio import AsyncIOMotorClient

sys.stderr.write("  [INIT] Importing logging & pathlib...\n")
sys.stderr.flush()
import os
import logging
from pathlib import Path

sys.stderr.write("✅ [INIT] Core imports successful\n")
sys.stderr.flush()
sys.stderr.write("  [INIT] Importing Pydantic...\n")
sys.stderr.flush()
from pydantic import BaseModel, Field, ConfigDict, EmailStr
sys.stderr.write("  [INIT] Importing typing & utils...\n")
sys.stderr.flush()
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
sys.stderr.write("  [INIT] Importing JWT...\n")
sys.stderr.flush()
import jwt
sys.stderr.write("  [INIT] Importing passlib (bcrypt)...\n")
sys.stderr.flush()
from passlib.context import CryptContext
sys.stderr.write("  [INIT] Importing CSV & IO...\n")
sys.stderr.flush()
import csv
from io import StringIO
sys.stderr.write("  [INIT] Importing responses...\n")
sys.stderr.flush()
from fastapi.responses import StreamingResponse, Response
sys.stderr.write("  [INIT] Importing aiosmtplib...\n")
sys.stderr.flush()
import aiosmtplib
sys.stderr.write("  [INIT] Importing email MIME...\n")
sys.stderr.flush()
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.stderr.write("  [INIT] Importing cryptography (Fernet)...\n")
sys.stderr.flush()
from cryptography.fernet import Fernet
sys.stderr.write("  [INIT] Importing hashlib...\n")
sys.stderr.flush()
import hashlib
sys.stderr.write("  [INIT] Importing Discord.py...\n")
sys.stderr.flush()
import discord
import asyncio
import aiohttp
import re  # For regex escaping (security)

sys.stderr.write("✅ [INIT] All imports completed successfully\n")
sys.stderr.flush()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - deferred initialization to avoid blocking at import time
sys.stderr.write("🔧 [INIT] Preparing MongoDB configuration...\n")
sys.stderr.flush()
mongo_url = os.environ['MONGO_URL']
# Don't connect immediately - let Motor connect lazily on first use
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
db = client[os.environ['DB_NAME']]
sys.stderr.write("✅ [INIT] MongoDB client configured (will connect on first use)\n")
sys.stderr.flush()

# Encryption setup (AES-256)
sys.stderr.write("🔧 [INIT] Setting up encryption...\n")
sys.stderr.flush()
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())
sys.stderr.write("✅ [INIT] Encryption configured\n")
sys.stderr.flush()

# SMTP Email Configuration
sys.stderr.write("🔧 [INIT] Setting up SMTP email...\n")
sys.stderr.flush()
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'

# Support email configuration
SUPPORT_SMTP_USERNAME = os.environ.get('SUPPORT_SMTP_USERNAME')
SUPPORT_SMTP_PASSWORD = os.environ.get('SUPPORT_SMTP_PASSWORD')

smtp_configured = all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL])
support_smtp_configured = all([SMTP_HOST, SUPPORT_SMTP_USERNAME, SUPPORT_SMTP_PASSWORD])

if smtp_configured:
    sys.stderr.write(f"✅ [INIT] SMTP configured: {SMTP_HOST}:{SMTP_PORT} (from: {SMTP_FROM_EMAIL})\n")
else:
    sys.stderr.write("⚠️ [INIT] SMTP not configured (missing SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, or SMTP_FROM_EMAIL)\n")

if support_smtp_configured:
    sys.stderr.write(f"✅ [INIT] Support SMTP configured: {SUPPORT_SMTP_USERNAME}\n")
sys.stderr.flush()

# Discord configuration
sys.stderr.write("🔧 [INIT] Setting up Discord...\n")
sys.stderr.flush()
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
DISCORD_PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')
DISCORD_GUILD_ID = os.environ.get('DISCORD_GUILD_ID')
DISCORD_SUSPENDED_ROLE_ID = os.environ.get('DISCORD_SUSPENDED_ROLE_ID')
DISCORD_HANGAROUND_ROLE_ID = os.environ.get('DISCORD_HANGAROUND_ROLE_ID')
DISCORD_PROSPECT_ROLE_ID = os.environ.get('DISCORD_PROSPECT_ROLE_ID')

# Discord bot for activity tracking
discord_bot = None
discord_task = None

# Square Payment Configuration
sys.stderr.write("🔧 [INIT] Setting up Square payments...\n")
sys.stderr.flush()
SQUARE_ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN')
SQUARE_APPLICATION_ID = os.environ.get('SQUARE_APPLICATION_ID')
SQUARE_LOCATION_ID = os.environ.get('SQUARE_LOCATION_ID')
SQUARE_ENVIRONMENT = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
SQUARE_WEBHOOK_SIGNATURE_KEY = os.environ.get('SQUARE_WEBHOOK_SIGNATURE_KEY', '')

square_client = None
if SQUARE_ACCESS_TOKEN:
    try:
        from square import Square
        from square.utils.webhooks_helper import verify_signature as square_verify_signature
        square_client = Square(
            token=SQUARE_ACCESS_TOKEN,
        )
        sys.stderr.write(f"✅ [INIT] Square client initialized ({SQUARE_ENVIRONMENT})\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"⚠️ [INIT] Square client initialization failed: {str(e)}\n")
        sys.stderr.flush()
else:
    sys.stderr.write("⚠️ [INIT] Square credentials not configured\n")
    sys.stderr.flush()

async def start_discord_bot():
    """Start Discord analytics bot with voice and text tracking"""
    global discord_bot, discord_task
    try:
        sys.stderr.write("🔧 [DISCORD] Starting Discord analytics bot...\n")
        sys.stderr.flush()
        
        if not DISCORD_BOT_TOKEN:
            sys.stderr.write("❌ [DISCORD] Bot token not found\n")
            sys.stderr.flush()
            return
        
        # Import Discord bot components
        import discord
        from datetime import timezone
        
        # Users to ignore in Discord analytics (by display name)
        IGNORED_DISCORD_USERS = [
            "HSB Hillbilly",
            "hsb hillbilly",
        ]
        
        def should_ignore_user(member):
            """Check if a user should be ignored from analytics"""
            display_name = member.display_name if hasattr(member, 'display_name') else str(member)
            return display_name.lower() in [name.lower() for name in IGNORED_DISCORD_USERS]
        
        # Discord Analytics Bot Class with Voice and Text Tracking
        class DiscordActivityBot(discord.Client):
            def __init__(self):
                intents = discord.Intents.default()
                intents.voice_states = True
                intents.message_content = True
                intents.members = True
                super().__init__(intents=intents)
                self.voice_sessions = {}
                
            async def on_ready(self):
                sys.stderr.write(f"✅ [DISCORD] Bot logged in as {self.user}\n")
                sys.stderr.write(f"✅ [DISCORD] Monitoring {len(self.guilds)} guild(s):\n")
                for guild in self.guilds:
                    sys.stderr.write(f"   - {guild.name} ({guild.id}): {guild.member_count} members\n")
                
                # Clear stale active prospect sessions from previous runs
                await db.prospect_channel_active_sessions.delete_many({})
                
                for guild in self.guilds:
                    # Scan for users already in voice channels and start tracking them
                    for voice_channel in guild.voice_channels:
                        for member in voice_channel.members:
                            if not member.bot and not should_ignore_user(member):
                                user_id = str(member.id)
                                if user_id not in self.voice_sessions:
                                    # Capture who else is in the channel
                                    others_in_channel = []
                                    for other_member in voice_channel.members:
                                        if str(other_member.id) != user_id and not other_member.bot:
                                            others_in_channel.append({
                                                'discord_id': str(other_member.id),
                                                'display_name': other_member.display_name
                                            })
                                    
                                    session_id = str(uuid.uuid4())
                                    now = datetime.now(timezone.utc)
                                    self.voice_sessions[user_id] = {
                                        'session_id': session_id,
                                        'joined_at': now,
                                        'channel_id': str(voice_channel.id),
                                        'channel_name': voice_channel.name,
                                        'others_in_channel': others_in_channel
                                    }
                                    sys.stderr.write(f"🎤 [DISCORD] Tracking {member.display_name} already in {voice_channel.name}\n")
                                    
                                    # Save active session for Prospect channels
                                    await self.save_active_prospect_session(
                                        session_id, user_id, member.display_name,
                                        voice_channel.name, now, others_in_channel
                                    )
                    
                sys.stderr.write(f"✅ [DISCORD] Now tracking {len(self.voice_sessions)} user(s) already in voice\n")
                sys.stderr.flush()
                
            async def on_voice_state_update(self, member, before, after):
                """Track voice channel activity"""
                if member.bot:
                    return
                
                # Check if user should be ignored
                if should_ignore_user(member):
                    return
                    
                user_id = str(member.id)
                now = datetime.now(timezone.utc)
                
                try:
                    # User joined voice channel
                    if before.channel is None and after.channel is not None:
                        # Capture who else is in the channel (for Prospect channel tracking)
                        others_in_channel = []
                        for other_member in after.channel.members:
                            if str(other_member.id) != user_id and not other_member.bot:
                                others_in_channel.append({
                                    'discord_id': str(other_member.id),
                                    'display_name': other_member.display_name
                                })
                        
                        session_id = str(uuid.uuid4())
                        self.voice_sessions[user_id] = {
                            'session_id': session_id,
                            'joined_at': now,
                            'channel_id': str(after.channel.id),
                            'channel_name': after.channel.name,
                            'others_in_channel': others_in_channel
                        }
                        sys.stderr.write(f"🎤 [DISCORD] {member.display_name} joined {after.channel.name}\n")
                        sys.stderr.flush()
                        
                        # Save active session for Prospect channels
                        await self.save_active_prospect_session(
                            session_id, user_id, member.display_name, 
                            after.channel.name, now, others_in_channel
                        )
                        
                    # User left voice channel
                    elif before.channel is not None and after.channel is None:
                        # If this user is a prospect, update other sessions in the channel they're leaving
                        if 'ha(p)' in member.display_name.lower():
                            channel_name_lower = before.channel.name.lower()
                            prospect_channels = ['prospect', 'prospect 2', 'prospect2', 'prospects']
                            if any(pc in channel_name_lower for pc in prospect_channels):
                                await self.update_sessions_prospect_left(
                                    before.channel.name, user_id, member.display_name, now.isoformat()
                                )
                        
                        if user_id in self.voice_sessions:
                            # We have a tracked session - calculate duration
                            session = self.voice_sessions[user_id]
                            duration = (now - session['joined_at']).total_seconds()
                            
                            # Only save if duration is at least 1 second
                            if duration >= 1:
                                voice_activity = {
                                    'id': str(uuid.uuid4()),
                                    'discord_id': user_id,
                                    'discord_user_id': user_id,  # Keep for backwards compatibility
                                    'channel_id': session['channel_id'],
                                    'channel_name': session['channel_name'],
                                    'joined_at': session['joined_at'],
                                    'left_at': now,
                                    'duration_seconds': int(duration),
                                    'date': now.date().isoformat()
                                }
                                
                                await db.discord_voice_activity.insert_one(voice_activity)
                                sys.stderr.write(f"💾 [DISCORD] Saved {member.display_name} voice session: {duration/60:.1f} min in {session['channel_name']}\n")
                                sys.stderr.flush()
                                
                                # Track Prospect channel activity separately if enabled
                                await self.track_prospect_channel_activity(
                                    user_id, member.display_name, session, duration, now
                                )
                            else:
                                sys.stderr.write(f"⏭️ [DISCORD] Skipping {member.display_name} session < 1s\n")
                                sys.stderr.flush()
                            del self.voice_sessions[user_id]
                        else:
                            # User was already in voice when bot started but we didn't catch them in on_ready
                            # Start tracking them now for future sessions
                            sys.stderr.write(f"🎤 [DISCORD] {member.display_name} left {before.channel.name} (untracked session)\n")
                            sys.stderr.flush()
                            
                    # User moved between channels
                    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                        # If this user is a prospect, update other sessions in the channel they're leaving
                        if 'ha(p)' in member.display_name.lower():
                            channel_name_lower = before.channel.name.lower()
                            prospect_channels = ['prospect', 'prospect 2', 'prospect2', 'prospects']
                            if any(pc in channel_name_lower for pc in prospect_channels):
                                await self.update_sessions_prospect_left(
                                    before.channel.name, user_id, member.display_name, now.isoformat()
                                )
                        
                        # End previous session
                        if user_id in self.voice_sessions:
                            session = self.voice_sessions[user_id]
                            duration = (now - session['joined_at']).total_seconds()
                            
                            voice_activity = {
                                'id': str(uuid.uuid4()),
                                'discord_id': user_id,
                                'discord_user_id': user_id,
                                'channel_id': session['channel_id'],
                                'channel_name': session['channel_name'],
                                'joined_at': session['joined_at'],
                                'left_at': now,
                                'duration_seconds': int(duration),
                                'date': now.date().isoformat()
                            }
                            
                            await db.discord_voice_activity.insert_one(voice_activity)
                            
                            # Track prospect channel activity for the previous channel
                            await self.track_prospect_channel_activity(
                                user_id, member.display_name, session, duration, now
                            )
                        
                        # Start new session with others in channel info
                        others_in_channel = []
                        for other_member in after.channel.members:
                            if str(other_member.id) != user_id and not other_member.bot:
                                others_in_channel.append({
                                    'discord_id': str(other_member.id),
                                    'display_name': other_member.display_name
                                })
                        
                        new_session_id = str(uuid.uuid4())
                        self.voice_sessions[user_id] = {
                            'session_id': new_session_id,
                            'joined_at': now,
                            'channel_id': str(after.channel.id),
                            'channel_name': after.channel.name,
                            'others_in_channel': others_in_channel
                        }
                        
                        # Save active session for new Prospect channel
                        await self.save_active_prospect_session(
                            new_session_id, user_id, member.display_name,
                            after.channel.name, now, others_in_channel
                        )
                
                except Exception as e:
                    sys.stderr.write(f"❌ [DISCORD] Voice tracking error: {str(e)}\n")
                    sys.stderr.flush()
            
            async def save_active_prospect_session(self, session_id, user_id, display_name, channel_name, joined_at, others_in_channel):
                """Save an active session when user joins a Prospect channel"""
                try:
                    channel_name_lower = channel_name.lower()
                    
                    # Check if this is a Prospect channel
                    prospect_channels = ['prospect', 'prospect 2', 'prospect2', 'prospects']
                    is_prospect_channel = any(pc in channel_name_lower for pc in prospect_channels)
                    
                    if not is_prospect_channel:
                        return
                    
                    # Check if tracking is enabled
                    settings = await db.prospect_channel_settings.find_one({"_id": "main"})
                    if not settings or not settings.get("tracking_enabled", True):
                        return
                    
                    # Delete any existing active session for this user (prevent duplicates)
                    await db.prospect_channel_active_sessions.delete_many({"discord_id": user_id})
                    
                    # Check if any others are Prospects (identified by "HA(p)" in their name)
                    # Build prospect_timings to track when each prospect was present
                    prospect_timings = {}  # {prospect_name: {'discord_id': id, 'joined_at': timestamp}}
                    
                    # Get hangarounds from database for matching
                    hangarounds = await db.hangarounds.find({}, {"handle": 1, "_id": 0}).to_list(1000)
                    hangaround_handle_set = {h['handle'].lower() for h in hangarounds if h.get('handle')}
                    
                    joined_at_iso = joined_at.isoformat()
                    
                    for other in others_in_channel:
                        other_name = other.get('display_name', '')
                        other_id = other.get('discord_id', '')
                        other_name_lower = other_name.lower()
                        
                        # Check for Prospect: "HA(p)" in name (case insensitive)
                        if 'ha(p)' in other_name_lower:
                            # Prospect was already in channel when user joined
                            prospect_timings[other_name] = {
                                'discord_id': other_id,
                                'joined_at': joined_at_iso,  # They were there from the start of this user's session
                                'left_at': None  # Still present
                            }
                    
                    # Save active session with prospect_timings for overlap calculation
                    active_session = {
                        'id': session_id,
                        'discord_id': user_id,
                        'display_name': display_name,
                        'channel_name': channel_name,
                        'joined_at': joined_at_iso,
                        'status': 'active',
                        'others_in_channel': others_in_channel,
                        'prospect_timings': prospect_timings  # Track prospect join/leave times
                    }
                    
                    await db.prospect_channel_active_sessions.insert_one(active_session)
                    
                    # If this user is a prospect, update all other active sessions in this channel
                    if 'ha(p)' in display_name.lower():
                        await self.update_sessions_prospect_joined(channel_name, user_id, display_name, joined_at_iso)
                    
                    sys.stderr.write(f"📊 [PROSPECT] Started tracking {display_name} in {channel_name}\n")
                    sys.stderr.flush()
                    
                except Exception as e:
                    sys.stderr.write(f"❌ [PROSPECT] Error saving active session: {str(e)}\n")
                    sys.stderr.flush()
            
            async def update_sessions_prospect_joined(self, channel_name, prospect_id, prospect_name, joined_at_iso):
                """When a prospect joins, update all other active sessions in the channel"""
                try:
                    # Find all active sessions in this channel (excluding the prospect themselves)
                    active_sessions = await db.prospect_channel_active_sessions.find({
                        'channel_name': channel_name,
                        'discord_id': {'$ne': prospect_id}
                    }).to_list(1000)
                    
                    for session in active_sessions:
                        prospect_timings = session.get('prospect_timings', {})
                        if prospect_name not in prospect_timings:
                            prospect_timings[prospect_name] = {
                                'discord_id': prospect_id,
                                'joined_at': joined_at_iso,
                                'left_at': None
                            }
                            await db.prospect_channel_active_sessions.update_one(
                                {'id': session['id']},
                                {'$set': {'prospect_timings': prospect_timings}}
                            )
                    
                    sys.stderr.write(f"📊 [PROSPECT] Updated {len(active_sessions)} sessions: {prospect_name} joined\n")
                    sys.stderr.flush()
                except Exception as e:
                    sys.stderr.write(f"❌ [PROSPECT] Error updating sessions on prospect join: {str(e)}\n")
                    sys.stderr.flush()
            
            async def update_sessions_prospect_left(self, channel_name, prospect_id, prospect_name, left_at_iso):
                """When a prospect leaves, update all other active sessions in the channel"""
                try:
                    # Find all active sessions in this channel
                    active_sessions = await db.prospect_channel_active_sessions.find({
                        'channel_name': channel_name,
                        'discord_id': {'$ne': prospect_id}
                    }).to_list(1000)
                    
                    for session in active_sessions:
                        prospect_timings = session.get('prospect_timings', {})
                        if prospect_name in prospect_timings and prospect_timings[prospect_name].get('left_at') is None:
                            prospect_timings[prospect_name]['left_at'] = left_at_iso
                            await db.prospect_channel_active_sessions.update_one(
                                {'id': session['id']},
                                {'$set': {'prospect_timings': prospect_timings}}
                            )
                    
                    sys.stderr.write(f"📊 [PROSPECT] Updated {len(active_sessions)} sessions: {prospect_name} left\n")
                    sys.stderr.flush()
                except Exception as e:
                    sys.stderr.write(f"❌ [PROSPECT] Error updating sessions on prospect leave: {str(e)}\n")
                    sys.stderr.flush()
            
            async def track_prospect_channel_activity(self, user_id, display_name, session, duration, left_at):
                """Track activity in Prospect voice channels with additional context"""
                try:
                    channel_name = session['channel_name'].lower()
                    
                    # Check if this is a Prospect channel (case insensitive)
                    prospect_channels = ['prospect', 'prospect 2', 'prospect2', 'prospects']
                    is_prospect_channel = any(pc in channel_name for pc in prospect_channels)
                    
                    if not is_prospect_channel:
                        return
                    
                    # Check if tracking is enabled
                    settings = await db.prospect_channel_settings.find_one({"_id": "main"})
                    if not settings or not settings.get("tracking_enabled", True):
                        return
                    
                    # Get prospect timings from the active session in the database
                    session_id = session.get('session_id')
                    active_session_data = None
                    if session_id:
                        active_session_data = await db.prospect_channel_active_sessions.find_one({'id': session_id})
                    if not active_session_data:
                        active_session_data = await db.prospect_channel_active_sessions.find_one({'discord_id': user_id})
                    
                    prospect_timings = active_session_data.get('prospect_timings', {}) if active_session_data else {}
                    
                    # Calculate time spent with each prospect
                    user_joined_at = session['joined_at']
                    user_left_at = left_at
                    
                    prospect_time_breakdown = []
                    total_time_with_prospects = 0
                    
                    for prospect_name, timing in prospect_timings.items():
                        prospect_joined_str = timing.get('joined_at')
                        prospect_left_str = timing.get('left_at')
                        
                        if not prospect_joined_str:
                            continue
                        
                        # Parse timestamps
                        prospect_joined = datetime.fromisoformat(prospect_joined_str.replace('Z', '+00:00'))
                        prospect_left = datetime.fromisoformat(prospect_left_str.replace('Z', '+00:00')) if prospect_left_str else user_left_at
                        
                        # Calculate overlap
                        overlap_start = max(user_joined_at, prospect_joined)
                        overlap_end = min(user_left_at, prospect_left)
                        
                        if overlap_end > overlap_start:
                            overlap_seconds = int((overlap_end - overlap_start).total_seconds())
                            total_time_with_prospects += overlap_seconds
                            
                            prospect_time_breakdown.append({
                                'prospect_name': prospect_name,
                                'prospect_discord_id': timing.get('discord_id'),
                                'time_together_seconds': overlap_seconds,
                                'prospect_joined_at': prospect_joined_str,
                                'prospect_left_at': prospect_left_str or user_left_at.isoformat()
                            })
                    
                    # Calculate time alone (total duration minus time with any prospect)
                    time_alone_seconds = max(0, int(duration) - total_time_with_prospects)
                    
                    # Get hangarounds from database for backward compatibility
                    hangarounds = await db.hangarounds.find({}, {"handle": 1, "_id": 0}).to_list(1000)
                    hangaround_handle_set = {h['handle'].lower() for h in hangarounds if h.get('handle')}
                    
                    others_in_channel = session.get('others_in_channel', [])
                    hangaround_handles = set()
                    
                    for other in others_in_channel:
                        other_name = other.get('display_name', '')
                        other_name_lower = other_name.lower()
                        for hh in hangaround_handle_set:
                            if hh in other_name_lower:
                                hangaround_handles.add(other_name)
                                break
                    
                    # Build list of prospect names for backward compatibility
                    prospect_names = [p['prospect_name'] for p in prospect_time_breakdown]
                    
                    # Save the prospect channel activity with time breakdown
                    prospect_activity = {
                        'id': str(uuid.uuid4()),
                        'discord_id': user_id,
                        'display_name': display_name,
                        'channel_name': session['channel_name'],
                        'joined_at': user_joined_at,
                        'left_at': user_left_at,
                        'duration_seconds': int(duration),
                        'date': left_at.date().isoformat(),
                        'others_in_channel': others_in_channel,
                        'prospects_present': prospect_names,
                        'hangarounds_present': list(hangaround_handles),
                        'had_prospect_interaction': len(prospect_time_breakdown) > 0 or len(hangaround_handles) > 0,
                        # New fields for time breakdown
                        'prospect_time_breakdown': prospect_time_breakdown,
                        'total_time_with_prospects_seconds': total_time_with_prospects,
                        'time_alone_seconds': time_alone_seconds
                    }
                    
                    await db.prospect_channel_activity.insert_one(prospect_activity)
                    
                    # Remove the active session now that it's completed
                    session_id = session.get('session_id')
                    if session_id:
                        await db.prospect_channel_active_sessions.delete_one({"id": session_id})
                    else:
                        # Fallback: delete by discord_id if no session_id
                        await db.prospect_channel_active_sessions.delete_one({"discord_id": user_id})
                    
                    sys.stderr.write(f"📊 [PROSPECT] Completed {display_name} in {session['channel_name']}: {duration/60:.1f}min, prospects: {list(prospect_handles)}\n")
                    sys.stderr.flush()
                    
                except Exception as e:
                    sys.stderr.write(f"❌ [PROSPECT] Tracking error: {str(e)}\n")
                    sys.stderr.flush()
                        
            async def on_message(self, message):
                """Track text message activity"""
                if message.author.bot or not message.guild:
                    return
                
                # Check if user should be ignored
                if should_ignore_user(message.author):
                    return
                    
                user_id = str(message.author.id)
                channel_id = str(message.channel.id)
                channel_name = message.channel.name
                today = datetime.now(timezone.utc).date().isoformat()
                
                try:
                    # Check existing record for today
                    existing_record = await db.discord_text_activity.find_one({
                        'discord_user_id': user_id,
                        'channel_id': channel_id,
                        'date': today
                    })
                    
                    if existing_record:
                        await db.discord_text_activity.update_one(
                            {'_id': existing_record['_id']},
                            {
                                '$inc': {'message_count': 1},
                                '$set': {'last_message_at': datetime.now(timezone.utc)}
                            }
                        )
                    else:
                        text_activity = {
                            'id': str(uuid.uuid4()),
                            'discord_user_id': user_id,
                            'channel_id': channel_id,
                            'channel_name': channel_name,
                            'message_count': 1,
                            'date': today,
                            'last_message_at': datetime.now(timezone.utc)
                        }
                        await db.discord_text_activity.insert_one(text_activity)
                
                except Exception as e:
                    sys.stderr.write(f"❌ [DISCORD] Text tracking error: {str(e)}\n")
                    sys.stderr.flush()
        
        # Start the bot
        discord_bot = DiscordActivityBot()
        discord_task = asyncio.create_task(discord_bot.start(DISCORD_BOT_TOKEN))
        
        sys.stderr.write("✅ [DISCORD] Analytics bot started (tracking voice & text)\n")
        sys.stderr.flush()
        
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error starting bot: {str(e)}\n")
        sys.stderr.flush()


async def add_discord_role_by_name(member_handle: str, role_id: str, reason: str = "Role assignment") -> dict:
    """Add a Discord role to a member by their handle"""
    global discord_bot
    
    if not discord_bot or not DISCORD_GUILD_ID:
        return {"success": False, "message": "Discord bot not configured"}
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"success": False, "message": "Guild not found"}
        
        # Find member by handle
        discord_member = None
        for member in guild.members:
            display_name = member.nick or member.display_name or member.name
            if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                discord_member = member
                break
        
        if not discord_member:
            return {"success": False, "message": f"Could not find Discord user for {member_handle}"}
        
        role = guild.get_role(int(role_id))
        if not role:
            return {"success": False, "message": f"Role {role_id} not found"}
        
        await discord_member.add_roles(role, reason=reason)
        sys.stderr.write(f"✅ [DISCORD] Added role {role.name} to {member_handle}\n")
        sys.stderr.flush()
        return {"success": True, "message": f"Added role {role.name} to {member_handle}"}
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error adding role: {e}\n")
        sys.stderr.flush()
        return {"success": False, "message": str(e)}


async def remove_discord_role_by_name(member_handle: str, role_id: str, reason: str = "Role removal") -> dict:
    """Remove a Discord role from a member by their handle"""
    global discord_bot
    
    if not discord_bot or not DISCORD_GUILD_ID:
        return {"success": False, "message": "Discord bot not configured"}
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"success": False, "message": "Guild not found"}
        
        # Find member by handle
        discord_member = None
        for member in guild.members:
            display_name = member.nick or member.display_name or member.name
            if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                discord_member = member
                break
        
        if not discord_member:
            return {"success": False, "message": f"Could not find Discord user for {member_handle}"}
        
        role = guild.get_role(int(role_id))
        if not role:
            return {"success": False, "message": f"Role {role_id} not found"}
        
        if role in discord_member.roles:
            await discord_member.remove_roles(role, reason=reason)
            sys.stderr.write(f"✅ [DISCORD] Removed role {role.name} from {member_handle}\n")
            sys.stderr.flush()
        return {"success": True, "message": f"Removed role {role.name} from {member_handle}"}
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error removing role: {e}\n")
        sys.stderr.flush()
        return {"success": False, "message": str(e)}


async def suspend_discord_member(member_handle: str, member_id: str, reason: str = "Dues suspension") -> dict:
    """
    Suspend a member's Discord permissions by removing their roles.
    
    Args:
        member_handle: The member's handle/nickname in the system
        member_id: The member's ID in our system
        reason: Reason for the suspension
        
    Returns:
        dict with success status and message
    """
    global discord_bot
    
    if not discord_bot:
        return {"success": False, "message": "Discord bot not running"}
    
    if not DISCORD_GUILD_ID:
        return {"success": False, "message": "Discord guild ID not configured"}
    
    try:
        # First, try to find the Discord member by their linked discord_id
        linked_member = await db.discord_members.find_one({
            "$or": [
                {"linked_member_id": member_id},
                {"linked_handle": member_handle}
            ]
        })
        
        discord_user_id = None
        if linked_member:
            discord_user_id = linked_member.get("discord_id")
        
        if not discord_user_id:
            # Try to find by matching display name to handle
            sys.stderr.write(f"🔍 [DISCORD] Searching for member {member_handle} by name match...\n")
            sys.stderr.flush()
            
            guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
            if not guild:
                return {"success": False, "message": f"Could not find guild {DISCORD_GUILD_ID}"}
            
            # Search for member by nickname or username
            for discord_member in guild.members:
                display_name = discord_member.nick or discord_member.display_name or discord_member.name
                # Check for exact match or if handle is contained in display name (for prefixed names like "HAB Goat Roper")
                if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                    discord_user_id = str(discord_member.id)
                    sys.stderr.write(f"✅ [DISCORD] Matched {member_handle} to Discord user {display_name}\n")
                    sys.stderr.flush()
                    break
        
        if not discord_user_id:
            return {"success": False, "message": f"Could not find Discord user for member {member_handle}"}
        
        # Get the guild and member
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"success": False, "message": f"Could not find guild {DISCORD_GUILD_ID}"}
        
        discord_member = guild.get_member(int(discord_user_id))
        if not discord_member:
            # Try to fetch the member
            try:
                discord_member = await guild.fetch_member(int(discord_user_id))
            except:
                return {"success": False, "message": f"Could not find Discord member {discord_user_id} in guild"}
        
        # Store the member's current roles before removing them
        current_roles = [{"id": str(role.id), "name": role.name} for role in discord_member.roles if role.name != "@everyone"]
        
        # Save the roles to the database so we can restore them later
        await db.discord_suspensions.update_one(
            {"member_id": member_id},
            {
                "$set": {
                    "member_id": member_id,
                    "member_handle": member_handle,
                    "discord_user_id": discord_user_id,
                    "previous_roles": current_roles,
                    "suspended_at": datetime.now(timezone.utc).isoformat(),
                    "reason": reason
                }
            },
            upsert=True
        )
        
        # Remove all roles from the member (except @everyone which can't be removed)
        roles_to_remove = [role for role in discord_member.roles if role.name != "@everyone" and not role.is_bot_managed()]
        
        if roles_to_remove:
            try:
                await discord_member.remove_roles(*roles_to_remove, reason=reason)
                sys.stderr.write(f"🚫 [DISCORD] Suspended {member_handle}: removed {len(roles_to_remove)} roles\n")
                sys.stderr.flush()
            except Exception as e:
                error_msg = str(e)
                sys.stderr.write(f"❌ [DISCORD] Failed to remove roles from {member_handle}: {error_msg}\n")
                sys.stderr.flush()
                
                # If we can't remove roles, at least notify officers
                try:
                    webhook_url = os.environ.get('DISCORD_WEBHOOK_OFFICERS')
                    if webhook_url:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            embed = {
                                "title": "⚠️ Manual Action Required - Dues Suspension",
                                "description": f"**{member_handle}** needs to be suspended for unpaid dues, but the bot couldn't remove their roles automatically.\n\n**Please manually remove their roles.**",
                                "color": 15105570,  # Orange color
                                "fields": [
                                    {"name": "Reason", "value": reason, "inline": True},
                                    {"name": "Error", "value": error_msg[:200], "inline": False}
                                ],
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            await session.post(webhook_url, json={"embeds": [embed]})
                            sys.stderr.write(f"📢 [DISCORD] Sent manual suspension alert for {member_handle}\n")
                            sys.stderr.flush()
                except Exception as notify_error:
                    sys.stderr.write(f"⚠️ [DISCORD] Failed to send suspension alert: {str(notify_error)}\n")
                
                return {"success": False, "message": f"Failed to remove roles (bot may need higher permissions): {error_msg}"}
        
        # Optionally add a "Suspended" role if configured
        if DISCORD_SUSPENDED_ROLE_ID:
            try:
                suspended_role = guild.get_role(int(DISCORD_SUSPENDED_ROLE_ID))
                if suspended_role:
                    await discord_member.add_roles(suspended_role, reason=reason)
                    sys.stderr.write(f"🏷️ [DISCORD] Added 'Suspended' role to {member_handle}\n")
                    sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"⚠️ [DISCORD] Failed to add suspended role: {str(e)}\n")
                sys.stderr.flush()
        
        # Send notification to Discord about the suspension
        try:
            webhook_url = os.environ.get('DISCORD_WEBHOOK_OFFICERS')
            if webhook_url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    embed = {
                        "title": "⚠️ Member Suspended - Unpaid Dues",
                        "description": f"**{member_handle}** has been suspended from Discord due to unpaid dues (Day 10+ overdue).",
                        "color": 15158332,  # Red color
                        "fields": [
                            {"name": "Reason", "value": reason, "inline": True},
                            {"name": "Roles Removed", "value": str(len(roles_to_remove)), "inline": True}
                        ],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await session.post(webhook_url, json={"embeds": [embed]})
        except Exception as e:
            sys.stderr.write(f"⚠️ [DISCORD] Failed to send suspension notification: {str(e)}\n")
            sys.stderr.flush()
        
        return {
            "success": True, 
            "message": f"Suspended {member_handle} - removed {len(roles_to_remove)} roles",
            "roles_removed": len(roles_to_remove)
        }
        
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error suspending member {member_handle}: {str(e)}\n")
        sys.stderr.flush()
        return {"success": False, "message": str(e)}


async def restore_discord_member(member_id: str) -> dict:
    """
    Restore a suspended member's Discord roles.
    
    Args:
        member_id: The member's ID in our system
        
    Returns:
        dict with success status and message
    """
    global discord_bot
    
    if not discord_bot:
        return {"success": False, "message": "Discord bot not running"}
    
    try:
        # Find the suspension record
        suspension = await db.discord_suspensions.find_one({"member_id": member_id})
        if not suspension:
            return {"success": False, "message": "No suspension record found"}
        
        discord_user_id = suspension.get("discord_user_id")
        previous_roles = suspension.get("previous_roles", [])
        member_handle = suspension.get("member_handle", "Unknown")
        
        # Get the guild and member
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"success": False, "message": f"Could not find guild {DISCORD_GUILD_ID}"}
        
        discord_member = guild.get_member(int(discord_user_id))
        if not discord_member:
            try:
                discord_member = await guild.fetch_member(int(discord_user_id))
            except:
                return {"success": False, "message": f"Could not find Discord member {discord_user_id}"}
        
        # Remove suspended role if configured
        if DISCORD_SUSPENDED_ROLE_ID:
            try:
                suspended_role = guild.get_role(int(DISCORD_SUSPENDED_ROLE_ID))
                if suspended_role and suspended_role in discord_member.roles:
                    await discord_member.remove_roles(suspended_role, reason="Dues paid - suspension lifted")
                    sys.stderr.write(f"🏷️ [DISCORD] Removed 'Unpaid Dues' role from {member_handle}\n")
                    sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"⚠️ [DISCORD] Failed to remove suspended role: {str(e)}\n")
        
        # Restore previous roles
        roles_restored = 0
        for role_data in previous_roles:
            try:
                role = guild.get_role(int(role_data["id"]))
                if role and role not in discord_member.roles:
                    await discord_member.add_roles(role, reason="Dues paid - roles restored")
                    roles_restored += 1
            except Exception as e:
                sys.stderr.write(f"⚠️ [DISCORD] Failed to restore role {role_data['name']}: {str(e)}\n")
        
        # Delete the suspension record
        await db.discord_suspensions.delete_one({"member_id": member_id})
        
        sys.stderr.write(f"✅ [DISCORD] Restored {member_handle}: {roles_restored} roles restored\n")
        sys.stderr.flush()
        
        # Send notification about restoration
        try:
            webhook_url = os.environ.get('DISCORD_WEBHOOK_OFFICERS')
            if webhook_url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    embed = {
                        "title": "✅ Member Restored - Dues Paid",
                        "description": f"**{member_handle}**'s Discord permissions have been restored after paying dues.",
                        "color": 5763719,  # Green color
                        "fields": [
                            {"name": "Roles Restored", "value": str(roles_restored), "inline": True}
                        ],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await session.post(webhook_url, json={"embeds": [embed]})
        except Exception as e:
            pass
        
        return {"success": True, "message": f"Restored {roles_restored} roles to {member_handle}"}
        
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error restoring member: {str(e)}\n")
        return {"success": False, "message": str(e)}


async def kick_discord_member(member_handle: str, member_id: str, reason: str = "Dues non-payment - 30 days overdue") -> dict:
    """
    Kick/remove a member from the Discord server for non-payment.
    
    Args:
        member_handle: The member's handle/nickname in the system
        member_id: The member's ID in our system
        reason: Reason for the kick
        
    Returns:
        dict with success status and message
    """
    global discord_bot
    
    if not discord_bot:
        return {"success": False, "message": "Discord bot not running"}
    
    if not DISCORD_GUILD_ID:
        return {"success": False, "message": "Discord guild ID not configured"}
    
    try:
        # First, try to find the Discord member by their linked discord_id
        linked_member = await db.discord_members.find_one({
            "$or": [
                {"linked_member_id": member_id},
                {"linked_handle": member_handle}
            ]
        })
        
        discord_user_id = None
        if linked_member:
            discord_user_id = linked_member.get("discord_id")
        
        if not discord_user_id:
            # Try to find by matching display name to handle
            sys.stderr.write(f"🔍 [DISCORD] Searching for member {member_handle} to kick...\n")
            sys.stderr.flush()
            
            guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
            if not guild:
                return {"success": False, "message": f"Could not find guild {DISCORD_GUILD_ID}"}
            
            # Search for member by nickname or username
            for discord_member in guild.members:
                display_name = discord_member.nick or discord_member.display_name or discord_member.name
                if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                    discord_user_id = str(discord_member.id)
                    sys.stderr.write(f"✅ [DISCORD] Matched {member_handle} to Discord user {display_name}\n")
                    sys.stderr.flush()
                    break
        
        if not discord_user_id:
            return {"success": False, "message": f"Could not find Discord user for member {member_handle}"}
        
        # Get the guild and member
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"success": False, "message": f"Could not find guild {DISCORD_GUILD_ID}"}
        
        discord_member = guild.get_member(int(discord_user_id))
        if not discord_member:
            try:
                discord_member = await guild.fetch_member(int(discord_user_id))
            except:
                return {"success": False, "message": f"Could not find Discord member {discord_user_id} in guild"}
        
        # Record the removal in database before kicking
        await db.discord_removals.insert_one({
            "member_id": member_id,
            "member_handle": member_handle,
            "discord_user_id": discord_user_id,
            "discord_display_name": discord_member.display_name,
            "removed_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        })
        
        # Kick the member from the server
        try:
            await discord_member.kick(reason=reason)
            sys.stderr.write(f"🚫 [DISCORD] Kicked {member_handle} from server: {reason}\n")
            sys.stderr.flush()
        except Exception as e:
            error_msg = str(e)
            sys.stderr.write(f"❌ [DISCORD] Failed to kick {member_handle}: {error_msg}\n")
            sys.stderr.flush()
            
            # Send notification to officers for manual action
            try:
                webhook_url = os.environ.get('DISCORD_WEBHOOK_OFFICERS')
                if webhook_url:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        embed = {
                            "title": "⚠️ Manual Action Required - Member Removal",
                            "description": f"**{member_handle}** needs to be removed from the server for 30-day dues non-payment, but the bot couldn't kick them automatically.\n\n**Please manually remove this member.**",
                            "color": 15105570,  # Orange
                            "fields": [
                                {"name": "Reason", "value": reason, "inline": True},
                                {"name": "Error", "value": error_msg[:200], "inline": False}
                            ],
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await session.post(webhook_url, json={"embeds": [embed]})
            except:
                pass
            
            return {"success": False, "message": f"Failed to kick member: {error_msg}"}
        
        # Send notification to Discord about the removal
        try:
            webhook_url = os.environ.get('DISCORD_WEBHOOK_OFFICERS')
            if webhook_url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    embed = {
                        "title": "🚫 Member Removed - 30 Day Non-Payment",
                        "description": f"**{member_handle}** has been kicked from the Discord server due to 30+ days of unpaid dues.",
                        "color": 10038562,  # Dark red
                        "fields": [
                            {"name": "Reason", "value": reason, "inline": True}
                        ],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    await session.post(webhook_url, json={"embeds": [embed]})
        except Exception as e:
            sys.stderr.write(f"⚠️ [DISCORD] Failed to send removal notification: {str(e)}\n")
        
        # Also mark member as removed in the members collection
        await db.members.update_one(
            {"id": member_id},
            {"$set": {
                "dues_removed": True,
                "dues_removed_at": datetime.now(timezone.utc).isoformat(),
                "dues_removed_reason": reason
            }}
        )
        
        return {
            "success": True, 
            "message": f"Kicked {member_handle} from Discord server",
        }
        
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error kicking member {member_handle}: {str(e)}\n")
        sys.stderr.flush()
        return {"success": False, "message": str(e)}


sys.stderr.write("✅ [INIT] Discord configuration loaded\n")
sys.stderr.flush()

# Configure logging (must be early so it's available throughout the module)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def send_email_smtp(to_email: str, subject: str, html_body: str, plain_body: str = None) -> dict:
    """
    Send email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML content of the email
        plain_body: Plain text fallback (optional)
        
    Returns:
        dict with success status and message
    """
    if not smtp_configured:
        logger.warning(f"SMTP not configured - email to {to_email} not sent")
        return {"success": False, "message": "SMTP not configured"}
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        
        # Add plain text part
        if plain_body:
            part1 = MIMEText(plain_body, 'plain')
            msg.attach(part1)
        
        # Add HTML part
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)
        
        # Send email
        if SMTP_USE_TLS:
            # Port 587 with STARTTLS
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
        else:
            # Port 465 with SSL
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return {"success": True, "message": f"Email sent to {to_email}"}
            
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return {"success": False, "message": str(e)}


def encrypt_data(data: str) -> str:
    """Encrypt data using AES-256 encryption"""
    if not data:
        return ""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using AES-256 encryption"""
    if not encrypted_data:
        return ""
    try:
        # Try to decrypt - if it fails, data might not be encrypted yet
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails, assume data is not encrypted and return as-is
        # This provides backward compatibility with existing unencrypted data
        logger.debug(f"Decryption skipped (data not encrypted): {str(e)[:50]}")
        return encrypted_data


def hash_for_duplicate_detection(data: str) -> str:
    """Create a deterministic hash for duplicate detection of encrypted fields"""
    if not data:
        return ""
    # Use SHA-256 hash for deterministic duplicate detection
    # Lowercase email before hashing for case-insensitive duplicate detection
    normalized_data = data.lower().strip()
    return hashlib.sha256(normalized_data.encode()).hexdigest()


# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'brothers-highway-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Email configuration
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')


# Helper functions for encrypting/decrypting member data
def encrypt_member_sensitive_data(member_data: dict) -> dict:
    """Encrypt sensitive member fields"""
    encrypted = member_data.copy()
    
    # Encrypt sensitive fields
    if 'email' in encrypted and encrypted['email']:
        encrypted['email'] = encrypt_data(encrypted['email'])
    if 'phone' in encrypted and encrypted['phone']:
        encrypted['phone'] = encrypt_data(encrypted['phone'])
    if 'address' in encrypted and encrypted['address']:
        encrypted['address'] = encrypt_data(encrypted['address'])
    
    return encrypted

def format_phone_number(phone: str) -> str:
    """Format phone number to (xxx) xxx-xxxx format"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Return original if not 10 digits
    return phone

def sanitize_for_regex(input_str: str) -> str:
    """
    Sanitize user input for safe use in MongoDB regex queries.
    Escapes all regex special characters to prevent ReDoS and injection attacks.
    """
    if not isinstance(input_str, str):
        return ""
    # Escape all regex metacharacters
    return re.escape(input_str)

def sanitize_string_input(input_val) -> str:
    """
    Ensure input is a plain string - prevents NoSQL injection via object injection.
    If input is not a string, convert it or return empty string.
    """
    if input_val is None:
        return ""
    if isinstance(input_val, str):
        return input_val
    # If someone tries to pass {"$ne": ""} or similar, convert to string representation
    return str(input_val)

def decrypt_member_sensitive_data(member_data: dict) -> dict:
    """Decrypt sensitive member fields"""
    decrypted = member_data.copy()
    
    # Decrypt sensitive fields
    if 'email' in decrypted and decrypted['email']:
        decrypted['email'] = decrypt_data(decrypted['email'])
    if 'phone' in decrypted and decrypted['phone']:
        decrypted_phone = decrypt_data(decrypted['phone'])
        decrypted['phone'] = format_phone_number(decrypted_phone)
    if 'address' in decrypted and decrypted['address']:
        decrypted['address'] = decrypt_data(decrypted['address'])
    
    return decrypted

def encrypt_support_message(message_data: dict) -> dict:
    """Encrypt support message content"""
    encrypted = message_data.copy()
    
    if 'email' in encrypted and encrypted['email']:
        encrypted['email'] = encrypt_data(encrypted['email'])
    if 'message' in encrypted and encrypted['message']:
        encrypted['message'] = encrypt_data(encrypted['message'])
    if 'reply_text' in encrypted and encrypted['reply_text']:
        encrypted['reply_text'] = encrypt_data(encrypted['reply_text'])
    
    return encrypted

def decrypt_support_message(message_data: dict) -> dict:
    """Decrypt support message content"""
    decrypted = message_data.copy()
    
    if 'email' in decrypted and decrypted['email']:
        decrypted['email'] = decrypt_data(decrypted['email'])
    if 'message' in decrypted and decrypted['message']:
        decrypted['message'] = decrypt_data(decrypted['message'])
    if 'reply_text' in decrypted and decrypted['reply_text']:
        decrypted['reply_text'] = decrypt_data(decrypted['reply_text'])
    
    return decrypted

# Frontend URL for invite links - use FRONTEND_URL env var, or derive from CORS_ORIGINS, or fallback
FRONTEND_URL = os.environ.get('FRONTEND_URL') or os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000').replace('/api', '')

# Email sending function
async def send_invite_email(email: str, token: str, role: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured")
        return False
    
    invite_link = f"{FRONTEND_URL}/accept-invite?token={token}"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Invitation to Brothers of the Highway Directory"
    message["From"] = "Brothers of the Highway <support@boh2158.org>"
    message["Reply-To"] = "support@boh2158.org"
    message["To"] = email
    
    text = f"""
    You've been invited to join the Brothers of the Highway Member Directory!
    
    Role: {role}
    
    Click the link below to set up your account:
    {invite_link}
    
    This invitation will expire in 7 days.
    """
    
    html = f"""
    <html>
      <body>
        <h2>You've been invited!</h2>
        <p>You've been invited to join the <strong>Brothers of the Highway Member Directory</strong></p>
        <p><strong>Role:</strong> {role}</p>
        <p>Click the button below to set up your account:</p>
        <p><a href="{invite_link}" style="background-color: #1e293b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Accept Invitation</a></p>
        <p>Or copy this link: {invite_link}</p>
        <p><em>This invitation will expire in 7 days.</em></p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD,
            use_tls=True
        )
        logger.info(f"Invite email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


# Generic email sending function for support replies
async def send_email(to_email: str, subject: str, body: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured")
        return False
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_EMAIL
    message["To"] = to_email
    
    # Create plain text and HTML versions
    html = f"""
    <html>
      <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #1e293b;">Brothers of the Highway TC Support</h2>
          <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            {body.replace(chr(10), '<br>')}
          </div>
          <p style="color: #64748b; font-size: 12px;">
            This is an automated message from Brothers of the Highway TC Member Directory Support.
          </p>
        </div>
      </body>
    </html>
    """
    
    part1 = MIMEText(body, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD,
            use_tls=True
        )
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# Support request model
class SupportRequest(BaseModel):
    name: str
    handle: Optional[str] = None
    contact_info: str
    reason: str

# Support email address
SUPPORT_EMAIL = "support@boh2158.org"


# Create the main app without a prefix
app = FastAPI()

# Security Headers Middleware - Addresses HSTS, CSP, Clickjacking, and Cookie security
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 1. Strict-Transport-Security (HSTS) - Forces HTTPS connections
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # 2. Content-Security-Policy (CSP) - Prevents XSS attacks
        # Allow self, inline scripts/styles (needed for React), and common CDNs
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'self'; "
            "form-action 'self'; "
            "base-uri 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # 3. X-Frame-Options - Prevents Clickjacking attacks
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # 4. X-Content-Type-Options - Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 5. X-XSS-Protection - Legacy XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 6. Referrer-Policy - Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 7. Permissions-Policy - Controls browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Health check endpoint for Kubernetes - must be at root level (not /api/health)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {"status": "healthy", "service": "backend"}

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Keep-alive ping endpoint
@api_router.get("/ping")
async def ping():
    """Simple ping endpoint for keep-alive requests"""
    return {"pong": True, "timestamp": datetime.now(timezone.utc).isoformat()}

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT token creation
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Add encryption layer to JWT token
    encrypted_token = encrypt_data(encoded_jwt)
    return encrypted_token

# Token verification
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        encrypted_token = credentials.credentials
        # Decrypt the token first
        token = decrypt_data(encrypted_token)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token format")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        chapter = payload.get("chapter")
        title = payload.get("title")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role, "chapter": chapter, "title": title}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin verification
async def verify_admin(current_user: dict = Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def verify_can_manage_users(current_user: dict = Depends(verify_token)):
    """Check if user can manage system users - permission based (no admin bypass)"""
    has_perm = await check_permission(current_user, "manage_system_users")
    if not has_perm:
        raise HTTPException(status_code=403, detail="You don't have permission to manage system users")
    return current_user

# Permission checking helpers
def is_national_admin(user: dict) -> bool:
    """Check if user is a National chapter admin"""
    return user.get("role") == "admin" and user.get("chapter") == "National"

def can_view_national_ad(user: dict) -> bool:
    """Check if user can view National chapter's Attendance & Dues.
    Only National Prez, VP, SEC, and T can see National A&D data.
    """
    user_chapter = user.get("chapter", "")
    user_title = user.get("title", "")
    user_role = user.get("role", "")
    
    # Must be in National chapter
    if user_chapter != "National":
        return False
    
    # Admins with National chapter can view
    if user_role == "admin":
        return True
    
    # Only specific National titles can view National A&D
    # Prez, VP, SEC, T (these are the executive officers)
    national_ad_titles = ["Prez", "VP", "SEC", "T"]
    return user_title in national_ad_titles

def can_view_prospects(user: dict) -> bool:
    """Check if user can view prospects list - DEPRECATED, use async version"""
    role = user.get("role", "")
    chapter = user.get("chapter", "")
    user_title = user.get("title", "")
    
    # PM (Prospect Master) can view prospects (read-only)
    if user_title == "PM":
        return True
    
    # National Admin and HA Admin can view prospects
    if role == "admin" and chapter in ["National", "HA"]:
        return True
    return False

async def can_view_prospects_async(user: dict) -> bool:
    """Check if user can view prospects list - permission based (no admin bypass)"""
    return await check_permission(user, "view_prospects")

async def can_edit_members_async(user: dict) -> bool:
    """Check if user can edit members - permission based (no admin bypass)"""
    return await check_permission(user, "edit_members")

async def can_view_reports_async(user: dict) -> bool:
    """Check if user can view reports - permission based (no admin bypass)"""
    return await check_permission(user, "view_reports")

async def can_manage_events_async(user: dict) -> bool:
    """Check if user can manage events - permission based (no admin bypass)"""
    return await check_permission(user, "manage_events")

def can_edit_member(user: dict, member_chapter: str) -> bool:
    """Check if user can edit a member based on their chapter and title restrictions"""
    role = user.get("role", "")
    user_chapter = user.get("chapter", "")
    user_title = user.get("title", "")
    
    if role != "admin":
        return False
    
    # PM (Prospect Master) cannot edit members - they have read-only access
    if user_title == "PM":
        return False
    
    # For National chapter members, only specific National officers can edit
    # Authorized titles: Prez, VP, S@A, ENF, CD, T, SEC
    NATIONAL_OFFICER_TITLES = ['Prez', 'VP', 'S@A', 'ENF', 'CD', 'T', 'SEC']
    
    if member_chapter == "National":
        # Only National officers with specific titles can edit National members
        return user_chapter == "National" and user_title in NATIONAL_OFFICER_TITLES
    
    # National admins can edit all non-National members
    if user_chapter == "National":
        return True
    
    # Chapter admins can only edit their own chapter
    return user_chapter == member_chapter

def can_edit_prospect(user: dict) -> bool:
    """Check if user can edit prospects"""
    role = user.get("role", "")
    chapter = user.get("chapter", "")
    user_title = user.get("title", "")
    
    # PM (Prospect Master) cannot edit prospects - they have read-only access
    if user_title == "PM":
        return False
    
    # Only National Admin and HA Admin can edit prospects
    return role == "admin" and chapter in ["National", "HA"]

def can_view_private_info(user: dict, data_chapter: str = None) -> bool:
    """Check if user can view private information"""
    role = user.get("role", "")
    user_chapter = user.get("chapter", "")
    
    # Prospects cannot view private info
    if role == "prospect":
        return False
    
    # National Admin can see all private info
    if role == "admin" and user_chapter == "National":
        return True
    
    # Other admins can see private info for their chapter only (unless they're HA for prospects)
    if role == "admin":
        return True  # Admins can view all unless specifically restricted
    
    # Members cannot see private info
    return False

def can_edit_fallen_member(user: dict) -> bool:
    """Check if user can edit Wall of Honor entries - only National Admin"""
    role = user.get("role", "")
    chapter = user.get("chapter", "")
    return role == "admin" and chapter == "National"

def can_manage_store(user: dict) -> bool:
    """Check if user can add/edit/delete store products - only National Prez, VP, and SEC"""
    role = user.get("role", "")
    chapter = user.get("chapter", "")
    title = user.get("title", "")
    
    # Must be an admin in National chapter with specific title
    if role != "admin" or chapter != "National":
        return False
    
    # Only Prez, VP, and SEC can manage store
    allowed_titles = ["Prez", "VP", "SEC"]
    return title in allowed_titles

def is_primary_store_admin(user: dict) -> bool:
    """Check if user is one of the 3 primary store admins (National Prez, VP, SEC)"""
    role = user.get("role", "")
    chapter = user.get("chapter", "")
    title = user.get("title", "")
    
    if role != "admin" or chapter != "National":
        return False
    
    allowed_titles = ["Prez", "VP", "SEC"]
    return title in allowed_titles

async def can_manage_store_async(user: dict) -> bool:
    """Check if user can manage store - permission based (no admin bypass)"""
    return await check_permission(user, "manage_store")

def filter_member_for_user(member: dict, user: dict) -> dict:
    """Filter member data based on user permissions"""
    role = user.get("role", "")
    user_chapter = user.get("chapter", "")
    
    # National Admin sees everything
    if role == "admin" and user_chapter == "National":
        return member
    
    # Create a copy to avoid modifying original
    filtered = dict(member)
    
    # Prospects can only see non-private info and cannot see names/emails
    if role == "prospect":
        if member.get("phone_private"):
            filtered["phone"] = "Private"
        if member.get("address_private"):
            filtered["address"] = "Private"
        # Prospects cannot see member names or emails
        filtered["name"] = "Private"
        filtered["email"] = "Private"
        return filtered
    
    # Members see everything except private fields
    if role == "member":
        if member.get("phone_private"):
            filtered["phone"] = "Private"
        if member.get("address_private"):
            filtered["address"] = "Private"
        if member.get("email_private"):
            filtered["email"] = "Private"
        return filtered
    
    # Chapter admins (non-National) see everything but respect privacy for other chapters
    if role == "admin":
        # Admins can see all data
        return filtered
    
    return filtered

def filter_prospect_for_user(prospect: dict, user: dict) -> dict:
    """Filter prospect data based on user permissions"""
    role = user.get("role", "")
    user_chapter = user.get("chapter", "")
    
    # National and HA Admin see everything
    if role == "admin" and user_chapter in ["National", "HA"]:
        return prospect
    
    # Prospects can only see their own data (handled at API level)
    # Other users shouldn't reach here as they don't have access
    return prospect

# Audit logging helper
async def log_activity(username: str, action: str, details: str, ip_address: str = None):
    """Log user activity to audit log"""
    try:
        log = AuditLog(
            username=username,
            action=action,
            details=details,
            ip_address=ip_address
        )
        doc = log.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.audit_logs.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails  # Required email field
    password_hash: str
    role: str = "member"  # admin, member, or prospect
    chapter: Optional[str] = None  # National, AD, HA, HS
    title: Optional[str] = None  # Prez, VP, S@A, Member, etc.
    permissions: dict = Field(default_factory=lambda: {
        "basic_info": True,        # Chapter, Title, Handle, Name
        "email": False,            # Email access
        "phone": False,            # Phone access
        "address": False,          # Address access
        "dues_tracking": False,    # View dues
        "meeting_attendance": False, # View/manage meeting attendance
        "admin_actions": False     # Add/Edit/Delete, Export CSV, User Management
    })
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails  # Required email field
    password: str
    role: str = "member"
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None  # Allow email updates - Changed from EmailStr to allow "Private"
    password: Optional[str] = None
    role: Optional[str] = None
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None  # Optional for backward compatibility
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    created_at: datetime

class Invite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = False

class InviteCreate(BaseModel):
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict

class InviteAccept(BaseModel):
    token: str
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    email: str
    code: str
    new_password: str

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    action: str  # e.g., "login", "member_create", "member_update", "user_delete"
    details: str  # Additional information about the action
    ip_address: Optional[str] = None

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    date: str  # ISO date string (YYYY-MM-DD)
    time: Optional[str] = None  # Time in HH:MM format
    location: Optional[str] = None
    chapter: Optional[str] = None  # National, AD, HA, HS, or None for all chapters
    title_filter: Optional[str] = None  # Prez, VP, etc., or None for all titles
    created_by: str  # Username of creator
    creator_chapter: Optional[str] = None  # Creator's chapter
    creator_title: Optional[str] = None  # Creator's title
    creator_handle: Optional[str] = None  # Creator's handle from members collection
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    discord_notifications_enabled: bool = True  # Allow Discord notifications for this event
    discord_channel: Optional[str] = "member-chat"  # Discord channel to post to
    notification_24h_sent: bool = False  # Track if 24h notification was sent
    notification_3h_sent: bool = False   # Track if 3h notification was sent
    # Repeat/Recurring fields
    repeat_type: Optional[str] = None  # none, daily, weekly, monthly, custom
    repeat_interval: Optional[int] = 1  # Every X days/weeks/months
    repeat_end_date: Optional[str] = None  # When to stop repeating (YYYY-MM-DD)
    repeat_count: Optional[int] = None  # Number of occurrences (alternative to end_date)
    repeat_days: Optional[List[int]] = None  # For weekly: [0,1,2,3,4,5,6] (Mon-Sun)
    parent_event_id: Optional[str] = None  # For recurring instances, link to parent
    is_recurring_instance: bool = False  # True if this is a generated instance

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str  # ISO date string (YYYY-MM-DD)
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: bool = True
    discord_channel: Optional[str] = "member-chat"  # Discord channel to post to
    # Repeat options
    repeat_type: Optional[str] = None  # none, daily, weekly, monthly, custom
    repeat_interval: Optional[int] = 1
    repeat_end_date: Optional[str] = None
    repeat_count: Optional[int] = None
    repeat_days: Optional[List[int]] = None  # For weekly custom: days of week

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: Optional[bool] = None
    discord_channel: Optional[str] = None  # Discord channel to post to

class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chapter: str  # National, AD, HA, HS
    title: str  # Prez, VP, S@A, ENF, SEC, T, CD, CC, CCLC, MD, PM
    handle: str
    name: str
    email: Optional[str] = None  # BOH Email - Optional, can be empty
    personal_email: Optional[str] = None  # Personal Email
    phone: str
    address: str
    dob: Optional[str] = None  # Date of Birth (YYYY-MM-DD format)
    join_date: Optional[str] = None  # Anniversary Date (MM/YYYY format)
    experience_start: Optional[str] = None  # Trucking experience start date (MM/YYYY format)
    phone_private: bool = False  # If True, only admins can see phone
    address_private: bool = False  # If True, only admins can see address
    email_private: bool = False  # If True, only National members and chapter officers (Prez, VP, S@A, Enf, SEC) can see email
    personal_email_private: bool = False  # If True, personal email is hidden from non-privileged users
    name_private: bool = False  # If True, only National members and chapter officers can see real name
    # Military Service
    military_service: bool = False  # If True, member has served in military
    military_branch: Optional[str] = None  # Army, Navy, Air Force, Marines, Coast Guard, Space Force, National Guard
    # First Responder Service
    is_first_responder: bool = False  # If True, member has served as Police, Fire, or EMS
    # Dues Exemption
    non_dues_paying: bool = False  # If True, member is exempt from dues (honorary members, etc.)
    actions: list = Field(default_factory=list)  # Merit, Promotion, Disciplinary actions
    # Format: [{"type": "merit|promotion|disciplinary", "date": "YYYY-MM-DD", "description": "...", "added_by": "username", "added_at": "ISO timestamp"}]
    dues: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
        # Format: {"2025": [{"status": "paid|unpaid|late", "note": "reason if late"}, ...], "2024": [...]}
    })
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    can_edit: Optional[bool] = None  # Permission flag for frontend
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberCreate(BaseModel):
    chapter: str
    title: str
    handle: str
    name: str
    email: Optional[str] = None  # BOH Email - Optional, can be empty
    personal_email: Optional[str] = None  # Personal Email
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    experience_start: Optional[str] = None  # Trucking experience start date (MM/YYYY format)
    phone_private: bool = False
    address_private: bool = False
    email_private: bool = False
    personal_email_private: bool = False
    name_private: bool = False
    # Military Service
    military_service: bool = False
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: bool = False
    # Dues Exemption
    non_dues_paying: bool = False
    dues: Optional[dict] = None

class MemberUpdate(BaseModel):
    chapter: Optional[str] = None
    title: Optional[str] = None
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None  # BOH Email
    personal_email: Optional[str] = None  # Personal Email
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    experience_start: Optional[str] = None  # Trucking experience start date (MM/YYYY format)
    phone_private: Optional[bool] = None
    address_private: Optional[bool] = None
    email_private: Optional[bool] = None
    personal_email_private: Optional[bool] = None
    name_private: Optional[bool] = None
    # Military Service
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: Optional[bool] = None
    # Dues Exemption
    non_dues_paying: Optional[bool] = None
    dues: Optional[dict] = None
    meeting_attendance: Optional[dict] = None

# Hangaround models (Entry level - minimal info required)
class Hangaround(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): []
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    actions: list = Field(default_factory=list)  # Merit, Promotion, Disciplinary actions
    can_edit: Optional[bool] = None  # Permission flag for frontend
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HangaroundCreate(BaseModel):
    handle: str
    name: str

class HangaroundUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    meeting_attendance: Optional[dict] = None

# Prospect models (Promoted from Hangaround - full info required)
class Prospect(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None  # Date of Birth (YYYY-MM-DD format)
    join_date: Optional[str] = None  # Anniversary Date (MM/YYYY format)
    # Military Service
    military_service: bool = False  # If True, prospect has served in military
    military_branch: Optional[str] = None  # Army, Navy, Air Force, Marines, Coast Guard, Space Force, National Guard
    # First Responder Service
    is_first_responder: bool = False  # If True, prospect has served as Police, Fire, or EMS
    actions: list = Field(default_factory=list)  # Merit, Promotion, Disciplinary actions
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): []
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    can_edit: Optional[bool] = None  # Permission flag for frontend
    promoted_from_hangaround: Optional[str] = None  # ID of original hangaround record
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProspectCreate(BaseModel):
    handle: str
    name: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    # Military Service
    military_service: bool = False
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: bool = False
    meeting_attendance: Optional[dict] = None

class ProspectUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None  # Changed from EmailStr to allow "Private" for hidden emails
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    # Military Service
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: Optional[bool] = None
    meeting_attendance: Optional[dict] = None

# Model for promoting Hangaround to Prospect
class HangaroundToProspectPromotion(BaseModel):
    email: str
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False

# Fallen Member (Wall of Honor) models
class FallenMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    handle: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None  # YYYY-MM-DD format
    join_date: Optional[str] = None  # When they joined the club
    tribute: Optional[str] = None  # Memorial message
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class FallenMemberCreate(BaseModel):
    name: str
    handle: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None
    join_date: Optional[str] = None
    tribute: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False

class FallenMemberUpdate(BaseModel):
    name: Optional[str] = None
    handle: Optional[str] = None
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None
    join_date: Optional[str] = None
    tribute: Optional[str] = None
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    is_first_responder: Optional[bool] = None

# Meeting models for flexible meeting tracking
class Meeting(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str  # YYYY-MM-DD format
    name: Optional[str] = None  # e.g., "Weekly Meeting", "Special Meeting"
    year: str = Field(default_factory=lambda: str(datetime.now(timezone.utc).year))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class MeetingCreate(BaseModel):
    date: str
    name: Optional[str] = None

class MeetingAttendanceRecord(BaseModel):
    meeting_id: str
    member_id: str
    status: int = 0  # 0=absent, 1=present, 2=excused
    note: Optional[str] = None

class PrivateMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message: str
    timestamp: str
    read: bool = False
    archived_by: List[str] = Field(default_factory=list)  # List of users who archived this conversation

class PrivateMessageCreate(BaseModel):
    recipient: str
    message: str


class SupportMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    message: str
    timestamp: str
    status: str = "open"  # open, closed
    reply_text: Optional[str] = None
    replied_at: Optional[str] = None

class SupportMessageCreate(BaseModel):
    name: str
    email: str
    message: str

class SupportReply(BaseModel):
    reply_text: str

# Discord Analytics Models
class DiscordMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_id: str  # Discord user ID
    username: str    # Discord username
    display_name: Optional[str] = None  # Discord display name/nickname
    avatar_url: Optional[str] = None
    joined_at: Optional[datetime] = None  # When they joined the Discord server
    roles: List[str] = Field(default_factory=list)  # Discord role IDs
    is_bot: bool = False
    member_id: Optional[str] = None  # Link to our member database
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DiscordVoiceActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_user_id: str
    channel_id: str
    channel_name: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None  # Calculated when they leave
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

class DiscordTextActivity(BaseModel):
    model_config = ConfigDict(extra="ignore") 
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_user_id: str
    channel_id: str
    channel_name: str
    message_count: int = 1
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DiscordAnalytics(BaseModel):
    total_members: int
    voice_stats: dict
    text_stats: dict
    top_voice_users: List[dict]
    top_text_users: List[dict]
    daily_activity: List[dict]

# ==================== STORE MODELS ====================

class ProductVariation(BaseModel):
    """A size/variation of a product"""
    id: str
    name: str  # e.g., "S", "M", "L", "XL", "2XL"
    price: float
    square_variation_id: Optional[str] = None
    inventory_count: int = 0
    sold_out: bool = False

class StoreProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: float  # Base/starting price in dollars
    category: str  # "merchandise" or "dues"
    image_url: Optional[str] = None
    square_catalog_id: Optional[str] = None
    inventory_count: int = 0  # Total across all variations
    is_active: bool = True
    member_price: Optional[float] = None  # Discounted price for members
    variations: List[dict] = []  # List of size/variation options
    has_variations: bool = False  # True if product has multiple sizes
    allows_customization: bool = False  # True if handle/name can be added
    show_in_supporter_store: bool = True  # True if available in public supporter store
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StoreProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    inventory_count: int = 0
    member_price: Optional[float] = None
    show_in_supporter_store: bool = True
    allows_customization: bool = False

class StoreProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    inventory_count: Optional[int] = None
    is_active: Optional[bool] = None
    member_price: Optional[float] = None
    show_in_supporter_store: Optional[bool] = None
    allows_customization: Optional[bool] = None

class CartItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None
    variation_id: Optional[str] = None  # Selected size/variation ID
    variation_name: Optional[str] = None  # e.g., "L", "XL"
    customization: Optional[str] = None  # Handle/name to print on item

class ShoppingCart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StoreOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    items: List[CartItem]
    subtotal: float
    tax: float = 0.0
    total: float
    status: str = "pending"  # pending, paid, shipped, completed, cancelled, refunded
    square_order_id: Optional[str] = None
    square_payment_id: Optional[str] = None
    payment_method: str = "card"
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentRequest(BaseModel):
    source_id: str  # Payment token from Square Web Payments SDK
    amount_cents: int
    order_id: str
    customer_email: Optional[str] = None

# ==================== STORE ADMIN MODELS ====================

class StoreAdmin(BaseModel):
    """Delegated store admin - users granted store management permissions by primary admins"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str  # Username of the user being granted access
    granted_by: str  # Username of the primary admin who granted access
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StoreAdminCreate(BaseModel):
    username: str

# ==================== END STORE MODELS ====================

# Initialize default admin user
@app.on_event("startup")
async def create_default_admin():
    try:
        import sys
        print("🔧 [STARTUP] Checking for default admin user...", file=sys.stderr, flush=True)
        admin_exists = await db.users.find_one({"username": "admin"})
        if not admin_exists:
            print("🔧 [STARTUP] Creating default admin user...", file=sys.stderr, flush=True)
            admin_user = User(
                username="admin",
                email="admin@brothersofthehighway.com",  # Required email field
                password_hash=hash_password("admin123"),
                role="admin",
                permissions={
                    "basic_info": True,
                    "email": True,
                    "phone": True,
                    "address": True,
                    "dues_tracking": True,
                    "meeting_attendance": True,  # All admins need access to all features
                    "admin_actions": True
                }
            )
            doc = admin_user.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.users.insert_one(doc)
            logger.info("Default admin user created: username=admin, password=admin123")
            print("✅ [STARTUP] Default admin user created", file=sys.stderr, flush=True)
        else:
            print("✅ [STARTUP] Default admin user already exists", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"❌ [STARTUP] Error in create_default_admin: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

# New Year Initialization - runs on January 1st at 12:01 AM CST (06:01 UTC)
def run_new_year_initialization():
    """Initialize new year for dues and meeting attendance for all members and prospects"""
    import asyncio
    
    async def init_new_year():
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import pytz
            
            # Get current year in CST
            cst = pytz.timezone('America/Chicago')
            now_cst = datetime.now(pytz.UTC).astimezone(cst)
            new_year = str(now_cst.year)
            
            client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
            database = client[os.environ.get('DB_NAME', 'member_management')]
            
            # Initialize new year for all members
            members = await database.members.find({}).to_list(None)
            for member in members:
                dues = member.get('dues', {})
                meeting_attendance = member.get('meeting_attendance', {})
                
                # Only add new year if it doesn't exist
                if new_year not in dues:
                    dues[new_year] = [{"status": "unpaid", "note": ""} for _ in range(12)]
                
                if new_year not in meeting_attendance:
                    meeting_attendance[new_year] = [{"status": 0, "note": ""} for _ in range(24)]
                
                await database.members.update_one(
                    {"id": member["id"]},
                    {"$set": {"dues": dues, "meeting_attendance": meeting_attendance}}
                )
            
            # Initialize new year for all prospects
            prospects = await database.prospects.find({}).to_list(None)
            for prospect in prospects:
                meeting_attendance = prospect.get('meeting_attendance', {})
                
                # Convert old format if needed
                if 'year' in meeting_attendance and 'meetings' in meeting_attendance:
                    old_year = str(meeting_attendance.get('year'))
                    old_meetings = meeting_attendance.get('meetings', [])
                    meeting_attendance = {old_year: old_meetings}
                
                if new_year not in meeting_attendance:
                    meeting_attendance[new_year] = [{"status": 0, "note": ""} for _ in range(24)]
                
                await database.prospects.update_one(
                    {"id": prospect["id"]},
                    {"$set": {"meeting_attendance": meeting_attendance}}
                )
            
            client.close()
            print(f"✅ [NEW YEAR] Initialized {new_year} for {len(members)} members and {len(prospects)} prospects", file=sys.stderr, flush=True)
            
        except Exception as e:
            print(f"❌ [NEW YEAR] Error initializing new year: {str(e)}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_new_year())
    finally:
        loop.close()

@app.on_event("startup")
async def start_scheduler():
    """Start the APScheduler for Discord event notifications and birthday checks"""
    import sys
    global scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        sys.stderr.write("🔧 [SCHEDULER] Initializing Discord notification system...\n")
        sys.stderr.flush()
        
        scheduler = BackgroundScheduler()
        
        # Event notifications - check every 30 minutes
        scheduler.add_job(
            run_notification_check,
            'interval',
            minutes=30,
            id='event_notifications',
            replace_existing=True
        )
        
        # Birthday notifications - run daily at 9:00 AM CST (15:00 UTC)
        scheduler.add_job(
            run_birthday_check,
            CronTrigger(hour=15, minute=0),  # 9:00 AM CST = 15:00 UTC
            id='birthday_notifications',
            replace_existing=True
        )
        
        # Anniversary notifications - run on 1st of each month at 9:00 AM CST (15:00 UTC)
        scheduler.add_job(
            run_anniversary_check,
            CronTrigger(day=1, hour=15, minute=0),  # 1st of month, 9:00 AM CST = 15:00 UTC
            id='anniversary_notifications',
            replace_existing=True
        )
        
        # New Year initialization - run on January 1st at 12:01 AM CST (06:01 UTC)
        scheduler.add_job(
            run_new_year_initialization,
            CronTrigger(month=1, day=1, hour=6, minute=1),  # Jan 1st, 12:01 AM CST = 06:01 UTC
            id='new_year_initialization',
            replace_existing=True
        )
        
        # Dues reminder check - run daily at 12:30 AM CST (06:30 UTC)
        scheduler.add_job(
            run_dues_reminder_job,
            CronTrigger(hour=6, minute=30),  # 12:30 AM CST = 06:30 UTC
            id='dues_reminder_check',
            replace_existing=True
        )
        
        # Square dues sync - run twice daily at 12:01 AM CST (06:01 UTC) and 12:01 PM CST (18:01 UTC)
        scheduler.add_job(
            run_square_sync_job,
            CronTrigger(hour=6, minute=1),  # 12:01 AM CST = 06:01 UTC
            id='square_sync_morning',
            replace_existing=True
        )
        scheduler.add_job(
            run_square_sync_job,
            CronTrigger(hour=18, minute=1),  # 12:01 PM CST = 18:01 UTC
            id='square_sync_afternoon',
            replace_existing=True
        )
        
        scheduler.start()
        sys.stderr.write("✅ [SCHEDULER] Discord notification system started:\n")
        sys.stderr.write("   📅 Event notifications: every 30 minutes\n")
        sys.stderr.write("   🎂 Birthday notifications: daily at 9:00 AM CST\n")
        sys.stderr.write("   🎉 Anniversary notifications: 1st of month at 9:00 AM CST\n")
        sys.stderr.write("   🎆 New Year initialization: Jan 1st at 12:01 AM CST\n")
        sys.stderr.write("   💰 Dues reminder check: daily at 12:30 AM CST\n")
        sys.stderr.write("   💳 Square dues sync: daily at 12:01 AM & 12:01 PM CST\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"⚠️ [SCHEDULER] Failed to start scheduler (app will continue without it): {str(e)}\n")
        sys.stderr.flush()
        # Don't crash the application if scheduler fails to start - this is non-critical functionality
        import traceback
        traceback.print_exc(file=sys.stderr)
        scheduler = None

@app.on_event("startup")
async def start_discord_activity_bot():
    """Start Discord activity tracking bot"""
    if DISCORD_BOT_TOKEN:
        asyncio.create_task(start_discord_bot())

@app.on_event("startup")
async def seed_dues_email_templates():
    """Initialize default dues reminder email templates if they don't exist"""
    try:
        existing = await db.dues_email_templates.count_documents({})
        if existing == 0:
            default_templates = [
                {
                    "id": "dues_reminder_day3",
                    "name": "Day 3 - Courtesy Reminder",
                    "day_trigger": 3,
                    "subject": "Friendly Reminder: Monthly Dues Payment",
                    "body": """Hello {{member_name}},

This is a friendly reminder that your monthly dues payment for {{month}} {{year}} has not yet been received.

As a courtesy, we wanted to reach out early to ensure you have time to make your payment. If you've already sent your payment, please disregard this message.

You can make your payment through the Member Store or contact your chapter Secretary for assistance.

Thank you for being a valued member of Brothers of the Highway.

Ride Safe,
Brothers of the Highway""",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "dues_reminder_day8",
                    "name": "Day 8 - Second Reminder",
                    "day_trigger": 8,
                    "subject": "Second Notice: Dues Payment Overdue",
                    "body": """Hello {{member_name}},

This is a second reminder that your dues payment for {{month}} {{year}} is now 8 days overdue.

Please submit your payment as soon as possible to avoid any interruption to your membership privileges.

If you're experiencing financial difficulties or have questions about your payment, please reach out to your chapter Secretary immediately.

Payment options:
- Member Store (Square payment)
- Contact your chapter SEC

Thank you for your prompt attention to this matter.

Ride Safe,
Brothers of the Highway""",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "dues_reminder_day10",
                    "name": "Day 10 - Final Notice & Suspension",
                    "day_trigger": 10,
                    "subject": "URGENT: Dues Overdue - Membership Privileges Suspended",
                    "body": """Hello {{member_name}},

IMPORTANT NOTICE

Your dues payment for {{month}} {{year}} is now 10 days overdue. As per our bylaws, your membership privileges have been temporarily suspended.

This means you will not be able to:
- Access member-only features
- Attend chapter meetings with voting rights
- Participate in official club activities

To restore your membership privileges, please submit your payment immediately through the Member Store or contact your chapter Secretary.

If you have any questions or concerns, please reach out to National leadership.

Ride Safe,
Brothers of the Highway""",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "dues_reminder_day30",
                    "name": "Day 30 - Removal Notice",
                    "day_trigger": 30,
                    "subject": "FINAL NOTICE: Membership Terminated Due to Non-Payment",
                    "body": """Hello {{member_name}},

FINAL NOTICE - MEMBERSHIP TERMINATED

Your dues payment for {{month}} {{year}} is now 30 days overdue. As per our bylaws, your membership has been terminated and you have been removed from the Brothers of the Highway Discord server.

This action was taken after multiple payment reminders were sent without response.

If you wish to rejoin the organization in the future, you will need to:
1. Contact National leadership to discuss reinstatement
2. Pay all outstanding dues
3. Go through the re-application process

We're sorry to see you go. If there were extenuating circumstances that prevented payment, please reach out to discuss options.

Ride Safe,
Brothers of the Highway""",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
            
            await db.dues_email_templates.insert_many(default_templates)
            print("✅ [STARTUP] Dues email templates seeded successfully", file=sys.stderr, flush=True)
        else:
            print(f"✅ [STARTUP] Dues email templates already exist ({existing} templates)", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"⚠️ [STARTUP] Failed to seed dues email templates: {str(e)}", file=sys.stderr, flush=True)

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = await db.users.find_one({"username": login_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_chapter = user.get("chapter")
    user_title = user.get("title")
    
    token = create_access_token({
        "sub": user["username"], 
        "role": user["role"],
        "chapter": user_chapter,  # Include chapter for privacy/access control
        "title": user_title  # Include title for email privacy access control
    })
    
    # Log login activity
    await log_activity(
        username=user["username"],
        action="login",
        details="User logged in successfully"
    )
    
    # Get dynamic permissions from role_permissions collection
    dynamic_permissions = await get_title_permissions(user_title or "", user_chapter or "")
    
    # Merge with static user permissions
    static_permissions = user.get("permissions", {
        "basic_info": True,
        "email": False,
        "phone": False,
        "address": False,
        "dues_tracking": False,
        "admin_actions": False
    })
    
    # Combine both permission sets
    all_permissions = {**static_permissions, **dynamic_permissions}
    
    # Trigger Square catalog sync in background (non-blocking)
    # Only runs if user is a store admin (doesn't matter, sync is idempotent)
    try:
        asyncio.create_task(trigger_catalog_sync_background())
        logger.info(f"Auto-sync triggered on login for user: {user['username']}")
    except Exception as e:
        logger.warning(f"Failed to trigger auto-sync: {str(e)}")
    
    return LoginResponse(
        token=token, 
        username=user["username"], 
        role=user["role"],
        chapter=user_chapter,
        title=user_title,
        permissions=all_permissions
    )

@api_router.get("/auth/verify")
async def verify(current_user: dict = Depends(verify_token)):
    # Get full user details including permissions
    user = await db.users.find_one({"username": current_user["username"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get dynamic permissions from role_permissions collection
    user_title = user.get("title", "")
    user_chapter = current_user.get("chapter", "")
    dynamic_permissions = await get_title_permissions(user_title, user_chapter)
    
    # Merge with static user permissions
    static_permissions = user.get("permissions", {
        "basic_info": True,
        "email": False,
        "phone": False,
        "address": False,
        "dues_tracking": False,
        "admin_actions": False
    })
    
    # Combine both permission sets
    all_permissions = {**static_permissions, **dynamic_permissions}
    
    return {
        "username": user["username"],
        "role": user["role"],
        "chapter": current_user.get("chapter"),  # Include chapter from JWT token
        "title": user.get("title", ""),  # Include title for permission checks
        "permissions": all_permissions
    }

# Password Reset - Request reset code
@api_router.post("/auth/request-reset")
async def request_password_reset(request: PasswordResetRequest):
    """Send a password reset code to the user's email"""
    import random
    
    # Find user by email OR username (case-insensitive)
    user = await db.users.find_one({"email": request.email.lower()})
    if not user:
        # Try finding by username (case-insensitive)
        user = await db.users.find_one({"username": {"$regex": f"^{request.email}$", "$options": "i"}})
    
    if not user:
        logger.info(f"Password reset requested for non-existent email/username: {request.email}")
        raise HTTPException(status_code=404, detail="No account found with this email or username")
    
    # Get the user's email
    user_email = user.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="This account does not have an email address on file. Please contact support.")
    
    # Generate 6-digit reset code
    reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Store reset code with expiration (15 minutes)
    expiration = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    await db.password_resets.update_one(
        {"email": user_email.lower()},
        {
            "$set": {
                "email": user_email.lower(),
                "username": user.get("username"),
                "code": reset_code,
                "expires_at": expiration,
                "attempts": 0
            }
        },
        upsert=True
    )
    
    # Send reset code email
    if SMTP_EMAIL and SMTP_PASSWORD:
        try:
            subject = "Brothers of the Highway - Password Reset Code"
            body = f"""
Password Reset Request

Hi {user.get('username', 'Member')},

Your password reset code is: {reset_code}

This code will expire in 15 minutes.

If you did not request this password reset, please ignore this email.

- Brothers of the Highway Support
            """.strip()
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"Brothers of the Highway <{SMTP_EMAIL}>"
            message["To"] = user_email
            
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # HTML version
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #1e293b; color: #f1f5f9; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #334155; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #60a5fa; margin-bottom: 20px;">Password Reset Request</h2>
                    <p>Hi {user.get('username', 'Member')},</p>
                    <p>Your password reset code is:</p>
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #60a5fa;">{reset_code}</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px;">This code will expire in 15 minutes.</p>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 20px;">If you did not request this password reset, please ignore this email.</p>
                    <hr style="border-color: #475569; margin: 20px 0;">
                    <p style="color: #64748b; font-size: 12px;">Brothers of the Highway Support</p>
                </div>
            </body>
            </html>
            """
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_EMAIL,
                password=SMTP_PASSWORD,
                use_tls=True
            )
            
            # Return masked email for privacy
            email_parts = user_email.split('@')
            masked_email = email_parts[0][:2] + '***@' + email_parts[1] if len(email_parts) == 2 else user_email
            logger.info(f"Password reset code sent to {user_email} for user {user.get('username')}")
            return {"message": f"Reset code sent to {masked_email}"}
        except Exception as e:
            logger.error(f"Failed to send reset email: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again.")
    else:
        raise HTTPException(status_code=500, detail="Email service not configured")

# Password Reset - Confirm and set new password
@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Verify reset code and set new password"""
    
    # Find the reset record by email or username
    reset_record = await db.password_resets.find_one({"email": request.email.lower()})
    if not reset_record:
        # Try finding by username stored in reset record
        reset_record = await db.password_resets.find_one({"username": {"$regex": f"^{request.email}$", "$options": "i"}})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="No reset request found. Please request a new code.")
    
    # Get the actual email from the reset record
    reset_email = reset_record.get("email")
    
    # Check if code has expired (handle both timezone-aware and naive datetimes)
    expires_at = reset_record.get("expires_at")
    if expires_at:
        # Make the comparison work regardless of timezone awareness
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            await db.password_resets.delete_one({"email": reset_email})
            raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")
    
    # Check attempt count (max 5 attempts)
    if reset_record.get("attempts", 0) >= 5:
        await db.password_resets.delete_one({"email": reset_email})
        raise HTTPException(status_code=400, detail="Too many failed attempts. Please request a new code.")
    
    # Verify the code
    if reset_record.get("code") != request.code:
        # Increment attempt count
        await db.password_resets.update_one(
            {"email": reset_email},
            {"$inc": {"attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Find the user and update password
    user = await db.users.find_one({"email": reset_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash the new password
    new_password_hash = hash_password(request.new_password)
    
    # Update user's password
    await db.users.update_one(
        {"email": reset_email},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # Delete the reset record
    await db.password_resets.delete_one({"email": reset_email})
    
    # Log the password reset
    await log_activity(
        username=user["username"],
        action="password_reset",
        details=f"Password reset via email verification"
    )
    
    logger.info(f"Password reset successful for user: {user['username']}")
    
    return {"message": "Password reset successfully"}

# Support request endpoint (no auth required - accessible from login page)
@api_router.post("/support/request")
async def submit_support_request(request: SupportRequest):
    """Submit a support request from the login page"""
    try:
        # Determine if contact info is an email
        contact_is_email = "@" in request.contact_info
        reply_to_email = request.contact_info if contact_is_email else None
        
        # Build the email body
        body = f"""
New Support Request

From: {request.name}
Handle: {request.handle or 'Not provided'}
Contact: {request.contact_info}

Reason for Request:
{request.reason}

---
{"Reply directly to this email to respond to " + request.name if contact_is_email else "Note: Contact provided is not an email. Please use: " + request.contact_info}
        """.strip()
        
        # Send email to support
        if SMTP_EMAIL and SMTP_PASSWORD:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Support Request from {request.name}"
            message["From"] = SMTP_EMAIL
            message["To"] = SUPPORT_EMAIL
            
            # Set Reply-To so clicking "Reply" goes to the requester
            if reply_to_email:
                message["Reply-To"] = reply_to_email
            
            # Build HTML with clear reply instructions
            reply_instruction = f'''
                <div style="background-color: #dbeafe; padding: 12px; border-radius: 6px; margin-top: 16px; border-left: 4px solid #3b82f6;">
                    <p style="margin: 0; color: #1e40af; font-size: 14px;">
                        <strong>💡 To respond:</strong> {"Simply reply to this email - it will go directly to " + request.name + " at " + request.contact_info if contact_is_email else "Contact " + request.name + " at: <strong>" + request.contact_info + "</strong> (phone number provided)"}
                    </p>
                </div>
            ''' if True else ''
            
            html = f"""
            <html>
              <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                  <h2 style="color: #1e293b;">New Support Request</h2>
                  <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>From:</strong> {request.name}</p>
                    <p><strong>Handle:</strong> {request.handle or 'Not provided'}</p>
                    <p><strong>Contact:</strong> {request.contact_info}</p>
                    <hr style="border: 1px solid #e2e8f0; margin: 16px 0;">
                    <p><strong>Reason for Request:</strong></p>
                    <p style="white-space: pre-wrap;">{request.reason}</p>
                  </div>
                  {reply_instruction}
                </div>
              </body>
            </html>
            """
            
            part1 = MIMEText(body, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_EMAIL,
                password=SMTP_PASSWORD,
                use_tls=True
            )
            logger.info(f"Support request sent from {request.name}")
            return {"success": True, "message": "Support request submitted successfully"}
        else:
            # Log the request if email isn't configured
            logger.warning(f"SMTP not configured. Support request from {request.name}: {request.reason}")
            return {"success": True, "message": "Support request received (email notification pending)"}
            
    except Exception as e:
        logger.error(f"Failed to submit support request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit support request")

# Member endpoints
@api_router.get("/members", response_model=List[Member])
async def get_members(current_user: dict = Depends(verify_token)):
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    user_role = current_user.get('role')
    user_chapter = current_user.get('chapter')
    user_title = current_user.get('title', '')
    
    # Officer titles that can see their chapter's private info (PM is excluded)
    officer_titles = ['Prez', 'VP', 'S@A', 'Enf', 'SEC', 'CD', 'T', 'ENF']
    
    # Check permission from database for full member info view
    has_full_view_permission = await check_permission(current_user, "view_full_member_info")
    
    # Check user permissions
    is_national_member = user_chapter == 'National'
    is_officer = user_title in officer_titles and user_title != 'PM'
    
    # Debug logging
    print(f"[PRIVACY DEBUG] User: chapter={user_chapter}, title={user_title}, is_national={is_national_member}, is_officer={is_officer}, has_full_view={has_full_view_permission}")
    
    for i, member in enumerate(members):
        # Decrypt sensitive data
        members[i] = decrypt_member_sensitive_data(member)
        member_chapter = members[i].get('chapter', '')
        
        # Users without view_full_member_info: limited view - only Chapter, Title, Name, Email, Phone
        if not has_full_view_permission and user_role != 'admin':
            limited_member = {
                "id": members[i].get("id"),
                "chapter": members[i].get("chapter"),
                "title": members[i].get("title"),
                "handle": members[i].get("handle"),
                "name": members[i].get("name"),
                "email": members[i].get("email"),
                "phone": members[i].get("phone"),
                # Set defaults for required fields
                "address": "",
                "dob": "",
                "join_date": "",
                "experience_start": "",
                "phone_private": False,
                "address_private": False,
                "email_private": False,
                "name_private": False,
                "military_service": False,
                "military_branch": "",
                "is_first_responder": False,
                "dues": {},
                "meeting_attendance": {},
                "actions": [],
                "can_edit": False,
                "created_at": members[i].get("created_at"),
                "updated_at": members[i].get("updated_at")
            }
            members[i] = limited_member
            continue
        
        # Prospect users: hide names and emails
        if user_role == 'prospect':
            members[i]['name'] = 'Private'
            members[i]['email'] = 'Private'
            if members[i].get('phone_private', False):
                members[i]['phone'] = 'Private'
            if members[i].get('address_private', False):
                members[i]['address'] = 'Private'
            continue
        
        # Determine if user can see this member's private info
        # - National members can see ALL private info
        # - Chapter officers (except PM) can see their OWN chapter's private info
        can_see_member_private = is_national_member or (is_officer and user_chapter == member_chapter)
        
        # Apply privacy settings
        if not can_see_member_private:
            # Apply name privacy
            if members[i].get('name_private', False):
                members[i]['name'] = 'Private'
            
            # Apply email privacy
            if members[i].get('email_private', False):
                members[i]['email'] = 'Private'
            
            # Apply phone privacy
            if members[i].get('phone_private', False):
                members[i]['phone'] = 'Private'
            
            # Apply address privacy
            if members[i].get('address_private', False):
                members[i]['address'] = 'Private'
        
        # Add can_edit flag for frontend to show/hide edit buttons
        members[i]['can_edit'] = can_edit_member(current_user, member_chapter)
        
        if isinstance(members[i].get('created_at'), str):
            members[i]['created_at'] = datetime.fromisoformat(members[i]['created_at'])
        if isinstance(members[i].get('updated_at'), str):
            members[i]['updated_at'] = datetime.fromisoformat(members[i]['updated_at'])
    return members

@api_router.get("/members/{member_id}", response_model=Member)
async def get_member(member_id: str, current_user: dict = Depends(verify_token)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Decrypt sensitive data
    member = decrypt_member_sensitive_data(member)
    
    user_role = current_user.get('role')
    user_chapter = current_user.get('chapter')
    user_title = current_user.get('title', '')
    
    # NOTE: National members are viewable by all users
    # Action buttons are restricted via can_edit_member function
    is_national_member = user_chapter == 'National'
    member_chapter = member.get('chapter', '')
    
    # Officer titles that can see their chapter's private info (PM excluded)
    officer_titles = ['Prez', 'VP', 'S@A', 'Enf', 'SEC', 'CD', 'T', 'ENF']
    
    # Check if user is an officer (not PM)
    is_officer = user_title in officer_titles and user_title != 'PM'
    
    # Determine if user can see this member's private info
    # - National members can see ALL private info
    # - Chapter officers (except PM) can see their OWN chapter's private info
    can_see_member_private = is_national_member or (is_officer and user_chapter == member_chapter)
    
    # Hide names for prospect users
    if user_role == 'prospect':
        member['name'] = 'Hidden'
    
    # Apply privacy settings if user cannot see private info
    if not can_see_member_private:
        if member.get('name_private', False):
            member['name'] = 'Private'
        if member.get('email_private', False):
            member['email'] = 'Private'
        if member.get('phone_private', False):
            member['phone'] = 'Private'
        if member.get('address_private', False):
            member['address'] = 'Private'
    
    if isinstance(member.get('created_at'), str):
        member['created_at'] = datetime.fromisoformat(member['created_at'])
    if isinstance(member.get('updated_at'), str):
        member['updated_at'] = datetime.fromisoformat(member['updated_at'])
    return member

@api_router.post("/members", response_model=Member, status_code=201)
async def create_member(member_data: MemberCreate, current_user: dict = Depends(verify_token)):
    """Create a new member - permission based"""
    # Check permission
    if not await can_edit_members_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to create members")
    
    # Check for duplicate handle
    existing_by_handle = await db.members.find_one({"handle": member_data.handle})
    if existing_by_handle:
        raise HTTPException(
            status_code=400, 
            detail=f"A member with handle '{member_data.handle}' already exists"
        )
    
    # Check for duplicate email using hash comparison
    if member_data.email:
        email_hash = hash_for_duplicate_detection(member_data.email)
        existing_by_email_hash = await db.members.find_one({"email_hash": email_hash})
        
        if existing_by_email_hash:
            raise HTTPException(
                status_code=400,
                detail=f"A member with email '{member_data.email}' already exists"
            )
    
    # Filter out None values to allow default factories to work
    member_dict = {k: v for k, v in member_data.model_dump().items() if v is not None}
    member = Member(**member_dict)
    doc = member.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    # Add email hash for duplicate detection before encryption
    if doc.get('email'):
        doc['email_hash'] = hash_for_duplicate_detection(doc['email'])
    
    # Encrypt sensitive data before storing
    doc = encrypt_member_sensitive_data(doc)
    
    await db.members.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_create",
        details=f"Created member: {member.name} ({member.handle})"
    )
    
    return member

@api_router.put("/members/{member_id}", response_model=Member)
async def update_member(member_id: str, member_data: MemberUpdate, current_user: dict = Depends(verify_token)):
    """Update a member - permission based"""
    # Check permission
    if not await can_edit_members_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to edit members")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member (based on chapter)
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only edit members in your own chapter")
    
    # Check for duplicate handle if being updated
    if member_data.handle and member_data.handle != member.get('handle'):
        existing_by_handle = await db.members.find_one({
            "handle": member_data.handle,
            "id": {"$ne": member_id}  # Exclude current member
        })
        if existing_by_handle:
            raise HTTPException(
                status_code=400,
                detail=f"A member with handle '{member_data.handle}' already exists"
            )
    
    # Check for duplicate email using hash comparison if being updated
    if member_data.email:
        current_email_hash = member.get('email_hash', '')
        new_email_hash = hash_for_duplicate_detection(member_data.email)
        
        if new_email_hash != current_email_hash:
            existing_by_email_hash = await db.members.find_one({
                "email_hash": new_email_hash,
                "id": {"$ne": member_id}
            })
            
            if existing_by_email_hash:
                raise HTTPException(
                    status_code=400,
                    detail=f"A member with email '{member_data.email}' already exists"
                )
    
    update_data = {k: v for k, v in member_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Add email hash if email is being updated
    if update_data.get('email'):
        update_data['email_hash'] = hash_for_duplicate_detection(update_data['email'])
    
    # Encrypt sensitive fields in update data
    update_data = encrypt_member_sensitive_data(update_data)
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    # Decrypt for response
    updated_member = decrypt_member_sensitive_data(updated_member)
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_update",
        details=f"Updated member: {updated_member.get('name', 'Unknown')} ({updated_member.get('handle', 'Unknown')})"
    )
    
    return updated_member

@api_router.get("/admin/available-years")
async def get_available_years(current_user: dict = Depends(verify_admin)):
    """Get all available years from dues and meeting attendance data"""
    years = set()
    current_year = datetime.now(timezone.utc).year
    years.add(str(current_year))
    
    # Get years from members
    members = await db.members.find({}, {"_id": 0, "dues": 1, "meeting_attendance": 1}).to_list(None)
    for member in members:
        if member.get('dues'):
            years.update(member['dues'].keys())
        if member.get('meeting_attendance'):
            years.update(member['meeting_attendance'].keys())
    
    # Get years from prospects
    prospects = await db.prospects.find({}, {"_id": 0, "meeting_attendance": 1}).to_list(None)
    for prospect in prospects:
        ma = prospect.get('meeting_attendance', {})
        if isinstance(ma, dict):
            if 'year' in ma:  # Old format
                years.add(str(ma['year']))
            else:  # New format
                years.update(ma.keys())
    
    return {"years": sorted(list(years), reverse=True)}

@api_router.post("/admin/initialize-year/{year}")
async def initialize_year(year: int, current_user: dict = Depends(verify_admin)):
    """Manually initialize a specific year for all members and prospects"""
    year_str = str(year)
    members_updated = 0
    prospects_updated = 0
    
    # Initialize for all members
    members = await db.members.find({}).to_list(None)
    for member in members:
        dues = member.get('dues', {})
        meeting_attendance = member.get('meeting_attendance', {})
        updated = False
        
        if year_str not in dues:
            dues[year_str] = [{"status": "unpaid", "note": ""} for _ in range(12)]
            updated = True
        
        if year_str not in meeting_attendance:
            meeting_attendance[year_str] = [{"status": 0, "note": ""} for _ in range(24)]
            updated = True
        
        if updated:
            await db.members.update_one(
                {"id": member["id"]},
                {"$set": {"dues": dues, "meeting_attendance": meeting_attendance}}
            )
            members_updated += 1
    
    # Initialize for all prospects
    prospects = await db.prospects.find({}).to_list(None)
    for prospect in prospects:
        meeting_attendance = prospect.get('meeting_attendance', {})
        
        # Convert old format if needed
        if 'year' in meeting_attendance and 'meetings' in meeting_attendance:
            old_year = str(meeting_attendance.get('year'))
            old_meetings = meeting_attendance.get('meetings', [])
            meeting_attendance = {old_year: old_meetings}
        
        if year_str not in meeting_attendance:
            meeting_attendance[year_str] = [{"status": 0, "note": ""} for _ in range(24)]
            await db.prospects.update_one(
                {"id": prospect["id"]},
                {"$set": {"meeting_attendance": meeting_attendance}}
            )
            prospects_updated += 1
    
    # Log activity
    await log_activity(
        current_user["username"],
        "initialize_year",
        f"Initialized year {year} for {members_updated} members and {prospects_updated} prospects"
    )
    
    return {
        "message": f"Year {year} initialized successfully",
        "members_updated": members_updated,
        "prospects_updated": prospects_updated
    }

# ==================== MEETING MANAGEMENT ====================

@api_router.get("/meetings")
async def get_meetings(
    year: Optional[int] = None,
    current_user: dict = Depends(verify_token)
):
    """Get all meetings, optionally filtered by year"""
    query = {}
    if year:
        query["year"] = str(year)
    else:
        # Default to current year
        query["year"] = str(datetime.now(timezone.utc).year)
    
    meetings = await db.meetings.find(query, {"_id": 0}).to_list(1000)
    # Sort by date descending (most recent first)
    meetings.sort(key=lambda x: x.get('date', ''), reverse=True)
    return meetings

@api_router.post("/meetings", response_model=Meeting, status_code=201)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: dict = Depends(verify_admin)
):
    """Create a new meeting (admin only)"""
    # Parse the date to get the year
    try:
        meeting_date = datetime.strptime(meeting.date, "%Y-%m-%d")
        year = str(meeting_date.year)
    except:
        year = str(datetime.now(timezone.utc).year)
    
    meeting_dict = meeting.model_dump()
    meeting_dict["id"] = str(uuid.uuid4())
    meeting_dict["year"] = year
    meeting_dict["created_at"] = datetime.now(timezone.utc)
    meeting_dict["created_by"] = current_user["username"]
    
    await db.meetings.insert_one(meeting_dict)
    
    # Log activity
    await log_activity(
        current_user["username"],
        "create_meeting",
        f"Created meeting on {meeting.date}"
    )
    
    return Meeting(**meeting_dict)

@api_router.delete("/meetings/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user: dict = Depends(verify_admin)
):
    """Delete a meeting (admin only)"""
    meeting = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    await db.meetings.delete_one({"id": meeting_id})
    
    # Also delete all attendance records for this meeting
    await db.meeting_attendance.delete_many({"meeting_id": meeting_id})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "delete_meeting",
        f"Deleted meeting on {meeting.get('date')}"
    )
    
    return {"message": "Meeting deleted successfully"}

@api_router.get("/meetings/{meeting_id}/attendance")
async def get_meeting_attendance(
    meeting_id: str,
    current_user: dict = Depends(verify_token)
):
    """Get attendance records for a specific meeting"""
    meeting = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get all members
    members = await db.members.find({}, {"_id": 0, "id": 1, "name": 1, "handle": 1, "chapter": 1}).to_list(1000)
    
    # Get attendance records for this meeting
    attendance_records = await db.meeting_attendance.find(
        {"meeting_id": meeting_id}, 
        {"_id": 0}
    ).to_list(1000)
    
    # Create a map of member_id -> attendance
    attendance_map = {r["member_id"]: r for r in attendance_records}
    
    # Build response with all members and their attendance
    result = []
    for member in members:
        attendance = attendance_map.get(member["id"], {"status": 0, "note": ""})
        result.append({
            "member_id": member["id"],
            "name": member["name"],
            "handle": member["handle"],
            "chapter": member.get("chapter", ""),
            "status": attendance.get("status", 0),
            "note": attendance.get("note", "")
        })
    
    # Sort by chapter then handle
    result.sort(key=lambda x: (x.get("chapter", ""), x.get("handle", "")))
    
    return {
        "meeting": meeting,
        "attendance": result
    }

@api_router.post("/meetings/{meeting_id}/attendance")
async def update_meeting_attendance(
    meeting_id: str,
    attendance: List[MeetingAttendanceRecord],
    current_user: dict = Depends(verify_admin)
):
    """Update attendance for a meeting (admin only)"""
    meeting = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Update or insert attendance records
    for record in attendance:
        await db.meeting_attendance.update_one(
            {"meeting_id": meeting_id, "member_id": record.member_id},
            {"$set": {
                "meeting_id": meeting_id,
                "member_id": record.member_id,
                "status": record.status,
                "note": record.note or ""
            }},
            upsert=True
        )
    
    return {"message": "Attendance updated successfully"}

@api_router.put("/meetings/{meeting_id}/attendance/{member_id}")
async def update_single_attendance(
    meeting_id: str,
    member_id: str,
    status: int,
    note: Optional[str] = "",
    current_user: dict = Depends(verify_admin)
):
    """Update attendance for a single member at a meeting"""
    meeting = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    await db.meeting_attendance.update_one(
        {"meeting_id": meeting_id, "member_id": member_id},
        {"$set": {
            "meeting_id": meeting_id,
            "member_id": member_id,
            "status": status,
            "note": note or ""
        }},
        upsert=True
    )
    
    return {"message": "Attendance updated"}

@api_router.get("/members/{member_id}/attendance-summary")
async def get_member_attendance_summary(
    member_id: str,
    year: Optional[int] = None,
    current_user: dict = Depends(verify_token)
):
    """Get attendance summary for a specific member"""
    target_year = str(year) if year else str(datetime.now(timezone.utc).year)
    
    # Get all meetings for the year
    meetings = await db.meetings.find({"year": target_year}, {"_id": 0}).to_list(1000)
    meeting_ids = [m["id"] for m in meetings]
    
    # Get attendance records for this member
    attendance_records = await db.meeting_attendance.find(
        {"member_id": member_id, "meeting_id": {"$in": meeting_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    # Create map
    attendance_map = {r["meeting_id"]: r for r in attendance_records}
    
    # Calculate summary
    total = len(meetings)
    present = sum(1 for m in meetings if attendance_map.get(m["id"], {}).get("status") == 1)
    excused = sum(1 for m in meetings if attendance_map.get(m["id"], {}).get("status") == 2)
    absent = total - present - excused
    
    # Build detailed list
    details = []
    for meeting in sorted(meetings, key=lambda x: x.get("date", ""), reverse=True):
        att = attendance_map.get(meeting["id"], {"status": 0, "note": ""})
        details.append({
            "meeting_id": meeting["id"],
            "date": meeting["date"],
            "name": meeting.get("name"),
            "status": att.get("status", 0),
            "note": att.get("note", "")
        })
    
    return {
        "year": target_year,
        "total_meetings": total,
        "present": present,
        "excused": excused,
        "absent": absent,
        "attendance_rate": round(present / total * 100, 1) if total > 0 else 0,
        "details": details
    }

# ==================== END MEETING MANAGEMENT ====================

async def cancel_member_square_subscription(member_id: str, member_handle: str):
    """Cancel a member's Square subscription if they have one"""
    result = {
        "had_subscription": False,
        "cancelled": False,
        "subscription_id": None,
        "error": None
    }
    
    if not square_client:
        result["error"] = "Square client not configured"
        return result
    
    try:
        # First check if member has a linked subscription in our database
        subscription_link = await db.member_subscriptions.find_one({"member_id": member_id})
        
        if not subscription_link:
            # Try to find by member handle in subscription links
            subscription_link = await db.member_subscriptions.find_one({"member_handle": member_handle})
        
        if not subscription_link:
            return result  # No linked subscription
        
        square_customer_id = subscription_link.get("square_customer_id")
        if not square_customer_id:
            return result
        
        # Search for active subscriptions for this customer
        search_result = square_client.subscriptions.search(
            query={
                "filter": {
                    "customer_ids": [square_customer_id],
                    "location_ids": [SQUARE_LOCATION_ID]
                }
            }
        )
        
        subscriptions = search_result.subscriptions or []
        # Filter to ACTIVE subscriptions that are NOT scheduled for cancellation
        active_subscriptions = [s for s in subscriptions if s.status == "ACTIVE" and not s.canceled_date]
        
        if not active_subscriptions:
            # No active subscription found, just clean up the link
            await db.member_subscriptions.delete_one({"square_customer_id": square_customer_id})
            return result
        
        result["had_subscription"] = True
        
        # Cancel each active subscription
        for sub in active_subscriptions:
            try:
                cancel_result = square_client.subscriptions.cancel(
                    subscription_id=sub.id
                )
                
                if cancel_result.subscription:
                    result["cancelled"] = True
                    result["subscription_id"] = sub.id
                    logger.info(f"Cancelled Square subscription {sub.id} for member {member_handle}")
                else:
                    result["error"] = f"Failed to cancel subscription {sub.id}"
                    if cancel_result.errors:
                        result["error"] += f": {cancel_result.errors}"
            except Exception as e:
                result["error"] = f"Error cancelling subscription {sub.id}: {str(e)}"
                logger.error(f"Error cancelling Square subscription: {e}")
        
        # Clean up the subscription link in our database
        await db.member_subscriptions.delete_one({"square_customer_id": square_customer_id})
        
    except Exception as e:
        result["error"] = f"Error processing subscription cancellation: {str(e)}"
        logger.error(f"Error in cancel_member_square_subscription: {e}")
    
    return result


@api_router.delete("/members/{member_id}")
async def delete_member(
    member_id: str, 
    reason: str,
    kick_from_discord: bool = False,
    cancel_square_subscription: bool = True,
    current_user: dict = Depends(verify_token)
):
    """Archive a member with deletion reason, optionally kick from Discord and cancel Square subscription"""
    # Check permission
    if not await can_edit_members_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to delete members")
    
    # Get member info before archiving
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can delete this member (based on chapter)
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only archive members in your own chapter")
    
    # Kick from Discord if requested
    discord_result = None
    if kick_from_discord:
        try:
            discord_result = await kick_discord_member(
                member_handle=member.get("handle", "Unknown"),
                member_id=member_id,
                reason=f"Member deleted: {reason}"
            )
        except Exception as e:
            discord_result = {"success": False, "message": str(e)}
    
    # Cancel Square subscription if requested
    square_result = None
    if cancel_square_subscription:
        try:
            square_result = await cancel_member_square_subscription(
                member_id=member_id,
                member_handle=member.get("handle", "Unknown")
            )
        except Exception as e:
            square_result = {"cancelled": False, "error": str(e)}
    
    # Create archived record
    archived_member = {
        **member,
        "deletion_reason": reason,
        "deleted_by": current_user["username"],
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "kicked_from_discord": kick_from_discord,
        "discord_kick_result": discord_result,
        "square_subscription_cancelled": square_result.get("cancelled") if square_result else False,
        "square_cancellation_result": square_result
    }
    
    # Move to archived collection
    await db.archived_members.insert_one(archived_member)
    
    # Remove from active members
    await db.members.delete_one({"id": member_id})
    
    # Clean up any Discord suspension records
    await db.discord_suspensions.delete_one({"member_id": member_id})
    
    # Log activity
    discord_note = " (kicked from Discord)" if kick_from_discord and discord_result and discord_result.get("success") else ""
    square_note = " (Square subscription cancelled)" if square_result and square_result.get("cancelled") else ""
    await log_activity(
        username=current_user["username"],
        action="member_archive",
        details=f"Archived member: {member.get('name', 'Unknown')} ({member.get('handle', 'Unknown')}) - Reason: {reason}{discord_note}{square_note}"
    )
    
    return {
        "message": "Member archived successfully",
        "discord_kicked": kick_from_discord,
        "discord_result": discord_result,
        "square_subscription_cancelled": square_result.get("cancelled") if square_result else False,
        "square_result": square_result
    }

# Dues tracking endpoint
@api_router.put("/members/{member_id}/dues")
async def update_member_dues(member_id: str, dues_data: dict, current_user: dict = Depends(verify_token)):
    # Check if user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only edit dues for members in your own chapter")
    
    update_data = {
        'dues': dues_data,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    return updated_member

# Meeting attendance tracking endpoint
@api_router.put("/members/{member_id}/attendance")
async def update_member_attendance(member_id: str, attendance_data: dict, current_user: dict = Depends(verify_token)):
    # Check if user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only edit attendance for members in your own chapter")
    
    update_data = {
        'meeting_attendance': attendance_data,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    return updated_member

# CSV Export endpoint
@api_router.get("/members/export/csv")
async def export_members_csv(current_user: dict = Depends(verify_token)):
    # Get user permissions
    user = await db.users.find_one({"username": current_user["username"]}, {"_id": 0, "role": 1, "permissions": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = user.get("permissions", {})
    is_admin = user.get("role") == "admin"
    user_chapter = current_user.get('chapter')
    is_national_member = user_chapter == 'National'
    
    # Check if user has admin_actions permission or any data permission (required to export)
    has_data_permission = any([
        permissions.get("basic_info"),
        permissions.get("email"),
        permissions.get("phone"),
        permissions.get("address"),
        permissions.get("dues_tracking"),
        permissions.get("meeting_attendance")
    ])
    
    if not is_admin and not permissions.get("admin_actions") and not has_data_permission:
        raise HTTPException(status_code=403, detail="Data access permission required to export CSV")
    
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    
    # NOTE: National members are included in export for all users
    # Action restrictions are handled separately in the UI
    
    # Decrypt sensitive data for all members
    decrypted_members = [decrypt_member_sensitive_data(member) for member in members]
    
    # Define sort order
    CHAPTERS = ["National", "AD", "HA", "HS"]
    TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM"]
    
    # Sort members by chapter and title
    def sort_key(member):
        chapter_index = CHAPTERS.index(member.get('chapter', '')) if member.get('chapter', '') in CHAPTERS else 999
        title_index = TITLES.index(member.get('title', '')) if member.get('title', '') in TITLES else 999
        return (chapter_index, title_index)
    
    sorted_members = sorted(decrypted_members, key=sort_key)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Build header based on permissions with better formatting
    header = []
    if is_admin or permissions.get("basic_info"):
        header.extend(['Chapter', 'Title', 'Member Handle', 'Name'])
    if is_admin or permissions.get("email"):
        header.append('Email Address')
        header.append('Personal Email')
    if is_admin or permissions.get("phone"):
        header.append('Phone Number')
    if is_admin or permissions.get("address"):
        header.append('Mailing Address')
    
    # Always include Military and First Responder fields for admin
    if is_admin:
        header.extend(['Military Service', 'Military Branch', 'First Responder'])
    
    # Add Trucking Experience for basic_info permission
    if is_admin or permissions.get("basic_info"):
        header.append('Trucking Experience Start')
        header.append('Years of Experience')
    
    if is_admin or permissions.get("dues_tracking"):
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        header.append('Dues Year')
        header.extend([f'Dues - {month}' for month in month_names])
    if is_admin or permissions.get("meeting_attendance"):
        # New flexible meeting format - just add summary columns
        # Individual meeting dates vary per member, so we show summary stats
        header.append('Attendance Year')
        header.append('Total Meetings')
        header.append('Present')
        header.append('Excused')
        header.append('Absent')
        header.append('Attendance %')
        header.append('Meeting Details')
    
    writer.writerow(header)
    
    # Write data based on permissions
    for member in sorted_members:
        row = []
        
        if is_admin or permissions.get("basic_info"):
            row.extend([
                member.get('chapter', ''),
                member.get('title', ''),
                member.get('handle', ''),
                member.get('name', '')
            ])
        
        if is_admin or permissions.get("email"):
            row.append(member.get('email', ''))
            row.append(member.get('personal_email', '') or '')
        
        if is_admin or permissions.get("phone"):
            row.append(member.get('phone', ''))
        
        if is_admin or permissions.get("address"):
            row.append(member.get('address', ''))
        
        # Always include Military and First Responder fields for admin
        if is_admin:
            row.append('Yes' if member.get('military_service', False) else 'No')
            row.append(member.get('military_branch', '') or '')
            row.append('Yes' if member.get('is_first_responder', False) else 'No')
        
        # Add Trucking Experience for basic_info permission
        if is_admin or permissions.get("basic_info"):
            exp_start = member.get('experience_start', '')
            row.append(exp_start or '')
            # Calculate years of experience
            years_exp = ''
            if exp_start:
                try:
                    from datetime import datetime
                    parts = exp_start.split('/')
                    if len(parts) == 2:
                        month, year = int(parts[0]), int(parts[1])
                        start_date = datetime(year, month, 1)
                        now = datetime.now()
                        years = (now.year - start_date.year) + (now.month - start_date.month) / 12
                        years_exp = f"{years:.1f}"
                except:
                    years_exp = ''
            row.append(years_exp)
        
        if is_admin or permissions.get("dues_tracking"):
            dues = member.get('dues', {})
            
            # Handle new format (dict with years as keys) and old format (has 'year' key)
            if dues and isinstance(dues, dict):
                if 'year' in dues:
                    # Old format - convert
                    old_year = str(dues.get('year', ''))
                    old_months = dues.get('months', [False] * 12)
                    dues = {old_year: old_months}
                
                # Get most recent year
                years = sorted(dues.keys(), reverse=True)
                if years:
                    export_year = years[0]
                    dues_months = dues.get(export_year, [{"status": "unpaid", "note": ""} for _ in range(12)])
                else:
                    export_year = str(datetime.now(timezone.utc).year)
                    dues_months = [{"status": "unpaid", "note": ""} for _ in range(12)]
            else:
                export_year = str(datetime.now(timezone.utc).year)
                dues_months = [{"status": "unpaid", "note": ""} for _ in range(12)]
            
            # Convert dues to status strings with notes
            dues_data = []
            for month_due in dues_months:
                if isinstance(month_due, dict):
                    status = month_due.get('status', 'unpaid')
                    note = month_due.get('note', '')
                    if status == 'late' and note:
                        dues_data.append(f'Late ({note})')
                    else:
                        dues_data.append(status.capitalize())
                elif isinstance(month_due, bool):
                    # Handle old boolean format for backward compatibility
                    dues_data.append('Paid' if month_due else 'Unpaid')
                else:
                    dues_data.append('Unpaid')
            
            row.append(export_year)
            row.extend(dues_data)
        
        if is_admin or permissions.get("meeting_attendance"):
            attendance = member.get('meeting_attendance', {})
            current_year_str = str(datetime.now(timezone.utc).year)
            
            # Handle new format (dict with years as keys containing arrays of {date, status, note})
            # and old format (has 'year' key with 'meetings' array of 24 items)
            meetings = []
            export_year = current_year_str
            
            if attendance and isinstance(attendance, dict):
                if 'year' in attendance:
                    # Old format - convert
                    export_year = str(attendance.get('year', current_year_str))
                    old_meetings = attendance.get('meetings', [])
                    # Old format was 24 indexed meetings, convert to dated format
                    for idx, m in enumerate(old_meetings):
                        if isinstance(m, dict) and (m.get('status', 0) != 0 or m.get('note')):
                            month_idx = idx // 2
                            week_num = (idx % 2) + 1
                            approx_date = f"{export_year}-{month_idx+1:02d}-{week_num * 7:02d}"
                            meetings.append({
                                'date': approx_date,
                                'status': m.get('status', 0),
                                'note': m.get('note', '')
                            })
                        elif isinstance(m, int) and m != 0:
                            month_idx = idx // 2
                            week_num = (idx % 2) + 1
                            approx_date = f"{export_year}-{month_idx+1:02d}-{week_num * 7:02d}"
                            meetings.append({
                                'date': approx_date,
                                'status': m,
                                'note': ''
                            })
                else:
                    # New format - years as keys with array of {date, status, note}
                    years = sorted([k for k in attendance.keys() if k.isdigit()], reverse=True)
                    if years:
                        export_year = years[0]
                        meetings = attendance.get(export_year, [])
            
            # Calculate stats
            total = len(meetings)
            present = sum(1 for m in meetings if m.get('status') == 1)
            excused = sum(1 for m in meetings if m.get('status') == 2)
            absent = sum(1 for m in meetings if m.get('status') == 0)
            attendance_pct = f"{(present / total * 100):.1f}%" if total > 0 else "N/A"
            
            # Build meeting details string
            details_parts = []
            for m in sorted(meetings, key=lambda x: x.get('date', '')):
                date_str = m.get('date', '')
                if date_str:
                    # Format date as MM/DD
                    try:
                        parts = date_str.split('-')
                        if len(parts) == 3:
                            date_str = f"{parts[1]}/{parts[2]}"
                    except:
                        pass
                status = m.get('status', 0)
                status_char = 'P' if status == 1 else ('E' if status == 2 else 'A')
                note = m.get('note', '')
                if note:
                    details_parts.append(f"{date_str}:{status_char}({note})")
                else:
                    details_parts.append(f"{date_str}:{status_char}")
            
            details_str = "; ".join(details_parts) if details_parts else "No meetings"
            
            row.append(export_year)
            row.append(str(total))
            row.append(str(present))
            row.append(str(excused))
            row.append(str(absent))
            row.append(attendance_pct)
            row.append(details_str)
        
        writer.writerow(row)
    
    output.seek(0)
    # Add UTF-8 BOM for proper encoding detection in Excel/Google Sheets
    csv_content = '\ufeff' + output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=members.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


# Quarterly Report Endpoints
@api_router.get("/reports/attendance/quarterly")
async def get_attendance_quarterly_report(
    year: int = None,
    quarter: str = None,
    chapter: str = None,
    current_user: dict = Depends(verify_token)
):
    """Get quarterly or yearly meeting attendance report by chapter"""
    # Check permission
    if not await can_view_reports_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view reports")
    
    if year is None:
        year = datetime.now(timezone.utc).year
    
    # Determine months based on quarter or full year
    if quarter == "all" or quarter is None:
        months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        period_name = f"Full Year {year}"
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    else:
        quarter_int = int(quarter)
        quarter_months = {
            1: (1, 2, 3),
            2: (4, 5, 6),
            3: (7, 8, 9),
            4: (10, 11, 12)
        }
        months = quarter_months.get(quarter_int, (1, 2, 3))
        period_name = f"Q{quarter_int} {year}"
        start_date = f"{year}-{months[0]:02d}-01"
        end_date = f"{year}-{months[2]:02d}-31"
    
    # Build query
    query = {}
    if chapter and chapter != "All":
        query["chapter"] = chapter
    
    members = await db.members.find(query, {"_id": 0}).to_list(10000)
    decrypted_members = [decrypt_member_sensitive_data(m) for m in members]
    
    # Sort by chapter and title
    CHAPTERS = ["National", "AD", "HA", "HS"]
    TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "Member", "Honorary"]
    
    def sort_key(member):
        ch_idx = CHAPTERS.index(member.get('chapter', '')) if member.get('chapter', '') in CHAPTERS else 999
        ti_idx = TITLES.index(member.get('title', '')) if member.get('title', '') in TITLES else 999
        return (ch_idx, ti_idx)
    
    sorted_members = sorted(decrypted_members, key=sort_key)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    header = ["Chapter", "Title", "Handle", "Name"]
    
    # Add columns for each meeting in the period
    for month_idx in months:
        header.append(f"{month_names[month_idx-1]} Meetings")
    header.extend(["Total Meetings", "Present", "Excused", "Absent", "Attendance %"])
    
    writer.writerow([f"Meeting Attendance Report - {period_name}" + (f" - {chapter}" if chapter and chapter != "All" else " - All Chapters")])
    writer.writerow([])
    writer.writerow(header)
    
    # Data rows
    for member in sorted_members:
        attendance = member.get("meeting_attendance", {})
        year_str = str(year)
        
        # Handle both old and new format
        if 'year' in attendance:
            meetings = attendance.get('meetings', [])
        else:
            meetings = attendance.get(year_str, [])
        
        # Filter meetings for this quarter
        quarter_meetings = []
        for m in meetings:
            if isinstance(m, dict) and m.get('date'):
                meeting_date = m['date']
                meeting_month = int(meeting_date.split('-')[1])
                if meeting_month in months:
                    quarter_meetings.append(m)
        
        # Calculate stats
        total = len(quarter_meetings)
        present = sum(1 for m in quarter_meetings if m.get('status') == 1)
        excused = sum(1 for m in quarter_meetings if m.get('status') == 2)
        absent = sum(1 for m in quarter_meetings if m.get('status') == 0)
        attendance_pct = f"{(present / total * 100):.1f}%" if total > 0 else "N/A"
        
        # Count meetings per month
        month_counts = []
        for month_idx in months:
            month_meetings = [m for m in quarter_meetings if int(m['date'].split('-')[1]) == month_idx]
            month_counts.append(str(len(month_meetings)))
        
        row = [
            member.get('chapter', ''),
            member.get('title', ''),
            member.get('handle', ''),
            member.get('name', ''),
        ]
        row.extend(month_counts)
        row.extend([str(total), str(present), str(excused), str(absent), attendance_pct])
        
        writer.writerow(row)
    
    output.seek(0)
    csv_content = '\ufeff' + output.getvalue()
    
    if quarter == "all" or quarter is None:
        filename = f"attendance_{year}"
    else:
        filename = f"attendance_Q{quarter}_{year}"
    if chapter and chapter != "All":
        filename += f"_{chapter}"
    filename += ".csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@api_router.get("/reports/dues/quarterly")
async def get_dues_quarterly_report(
    year: int = None,
    quarter: str = None,
    chapter: str = None,
    current_user: dict = Depends(verify_token)
):
    """Get quarterly or yearly dues report by chapter"""
    # Check permission
    if not await can_view_reports_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view reports")
    
    if year is None:
        year = datetime.now(timezone.utc).year
    
    # Determine months based on quarter or full year
    if quarter == "all" or quarter is None:
        months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
        period_name = f"Full Year {year}"
    else:
        quarter_int = int(quarter)
        quarter_months = {
            1: (1, 2, 3),
            2: (4, 5, 6),
            3: (7, 8, 9),
            4: (10, 11, 12)
        }
        months = quarter_months.get(quarter_int, (1, 2, 3))
        period_name = f"Q{quarter_int} {year}"
    
    # Build query
    query = {}
    if chapter and chapter != "All":
        query["chapter"] = chapter
    
    members = await db.members.find(query, {"_id": 0}).to_list(10000)
    decrypted_members = [decrypt_member_sensitive_data(m) for m in members]
    
    # Sort by chapter and title
    CHAPTERS = ["National", "AD", "HA", "HS"]
    TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "Member", "Honorary"]
    
    def sort_key(member):
        ch_idx = CHAPTERS.index(member.get('chapter', '')) if member.get('chapter', '') in CHAPTERS else 999
        ti_idx = TITLES.index(member.get('title', '')) if member.get('title', '') in TITLES else 999
        return (ch_idx, ti_idx)
    
    sorted_members = sorted(decrypted_members, key=sort_key)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    header = ["Chapter", "Title", "Handle", "Name"]
    
    for month_idx in months:
        header.append(month_names[month_idx - 1])
    header.extend(["Total Paid", "Total Late", "Total Unpaid"])
    
    writer.writerow([f"Dues Report - {period_name}" + (f" - {chapter}" if chapter and chapter != "All" else " - All Chapters")])
    writer.writerow([])
    writer.writerow(header)
    
    # Get all officer_dues records for the year
    month_names_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    officer_dues_records = await db.officer_dues.find({
        "month": {"$regex": f"_{year}$"}
    }, {"_id": 0}).to_list(length=None)
    
    # Build a lookup: member_id -> {month_key: status}
    officer_dues_lookup = {}
    for record in officer_dues_records:
        member_id = record.get("member_id")
        month_key = record.get("month")  # e.g., "Jan_2026"
        status = record.get("status", "unpaid")
        if member_id not in officer_dues_lookup:
            officer_dues_lookup[member_id] = {}
        officer_dues_lookup[member_id][month_key] = status
    
    # Get active dues extensions
    today_str = datetime.now().strftime("%Y-%m-%d")
    active_extensions = await db.dues_extensions.find({
        "extension_until": {"$gte": today_str}
    }, {"_id": 0}).to_list(length=None)
    extended_member_ids = set(ext.get("member_id") for ext in active_extensions)
    
    # Data rows
    for member in sorted_members:
        member_id = member.get("id")
        is_non_dues_paying = member.get("non_dues_paying", False)
        has_extension = member_id in extended_member_ids
        
        # Get status for each month in the report period
        quarter_paid = 0
        quarter_late = 0
        quarter_unpaid = 0
        month_statuses = []
        
        for month_idx in months:
            month_key = f"{month_names_short[month_idx - 1]}_{year}"
            
            # Check officer_dues collection first (A&D source)
            officer_dues_status = officer_dues_lookup.get(member_id, {}).get(month_key)
            
            if officer_dues_status:
                status = officer_dues_status
            else:
                # Fallback to member.dues field
                dues = member.get("dues", {})
                year_str = str(year)
                
                if 'year' in dues:
                    months_data = dues.get('months', [])
                else:
                    months_data = dues.get(year_str, [])
                
                idx = month_idx - 1
                if idx < len(months_data):
                    month_due = months_data[idx]
                    if isinstance(month_due, dict):
                        status = month_due.get('status', 'unpaid')
                    elif month_due == True or month_due == 'paid':
                        status = 'paid'
                    else:
                        status = 'unpaid'
                else:
                    status = 'unpaid'
            
            # Non-dues paying members show as "Exempt"
            if is_non_dues_paying:
                month_statuses.append("Exempt")
            # Members with extension show as "Extended" for current/future months
            elif has_extension and status == 'unpaid':
                current_month = datetime.now().month
                if month_idx >= current_month:
                    month_statuses.append("Extended")
                    status = 'extended'
                else:
                    month_statuses.append(status.capitalize())
            else:
                month_statuses.append(status.capitalize())
            
            if is_non_dues_paying or status == 'extended':
                pass  # Don't count in totals
            elif status == 'paid':
                quarter_paid += 1
            elif status == 'late':
                quarter_late += 1
            else:
                quarter_unpaid += 1
        
        row = [
            member.get('chapter', ''),
            member.get('title', ''),
            member.get('handle', ''),
            member.get('name', ''),
        ]
        row.extend(month_statuses)
        
        # For exempt members, show N/A for totals
        if is_non_dues_paying:
            row.extend(["N/A", "N/A", "N/A"])
        else:
            row.extend([str(quarter_paid), str(quarter_late), str(quarter_unpaid)])
        
        writer.writerow(row)
    
    output.seek(0)
    csv_content = '\ufeff' + output.getvalue()
    
    if quarter == "all" or quarter is None:
        filename = f"dues_{year}"
    else:
        filename = f"dues_Q{quarter}_{year}"
    if chapter and chapter != "All":
        filename += f"_{chapter}"
    filename += ".csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@api_router.get("/reports/prospects/attendance/quarterly")
async def get_prospects_attendance_quarterly_report(
    year: int = None,
    quarter: int = None,
    current_user: dict = Depends(verify_token)
):
    """Get quarterly meeting attendance report for prospects"""
    # Check permission
    if not await can_view_reports_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view reports")
    
    if year is None:
        year = datetime.now(timezone.utc).year
    if quarter is None:
        quarter = (datetime.now(timezone.utc).month - 1) // 3 + 1
    
    # Calculate quarter date range
    quarter_months = {
        1: (1, 2, 3),
        2: (4, 5, 6),
        3: (7, 8, 9),
        4: (10, 11, 12)
    }
    months = quarter_months.get(quarter, (1, 2, 3))
    
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(10000)
    decrypted_prospects = [decrypt_member_sensitive_data(p) for p in prospects]
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    quarter_name = f"Q{quarter} {year}"
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    header = ["Handle", "Name", "Email", "Phone"]
    
    for month_idx in months:
        header.append(f"{month_names[month_idx-1]} Meetings")
    header.extend(["Total Meetings", "Present", "Excused", "Absent", "Attendance %"])
    
    writer.writerow([f"Prospects Meeting Attendance Report - {quarter_name}"])
    writer.writerow([])
    writer.writerow(header)
    
    # Data rows
    for prospect in decrypted_prospects:
        attendance = prospect.get("meeting_attendance", {})
        year_str = str(year)
        
        # Handle both old and new format
        if 'year' in attendance:
            meetings = attendance.get('meetings', [])
        else:
            meetings = attendance.get(year_str, [])
        
        # Filter meetings for this quarter
        quarter_meetings = []
        for m in meetings:
            if isinstance(m, dict) and m.get('date'):
                meeting_date = m['date']
                meeting_month = int(meeting_date.split('-')[1])
                if meeting_month in months:
                    quarter_meetings.append(m)
        
        # Calculate stats
        total = len(quarter_meetings)
        present = sum(1 for m in quarter_meetings if m.get('status') == 1)
        excused = sum(1 for m in quarter_meetings if m.get('status') == 2)
        absent = sum(1 for m in quarter_meetings if m.get('status') == 0)
        attendance_pct = f"{(present / total * 100):.1f}%" if total > 0 else "N/A"
        
        # Count meetings per month
        month_counts = []
        for month_idx in months:
            month_meetings = [m for m in quarter_meetings if int(m['date'].split('-')[1]) == month_idx]
            month_counts.append(str(len(month_meetings)))
        
        row = [
            prospect.get('handle', ''),
            prospect.get('name', ''),
            prospect.get('email', ''),
            prospect.get('phone', ''),
        ]
        row.extend(month_counts)
        row.extend([str(total), str(present), str(excused), str(absent), attendance_pct])
        
        writer.writerow(row)
    
    output.seek(0)
    csv_content = '\ufeff' + output.getvalue()
    
    filename = f"prospects_attendance_Q{quarter}_{year}.csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


# Member Actions endpoints (admin only)
@api_router.post("/members/{member_id}/actions")
async def add_member_action(
    member_id: str,
    action_type: str,
    date: str,
    description: str,
    current_user: dict = Depends(verify_token)
):
    """Add a merit, promotion, or disciplinary action to a member"""
    # Check if user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member (chapter-based)
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only add actions for members in your own chapter")
    
    # Create action record
    action = {
        "id": str(uuid.uuid4()),
        "type": action_type,  # merit, promotion, disciplinary
        "date": date,
        "description": description,
        "added_by": current_user["username"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add action to member's actions list
    actions = member.get("actions", [])
    actions.append(action)
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "add_action",
        f"Added {action_type} action for member {member['handle']}"
    )
    
    return {"message": "Action added successfully", "action": action}

@api_router.delete("/members/{member_id}/actions/{action_id}")
async def delete_member_action(
    member_id: str,
    action_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete an action from a member"""
    # Check if user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member (chapter-based)
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only delete actions for members in your own chapter")
    
    actions = member.get("actions", [])
    actions = [a for a in actions if a.get("id") != action_id]
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "delete_action",
        f"Deleted action from member {member['handle']}"
    )
    
    return {"message": "Action deleted successfully"}

@api_router.put("/members/{member_id}/actions/{action_id}")
async def update_member_action(
    member_id: str,
    action_id: str,
    action_data: dict,
    current_user: dict = Depends(verify_token)
):
    """Update an action for a member"""
    # Check if user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if user can edit this member (chapter-based)
    if not can_edit_member(current_user, member.get("chapter", "")):
        raise HTTPException(status_code=403, detail="You can only update actions for members in your own chapter")
    
    # Extract action data
    action_type = action_data.get("action_type")
    date = action_data.get("date")
    description = action_data.get("description")
    
    if not all([action_type, date, description]):
        raise HTTPException(status_code=400, detail="Missing required fields: action_type, date, description")
    
    # Validate action type
    if action_type not in ["merit", "promotion", "disciplinary"]:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    # Find and update the action
    actions = member.get("actions", [])
    action_found = False
    for action in actions:
        if action.get("id") == action_id:
            action["type"] = action_type
            action["date"] = date
            action["description"] = description
            action["updated_at"] = datetime.now(timezone.utc).isoformat()
            action_found = True
            break
    
    if not action_found:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Update the member document
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "update_action",
        f"Updated action for member {member['handle']}: {action_type}"
    )
    
    return {"message": "Action updated successfully"}

# Prospect Actions endpoints (admin only - National/HA only)
@api_router.post("/prospects/{prospect_id}/actions")
async def add_prospect_action(
    prospect_id: str,
    action_type: str,
    date: str,
    description: str,
    current_user: dict = Depends(verify_token)
):
    """Add a merit, promotion, or disciplinary action to a prospect"""
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit prospects")
    
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create action record
    action = {
        "id": str(uuid.uuid4()),
        "type": action_type,  # merit, promotion, disciplinary
        "date": date,
        "description": description,
        "added_by": current_user["username"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add action to prospect's actions list
    actions = prospect.get("actions", [])
    actions.append(action)
    
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "add_action",
        f"Added {action_type} action for prospect {prospect['handle']}"
    )
    
    return {"message": "Action added successfully", "action": action}

@api_router.delete("/prospects/{prospect_id}/actions/{action_id}")
async def delete_prospect_action(
    prospect_id: str,
    action_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete an action from a prospect"""
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit prospects")
    
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    actions = prospect.get("actions", [])
    actions = [a for a in actions if a.get("id") != action_id]
    
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "delete_action",
        f"Deleted action from prospect {prospect['handle']}"
    )
    
    return {"message": "Action deleted successfully"}

@api_router.put("/prospects/{prospect_id}/actions/{action_id}")
async def update_prospect_action(
    prospect_id: str,
    action_id: str,
    action_data: dict,
    current_user: dict = Depends(verify_token)
):
    """Update an action for a prospect"""
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit prospects")
    
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Extract action data
    action_type = action_data.get("action_type")
    date = action_data.get("date")
    description = action_data.get("description")
    
    if not all([action_type, date, description]):
        raise HTTPException(status_code=400, detail="Missing required fields: action_type, date, description")
    
    # Validate action type
    if action_type not in ["merit", "promotion", "disciplinary"]:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    # Find and update the action
    actions = prospect.get("actions", [])
    action_found = False
    for action in actions:
        if action.get("id") == action_id:
            action["type"] = action_type
            action["date"] = date
            action["description"] = description
            action["updated_at"] = datetime.now(timezone.utc).isoformat()
            action_found = True
            break
    
    if not action_found:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Update the prospect document
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "update_action",
        f"Updated action for prospect {prospect['handle']}: {action_type}"
    )
    
    return {"message": "Action updated successfully"}

# ==================== HANGAROUND MANAGEMENT ENDPOINTS ====================
# Hangarounds are the entry level - only handle and name required

def can_view_hangarounds(user: dict) -> bool:
    """Check if user can view hangarounds list (same as prospects) - DEPRECATED"""
    return can_view_prospects(user)

async def can_view_hangarounds_async(user: dict) -> bool:
    """Check if user can view hangarounds list - permission based"""
    return await can_view_prospects_async(user)

def can_edit_hangaround(user: dict) -> bool:
    """Check if user can edit hangarounds (same as prospects)"""
    return can_edit_prospect(user)

@api_router.get("/hangarounds", response_model=List[Hangaround])
async def get_hangarounds(current_user: dict = Depends(verify_token)):
    """Get all hangarounds"""
    if not await can_view_hangarounds_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view hangarounds")
    
    hangarounds = await db.hangarounds.find({}, {"_id": 0}).to_list(1000)
    user_can_edit = can_edit_hangaround(current_user)
    
    for hangaround in hangarounds:
        if isinstance(hangaround.get('created_at'), str):
            hangaround['created_at'] = datetime.fromisoformat(hangaround['created_at'])
        if isinstance(hangaround.get('updated_at'), str):
            hangaround['updated_at'] = datetime.fromisoformat(hangaround['updated_at'])
        hangaround['can_edit'] = user_can_edit
    
    return hangarounds

@api_router.get("/hangarounds/{hangaround_id}", response_model=Hangaround)
async def get_hangaround(hangaround_id: str, current_user: dict = Depends(verify_token)):
    """Get a single hangaround by ID"""
    if not can_view_hangarounds(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can view hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    if isinstance(hangaround.get('created_at'), str):
        hangaround['created_at'] = datetime.fromisoformat(hangaround['created_at'])
    if isinstance(hangaround.get('updated_at'), str):
        hangaround['updated_at'] = datetime.fromisoformat(hangaround['updated_at'])
    
    return hangaround

@api_router.post("/hangarounds", response_model=Hangaround, status_code=201)
async def create_hangaround(hangaround_data: HangaroundCreate, current_user: dict = Depends(verify_token)):
    """Create a new hangaround (only handle and name required)"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can create hangarounds")
    
    hangaround = Hangaround(
        handle=hangaround_data.handle,
        name=hangaround_data.name
    )
    doc = hangaround.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.hangarounds.insert_one(doc)
    
    # Try to add Discord role
    if DISCORD_HANGAROUND_ROLE_ID and discord_bot:
        try:
            await add_discord_role_by_name(hangaround.handle, DISCORD_HANGAROUND_ROLE_ID, "New Hangaround")
        except Exception as e:
            sys.stderr.write(f"⚠️ Failed to add Discord Hangaround role: {e}\n")
            sys.stderr.flush()
    
    await log_activity(
        username=current_user["username"],
        action="hangaround_create",
        details=f"Created hangaround: {hangaround.name} ({hangaround.handle})"
    )
    
    return hangaround

@api_router.put("/hangarounds/{hangaround_id}", response_model=Hangaround)
async def update_hangaround(hangaround_id: str, hangaround_data: HangaroundUpdate, current_user: dict = Depends(verify_token)):
    """Update a hangaround"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    update_data = {k: v for k, v in hangaround_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.hangarounds.update_one({"id": hangaround_id}, {"$set": update_data})
    
    updated_hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if isinstance(updated_hangaround.get('created_at'), str):
        updated_hangaround['created_at'] = datetime.fromisoformat(updated_hangaround['created_at'])
    if isinstance(updated_hangaround.get('updated_at'), str):
        updated_hangaround['updated_at'] = datetime.fromisoformat(updated_hangaround['updated_at'])
    
    await log_activity(
        username=current_user["username"],
        action="hangaround_update",
        details=f"Updated hangaround: {updated_hangaround.get('name', 'Unknown')} ({updated_hangaround.get('handle', 'Unknown')})"
    )
    
    return updated_hangaround

@api_router.delete("/hangarounds/{hangaround_id}")
async def delete_hangaround(
    hangaround_id: str,
    reason: str,
    current_user: dict = Depends(verify_token)
):
    """Archive a hangaround with deletion reason"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can archive hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    # Create archived record
    archived_hangaround = {
        **hangaround,
        "deletion_reason": reason,
        "deleted_by": current_user["username"],
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.archived_hangarounds.insert_one(archived_hangaround)
    await db.hangarounds.delete_one({"id": hangaround_id})
    
    await log_activity(
        username=current_user["username"],
        action="hangaround_archive",
        details=f"Archived hangaround: {hangaround.get('name', 'Unknown')} ({hangaround.get('handle', 'Unknown')}) - Reason: {reason}"
    )
    
    return {"message": "Hangaround archived successfully"}

@api_router.post("/hangarounds/{hangaround_id}/promote", response_model=Prospect, status_code=201)
async def promote_hangaround_to_prospect(
    hangaround_id: str,
    promotion_data: HangaroundToProspectPromotion,
    current_user: dict = Depends(verify_token)
):
    """Promote a hangaround to prospect by adding required info"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can promote hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    # Create prospect from hangaround data + promotion data
    prospect = Prospect(
        handle=hangaround['handle'],
        name=hangaround['name'],
        email=promotion_data.email,
        phone=promotion_data.phone,
        address=promotion_data.address,
        dob=promotion_data.dob,
        join_date=promotion_data.join_date,
        military_service=promotion_data.military_service,
        military_branch=promotion_data.military_branch,
        is_first_responder=promotion_data.is_first_responder,
        meeting_attendance=hangaround.get('meeting_attendance', {str(datetime.now(timezone.utc).year): []}),
        actions=hangaround.get('actions', []),
        promoted_from_hangaround=hangaround_id
    )
    
    # Add promotion action
    promotion_action = {
        "id": str(uuid.uuid4()),
        "type": "promotion",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": f"Promoted from Hangaround to Prospect by {current_user['username']}",
        "created_by": current_user["username"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    prospect.actions.append(promotion_action)
    
    # Save prospect
    doc = prospect.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.prospects.insert_one(doc)
    
    # Archive hangaround (not delete, keep history)
    archived_hangaround = {
        **hangaround,
        "promoted_to_prospect": prospect.id,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "promoted_by": current_user["username"]
    }
    await db.archived_hangarounds.insert_one(archived_hangaround)
    await db.hangarounds.delete_one({"id": hangaround_id})
    
    # Update Discord roles
    if discord_bot:
        try:
            # Remove Hangaround role, add Prospect role
            if DISCORD_HANGAROUND_ROLE_ID:
                await remove_discord_role_by_name(hangaround['handle'], DISCORD_HANGAROUND_ROLE_ID, "Promoted to Prospect")
            if DISCORD_PROSPECT_ROLE_ID:
                await add_discord_role_by_name(prospect.handle, DISCORD_PROSPECT_ROLE_ID, "Promoted to Prospect")
        except Exception as e:
            sys.stderr.write(f"⚠️ Failed to update Discord roles for promotion: {e}\n")
            sys.stderr.flush()
    
    await log_activity(
        username=current_user["username"],
        action="promote_hangaround",
        details=f"Promoted hangaround {hangaround['handle']} to Prospect"
    )
    
    return prospect

@api_router.post("/hangarounds/{hangaround_id}/actions")
async def add_hangaround_action(
    hangaround_id: str,
    action_type: str,
    date: str,
    description: str,
    current_user: dict = Depends(verify_token)
):
    """Add a merit, promotion, or disciplinary action to a hangaround"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    action = {
        "id": str(uuid.uuid4()),
        "type": action_type,
        "date": date,
        "description": description,
        "created_by": current_user["username"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    actions = hangaround.get("actions", [])
    actions.append(action)
    
    await db.hangarounds.update_one(
        {"id": hangaround_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "add_action",
        f"Added {action_type} action for hangaround {hangaround['handle']}"
    )
    
    return {"message": "Action added successfully", "action": action}

@api_router.delete("/hangarounds/{hangaround_id}/actions/{action_id}")
async def delete_hangaround_action(
    hangaround_id: str,
    action_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete an action from a hangaround"""
    if not can_edit_hangaround(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit hangarounds")
    
    hangaround = await db.hangarounds.find_one({"id": hangaround_id}, {"_id": 0})
    if not hangaround:
        raise HTTPException(status_code=404, detail="Hangaround not found")
    
    actions = hangaround.get("actions", [])
    actions = [a for a in actions if a.get("id") != action_id]
    
    await db.hangarounds.update_one(
        {"id": hangaround_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "delete_action",
        f"Deleted action from hangaround {hangaround['handle']}"
    )
    
    return {"message": "Action deleted successfully"}

# Migration endpoint to convert existing prospects to hangarounds
@api_router.post("/admin/migrate-prospects-to-hangarounds")
async def migrate_prospects_to_hangarounds(current_user: dict = Depends(verify_token)):
    """One-time migration: Convert all existing prospects to hangarounds"""
    if current_user.get("role") != "admin" or current_user.get("chapter") != "National":
        raise HTTPException(status_code=403, detail="Only National Admin can run migration")
    
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    migrated_count = 0
    
    for prospect in prospects:
        hangaround = {
            "id": prospect["id"],
            "handle": prospect["handle"],
            "name": prospect["name"],
            "meeting_attendance": prospect.get("meeting_attendance", {str(datetime.now(timezone.utc).year): []}),
            "actions": prospect.get("actions", []),
            "created_at": prospect.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "migrated_from_prospect": True,
            "original_prospect_data": {
                "email": prospect.get("email"),
                "phone": prospect.get("phone"),
                "address": prospect.get("address"),
                "dob": prospect.get("dob"),
                "join_date": prospect.get("join_date"),
                "military_service": prospect.get("military_service"),
                "military_branch": prospect.get("military_branch"),
                "is_first_responder": prospect.get("is_first_responder")
            }
        }
        await db.hangarounds.insert_one(hangaround)
        await db.prospects.delete_one({"id": prospect["id"]})
        migrated_count += 1
    
    await log_activity(
        username=current_user["username"],
        action="migrate_prospects",
        details=f"Migrated {migrated_count} prospects to hangarounds"
    )
    
    return {"message": f"Successfully migrated {migrated_count} prospects to hangarounds", "count": migrated_count}

# Prospect management endpoints (admin only)
@api_router.get("/prospects", response_model=List[Prospect])
async def get_prospects(current_user: dict = Depends(verify_token)):
    # Check if user can view prospects - permission based
    if not await can_view_prospects_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view prospects")
    
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Add can_edit flag for each prospect
    user_can_edit = can_edit_prospect(current_user)
    
    for prospect in prospects:
        if isinstance(prospect.get('created_at'), str):
            prospect['created_at'] = datetime.fromisoformat(prospect['created_at'])
        if isinstance(prospect.get('updated_at'), str):
            prospect['updated_at'] = datetime.fromisoformat(prospect['updated_at'])
        # Add can_edit flag for frontend to show/hide action buttons
        prospect['can_edit'] = user_can_edit
    
    return prospects


@api_router.get("/prospects/{prospect_id}", response_model=Prospect)
async def get_prospect(prospect_id: str, current_user: dict = Depends(verify_token)):
    """Get a single prospect by ID"""
    # Check if user can view prospects - permission based
    if not await can_view_prospects_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view prospects")
    
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    if isinstance(prospect.get('created_at'), str):
        prospect['created_at'] = datetime.fromisoformat(prospect['created_at'])
    if isinstance(prospect.get('updated_at'), str):
        prospect['updated_at'] = datetime.fromisoformat(prospect['updated_at'])
    
    return prospect


@api_router.post("/prospects", response_model=Prospect, status_code=201)
async def create_prospect(prospect_data: ProspectCreate, current_user: dict = Depends(verify_token)):
    # Check if user can edit prospects (National Admin or HA Admin only)
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can create prospects")
    
    prospect_dict = {k: v for k, v in prospect_data.model_dump().items() if v is not None}
    prospect = Prospect(**prospect_dict)
    doc = prospect.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.prospects.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_create",
        details=f"Created prospect: {prospect.name} ({prospect.handle})"
    )
    
    return prospect

@api_router.put("/prospects/{prospect_id}", response_model=Prospect)
async def update_prospect(prospect_id: str, prospect_data: ProspectUpdate, current_user: dict = Depends(verify_token)):
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can edit prospects")
    
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    update_data = {k: v for k, v in prospect_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.prospects.update_one({"id": prospect_id}, {"$set": update_data})
    
    updated_prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if isinstance(updated_prospect.get('created_at'), str):
        updated_prospect['created_at'] = datetime.fromisoformat(updated_prospect['created_at'])
    if isinstance(updated_prospect.get('updated_at'), str):
        updated_prospect['updated_at'] = datetime.fromisoformat(updated_prospect['updated_at'])
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_update",
        details=f"Updated prospect: {updated_prospect.get('name', 'Unknown')} ({updated_prospect.get('handle', 'Unknown')})"
    )
    
    return updated_prospect

@api_router.delete("/prospects/{prospect_id}")
async def delete_prospect(
    prospect_id: str,
    reason: str,
    current_user: dict = Depends(verify_token)
):
    """Archive a prospect with deletion reason"""
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can archive prospects")
    
    # Get prospect info before archiving
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create archived record
    archived_prospect = {
        **prospect,
        "deletion_reason": reason,
        "deleted_by": current_user["username"],
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Move to archived collection
    await db.archived_prospects.insert_one(archived_prospect)
    
    # Remove from active prospects
    await db.prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_archive",
        details=f"Archived prospect: {prospect.get('name', 'Unknown')} ({prospect.get('handle', 'Unknown')}) - Reason: {reason}"
    )
    
    return {"message": "Prospect archived successfully"}

@api_router.get("/prospects/export/csv")
async def export_prospects_csv(current_user: dict = Depends(verify_token)):
    # Check if user can view prospects - permission based
    if not await can_view_prospects_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to export prospects")
    
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all prospects
    decrypted_prospects = [decrypt_member_sensitive_data(prospect) for prospect in prospects]
    
    current_year_str = str(datetime.now(timezone.utc).year)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Create CSV header with new flexible format
    header = ["Handle", "Name", "Email", "Phone", "Address", "Military Service", "Military Branch", 
              "First Responder", "Attendance Year", "Total Meetings", "Present", "Excused", "Absent", 
              "Attendance %", "Meeting Details"]
    writer.writerow(header)
    
    # Add data rows
    for prospect in decrypted_prospects:
        attendance = prospect.get('meeting_attendance', {})
        meetings = []
        export_year = current_year_str
        
        # Handle both old and new format
        if attendance and isinstance(attendance, dict):
            if 'year' in attendance:
                # Old format
                export_year = str(attendance.get('year', current_year_str))
                old_meetings = attendance.get('meetings', [])
                for idx, m in enumerate(old_meetings):
                    if isinstance(m, dict) and (m.get('status', 0) != 0 or m.get('note')):
                        month_idx = idx // 2
                        week_num = (idx % 2) + 1
                        approx_date = f"{export_year}-{month_idx+1:02d}-{week_num * 7:02d}"
                        meetings.append({
                            'date': approx_date,
                            'status': m.get('status', 0),
                            'note': m.get('note', '')
                        })
            else:
                # New format
                years = sorted([k for k in attendance.keys() if k.isdigit()], reverse=True)
                if years:
                    export_year = years[0]
                    meetings = attendance.get(export_year, [])
        
        # Calculate stats
        total = len(meetings)
        present = sum(1 for m in meetings if m.get('status') == 1)
        excused = sum(1 for m in meetings if m.get('status') == 2)
        absent = sum(1 for m in meetings if m.get('status') == 0)
        attendance_pct = f"{(present / total * 100):.1f}%" if total > 0 else "N/A"
        
        # Build meeting details string
        details_parts = []
        for m in sorted(meetings, key=lambda x: x.get('date', '')):
            date_str = m.get('date', '')
            if date_str:
                try:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        date_str = f"{parts[1]}/{parts[2]}"
                except:
                    pass
            status = m.get('status', 0)
            status_char = 'P' if status == 1 else ('E' if status == 2 else 'A')
            note = m.get('note', '')
            if note:
                details_parts.append(f"{date_str}:{status_char}({note})")
            else:
                details_parts.append(f"{date_str}:{status_char}")
        
        details_str = "; ".join(details_parts) if details_parts else "No meetings"
        
        # Military and First Responder status
        military_service = "Yes" if prospect.get('military_service', False) else "No"
        military_branch = prospect.get('military_branch', '') or ''
        is_first_responder = "Yes" if prospect.get('is_first_responder', False) else "No"
        
        row = [
            prospect.get('handle', ''),
            prospect.get('name', ''),
            prospect.get('email', ''),
            prospect.get('phone', ''),
            prospect.get('address', ''),
            military_service,
            military_branch,
            is_first_responder,
            export_year,
            str(total),
            str(present),
            str(excused),
            str(absent),
            attendance_pct,
            details_str
        ]
        writer.writerow(row)
    
    output.seek(0)
    csv_content = '\ufeff' + output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=prospects_export.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@api_router.post("/prospects/{prospect_id}/promote", response_model=Member, status_code=201)
async def promote_prospect_to_member(
    prospect_id: str,
    chapter: str,
    title: str,
    current_user: dict = Depends(verify_token)
):
    """
    Promote a prospect to a member by copying their data to members collection
    and deleting from prospects collection
    """
    # Check if user can edit prospects (only National/HA can promote)
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can promote prospects")
    
    # Get the prospect
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create member data from prospect data
    member_data = {
        "id": str(uuid.uuid4()),  # Generate new ID for member
        "chapter": chapter,
        "title": title,
        "handle": prospect["handle"],
        "name": prospect["name"],
        "email": prospect["email"],
        "phone": prospect["phone"],
        "address": prospect["address"],
        "dob": prospect.get("dob"),
        "join_date": prospect.get("join_date"),
        "phone_private": False,
        "address_private": False,
        "actions": prospect.get("actions", []),  # Carry over actions history
        "dues": {
            str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
        },
        "meeting_attendance": prospect.get("meeting_attendance", {
            str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
        }),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Encrypt sensitive data
    member_data = encrypt_member_sensitive_data(member_data)
    
    # Check for duplicate handle or email
    existing_handle = await db.members.find_one({"handle": member_data["handle"]})
    if existing_handle:
        raise HTTPException(status_code=400, detail="A member with this handle already exists")
    
    email_hash = hashlib.sha256(member_data["email"].lower().encode()).hexdigest()
    existing_email = await db.members.find_one({"email_hash": email_hash})
    if existing_email:
        raise HTTPException(status_code=400, detail="A member with this email already exists")
    
    member_data["email_hash"] = email_hash
    
    # Insert into members collection
    await db.members.insert_one(member_data)
    
    # Delete from prospects collection
    await db.prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "promote_prospect",
        f"Promoted prospect {prospect['handle']} to member in chapter {chapter}"
    )
    
    # Decrypt for response
    member_data = decrypt_member_sensitive_data(member_data)
    
    return member_data

@api_router.post("/prospects/bulk-promote")
async def bulk_promote_prospects(
    prospect_ids: list[str],
    chapter: str,
    title: str,
    current_user: dict = Depends(verify_token)
):
    """
    Bulk promote multiple prospects to members with same chapter and title
    """
    # Check if user can edit prospects
    if not can_edit_prospect(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin and HA Admin can promote prospects")
    
    promoted_count = 0
    failed_prospects = []
    
    for prospect_id in prospect_ids:
        try:
            # Get the prospect
            prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
            if not prospect:
                failed_prospects.append({"id": prospect_id, "reason": "Prospect not found"})
                continue
            
            # Create member data from prospect data
            member_data = {
                "id": str(uuid.uuid4()),
                "chapter": chapter,
                "title": title,
                "handle": prospect["handle"],
                "name": prospect["name"],
                "email": prospect["email"],
                "phone": prospect["phone"],
                "address": prospect["address"],
                "dob": prospect.get("dob"),
                "join_date": prospect.get("join_date"),
                "phone_private": False,
                "address_private": False,
                "actions": prospect.get("actions", []),
                "dues": {
                    str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
                },
                "meeting_attendance": prospect.get("meeting_attendance", {
                    str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
                }),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Encrypt sensitive data
            member_data = encrypt_member_sensitive_data(member_data)
            
            # Check for duplicate handle or email
            existing_handle = await db.members.find_one({"handle": member_data["handle"]})
            if existing_handle:
                failed_prospects.append({"id": prospect_id, "handle": prospect["handle"], "reason": "Handle already exists in members"})
                continue
            
            email_hash = hashlib.sha256(member_data["email"].lower().encode()).hexdigest()
            existing_email = await db.members.find_one({"email_hash": email_hash})
            if existing_email:
                failed_prospects.append({"id": prospect_id, "handle": prospect["handle"], "reason": "Email already exists in members"})
                continue
            
            member_data["email_hash"] = email_hash
            
            # Insert into members collection
            await db.members.insert_one(member_data)
            
            # Delete from prospects collection
            await db.prospects.delete_one({"id": prospect_id})
            
            promoted_count += 1
            
        except Exception as e:
            failed_prospects.append({"id": prospect_id, "reason": str(e)})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "bulk_promote_prospects",
        f"Bulk promoted {promoted_count} prospects to {chapter} chapter"
    )
    
    return {
        "message": f"Successfully promoted {promoted_count} prospects",
        "promoted_count": promoted_count,
        "failed_count": len(failed_prospects),
        "failed_prospects": failed_prospects
    }

# ==================== WALL OF HONOR (Fallen Members) ====================

@api_router.get("/fallen", response_model=List[FallenMember])
async def get_fallen_members(current_user: dict = Depends(verify_token)):
    """Get all fallen members for the Wall of Honor"""
    fallen = await db.fallen_members.find({}, {"_id": 0}).to_list(1000)
    # Sort by date_of_passing (most recent first), then by name
    fallen.sort(key=lambda x: (x.get('date_of_passing') or '0000-00-00', x.get('name', '')), reverse=True)
    return fallen

@api_router.post("/fallen", response_model=FallenMember, status_code=201)
async def create_fallen_member(
    fallen: FallenMemberCreate,
    current_user: dict = Depends(verify_token)
):
    """Add a fallen member to the Wall of Honor (National Admin only)"""
    # Only National Admin can add to Wall of Honor
    if not can_edit_fallen_member(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin can add to the Wall of Honor")
    
    fallen_dict = fallen.model_dump()
    fallen_dict["id"] = str(uuid.uuid4())
    fallen_dict["created_at"] = datetime.now(timezone.utc)
    fallen_dict["created_by"] = current_user["username"]
    
    await db.fallen_members.insert_one(fallen_dict)
    
    # Log activity
    await log_activity(
        current_user["username"],
        "add_fallen_member",
        f"Added {fallen.handle} ({fallen.name}) to the Wall of Honor"
    )
    
    return FallenMember(**fallen_dict)

@api_router.put("/fallen/{fallen_id}", response_model=FallenMember)
async def update_fallen_member(
    fallen_id: str,
    fallen_update: FallenMemberUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update a fallen member entry (National Admin only)"""
    # Only National Admin can edit Wall of Honor
    if not can_edit_fallen_member(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin can edit the Wall of Honor")
    
    existing = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Fallen member not found")
    
    # Filter out None values, but also preserve existing photo_url if empty string is sent
    update_data = {}
    for k, v in fallen_update.model_dump().items():
        if v is not None:
            # Special handling for photo_url - don't overwrite with empty string unless explicitly clearing
            if k == 'photo_url' and v == '' and existing.get('photo_url'):
                # Keep the existing photo if new value is empty but old exists
                continue
            update_data[k] = v
    
    if update_data:
        await db.fallen_members.update_one(
            {"id": fallen_id},
            {"$set": update_data}
        )
        
        # Log activity
        await log_activity(
            current_user["username"],
            "update_fallen_member",
            f"Updated Wall of Honor entry for {existing.get('handle', existing.get('name'))}"
        )
    
    updated = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    return FallenMember(**updated)

@api_router.delete("/fallen/{fallen_id}")
async def delete_fallen_member(
    fallen_id: str,
    current_user: dict = Depends(verify_token)
):
    """Remove a fallen member from the Wall of Honor (National Admin only)"""
    # Only National Admin can delete from Wall of Honor
    if not can_edit_fallen_member(current_user):
        raise HTTPException(status_code=403, detail="Only National Admin can remove from the Wall of Honor")
    
    existing = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Fallen member not found")
    
    await db.fallen_members.delete_one({"id": fallen_id})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "delete_fallen_member",
        f"Removed {existing.get('handle', existing.get('name'))} from the Wall of Honor"
    )
    
    return {"message": "Fallen member removed from Wall of Honor"}

@api_router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_admin)
):
    """Upload an image file (admin only)"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, GIF, WEBP")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    
    # Save file
    upload_dir = Path(__file__).parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / unique_filename
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Return the URL path (will be served via /uploads static mount)
    return {"url": f"/api/uploads/{unique_filename}", "filename": unique_filename}

@api_router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve uploaded files"""
    from fastapi.responses import FileResponse
    upload_dir = Path(__file__).parent / "uploads"
    file_path = upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

# ==================== END WALL OF HONOR ====================

# User management endpoints (admin or users with manage_system_users permission)
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(verify_can_manage_users)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    # Convert and add default permissions if missing
    result = []
    for user in users:
        # Add id if missing (for old users)
        if 'id' not in user:
            user['id'] = str(uuid.uuid4())
            await db.users.update_one(
                {"username": user['username']},
                {"$set": {"id": user['id']}}
            )
        
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        
        # Add default permissions if not present
        if 'permissions' not in user:
            if user.get('role') == 'admin':
                user['permissions'] = {
                    "basic_info": True,
                    "email": True,
                    "phone": True,
                    "address": True,
                    "dues_tracking": True,
                    "meeting_attendance": True,
                    "admin_actions": True
                }
            else:
                user['permissions'] = {
                    "basic_info": True,
                    "email": False,
                    "phone": False,
                    "address": False,
                    "dues_tracking": False,
                    "meeting_attendance": False,
                    "admin_actions": False
                }
            # Update the user in database
            await db.users.update_one(
                {"id": user['id']},
                {"$set": {"permissions": user['permissions']}}
            )
        
        result.append(user)
    
    return result

@api_router.get("/users/admins")
async def get_admin_users(current_user: dict = Depends(verify_token)):
    """Get list of admin users - accessible to all authenticated users for messaging"""
    admin_users = await db.users.find(
        {"role": "admin"},
        {"_id": 0, "password_hash": 0, "permissions": 0}
    ).to_list(1000)
    
    # Return simple user info for messaging
    return [
        {
            "id": user.get("id", str(uuid.uuid4())),
            "username": user["username"],
            "role": user["role"]
        }
        for user in admin_users
    ]

@api_router.get("/users/all")
async def get_all_users_for_messaging(current_user: dict = Depends(verify_token)):
    """Get list of all users - accessible to all authenticated users for messaging"""
    current_username = current_user['username']
    user_role = current_user.get('role')
    
    # Define HA chapter officers (only these can be messaged by prospects)
    ha_officers = ['Chap', 'Sancho', 'Tapeworm', 'Hee Haw', 'Phantom']
    
    all_users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0, "permissions": 0}
    ).to_list(1000)
    
    # Filter based on role
    filtered_users = []
    for user in all_users:
        # Don't include current user
        if user["username"] == current_username:
            continue
            
        # If user is prospect, only show HA chapter officers
        if user_role == 'prospect':
            if user["username"] in ha_officers:
                filtered_users.append({
                    "id": user.get("id", str(uuid.uuid4())),
                    "username": user["username"],
                    "role": user["role"]
                })
        else:
            # Admin and member users can see all users
            filtered_users.append({
                "id": user.get("id", str(uuid.uuid4())),
                "username": user["username"],
                "role": user["role"]
            })
    
    return filtered_users

# Audit Logs endpoints
@api_router.get("/logs")
async def get_logs(
    limit: int = 100,
    skip: int = 0,
    username: str = None,
    action: str = None,
    current_user: dict = Depends(verify_admin)
):
    """Get audit logs with optional filters"""
    query = {}
    if username:
        query["username"] = username
    if action:
        query["action"] = action
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return logs

@api_router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, current_user: dict = Depends(verify_can_manage_users)):
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Set default permissions if not provided
    permissions = user_data.permissions
    if permissions is None:
        if user_data.role == "admin":
            permissions = {
                "basic_info": True,
                "email": True,
                "phone": True,
                "address": True,
                "dues_tracking": True,
                "meeting_attendance": True,
                "admin_actions": True
            }
        else:
            permissions = {
                "basic_info": True,
                "email": False,
                "phone": False,
                "address": False,
                "dues_tracking": False,
                "meeting_attendance": False,
                "admin_actions": False
            }
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        chapter=user_data.chapter,
        title=user_data.title,
        permissions=permissions
    )
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="user_create",
        details=f"Created user: {user.username} (role: {user.role})"
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        permissions=user.permissions,
        created_at=user.created_at
    )

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(verify_can_manage_users)):
    """Update a user - Only National Prez, VP, or SEC can edit system users"""
    # Check if current user is authorized (National Prez, VP, or SEC)
    user_chapter = current_user.get('chapter', '')
    user_title = current_user.get('title', '')
    AUTHORIZED_TITLES = ['Prez', 'VP', 'SEC']
    
    if user_chapter != 'National' or user_title not in AUTHORIZED_TITLES:
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can edit system users")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if user_data.email:
        # Check if email is already used by another user
        existing_email = await db.users.find_one({"email": user_data.email, "id": {"$ne": user_id}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data['email'] = user_data.email
    if user_data.password:
        update_data['password_hash'] = hash_password(user_data.password)
    if user_data.role:
        update_data['role'] = user_data.role
    if user_data.chapter is not None:
        update_data['chapter'] = user_data.chapter
    if user_data.title is not None:
        update_data['title'] = user_data.title
    if user_data.permissions is not None:
        update_data['permissions'] = user_data.permissions
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log activity
    updates = []
    if user_data.email:
        updates.append(f"email to {user_data.email}")
    if user_data.password:
        updates.append("password")
    if user_data.role:
        updates.append(f"role to {user_data.role}")
    if user_data.chapter is not None:
        updates.append(f"chapter to {user_data.chapter}")
    if user_data.title is not None:
        updates.append(f"title to {user_data.title}")
    if user_data.permissions is not None:
        updates.append("permissions")
    
    await log_activity(
        username=current_user["username"],
        action="user_update",
        details=f"Updated user: {user['username']} - changed: {', '.join(updates)}"
    )
    
    # Get updated user data to return
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if isinstance(updated_user.get('created_at'), str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    
    return updated_user

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(verify_can_manage_users)):
    """Delete a user - Only National Prez, VP, or SEC can delete system users"""
    # Check if current user is authorized (National Prez, VP, or SEC)
    user_chapter = current_user.get('chapter', '')
    user_title = current_user.get('title', '')
    AUTHORIZED_TITLES = ['Prez', 'VP', 'SEC']
    
    if user_chapter != 'National' or user_title not in AUTHORIZED_TITLES:
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can delete system users")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting the last admin
    if user['role'] == 'admin':
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="user_delete",
        details=f"Deleted user: {user['username']} (role: {user['role']})"
    )
    
    return {"message": "User deleted successfully"}

# Password change endpoint
class PasswordChange(BaseModel):
    new_password: str

@api_router.put("/users/{user_id}/password")
async def change_user_password(user_id: str, password_data: PasswordChange, current_user: dict = Depends(verify_can_manage_users)):
    """Change password for a user - Only National Prez, VP, or SEC can change other users' passwords"""
    # Check if current user is authorized (National Prez, VP, or SEC)
    user_chapter = current_user.get('chapter', '')
    user_title = current_user.get('title', '')
    AUTHORIZED_TITLES = ['Prez', 'VP', 'SEC']
    
    if user_chapter != 'National' or user_title not in AUTHORIZED_TITLES:
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can change other users' passwords")
    
    # Validate password
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Hash new password using helper function
    password_hash = hash_password(password_data.new_password)
    
    # Update user password
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": password_hash}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get username for logging
    user = await db.users.find_one({"id": user_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="password_change",
        details=f"Changed password for user: {user['username']}"
    )
    
    return {"message": "Password changed successfully"}


class OwnPasswordChange(BaseModel):
    current_password: str
    new_password: str


@api_router.put("/auth/change-password")
async def change_own_password(password_data: OwnPasswordChange, current_user: dict = Depends(verify_token)):
    """Allow any user to change their own password"""
    # Get the current user's full data
    user = await db.users.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update password
    await db.users.update_one(
        {"username": current_user["username"]},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="password_change",
        details="User changed their own password"
    )
    
    return {"message": "Password changed successfully"}


# Invite endpoints
@api_router.post("/invites")
async def create_invite(invite_data: InviteCreate, current_user: dict = Depends(verify_can_manage_users)):
    # Check if user with email already exists
    existing = await db.users.find_one({"username": invite_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check for existing unused invite
    existing_invite = await db.invites.find_one({"email": invite_data.email, "used": False})
    if existing_invite:
        raise HTTPException(status_code=400, detail="An active invitation already exists for this email")
    
    # Create invite - include chapter and title
    invite = Invite(
        email=invite_data.email,
        role=invite_data.role,
        chapter=invite_data.chapter,
        title=invite_data.title,
        permissions=invite_data.permissions,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    doc = invite.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['expires_at'] = doc['expires_at'].isoformat()
    await db.invites.insert_one(doc)
    
    # Send email
    email_sent = await send_invite_email(invite.email, invite.token, invite.role)
    
    return {
        "message": "Invitation created and email sent" if email_sent else "Invitation created (email failed to send)",
        "invite_link": f"{FRONTEND_URL}/accept-invite?token={invite.token}",
        "email_sent": email_sent
    }

@api_router.get("/invites/{token}")
async def get_invite(token: str):
    invite = await db.invites.find_one({"token": token, "used": False}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    
    # Check if expired
    if isinstance(invite['expires_at'], str):
        expires_at = datetime.fromisoformat(invite['expires_at'])
    else:
        expires_at = invite['expires_at']
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    return {
        "email": invite['email'],
        "role": invite['role'],
        "permissions": invite['permissions']
    }


@api_router.post("/invites/{token}/resend")
async def resend_invite(token: str, current_user: dict = Depends(verify_can_manage_users)):
    """Resend an invitation email"""
    invite = await db.invites.find_one({"token": token})
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invite['used']:
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    
    # Check if expired
    expires_at = datetime.fromisoformat(invite['expires_at']) if isinstance(invite['expires_at'], str) else invite['expires_at']
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This invitation has expired. Please create a new one.")
    
    # Resend email
    email_sent = await send_invite_email(invite['email'], invite['token'], invite['role'])
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send invitation email")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="invite_resend",
        details=f"Resent invitation to {invite['email']}"
    )
    
    return {
        "message": "Invitation email resent successfully",
        "email_sent": email_sent
    }


@api_router.post("/invites/accept")
async def accept_invite(accept_data: InviteAccept):
    invite = await db.invites.find_one({"token": accept_data.token, "used": False})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    
    # Check if expired
    if isinstance(invite['expires_at'], str):
        expires_at = datetime.fromisoformat(invite['expires_at'])
    else:
        expires_at = invite['expires_at']
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    # Check if username exists
    existing = await db.users.find_one({"username": accept_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user - include email from invite
    user = User(
        username=accept_data.username,
        email=invite['email'],  # Use email from the invite
        password_hash=hash_password(accept_data.password),
        role=invite['role'],
        chapter=invite.get('chapter'),  # Include chapter from invite
        title=invite.get('title'),  # Include title from invite
        permissions=invite['permissions']
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Mark invite as used
    await db.invites.update_one(
        {"token": accept_data.token},
        {"$set": {"used": True}}
    )
    
    # Generate login token
    token = create_access_token({
        "sub": user.username, 
        "role": user.role,
        "chapter": user.chapter,  # Include chapter for privacy/access control
        "title": user.title  # Include title for email privacy access control
    })
    
    return {
        "message": "Account created successfully",
        "token": token,
        "username": user.username,
        "role": user.role
    }

@api_router.get("/invites")
async def list_invites(current_user: dict = Depends(verify_can_manage_users)):
    """List all invites (used and unused)"""
    invites = await db.invites.find({}, {"_id": 0}).to_list(1000)
    
    # Convert datetime strings for display
    for invite in invites:
        if isinstance(invite.get('created_at'), str):
            invite['created_at'] = invite['created_at']
        if isinstance(invite.get('expires_at'), str):
            invite['expires_at'] = invite['expires_at']
    
    return invites

@api_router.delete("/invites/{token}")
async def delete_invite(token: str, current_user: dict = Depends(verify_admin)):
    """Delete a specific invite by token"""
    result = await db.invites.delete_one({"token": token})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invite not found")
    return {"message": "Invite deleted successfully"}

@api_router.delete("/invites/clear/unused")
async def clear_unused_invites(current_user: dict = Depends(verify_admin)):
    """Clear all unused invites"""
    result = await db.invites.delete_many({"used": False})
    return {
        "message": f"Cleared {result.deleted_count} unused invite(s)",
        "deleted_count": result.deleted_count
    }

# Archived records endpoints (admin only)
@api_router.get("/archived/members")
async def get_archived_members(current_user: dict = Depends(verify_admin)):
    """Get all archived members"""
    archived = await db.archived_members.find({}, {"_id": 0}).to_list(1000)
    # Sort by deletion date (newest first)
    archived.sort(key=lambda x: x.get('deleted_at', ''), reverse=True)
    return archived

@api_router.get("/archived/prospects")
async def get_archived_prospects(current_user: dict = Depends(verify_admin)):
    """Get all archived prospects"""
    archived = await db.archived_prospects.find({}, {"_id": 0}).to_list(1000)
    # Sort by deletion date (newest first)
    archived.sort(key=lambda x: x.get('deleted_at', ''), reverse=True)
    return archived

@api_router.post("/archived/members/{member_id}/restore")
async def restore_archived_member(member_id: str, current_user: dict = Depends(verify_admin)):
    """Restore an archived member back to active members"""
    global discord_bot
    
    # Get archived member
    archived_member = await db.archived_members.find_one({"id": member_id}, {"_id": 0})
    if not archived_member:
        raise HTTPException(status_code=404, detail="Archived member not found")
    
    # Remove archive-specific fields
    archived_member.pop("deletion_reason", None)
    archived_member.pop("deleted_by", None)
    archived_member.pop("deleted_at", None)
    
    # Update timestamps
    archived_member["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Move back to active members
    await db.members.insert_one(archived_member)
    
    # Remove from archived collection
    await db.archived_members.delete_one({"id": member_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_restore",
        details=f"Restored member: {archived_member.get('name', 'Unknown')} ({archived_member.get('handle', 'Unknown')})"
    )
    
    # Send Discord invite to the member's personal email
    discord_invite_sent = False
    personal_email = archived_member.get("personal_email")
    member_name = archived_member.get("name", "Member")
    member_handle = archived_member.get("handle", "")
    
    if personal_email and discord_bot and DISCORD_GUILD_ID:
        try:
            guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
            if guild:
                # Find a suitable channel to create invite from (first text channel)
                invite_channel = None
                for channel in guild.text_channels:
                    # Prefer a general/welcome channel if exists
                    if any(name in channel.name.lower() for name in ['general', 'welcome', 'lobby']):
                        invite_channel = channel
                        break
                if not invite_channel and guild.text_channels:
                    invite_channel = guild.text_channels[0]
                
                if invite_channel:
                    # Create a single-use invite that expires in 7 days
                    invite = await invite_channel.create_invite(
                        max_age=604800,  # 7 days in seconds
                        max_uses=1,
                        unique=True,
                        reason=f"Invite for restored member {member_handle}"
                    )
                    
                    # Send email with the invite from support email
                    if smtp_configured:
                        try:
                            subject = "Welcome Back to Brothers of the Highway Discord!"
                            support_email = "support@boh2158.org"
                            
                            text_content = f"""
Hello {member_name},

Great news! Your membership with Brothers of the Highway has been restored.

You're invited to rejoin our Discord server:
{invite.url}

This invite link is valid for 7 days and can only be used once.

Welcome back, Brother!

- Brothers of the Highway
"""
                            
                            html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #ffffff; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #16213e; padding: 30px; border-radius: 10px;">
        <h2 style="color: #e94560;">Welcome Back, {member_name}!</h2>
        <p>Great news! Your membership with <strong>Brothers of the Highway</strong> has been restored.</p>
        <p>You're invited to rejoin our Discord server:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{invite.url}" style="background-color: #5865F2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-size: 18px; display: inline-block;">
                Rejoin Discord Server
            </a>
        </p>
        <p style="color: #888; font-size: 12px;">This invite link is valid for 7 days and can only be used once.</p>
        <p style="margin-top: 30px;">Welcome back, Brother!</p>
        <p style="color: #e94560;">- Brothers of the Highway</p>
    </div>
</body>
</html>
"""
                            
                            msg = MIMEMultipart('alternative')
                            msg['Subject'] = subject
                            msg['From'] = support_email
                            msg['To'] = personal_email
                            msg.attach(MIMEText(text_content, 'plain'))
                            msg.attach(MIMEText(html_content, 'html'))
                            
                            with smtplib.SMTP_SSL(SMTP_HOST, int(SMTP_PORT)) as server:
                                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                                server.sendmail(support_email, personal_email, msg.as_string())
                            
                            discord_invite_sent = True
                            sys.stderr.write(f"✅ Discord invite sent to {personal_email} for restored member {member_handle}\n")
                            sys.stderr.flush()
                        except Exception as email_err:
                            sys.stderr.write(f"⚠️ Failed to send Discord invite email: {email_err}\n")
                            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"⚠️ Failed to create Discord invite: {e}\n")
            sys.stderr.flush()
    
    response_msg = "Member restored successfully"
    if discord_invite_sent:
        response_msg += f". Discord invite sent to {personal_email}"
    elif personal_email and not discord_bot:
        response_msg += ". Discord invite not sent (bot not connected)"
    elif not personal_email:
        response_msg += ". No personal email on file for Discord invite"
    
    return {"message": response_msg, "discord_invite_sent": discord_invite_sent}

@api_router.post("/archived/prospects/{prospect_id}/restore")
async def restore_archived_prospect(prospect_id: str, current_user: dict = Depends(verify_admin)):
    """Restore an archived prospect back to active prospects"""
    # Get archived prospect
    archived_prospect = await db.archived_prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not archived_prospect:
        raise HTTPException(status_code=404, detail="Archived prospect not found")
    
    # Remove archive-specific fields
    archived_prospect.pop("deletion_reason", None)
    archived_prospect.pop("deleted_by", None)
    archived_prospect.pop("deleted_at", None)
    
    # Update timestamps
    archived_prospect["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Move back to active prospects
    await db.prospects.insert_one(archived_prospect)
    
    # Remove from archived collection
    await db.archived_prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_restore",
        details=f"Restored prospect: {archived_prospect.get('name', 'Unknown')} ({archived_prospect.get('handle', 'Unknown')})"
    )
    
    return {"message": "Prospect restored successfully"}

@api_router.delete("/archived/members/{member_id}")
async def delete_archived_member(member_id: str, current_user: dict = Depends(verify_admin)):
    """Permanently delete an archived member"""
    # Get archived member
    archived_member = await db.archived_members.find_one({"id": member_id}, {"_id": 0})
    if not archived_member:
        raise HTTPException(status_code=404, detail="Archived member not found")
    
    # Delete from archived collection
    result = await db.archived_members.delete_one({"id": member_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete archived member")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="archived_member_delete",
        details=f"Permanently deleted archived member: {archived_member.get('name', 'Unknown')} ({archived_member.get('handle', 'Unknown')})"
    )
    
    return {"message": "Archived member permanently deleted"}

@api_router.delete("/archived/prospects/{prospect_id}")
async def delete_archived_prospect(prospect_id: str, current_user: dict = Depends(verify_admin)):
    """Permanently delete an archived prospect"""
    # Get archived prospect
    archived_prospect = await db.archived_prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not archived_prospect:
        raise HTTPException(status_code=404, detail="Archived prospect not found")
    
    # Delete from archived collection
    result = await db.archived_prospects.delete_one({"id": prospect_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete archived prospect")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="archived_prospect_delete",
        details=f"Permanently deleted archived prospect: {archived_prospect.get('name', 'Unknown')} ({archived_prospect.get('handle', 'Unknown')})"
    )
    
    return {"message": "Archived prospect permanently deleted"}

@api_router.get("/archived/members/export/csv")
async def export_archived_members_csv(current_user: dict = Depends(verify_admin)):
    """Export archived members to CSV"""
    archived = await db.archived_members.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all archived members
    decrypted_archived = [decrypt_member_sensitive_data(member) for member in archived]
    
    # Create CSV content
    csv_content = "Handle,Name,Email,Phone,Address,Chapter,Title,Date of Birth,Join Date,Deletion Reason,Archived By,Archived At (CST)\n"
    
    for member in decrypted_archived:
        # Convert archived timestamp to CST
        deleted_at = member.get('deleted_at', '')
        if deleted_at:
            from datetime import datetime
            dt = datetime.fromisoformat(deleted_at.replace('Z', '+00:00'))
            # Convert to CST (UTC-6)
            import pytz
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt.astimezone(cst)
            archived_time = dt_cst.strftime('%m/%d/%Y %I:%M %p')
        else:
            archived_time = ''
        
        row = [
            member.get('handle', ''),
            member.get('name', ''),
            member.get('email', ''),
            member.get('phone', ''),
            member.get('address', ''),
            member.get('chapter', ''),
            member.get('title', ''),
            member.get('dob', ''),
            member.get('join_date', ''),
            member.get('deletion_reason', '').replace(',', ';').replace('\n', ' '),
            member.get('deleted_by', ''),
            archived_time
        ]
        csv_content += ','.join(f'"{str(v)}"' for v in row) + '\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=archived_members.csv"}
    )

@api_router.get("/archived/prospects/export/csv")
async def export_archived_prospects_csv(current_user: dict = Depends(verify_admin)):
    """Export archived prospects to CSV"""
    archived = await db.archived_prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all archived prospects
    decrypted_archived = [decrypt_member_sensitive_data(prospect) for prospect in archived]
    
    # Create CSV content
    csv_content = "Handle,Name,Email,Phone,Address,Date of Birth,Join Date,Deletion Reason,Archived By,Archived At (CST)\n"
    
    for prospect in decrypted_archived:
        # Convert archived timestamp to CST
        deleted_at = prospect.get('deleted_at', '')
        if deleted_at:
            from datetime import datetime
            dt = datetime.fromisoformat(deleted_at.replace('Z', '+00:00'))
            # Convert to CST (UTC-6)
            import pytz
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt.astimezone(cst)
            archived_time = dt_cst.strftime('%m/%d/%Y %I:%M %p')
        else:
            archived_time = ''
        
        row = [
            prospect.get('handle', ''),
            prospect.get('name', ''),
            prospect.get('email', ''),
            prospect.get('phone', ''),
            prospect.get('address', ''),
            prospect.get('dob', ''),
            prospect.get('join_date', ''),
            prospect.get('deletion_reason', '').replace(',', ';').replace('\n', ' '),
            prospect.get('deleted_by', ''),
            archived_time
        ]
        csv_content += ','.join(f'"{str(v)}"' for v in row) + '\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=archived_prospects.csv"}
    )

# Private messaging endpoints (all authenticated users)
@api_router.post("/messages", response_model=PrivateMessage)
async def send_private_message(message: PrivateMessageCreate, current_user: dict = Depends(verify_token)):
    """Send a private message to another user"""
    user_role = current_user.get('role')
    
    # Verify recipient exists
    recipient_user = await db.users.find_one({"username": message.recipient})
    if not recipient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # If sender is prospect, verify recipient is HA chapter officer
    if user_role == 'prospect':
        ha_officers = ['Chap', 'Sancho', 'Tapeworm', 'Hee Haw', 'Phantom']
        if message.recipient not in ha_officers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Prospects can only message Highway Asylum chapter officers"
            )
    
    private_message = PrivateMessage(
        sender=current_user['username'],
        recipient=message.recipient,
        message=message.message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        read=False
    )
    
    await db.private_messages.insert_one(private_message.model_dump())
    
    return private_message

@api_router.get("/messages/conversations")
async def get_conversations(current_user: dict = Depends(verify_token)):
    """Get list of conversations with last message"""
    username = current_user['username']
    
    # Get all messages where user is sender or recipient, sorted by timestamp
    # Exclude archived conversations
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username},
                {"recipient": username}
            ],
            "archived_by": {"$ne": username}  # Exclude archived
        },
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).sort("timestamp", -1).to_list(None)
    
    # Group by conversation partner
    conversations_dict = {}
    for msg in messages:
        # Determine the other user in the conversation
        other_user = msg['recipient'] if msg['sender'] == username else msg['sender']
        
        if other_user not in conversations_dict:
            conversations_dict[other_user] = {
                "username": other_user,
                "lastMessage": msg,
                "unreadCount": 0
            }
        
        # Count unread messages (where current user is recipient and message is unread)
        if msg['recipient'] == username and not msg['read']:
            conversations_dict[other_user]['unreadCount'] += 1
    
    # Convert dict to list and sort by last message timestamp
    conversations = list(conversations_dict.values())
    conversations.sort(key=lambda x: x['lastMessage']['timestamp'], reverse=True)
    
    return conversations

@api_router.get("/messages/{other_user}")
async def get_messages_with_user(other_user: str, current_user: dict = Depends(verify_token)):
    """Get messages with a specific user"""
    username = current_user['username']
    
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ]
        },
        {"_id": 0}
    ).sort("timestamp", 1).limit(100).to_list(100)
    
    return messages

@api_router.post("/messages/mark_read/{other_user}")
async def mark_private_messages_read(other_user: str, current_user: dict = Depends(verify_token)):
    """Mark all messages from a specific user as read"""
    username = current_user['username']
    
    await db.private_messages.update_many(
        {
            "sender": other_user,
            "recipient": username,
            "read": False
        },
        {"$set": {"read": True}}
    )
    
    return {"message": "Messages marked as read"}

@api_router.get("/messages/unread/count")
async def get_unread_private_messages_count(current_user: dict = Depends(verify_token)):
    """Get count of unread private messages"""
    username = current_user['username']
    
    count = await db.private_messages.count_documents({
        "recipient": username,
        "read": False
    })
    
    return {"unread_count": count}

@api_router.post("/messages/conversation/{other_user}/archive")
async def archive_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Archive conversation with a specific user"""
    username = current_user['username']
    
    # Add current user to archived_by list for all messages in this conversation
    result = await db.private_messages.update_many(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ],
            "archived_by": {"$ne": username}
        },
        {"$push": {"archived_by": username}}
    )
    
    return {
        "message": f"Conversation with {other_user} archived",
        "modified_count": result.modified_count
    }

@api_router.post("/messages/conversation/{other_user}/unarchive")
async def unarchive_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Unarchive conversation with a specific user"""
    username = current_user['username']
    
    # Remove current user from archived_by list for all messages in this conversation
    result = await db.private_messages.update_many(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ]
        },
        {"$pull": {"archived_by": username}}
    )
    
    return {
        "message": f"Conversation with {other_user} unarchived",
        "modified_count": result.modified_count
    }

@api_router.get("/messages/conversations/archived")
async def get_archived_conversations(current_user: dict = Depends(verify_token)):
    """Get list of archived conversations"""
    username = current_user['username']
    
    # Get all messages where user is sender or recipient AND has archived the conversation
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username},
                {"recipient": username}
            ],
            "archived_by": username
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(None)
    
    # Group by conversation partner
    conversations_dict = {}
    for msg in messages:
        other_user = msg['recipient'] if msg['sender'] == username else msg['sender']
        
        if other_user not in conversations_dict:
            conversations_dict[other_user] = {
                "username": other_user,
                "lastMessage": msg,
                "unreadCount": 0
            }
        
        if msg['recipient'] == username and not msg['read']:
            conversations_dict[other_user]['unreadCount'] += 1
    
    conversations = list(conversations_dict.values())
    conversations.sort(key=lambda x: x['lastMessage']['timestamp'], reverse=True)
    
    return conversations

@api_router.delete("/messages/conversation/{other_user}")
async def delete_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Delete entire conversation with a specific user"""
    username = current_user['username']
    
    # Delete all messages between current user and the other user
    result = await db.private_messages.delete_many({
        "$or": [
            {"sender": username, "recipient": other_user},
            {"sender": other_user, "recipient": username}
        ]
    })
    
    return {
        "message": f"Conversation with {other_user} deleted",
        "deleted_count": result.deleted_count
    }

@api_router.get("/messages/monitor/all")
async def get_all_messages_for_monitoring(current_user: dict = Depends(verify_token)):
    """Get all private messages for monitoring - Lonestar only"""
    username = current_user['username']
    
    # Only allow user 'Lonestar' to access this endpoint
    if username.lower() != 'lonestar':
        raise HTTPException(status_code=403, detail="Access denied. This feature is restricted to Lonestar only.")
    
    # Get all private messages, sorted by timestamp (newest first)
    messages = await db.private_messages.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(1000).to_list(1000)
    
    return messages


# Support Message endpoints
@api_router.post("/support/messages")
async def create_support_message(support_msg: SupportMessageCreate):
    """Create a new support message (no authentication required)"""
    message = SupportMessage(
        name=support_msg.name,
        email=support_msg.email,
        message=support_msg.message,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    doc = message.model_dump()
    # Encrypt sensitive data
    doc = encrypt_support_message(doc)
    await db.support_messages.insert_one(doc)
    
    return {"message": "Support message submitted successfully", "id": message.id}

@api_router.get("/support/messages")
async def get_support_messages(current_user: dict = Depends(verify_token)):
    """Get all support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    messages = await db.support_messages.find({}).sort("timestamp", -1).to_list(length=None)
    
    for i, msg in enumerate(messages):
        messages[i].pop('_id', None)
        # Decrypt sensitive data
        messages[i] = decrypt_support_message(messages[i])
    
    return messages

@api_router.post("/support/messages/{message_id}/reply")
async def reply_to_support_message(message_id: str, reply: SupportReply, current_user: dict = Depends(verify_token)):
    """Reply to a support message and send email (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    # Get the support message
    message = await db.support_messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    # Update message with reply
    await db.support_messages.update_one(
        {"id": message_id},
        {
            "$set": {
                "reply_text": reply.reply_text,
                "replied_at": datetime.now(timezone.utc).isoformat(),
                "status": "closed"
            }
        }
    )
    
    # Send email reply
    try:
        await send_email(
            to_email=message['email'],
            subject=f"Re: Support Request - {message['name']}",
            body=f"""Hello {message['name']},

Thank you for contacting Brothers of the Highway TC support.

Your message:
{message['message']}

Our response:
{reply.reply_text}

Best regards,
Brothers of the Highway TC Support Team
"""
        )
        
        return {"message": "Reply sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email reply: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email reply")


@api_router.delete("/support/messages/{message_id}")
async def delete_support_message(message_id: str, current_user: dict = Depends(verify_token)):
    """Delete a single support message (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    result = await db.support_messages.delete_one({"id": message_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    return {"message": "Support message deleted successfully"}


@api_router.get("/support/messages/count")
async def get_open_support_count(current_user: dict = Depends(verify_token)):
    """Get count of open support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    count = await db.support_messages.count_documents({"status": "open"})
    
    return {"count": count}


@api_router.delete("/support/messages/closed/all")
async def delete_closed_messages(current_user: dict = Depends(verify_token)):
    """Delete all closed/replied support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    result = await db.support_messages.delete_many({"status": "closed"})
    
    return {
        "message": f"Deleted {result.deleted_count} closed messages",
        "deleted_count": result.deleted_count
    }

@api_router.get("/support/messages/export")
async def export_support_messages(current_user: dict = Depends(verify_token)):
    """Export support messages to CSV (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    messages = await db.support_messages.find({}).sort("timestamp", -1).to_list(length=None)
    
    if not messages:
        raise HTTPException(status_code=404, detail="No messages to export")
    
    # Create CSV content
    csv_content = "ID,Name,Email,Message,Status,Submitted At,Reply,Replied At\n"
    
    for msg in messages:
        # Escape fields that might contain commas or quotes
        name = msg.get('name', '').replace('"', '""')
        email = msg.get('email', '').replace('"', '""')
        message = msg.get('message', '').replace('"', '""').replace('\n', ' ')
        status = msg.get('status', '')
        timestamp = msg.get('timestamp', '')
        reply = msg.get('reply_text', '').replace('"', '""').replace('\n', ' ') if msg.get('reply_text') else ''
        replied_at = msg.get('replied_at', '') if msg.get('replied_at') else ''
        
        csv_content += f'"{msg.get("id", "")}","{name}","{email}","{message}","{status}","{timestamp}","{reply}","{replied_at}"\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=support_messages.csv"}
    )


# Discord Analytics Endpoints
@api_router.get("/discord/test-activity")
async def test_discord_activity(current_user: dict = Depends(verify_admin)):
    """Test endpoint to check if Discord activity is being recorded"""
    try:
        # Check if there's any voice or text activity in the database
        voice_count = await db.discord_voice_activity.count_documents({})
        text_count = await db.discord_text_activity.count_documents({})
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_voice = await db.discord_voice_activity.find({
            "joined_at": {"$gte": yesterday}
        }, {"_id": 0}).limit(5).to_list(None)
        
        recent_text = await db.discord_text_activity.find({
            "last_message_at": {"$gte": yesterday}
        }, {"_id": 0}).limit(5).to_list(None)
        
        # Check bot status and guild info
        bot_info = {
            "connected": discord_bot is not None,
            "guilds": len(discord_bot.guilds) if discord_bot else 0,
            "guild_info": []
        }
        
        if discord_bot:
            for guild in discord_bot.guilds:
                bot_info["guild_info"].append({
                    "name": guild.name,
                    "id": str(guild.id), 
                    "member_count": guild.member_count,
                    "voice_channels": len(guild.voice_channels),
                    "text_channels": len(guild.text_channels),
                    "bot_permissions": guild.me.guild_permissions.value
                })
        
        # Convert datetime objects to ISO strings for JSON serialization
        for record in recent_voice:
            if 'joined_at' in record and isinstance(record['joined_at'], datetime):
                record['joined_at'] = record['joined_at'].isoformat()
            if 'left_at' in record and isinstance(record['left_at'], datetime):
                record['left_at'] = record['left_at'].isoformat()
        
        for record in recent_text:
            if 'last_message_at' in record and isinstance(record['last_message_at'], datetime):
                record['last_message_at'] = record['last_message_at'].isoformat()
        
        return {
            "bot_status": "running" if discord_bot else "not_running",
            "bot_info": bot_info,
            "total_voice_records": voice_count,
            "total_text_records": text_count,
            "recent_voice_activity": len(recent_voice),
            "recent_text_activity": len(recent_text),
            "recent_voice_records": recent_voice,
            "recent_text_records": recent_text,
            "currently_tracking": len(discord_bot.voice_sessions) if discord_bot and hasattr(discord_bot, 'voice_sessions') else 0,
            "message": f"Bot is {'active' if discord_bot else 'inactive'}. Voice: {voice_count} records, Text: {text_count} records"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@api_router.post("/discord/resync-voice")
async def resync_discord_voice_tracking(current_user: dict = Depends(verify_admin)):
    """Resync voice tracking by scanning all voice channels for connected users"""
    try:
        if not discord_bot:
            raise HTTPException(status_code=503, detail="Discord bot is not running")
        
        # Clear existing tracked sessions (they may be stale)
        old_count = len(discord_bot.voice_sessions)
        discord_bot.voice_sessions.clear()
        
        # Scan all guilds for users in voice channels
        new_tracked = []
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        for guild in discord_bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if not member.bot:
                        user_id = str(member.id)
                        discord_bot.voice_sessions[user_id] = {
                            'joined_at': now,
                            'channel_id': str(voice_channel.id),
                            'channel_name': voice_channel.name
                        }
                        new_tracked.append({
                            "user": member.display_name,
                            "channel": voice_channel.name
                        })
        
        return {
            "success": True,
            "previous_tracking": old_count,
            "now_tracking": len(discord_bot.voice_sessions),
            "users": new_tracked,
            "message": f"Resynced voice tracking. Now tracking {len(new_tracked)} user(s) in voice channels."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resync error: {str(e)}")


@api_router.post("/discord/sync-members")
async def sync_discord_members(current_user: dict = Depends(verify_admin)):
    """Sync Discord members - remove members who left the server and clean up their analytics"""
    try:
        if not discord_bot:
            raise HTTPException(status_code=503, detail="Discord bot is not running")
        
        # Get current Discord members from the bot
        current_discord_ids = set()
        updated_count = 0
        added_count = 0
        
        for guild in discord_bot.guilds:
            for member in guild.members:
                discord_id = str(member.id)
                current_discord_ids.add(discord_id)
                
                # Update or insert member
                existing = await db.discord_members.find_one({"discord_id": discord_id})
                
                member_data = {
                    "discord_id": discord_id,
                    "username": member.name,
                    "display_name": member.display_name,
                    "avatar_url": str(member.avatar.url) if member.avatar else None,
                    "is_bot": member.bot,
                    "last_seen": datetime.now(timezone.utc)
                }
                
                if existing:
                    # Preserve linked member_id if exists
                    if existing.get("member_id"):
                        member_data["member_id"] = existing["member_id"]
                    await db.discord_members.update_one(
                        {"discord_id": discord_id},
                        {"$set": member_data}
                    )
                    updated_count += 1
                else:
                    await db.discord_members.insert_one(member_data)
                    added_count += 1
        
        # Remove members no longer in Discord and clean up their analytics
        db_members = await db.discord_members.find({}, {"discord_id": 1}).to_list(None)
        removed_count = 0
        removed_members = []
        analytics_cleaned = {"voice": 0, "text": 0}
        
        for db_member in db_members:
            if db_member["discord_id"] not in current_discord_ids:
                discord_id = db_member["discord_id"]
                
                # Get member info before removing
                full_member = await db.discord_members.find_one({"discord_id": discord_id})
                removed_members.append({
                    "discord_id": discord_id,
                    "username": full_member.get("username") if full_member else "Unknown",
                    "display_name": full_member.get("display_name") if full_member else "Unknown"
                })
                
                # Remove from discord_members collection
                await db.discord_members.delete_one({"discord_id": discord_id})
                
                # Clean up voice analytics for this member
                voice_result = await db.discord_voice_activity.delete_many({"discord_id": discord_id})
                analytics_cleaned["voice"] += voice_result.deleted_count
                
                # Clean up text analytics for this member
                text_result = await db.discord_text_activity.delete_many({"discord_id": discord_id})
                analytics_cleaned["text"] += text_result.deleted_count
                
                removed_count += 1
        
        # Get final count
        final_count = await db.discord_members.count_documents({})
        
        return {
            "success": True,
            "discord_server_count": len(current_discord_ids),
            "database_count": final_count,
            "updated": updated_count,
            "added": added_count,
            "removed": removed_count,
            "removed_members": removed_members,
            "analytics_cleaned": analytics_cleaned,
            "message": f"Synced members. Updated: {updated_count}, Added: {added_count}, Removed: {removed_count}. Cleaned {analytics_cleaned['voice']} voice and {analytics_cleaned['text']} text analytics records."
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@api_router.post("/discord/cleanup-analytics")
async def cleanup_discord_analytics(current_user: dict = Depends(verify_admin)):
    """Clean up Discord analytics for members no longer in the server.
    This removes orphaned voice and text activity records.
    """
    try:
        if not discord_bot:
            raise HTTPException(status_code=503, detail="Discord bot is not running")
        
        # Get current Discord member IDs from the bot
        current_discord_ids = set()
        for guild in discord_bot.guilds:
            for member in guild.members:
                current_discord_ids.add(str(member.id))
        
        # Find all unique discord IDs in analytics
        voice_ids = await db.discord_voice_activity.distinct("discord_id")
        text_ids = await db.discord_text_activity.distinct("discord_id")
        
        # Also check the old field name "discord_user_id" if it exists
        voice_user_ids = await db.discord_voice_activity.distinct("discord_user_id")
        text_user_ids = await db.discord_text_activity.distinct("discord_user_id")
        
        all_analytics_ids = set(str(id) for id in voice_ids + text_ids + voice_user_ids + text_user_ids if id)
        
        # Find IDs that are in analytics but not in Discord server
        orphaned_ids = all_analytics_ids - current_discord_ids
        
        cleaned = {"voice": 0, "text": 0, "orphaned_users": []}
        
        for orphaned_id in orphaned_ids:
            # Get user info if available
            member_info = await db.discord_members.find_one({"discord_id": orphaned_id})
            user_name = member_info.get("display_name") if member_info else f"Unknown ({orphaned_id})"
            
            # Delete voice analytics
            voice_result = await db.discord_voice_activity.delete_many({
                "$or": [
                    {"discord_id": orphaned_id},
                    {"discord_user_id": orphaned_id}
                ]
            })
            cleaned["voice"] += voice_result.deleted_count
            
            # Delete text analytics
            text_result = await db.discord_text_activity.delete_many({
                "$or": [
                    {"discord_id": orphaned_id},
                    {"discord_user_id": orphaned_id}
                ]
            })
            cleaned["text"] += text_result.deleted_count
            
            if voice_result.deleted_count > 0 or text_result.deleted_count > 0:
                cleaned["orphaned_users"].append({
                    "discord_id": orphaned_id,
                    "name": user_name,
                    "voice_records_removed": voice_result.deleted_count,
                    "text_records_removed": text_result.deleted_count
                })
        
        return {
            "success": True,
            "current_server_members": len(current_discord_ids),
            "orphaned_analytics_users": len(orphaned_ids),
            "voice_records_cleaned": cleaned["voice"],
            "text_records_cleaned": cleaned["text"],
            "details": cleaned["orphaned_users"],
            "message": f"Cleaned up analytics for {len(cleaned['orphaned_users'])} users no longer in Discord. Removed {cleaned['voice']} voice and {cleaned['text']} text records."
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")


@api_router.post("/discord/simulate-activity")
async def simulate_discord_activity(current_user: dict = Depends(verify_admin)):
    """Simulate Discord activity for testing purposes"""
    try:
        # Create sample voice activity
        now = datetime.now(timezone.utc)
        thirty_min_ago = now - timedelta(minutes=30)
        
        voice_activity = {
            'id': str(uuid.uuid4()),
            'discord_user_id': '12345678901234567890',  # Test user ID
            'channel_id': '98765432109876543210',
            'channel_name': 'General Voice',
            'joined_at': thirty_min_ago,
            'left_at': now,
            'duration_seconds': 1800,  # 30 minutes
            'date': now.date().isoformat()
        }
        
        # Create sample text activity
        text_activity = {
            'id': str(uuid.uuid4()),
            'discord_user_id': '12345678901234567890',  # Test user ID
            'channel_id': '11111111111111111111',
            'channel_name': 'general',
            'message_count': 5,
            'date': now.date().isoformat(),
            'last_message_at': now
        }
        
        # Insert test data (MongoDB will add _id automatically)
        voice_result = await db.discord_voice_activity.insert_one(voice_activity)
        text_result = await db.discord_text_activity.insert_one(text_activity)
        
        # Convert datetime objects to ISO strings for JSON serialization
        voice_activity_response = voice_activity.copy()
        voice_activity_response['joined_at'] = voice_activity['joined_at'].isoformat()
        voice_activity_response['left_at'] = voice_activity['left_at'].isoformat()
        
        text_activity_response = text_activity.copy()
        text_activity_response['last_message_at'] = text_activity['last_message_at'].isoformat()
        
        return {
            "message": "Test activity created successfully",
            "voice_activity": voice_activity_response,
            "text_activity": text_activity_response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@api_router.get("/discord/members")
async def get_discord_members(current_user: dict = Depends(verify_admin)):
    """Get Discord server members list - returns cached data from database"""
    try:
        # First try to fetch fresh data from Discord API
        api_success = False
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
            guild_id = "991898490743574628"  # Brothers of the Highway Discord server
            async with session.get(f'https://discord.com/api/v10/guilds/{guild_id}/members?limit=1000', headers=headers) as resp:
                if resp.status == 200:
                    api_success = True
                    discord_members = await resp.json()
                    
                    # Store/update members in database
                    for member in discord_members:
                        user = member['user']
                        discord_member = DiscordMember(
                            discord_id=user['id'],
                            username=user['username'],
                            display_name=member.get('nick') or user.get('display_name'),
                            avatar_url=f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else None,
                            joined_at=datetime.fromisoformat(member['joined_at'].replace('Z', '+00:00')) if member.get('joined_at') else None,
                            roles=member.get('roles', []),
                            is_bot=user.get('bot', False)
                        )
                        
                        # Upsert to database - preserve member_id if it exists
                        discord_data = discord_member.model_dump()
                        # Remove member_id from the update to preserve existing links
                        discord_data.pop('member_id', None)
                        
                        await db.discord_members.update_one(
                            {"discord_id": user['id']},
                            {"$set": discord_data},
                            upsert=True
                        )
                    
                    # Return stored members with linked member information
                    stored_members = await db.discord_members.find({}, {"_id": 0}).to_list(1000)
                    
                    # Enrich with linked member information
                    for discord_member in stored_members:
                        if discord_member.get("member_id"):
                            # Fetch the linked database member
                            db_member = await db.members.find_one(
                                {"id": discord_member["member_id"]},
                                {"_id": 0, "handle": 1, "name": 1}
                            )
                            if db_member:
                                discord_member["linked_member"] = {
                                    "handle": db_member.get("handle"),
                                    "name": db_member.get("name")
                                }
                    
                    return stored_members
        
        # If Discord API failed, return cached data from database
        if not api_success:
            print("⚠️ Discord API failed, returning cached members from database")
            stored_members = await db.discord_members.find(
                {"is_bot": {"$ne": True}},
                {"_id": 0}
            ).sort("display_name", 1).to_list(1000)
            
            # Enrich with linked member info
            for discord_member in stored_members:
                if discord_member.get("member_id"):
                    db_member = await db.members.find_one(
                        {"id": discord_member["member_id"]},
                        {"_id": 0, "handle": 1, "name": 1}
                    )
                    if db_member:
                        discord_member["linked_member"] = {
                            "handle": db_member.get("handle"),
                            "name": db_member.get("name")
                        }
            
            return stored_members
                
    except Exception as e:
        # On any error, try to return cached data
        try:
            print(f"⚠️ Error fetching Discord members: {str(e)}, returning cached data")
            stored_members = await db.discord_members.find(
                {"is_bot": {"$ne": True}},
                {"_id": 0}
            ).sort("display_name", 1).to_list(1000)
            
            for discord_member in stored_members:
                if discord_member.get("member_id"):
                    db_member = await db.members.find_one(
                        {"id": discord_member["member_id"]},
                        {"_id": 0, "handle": 1, "name": 1}
                    )
                    if db_member:
                        discord_member["linked_member"] = {
                            "handle": db_member.get("handle"),
                            "name": db_member.get("name")
                        }
            
            return stored_members
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"Discord API error: {str(e)}")


class DiscordLinkRequest(BaseModel):
    discord_id: str
    member_id: str


@api_router.post("/discord/link")
async def link_discord_member(request: DiscordLinkRequest, current_user: dict = Depends(verify_admin)):
    """Link a Discord member to a database member"""
    try:
        # Verify the database member exists
        db_member = await db.members.find_one({"id": request.member_id}, {"_id": 0, "handle": 1, "name": 1})
        if not db_member:
            raise HTTPException(status_code=404, detail="Database member not found")
        
        # Verify the Discord member exists
        discord_member = await db.discord_members.find_one({"discord_id": request.discord_id})
        if not discord_member:
            raise HTTPException(status_code=404, detail="Discord member not found")
        
        # Update the Discord member with the link
        result = await db.discord_members.update_one(
            {"discord_id": request.discord_id},
            {"$set": {
                "member_id": request.member_id,
                "linked_member_handle": db_member.get("handle"),
                "linked_member_name": db_member.get("name")
            }}
        )
        
        return {
            "message": f"Discord member linked to {db_member.get('handle')}",
            "discord_id": request.discord_id,
            "member_id": request.member_id,
            "linked_to": {
                "handle": db_member.get("handle"),
                "name": db_member.get("name")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking member: {str(e)}")


@api_router.post("/discord/unlink/{discord_id}")
async def unlink_discord_member(discord_id: str, current_user: dict = Depends(verify_admin)):
    """Unlink a Discord member from their database member"""
    try:
        # Verify the Discord member exists
        discord_member = await db.discord_members.find_one({"discord_id": discord_id})
        if not discord_member:
            raise HTTPException(status_code=404, detail="Discord member not found")
        
        # Remove the link
        result = await db.discord_members.update_one(
            {"discord_id": discord_id},
            {"$unset": {
                "member_id": "",
                "linked_member_handle": "",
                "linked_member_name": ""
            }}
        )
        
        return {
            "message": "Discord member unlinked successfully",
            "discord_id": discord_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking member: {str(e)}")


@api_router.get("/discord/linked-members")
async def get_linked_members_with_activity(current_user: dict = Depends(verify_admin)):
    """Get all linked Discord members with their last activity time"""
    try:
        # Get all linked Discord members
        linked_members = await db.discord_members.find(
            {"member_id": {"$exists": True, "$ne": None}},
            {"_id": 0}
        ).to_list(1000)
        
        result = []
        for dm in linked_members:
            discord_id = dm.get("discord_id")
            
            # Get last voice activity
            last_voice = await db.discord_voice_activity.find_one(
                {"discord_user_id": discord_id},
                {"_id": 0, "left_at": 1, "channel_name": 1},
                sort=[("left_at", -1)]
            )
            
            # Get last text activity
            last_text = await db.discord_text_activity.find_one(
                {"discord_user_id": discord_id},
                {"_id": 0, "last_message_at": 1, "channel_name": 1},
                sort=[("last_message_at", -1)]
            )
            
            # Get database member info
            db_member = None
            if dm.get("member_id"):
                db_member = await db.members.find_one(
                    {"id": dm["member_id"]},
                    {"_id": 0, "handle": 1, "name": 1, "chapter": 1, "title": 1}
                )
            
            # Helper to format time in CST using pytz
            def format_time_cst(dt):
                if not dt:
                    return None
                import pytz
                cst_tz = pytz.timezone('America/Chicago')
                
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                
                # If datetime is naive (no timezone), assume it's UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                
                # Convert to CST/CDT (handles DST automatically)
                cst_time = dt.astimezone(cst_tz)
                
                # Check if it's today in CST
                now_cst = datetime.now(timezone.utc).astimezone(cst_tz)
                if cst_time.date() == now_cst.date():
                    # Today: show only time
                    return cst_time.strftime("%-I:%M %p")
                else:
                    # Not today: show date and time
                    return cst_time.strftime("%b %-d, %-I:%M %p")
            
            # Format voice activity
            last_voice_time = None
            last_voice_time_raw = None
            last_voice_channel = None
            if last_voice and last_voice.get("left_at"):
                last_voice_time_raw = last_voice["left_at"].isoformat() if isinstance(last_voice["left_at"], datetime) else last_voice["left_at"]
                last_voice_time = format_time_cst(last_voice["left_at"])
                last_voice_channel = last_voice.get("channel_name")
            
            # Format text activity
            last_text_time = None
            last_text_time_raw = None
            last_text_channel = None
            if last_text and last_text.get("last_message_at"):
                last_text_time_raw = last_text["last_message_at"].isoformat() if isinstance(last_text["last_message_at"], datetime) else last_text["last_message_at"]
                last_text_time = format_time_cst(last_text["last_message_at"])
                last_text_channel = last_text.get("channel_name")
            
            # Determine overall last activity for sorting
            last_activity = None
            if last_voice_time_raw and last_text_time_raw:
                last_activity = max(last_voice_time_raw, last_text_time_raw)
            elif last_voice_time_raw:
                last_activity = last_voice_time_raw
            elif last_text_time_raw:
                last_activity = last_text_time_raw
            
            result.append({
                "discord_id": discord_id,
                "discord_username": dm.get("username"),
                "discord_display_name": dm.get("display_name"),
                "avatar_url": dm.get("avatar_url"),
                "member_id": dm.get("member_id"),
                "member_handle": db_member.get("handle") if db_member else dm.get("linked_member_handle"),
                "member_name": db_member.get("name") if db_member else dm.get("linked_member_name"),
                "member_chapter": db_member.get("chapter") if db_member else None,
                "member_title": db_member.get("title") if db_member else None,
                "last_activity": last_activity,
                "last_voice_time": last_voice_time,
                "last_voice_channel": last_voice_channel,
                "last_text_time": last_text_time,
                "last_text_channel": last_text_channel
            })
        
        # Sort by last activity (most recent first), with None values at the end
        result.sort(key=lambda x: x.get("last_activity") or "0000-00-00", reverse=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching linked members: {str(e)}")


@api_router.get("/discord/analytics")
async def get_discord_analytics(days: int = 90, current_user: dict = Depends(verify_admin)):
    """Get Discord analytics for specified number of days"""
    try:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        
        # Get voice activity stats (most active)
        voice_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id",
                "total_sessions": {"$sum": 1},
                "total_duration": {"$sum": "$duration_seconds"},
                "username": {"$first": "$discord_user_id"}  # We'll replace this with actual username
            }},
            {"$sort": {"total_duration": -1}},
            {"$limit": 10}
        ]
        
        # Get text activity stats (most active)
        text_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id", 
                "total_messages": {"$sum": "$message_count"},
                "username": {"$first": "$discord_user_id"}  # We'll replace this with actual username
            }},
            {"$sort": {"total_messages": -1}},
            {"$limit": 10}
        ]
        
        # Get daily activity aggregation
        daily_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$date",
                "voice_sessions": {"$sum": 1},
                "total_voice_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        # Execute aggregations
        voice_stats = await db.discord_voice_activity.aggregate(voice_pipeline).to_list(None)
        text_stats = await db.discord_text_activity.aggregate(text_pipeline).to_list(None)
        daily_activity = await db.discord_voice_activity.aggregate(daily_pipeline).to_list(None)
        
        # Get total members count
        total_members = await db.discord_members.count_documents({})
        
        # Get all Discord members for least active analysis
        all_members = await db.discord_members.find({}, {"discord_id": 1, "username": 1, "display_name": 1, "is_bot": 1, "_id": 0}).to_list(None)
        
        # Create member map for username resolution
        member_map = {}
        for member in all_members:
            member_map[member["discord_id"]] = {
                "username": member["username"],
                "display_name": member.get("display_name"),
                "is_bot": member.get("is_bot", False)
            }
        
        # Get all users who had voice activity
        voice_active_users = {stat["_id"] for stat in voice_stats}
        all_voice_users = await db.discord_voice_activity.distinct("discord_user_id", {
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        voice_active_users.update(all_voice_users)
        
        # Get all users who had text activity  
        text_active_users = {stat["_id"] for stat in text_stats}
        all_text_users = await db.discord_text_activity.distinct("discord_user_id", {
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        text_active_users.update(all_text_users)
        
        # Get voice activity totals per user (for scoring)
        voice_totals_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id",
                "total_duration": {"$sum": "$duration_seconds"},
                "last_voice_date": {"$max": "$date"}
            }}
        ]
        voice_totals = await db.discord_voice_activity.aggregate(voice_totals_pipeline).to_list(None)
        voice_totals_map = {v["_id"]: {"duration": v["total_duration"], "last_date": v["last_voice_date"]} for v in voice_totals}
        
        # Get text activity totals per user (for scoring)
        text_totals_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id",
                "total_messages": {"$sum": "$message_count"},
                "last_text_date": {"$max": "$date"}
            }}
        ]
        text_totals = await db.discord_text_activity.aggregate(text_totals_pipeline).to_list(None)
        text_totals_map = {t["_id"]: {"messages": t["total_messages"], "last_date": t["last_text_date"]} for t in text_totals}
        
        # Find least active members - include ALL members, sorted by activity score
        # Filter out bots and excluded usernames
        EXCLUDED_USERNAMES = ['bot', 'tv', 'aoh', 'craig', 'testdummy', 'gearjammerbot', 'bohadmin', 'boh admin', 'bohtc', 'hsb hillbilly', 'hillbilly']
        
        least_active_members = []
        for member in all_members:
            if member.get("is_bot"):
                continue  # Skip bots
            
            username = member.get("username", "").lower()
            display_name = (member.get("display_name") or "").lower()
            
            # Skip excluded usernames
            is_excluded = False
            for excluded in EXCLUDED_USERNAMES:
                if excluded in username or excluded in display_name or username.startswith(excluded) or display_name.startswith(excluded):
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
                
            discord_id = member["discord_id"]
            
            # Get activity data
            voice_data = voice_totals_map.get(discord_id, {"duration": 0, "last_date": None})
            text_data = text_totals_map.get(discord_id, {"messages": 0, "last_date": None})
            
            voice_duration = voice_data["duration"]
            text_messages = text_data["messages"]
            
            # Calculate activity score (voice duration in minutes + text messages * 2)
            # Lower score = less active
            activity_score = (voice_duration / 60) + (text_messages * 2)
            
            # Determine last activity date
            last_voice = voice_data["last_date"]
            last_text = text_data["last_date"]
            
            last_active = None
            if last_voice and last_text:
                last_active = max(last_voice, last_text)
            elif last_voice:
                last_active = last_voice
            elif last_text:
                last_active = last_text
            
            least_active_members.append({
                "discord_id": discord_id,
                "username": member["username"],
                "display_name": member.get("display_name") or member["username"],
                "voice_activity": voice_duration > 0,
                "text_activity": text_messages > 0,
                "voice_duration": voice_duration,
                "text_messages": text_messages,
                "activity_score": activity_score,
                "last_active": last_active
            })
        
        # Sort by activity score (ascending) - least active first
        least_active_members.sort(key=lambda x: (x["activity_score"], x["username"].lower()))
        
        # Limit to top 15 least active
        least_active_members = least_active_members[:15]
        
        # Add usernames to most active stats
        for stat in voice_stats:
            member_info = member_map.get(stat["_id"], {})
            stat["username"] = member_info.get("display_name") or member_info.get("username") or f"User {stat['_id'][:8]}"
        
        for stat in text_stats:
            member_info = member_map.get(stat["_id"], {})
            stat["username"] = member_info.get("display_name") or member_info.get("username") or f"User {stat['_id'][:8]}"
        
        # Calculate correct totals
        total_voice_sessions = sum(s["total_sessions"] for s in voice_stats) if voice_stats else 0
        total_text_messages = sum(s["total_messages"] for s in text_stats) if text_stats else 0
        
        # Get all voice sessions (not just top users)
        all_voice_sessions = await db.discord_voice_activity.count_documents({
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        
        # Get all text messages (not just top users)
        all_text_messages_result = await db.discord_text_activity.aggregate([
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
        ]).to_list(None)
        all_text_messages = all_text_messages_result[0]["total"] if all_text_messages_result else 0
        
        # Get top users per voice channel
        channel_voice_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": {
                    "channel_name": "$channel_name",
                    "channel_id": "$channel_id",
                    "user_id": "$discord_user_id"
                },
                "total_sessions": {"$sum": 1},
                "total_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"_id.channel_name": 1, "total_duration": -1}}
        ]
        
        channel_voice_stats = await db.discord_voice_activity.aggregate(channel_voice_pipeline).to_list(None)
        
        # Organize by channel with top 5 users per channel
        channels_data = {}
        for stat in channel_voice_stats:
            channel_name = stat["_id"]["channel_name"]
            user_id = stat["_id"]["user_id"]
            
            if channel_name not in channels_data:
                channels_data[channel_name] = {
                    "channel_name": channel_name,
                    "channel_id": stat["_id"]["channel_id"],
                    "total_sessions": 0,
                    "total_duration": 0,
                    "top_users": []
                }
            
            channels_data[channel_name]["total_sessions"] += stat["total_sessions"]
            channels_data[channel_name]["total_duration"] += stat["total_duration"]
            
            # Add to top users (limit to 5 per channel)
            if len(channels_data[channel_name]["top_users"]) < 5:
                member_info = member_map.get(user_id, {})
                username = member_info.get("display_name") or member_info.get("username") or f"User {user_id[:8]}"
                channels_data[channel_name]["top_users"].append({
                    "user_id": user_id,
                    "username": username,
                    "sessions": stat["total_sessions"],
                    "duration": stat["total_duration"]
                })
        
        # Convert to list and sort by total duration
        channel_stats = list(channels_data.values())
        channel_stats.sort(key=lambda x: x["total_duration"], reverse=True)
        
        analytics = DiscordAnalytics(
            total_members=total_members,
            voice_stats={"total_sessions": all_voice_sessions, "top_users": voice_stats},
            text_stats={"total_messages": all_text_messages, "top_users": text_stats},
            top_voice_users=voice_stats,
            top_text_users=text_stats,
            daily_activity=daily_activity
        )
        
        # Add least active members to response
        analytics_dict = analytics.model_dump()
        analytics_dict["least_active_members"] = least_active_members
        analytics_dict["channel_stats"] = channel_stats
        
        # Calculate engagement rate using UNIQUE active users (not double-counting)
        all_active_users = voice_active_users.union(text_active_users)
        engagement_rate = round((len(all_active_users) / total_members * 100), 1) if total_members > 0 else 0
        
        analytics_dict["engagement_stats"] = {
            "total_members": total_members,
            "voice_active_members": len(voice_active_users),
            "text_active_members": len(text_active_users),
            "inactive_members": len(least_active_members),
            "engagement_rate": engagement_rate
        }
        
        return analytics_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


# ==================== PROSPECT CHANNEL ANALYTICS ====================

def can_view_prospect_analytics(user: dict) -> bool:
    """Check if user can view Prospect channel analytics.
    Allowed: N Prez, VP, S@A, ENF, SEC and HA Prez, VP, S@A, ENF, SEC
    """
    role = user.get('role', '')
    chapter = user.get('chapter', '')
    title = user.get('title', '')
    
    if role != 'admin':
        return False
    
    allowed_chapters = ['National', 'HA']
    allowed_titles = ['Prez', 'VP', 'S@A', 'ENF', 'SEC']
    
    return chapter in allowed_chapters and title in allowed_titles


@api_router.get("/prospect-channel-analytics")
async def get_prospect_channel_analytics(
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(verify_token)
):
    """Get Prospect channel voice analytics"""
    if not can_view_prospect_analytics(current_user):
        raise HTTPException(
            status_code=403, 
            detail="Only National/HA Officers (Prez, VP, S@A, ENF, SEC) can view Prospect analytics"
        )
    
    try:
        # Get settings
        settings = await db.prospect_channel_settings.find_one({"_id": "main"})
        tracking_enabled = settings.get("tracking_enabled", True) if settings else True
        
        # Build query
        query = {}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        # Get all activity records
        activity = await db.prospect_channel_activity.find(query, {"_id": 0}).to_list(10000)
        
        # Aggregate by user
        user_stats = {}
        for record in activity:
            user_id = record.get('discord_id')
            display_name = record.get('display_name', 'Unknown')
            
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'discord_id': user_id,
                    'display_name': display_name,
                    'total_sessions': 0,
                    'total_duration_seconds': 0,
                    'sessions_with_prospect': 0,
                    'duration_with_prospect_seconds': 0,
                    'unique_prospects_met': set(),
                    'unique_hangarounds_met': set(),
                    'time_per_prospect': {},  # Aggregate time per prospect
                    'total_time_alone_seconds': 0,
                    'sessions': []
                }
            
            stats = user_stats[user_id]
            stats['total_sessions'] += 1
            stats['total_duration_seconds'] += record.get('duration_seconds', 0)
            stats['total_time_alone_seconds'] += record.get('time_alone_seconds', 0)
            
            if record.get('had_prospect_interaction'):
                stats['sessions_with_prospect'] += 1
                stats['duration_with_prospect_seconds'] += record.get('total_time_with_prospects_seconds', record.get('duration_seconds', 0))
            
            for p in record.get('prospects_present', []):
                stats['unique_prospects_met'].add(p)
            for h in record.get('hangarounds_present', []):
                stats['unique_hangarounds_met'].add(h)
            
            # Aggregate time per prospect from breakdown
            for breakdown in record.get('prospect_time_breakdown', []):
                prospect_name = breakdown.get('prospect_name')
                time_together = breakdown.get('time_together_seconds', 0)
                if prospect_name:
                    if prospect_name not in stats['time_per_prospect']:
                        stats['time_per_prospect'][prospect_name] = 0
                    stats['time_per_prospect'][prospect_name] += time_together
            
            # Add session detail with time breakdown
            prospect_time_breakdown = record.get('prospect_time_breakdown', [])
            stats['sessions'].append({
                'date': record.get('date'),
                'channel': record.get('channel_name'),
                'duration_minutes': round(record.get('duration_seconds', 0) / 60, 1),
                'duration_seconds': record.get('duration_seconds', 0),
                'prospects_present': record.get('prospects_present', []),
                'hangarounds_present': record.get('hangarounds_present', []),
                'others_present': [o.get('display_name') for o in record.get('others_in_channel', [])],
                # New time breakdown fields
                'prospect_time_breakdown': [
                    {
                        'prospect_name': p.get('prospect_name'),
                        'time_together_seconds': p.get('time_together_seconds', 0),
                        'time_together_formatted': format_duration(p.get('time_together_seconds', 0))
                    }
                    for p in prospect_time_breakdown
                ],
                'total_time_with_prospects_seconds': record.get('total_time_with_prospects_seconds', 0),
                'total_time_with_prospects_formatted': format_duration(record.get('total_time_with_prospects_seconds', 0)),
                'time_alone_seconds': record.get('time_alone_seconds', 0),
                'time_alone_formatted': format_duration(record.get('time_alone_seconds', 0))
            })
        
        # Convert sets to lists and format response
        result = []
        for user_id, stats in user_stats.items():
            # Format time per prospect as a list
            time_per_prospect_list = [
                {
                    'prospect_name': name,
                    'total_time_seconds': seconds,
                    'total_time_formatted': format_duration(seconds)
                }
                for name, seconds in sorted(stats['time_per_prospect'].items(), key=lambda x: x[1], reverse=True)
            ]
            
            result.append({
                'discord_id': stats['discord_id'],
                'display_name': stats['display_name'],
                'total_sessions': stats['total_sessions'],
                'total_time_minutes': round(stats['total_duration_seconds'] / 60, 1),
                'total_time_formatted': format_duration(stats['total_duration_seconds']),
                'sessions_with_prospect': stats['sessions_with_prospect'],
                'time_with_prospect_minutes': round(stats['duration_with_prospect_seconds'] / 60, 1),
                'time_with_prospect_formatted': format_duration(stats['duration_with_prospect_seconds']),
                'unique_prospects_met': list(stats['unique_prospects_met']),
                'unique_hangarounds_met': list(stats['unique_hangarounds_met']),
                # New aggregated time breakdown
                'time_per_prospect': time_per_prospect_list,
                'total_time_alone_seconds': stats['total_time_alone_seconds'],
                'total_time_alone_formatted': format_duration(stats['total_time_alone_seconds']),
                'sessions': sorted(stats['sessions'], key=lambda x: x['date'], reverse=True)
            })
        
        # Sort by total time
        result.sort(key=lambda x: x['total_time_minutes'], reverse=True)
        
        return {
            'tracking_enabled': tracking_enabled,
            'total_records': len(activity),
            'unique_users': len(result),
            'users': result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@api_router.get("/prospect-channel-analytics/active")
async def get_active_prospect_sessions(current_user: dict = Depends(verify_token)):
    """Get currently active sessions in Prospect channels (users currently in the channel)"""
    if not can_view_prospect_analytics(current_user):
        raise HTTPException(
            status_code=403, 
            detail="Only National/HA Officers (Prez, VP, S@A, ENF, SEC) can view Prospect analytics"
        )
    
    try:
        # Get all active sessions
        active_sessions = await db.prospect_channel_active_sessions.find({}, {"_id": 0}).to_list(1000)
        
        now = datetime.now(timezone.utc)
        
        # Deduplicate by discord_id - keep only the most recent session per user
        seen_users = {}
        for session in active_sessions:
            discord_id = session.get('discord_id')
            if discord_id not in seen_users:
                seen_users[discord_id] = session
            else:
                # Keep the one with more recent joined_at
                existing_joined = seen_users[discord_id].get('joined_at', '')
                new_joined = session.get('joined_at', '')
                if new_joined > existing_joined:
                    seen_users[discord_id] = session
        
        # Build a map of channel -> all users in that channel (for computing prospects_present)
        channel_users = {}
        for discord_id, session in seen_users.items():
            channel = session.get('channel_name', '')
            display_name = session.get('display_name', '')
            if channel not in channel_users:
                channel_users[channel] = []
            channel_users[channel].append({
                'discord_id': discord_id,
                'display_name': display_name
            })
        
        # Get hangarounds from database for matching
        hangarounds = await db.hangarounds.find({}, {"handle": 1, "_id": 0}).to_list(1000)
        hangaround_handle_set = {h['handle'].lower() for h in hangarounds if h.get('handle')}
        
        # Calculate current duration and compute prospects_present for each session
        result = []
        for discord_id, session in seen_users.items():
            joined_at_str = session.get('joined_at')
            if joined_at_str:
                try:
                    joined_at = datetime.fromisoformat(joined_at_str.replace('Z', '+00:00'))
                    duration_seconds = int((now - joined_at).total_seconds())
                except:
                    duration_seconds = 0
            else:
                duration_seconds = 0
            
            # Get all users in the same channel
            channel = session.get('channel_name', '')
            all_in_channel = channel_users.get(channel, [])
            
            # Build others_in_channel (everyone except current user)
            others_in_channel = [u for u in all_in_channel if u['discord_id'] != discord_id]
            
            # Find all prospects and hangarounds in the channel (excluding current user)
            prospects_present = []
            hangarounds_present = []
            
            for user in others_in_channel:
                other_name = user.get('display_name', '')
                other_name_lower = other_name.lower()
                
                # Check for Prospect: "HA(p)" in name (case insensitive)
                if 'ha(p)' in other_name_lower:
                    prospects_present.append(other_name)
                
                # Check for Hangaround by database match
                for hh in hangaround_handle_set:
                    if hh in other_name_lower:
                        hangarounds_present.append(other_name)
                        break
            
            result.append({
                'id': session.get('id'),
                'discord_id': discord_id,
                'display_name': session.get('display_name'),
                'channel_name': channel,
                'joined_at': joined_at_str,
                'duration_seconds': duration_seconds,
                'duration_formatted': format_duration(duration_seconds),
                'others_in_channel': others_in_channel,
                'prospects_present': prospects_present,
                'hangarounds_present': hangarounds_present
            })
        
        # Sort by duration (longest first)
        result.sort(key=lambda x: x['duration_seconds'], reverse=True)
        
        return {
            'active_count': len(result),
            'sessions': result,
            'timestamp': now.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active sessions: {str(e)}")


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


@api_router.get("/prospect-channel-analytics/settings")
async def get_prospect_channel_settings(current_user: dict = Depends(verify_token)):
    """Get Prospect channel tracking settings"""
    if not can_view_prospect_analytics(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings = await db.prospect_channel_settings.find_one({"_id": "main"})
    if not settings:
        settings = {"_id": "main", "tracking_enabled": True}
        await db.prospect_channel_settings.insert_one(settings)
    
    return {
        "tracking_enabled": settings.get("tracking_enabled", True),
        "last_reset": settings.get("last_reset"),
        "reset_by": settings.get("reset_by")
    }


@api_router.post("/prospect-channel-analytics/settings")
async def update_prospect_channel_settings(
    tracking_enabled: bool,
    current_user: dict = Depends(verify_token)
):
    """Enable or disable Prospect channel tracking"""
    if not can_view_prospect_analytics(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.prospect_channel_settings.update_one(
        {"_id": "main"},
        {"$set": {"tracking_enabled": tracking_enabled}},
        upsert=True
    )
    
    await log_activity(
        current_user["username"],
        "prospect_tracking_toggle",
        f"{'Enabled' if tracking_enabled else 'Disabled'} Prospect channel tracking"
    )
    
    return {"message": f"Prospect channel tracking {'enabled' if tracking_enabled else 'disabled'}"}


@api_router.post("/prospect-channel-analytics/reset")
async def reset_prospect_channel_analytics(current_user: dict = Depends(verify_token)):
    """Reset all Prospect channel analytics data"""
    if not can_view_prospect_analytics(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete all activity records (completed sessions)
    result = await db.prospect_channel_activity.delete_many({})
    
    # Also delete active sessions
    active_result = await db.prospect_channel_active_sessions.delete_many({})
    
    # Update settings with reset info
    await db.prospect_channel_settings.update_one(
        {"_id": "main"},
        {"$set": {
            "last_reset": datetime.now(timezone.utc).isoformat(),
            "reset_by": current_user["username"]
        }},
        upsert=True
    )
    
    await log_activity(
        current_user["username"],
        "prospect_analytics_reset",
        f"Reset Prospect channel analytics ({result.deleted_count} completed + {active_result.deleted_count} active records deleted)"
    )
    
    return {
        "message": f"Prospect channel analytics reset successfully",
        "records_deleted": result.deleted_count
    }


@api_router.post("/discord/import-members")
async def import_discord_members(current_user: dict = Depends(verify_admin)):
    """Import Discord members and link to existing members using enhanced fuzzy matching"""
    try:
        from rapidfuzz import fuzz, process
        
        # Fetch Discord members and database members
        discord_members = await db.discord_members.find({}, {"_id": 0}).to_list(None)
        database_members = await db.members.find({}, {"_id": 0, "id": 1, "handle": 1, "name": 1}).to_list(None)
        
        matched_count = 0
        match_details = []
        
        # Create lookup dictionaries for database members
        handle_to_member = {m.get("handle", "").lower(): m for m in database_members if m.get("handle")}
        name_to_member = {m.get("name", "").lower(): m for m in database_members if m.get("name")}
        
        for discord_member in discord_members:
            username = (discord_member.get("username") or "").strip()
            display_name = (discord_member.get("display_name") or "").strip()
            
            if not username:
                continue
            
            best_match = None
            best_score = 0
            match_type = ""
            
            # Strategy 1: Exact case-insensitive match on username/display_name with handle/name
            username_lower = username.lower()
            display_name_lower = display_name.lower() if display_name else ""
            
            if username_lower in handle_to_member:
                best_match = handle_to_member[username_lower]
                best_score = 100
                match_type = "exact_handle"
            elif display_name_lower and display_name_lower in handle_to_member:
                best_match = handle_to_member[display_name_lower]
                best_score = 100
                match_type = "exact_display_handle"
            elif username_lower in name_to_member:
                best_match = name_to_member[username_lower]
                best_score = 100
                match_type = "exact_name"
            elif display_name_lower and display_name_lower in name_to_member:
                best_match = name_to_member[display_name_lower]
                best_score = 100
                match_type = "exact_display_name"
            
            # Strategy 2: Partial contains matching (e.g., "lonestar379" contains "lonestar")
            if not best_match:
                for db_member in database_members:
                    handle = (db_member.get("handle") or "").lower()
                    name = (db_member.get("name") or "").lower()
                    
                    # Check if handle/name is contained in username or display_name
                    if handle and len(handle) >= 3:
                        if handle in username_lower or handle in display_name_lower:
                            score = 85
                            if score > best_score:
                                best_match = db_member
                                best_score = score
                                match_type = "partial_handle"
                    
                    # Check if username/display_name is contained in handle/name
                    if username_lower and len(username_lower) >= 3:
                        if username_lower in handle or username_lower in name:
                            score = 85
                            if score > best_score:
                                best_match = db_member
                                best_score = score
                                match_type = "partial_username"
            
            # Strategy 3: Fuzzy matching with threshold
            if not best_match or best_score < 90:
                # Build list of all possible matches
                match_candidates = []
                for db_member in database_members:
                    handle = db_member.get("handle", "")
                    name = db_member.get("name", "")
                    if handle:
                        match_candidates.append((handle, db_member, "handle"))
                    if name:
                        match_candidates.append((name, db_member, "name"))
                
                # Try fuzzy matching with username
                if username and match_candidates:
                    for candidate_str, db_member, field_type in match_candidates:
                        # Use token_sort_ratio for better matching with different word orders
                        score1 = fuzz.token_sort_ratio(username.lower(), candidate_str.lower())
                        score2 = fuzz.ratio(username.lower(), candidate_str.lower())
                        score = max(score1, score2)
                        
                        if score > best_score and score >= 80:  # 80% similarity threshold
                            best_match = db_member
                            best_score = score
                            match_type = f"fuzzy_{field_type}"
                
                # Try fuzzy matching with display_name
                if display_name and match_candidates:
                    for candidate_str, db_member, field_type in match_candidates:
                        score1 = fuzz.token_sort_ratio(display_name.lower(), candidate_str.lower())
                        score2 = fuzz.ratio(display_name.lower(), candidate_str.lower())
                        score = max(score1, score2)
                        
                        if score > best_score and score >= 80:
                            best_match = db_member
                            best_score = score
                            match_type = f"fuzzy_display_{field_type}"
            
            # Link if we found a good match (score >= 80)
            if best_match and best_score >= 80:
                await db.discord_members.update_one(
                    {"discord_id": discord_member["discord_id"]},
                    {"$set": {"member_id": best_match["id"]}}
                )
                matched_count += 1
                match_details.append({
                    "discord_user": username,
                    "discord_display": display_name,
                    "matched_handle": best_match.get("handle"),
                    "matched_name": best_match.get("name"),
                    "score": round(best_score, 1),
                    "method": match_type
                })
        
        # Log the activity
        await log_activity(
            current_user['username'],
            "discord_import",
            f"Imported Discord members with enhanced matching. Matched {matched_count} members."
        )
        
        return {
            "message": f"Imported Discord members. Matched {matched_count} with existing members.",
            "matched_count": matched_count,
            "total_discord_members": len(discord_members),
            "match_details": match_details[:10]  # Return first 10 matches for review
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")


# AI Chatbot endpoint
class ChatMessage(BaseModel):
    message: str

@api_router.post("/chat")
async def chat_with_bot(chat_msg: ChatMessage, current_user: dict = Depends(verify_token)):
    """AI chatbot for BOH knowledge - authenticated users only"""
    try:
        from openai import OpenAI
        
        # Get OpenAI API key
        api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM key not configured")
        
        # Check if user is admin
        is_admin = current_user.get('role') == 'admin'
        
        # Try to get knowledge from database first
        db_knowledge = await db.ai_knowledge.find({"is_active": True}, {"_id": 0}).to_list(length=None)
        
        if db_knowledge:
            # Build context from database entries
            base_parts = ["You are an AI assistant for Brothers of the Highway Trucker Club (BOH TC), a 501(c)(3) organization for professional truck drivers. Your role is to answer questions about the organization using ONLY the information provided below.\n"]
            admin_parts = []
            
            for entry in db_knowledge:
                section = f"\n{entry['title'].upper()}:\n{entry['content']}\n"
                if entry.get('admin_only'):
                    admin_parts.append(section)
                else:
                    base_parts.append(section)
            
            base_parts.append("\nIf asked about something not covered in this knowledge base, politely say you don't have that information and suggest they contact their Chain of Command or check Discord channels.\n\nBe helpful, respectful, and direct. Use BOH terminology (handles, Chain of Command, COC, prospects, Brother, S@A, NPrez, NVP, etc.).")
            
            base_context = "".join(base_parts)
            admin_context = "".join(admin_parts) if admin_parts else ""
            
            # Combine contexts based on user role
            if is_admin:
                system_context = base_context + admin_context
            else:
                system_context = base_context
        else:
            # Fallback to hardcoded content if database is empty
            # Base knowledge for all users
            base_context = """You are an AI assistant for Brothers of the Highway Trucker Club (BOH TC), a 501(c)(3) organization for professional truck drivers. Your role is to answer questions about the organization using ONLY the information provided below.

ORGANIZATION OVERVIEW:
- Brothers of the Highway TC is a men-only trucking organization
- Mission: Support and unite professional truck drivers
- Requirements: Must have Class A CDL, cannot be in 1% MC clubs
- Structure: National Board oversees Chapters (National, AD, HA, HS)
- Legal Status: 501(c)(3) non-profit organization

MISSION STATEMENT:
"We are a Trucker Club that is family oriented, community minded and dedicated to shaping the future while honoring the past. We are a Trucker Club working on bringing back the old school ways of trucking. We are committed to doing what it takes to bring back the respect to the industry by bringing a brotherhood to the industry again."

CORE VALUES & ACTIVITIES:
- Respect To Others While Driving
- Help Other Drivers In Need
- Doing Trash Pick Ups To Keep Lots Clean
- Creating The Family Away From Family
- Donating To Various Charities
- Create A Brotherhood
- Showing All Around Respect
- Doing What It Takes To Make A Change
- Most Of All Bring The Respect Back To Drivers

LOGO ELEMENTS & MEANINGS:
- Phoenix Wings: Represents "Rise of The Old School Brotherhood from the Ashes"
- Old School Truck: Represents Old School Trucking Ways
- Chains: Represents Unity among members
- Tombstones: Represents Our Fallen Brothers
- Truck Number (2158): Alphanumeric identifier for BOH
- TC: Truckers Club designation

MEMBERSHIP PROCESS:
1. Open Enrollment - Public recruiting phase
2. Vetting - Initial interview with Training Chapter
3. Hangaround Phase - Test commitment, chat activity
4. Prospect Phase - 4-6 weeks with assignments, weekly meetings
5. Brother - Full member after vote

CHAIN OF COMMAND:
National Officers: 
- National President (NPrez): Q-Ball - CEO, Chairman of National Board, handles external relations
- National Vice President (NVP): Keltic Reaper - Second in command, assumes NPrez duties in absence
- National Sergeant at Arms (NS@A): Repo - "Legal office" of organization, enforces and interprets By-laws
- National Enforcer (NENF): Gear Jammer - Prospect management oversight
- National Treasurer (NT): California Kid - Budget Committee member, handles finances
- National Secretary (NSEC): Lonestar - Budget Committee member, administrative duties
- National Chapter Director (NCD): Shooter - Administrative position (not in Chain of Command)

ADDITIONAL NATIONAL POSITIONS:
- Club Chaplain (CC): Sancho
- Club Media Director (CMD): Grizz
- Club Counselor & Life Coach (CCLC): Scar

HIGHWAY ASYLUM (HA) CHAPTER OFFICERS (Chain of Command):
- HA President (HAPrez): Chap
- HA Vice President (HAVP): Sancho
- HA Sergeant at Arms (HAS@A): Tapeworm
- HA Enforcer (HAENF): *Vacant*
- HA Secretary (HASEC): Hee Haw
- HA Prospect Manager (HAPM): Phantom

HIGHWAY SOULS (HS) CHAPTER OFFICERS:
- HS President (HSPrez): Bobkat
- HS Vice President (HSVP): Graveyard
- HS Sergeant at Arms (HSS@A): Trucker Dave
- HS Enforcer (HSENF): Rainwater
- HS Secretary (HSSEC): Sodbuster

ASPHALT DEMONS (AD) CHAPTER OFFICERS:
- AD President (ADPrez): Hotshot
- AD Vice President (ADVP): Clutch
- AD Sergeant at Arms (ADS@A): *Vacant*
- AD Enforcer (ADENF): Rookie
- AD Secretary (ADSEC): Two Stacks

CHAPTER OFFICER STRUCTURE:
- President - Chapter leader
- Vice President - Second in command
- Sergeant at Arms (S@A) - "Legal office" of chapter, enforces By-laws
- Enforcer - Prospect management
- Secretary - Administrative duties
- Prospect Manager (PM) - Manages prospects (only HA chapter has this position)

NOTE: Prospect Manager position exists only in Highway Asylum (HA) chapter. Other chapters (HS, AD) do not have this position.

PROSPECT REQUIREMENTS:
- Attend weekly meetings (Thursdays 4pm CST - MANDATORY)
- Complete weekly assignments (essays, trash pickup, meet-ups)
- Purchase 2 supporter gear items before membering
- Learn: Mission Statement, Logo Elements, Chain of Command
- 100% meeting attendance required
- Active chat participation in Discord
- Must memorize Chain of Command structure

KEY BYLAWS:
- No criminal activity, discrimination, or harassment
- Respect all officers, members, prospects at all times
- Follow Chain of Command always - MUST follow CoC without deviation
- No 1% MC affiliation while in BOH
- Class A CDL required (students with permit may prospect)
- No sex offenders, no drug use/possession
- No reckless driving or property damage

MEET-UPS & EVENTS:
- 3 annual sanctioned meet-ups
- Driver appreciation events
- Family days
- Community service (trash pickups)

SOCIAL MEDIA & COMMUNICATIONS:
- Discord: Primary platform for voice/text chat
- Facebook Family Page: Public outreach, professional posts only
- TikTok: Recruiting tool, PG-level content, 21+ only
- Respect and professional presentation required on all platforms

If asked about something not covered in this knowledge base, politely say you don't have that information and suggest they contact their Chain of Command or check Discord channels.

Be helpful, respectful, and direct. Use BOH terminology (handles, Chain of Command, COC, prospects, Brother, S@A, NPrez, NVP, etc.)."""

        # Admin-only additional context
        admin_context = """

ARTICLE I: GENERAL RULES OF ORDER
- Voting: Officers cannot vote for themselves for promotion/demotion/removal
- Service: Officers serve at pleasure of NPrez and National Board
- Observation Period: 7 days, new officers have no authority during this time
- Probation: 90 days with training and evaluation, can be removed for poor performance
- Guidance: Officers can meet with National Officer equivalents for guidance without subverting CoC

ARTICLE II: OFFICER DUTIES & RESPONSIBILITIES
- Officers must fulfill duties while upholding Member By-laws
- Chain of Command must always be followed
- Officer Meetings: National (Wed 3pm EST), Chapter (Wed 5pm EST)
- 100% attendance required unless approved by CoC
- Officers must obtain missed information if absent
- Cannot comment/vote if not current on events

ARTICLE III: CHAPTER OFFICER EXPECTATIONS
- Responsible for daily management of chapter members
- Conduct meetings, monitor activity, report infractions
- Approach members with respect and courtesy
- Chapter Ranks: President, Vice President, Sergeant at Arms, Enforcer, Secretary

ARTICLE IV: OFFICER NON-PERFORMANCE
- Dereliction of Duty: Can result in sanction up to removal
- 2/3 vote required to discipline (majority for National Board)
- Officers can be voted out except National Committee officers (NPrez removes them)

ARTICLE V: OFFICER DISCIPLINARY PROCESS
- Sanction requests must be submitted within 72 hours to NENF
- Investigation begins within 72 hours by Chapter President
- NS@A drafts Notification of Sanction
- NRC convenes Disciplinary Hearing (with NVP, NS@A, NRC)
- Officer receives notification within 7 days for signature
- Appeals: Submit within 72 hours to NENF, committee reviews within 72 hours
- Officers limited to 2 strikes (vs 3 for members)
- Strikes remain 90 days on record

ARTICLE VI: OFFICER RESIGNATION
- Voluntary positions, can resign anytime
- Must email NS@A AND NRC
- Complete formal letter of resignation

ARTICLE VII: MISCELLANEOUS RULES
- No solicitation, special favors, or personal gain from BOH business
- Higher standards at public events (less intoxicated, professional demeanor)
- Retired NPrez (2+ years): "OG Legacy President" or "BOH NP(r)"
- No voting power but can provide advice/consultation

NATIONAL GOVERNING BODIES:
- National Budget Committee: Oversees quarterly/annual budget, maintains IRS compliance
  Members: National President (Q-Ball), National Treasurer (California Kid), National Secretary (Lonestar)
- National Board: All National Officers (sans National President for voting to maintain odd number)
  Includes: National Vice President (Keltic Reaper), National Sergeant at Arms (Repo), National Enforcer (Gear Jammer), National Treasurer (California Kid), National Secretary (Lonestar)
  Responsible for: Policy creation, membership roll, general operating orders

OFFICER-SPECIFIC BYLAWS:
- Officers serve at pleasure of National President and National Board
- 7-day observation period for newly promoted officers (no authority during this time)
- 90-day probationary period with training and evaluation
- Officers limited to 2 strikes (vs 3 for members)
- 100% attendance required at officer meetings
- Officer meetings: National (Wed 3pm EST), Chapter (Wed 5pm EST)
- Voting: Officers cannot vote for themselves for promotion/demotion/removal
- Sanctions must be requested within 72 hours of infraction
- Officers can resign at any time (notify NS@A and NRC via email)
- No solicitation, special favors, or use of BOH for personal gain
- Higher standard of conduct at public events
- Retired National Presidents (2+ years service) become "BOH NP(r)" or "OG Legacy President"

MEETINGS:
- National Officer: Wednesdays 3pm EST
- Chapter Officer: Wednesdays 5pm EST  
- Prospect: Thursdays 4pm CST (mandatory, 100% attendance)
- Member meetings vary by chapter
- Meeting rules: Microphones muted in app, cameras on (when <20 people), follow Robert's Rules of Order

SANCTIONS (Progressive Discipline):
1. Verbal Warning - Least severe, discussion with Officer
2. Written Warning - Progressive step, documented in Member file
3. Strike - Most severe (3 strikes for members = removal, 2 strikes for Officers = removal)
- Special Assignments may be given instead of standard sanctions
- Chapter Presidents approve sanctions with ½ majority of Officer corp vote
- Prospects can appeal sanctions to National Board

FINANCIAL:
- Monthly member dues (National + Chapter)
- Financial Assistance Program available for hardship cases
- Financial Hardship applications reviewed by Budget Committee
- Merchandise: 2 supporter items required for prospects before membering
- All merchandise sold only on sanctioned BOH platforms

ADDITIONAL OFFICER DUTIES:
- Sergeant at Arms: Activity reports (monthly/weekly/daily), By-law enforcement, interpretation guidance
- National President: External liaison, Executive Orders, conflict resolution, CEO/Chairman, tie-breaking vote
- National Vice President: Information relay, assumes duties in absences, coordinates committees, second in command
- National Sergeant at Arms: Maintains bylaws, ensures National Board orders executed, Discord access management, membership records, protects organization reputation
- National Road Captain: Assists NS@A and NENF, mediates conflicts, project manager for events, ensures bylaw integrity
- National Enforcer: First reportable position, oversees prospect rounds, liaison for disciplinary action, protects organization reputation
- National Treasurer: Oversees spending, maintains financial records, manages dues collection, quarterly financial reports
- National Secretary: Keeps all records/minutes, performs roll calls, handles correspondence, reports to NPrez
- Club Chaplain: Counselor for members, confidential conversations, mental health support (limited capacity)"""

        # Combine contexts based on user role (fallback hardcoded)
        if is_admin:
            system_context = base_context + admin_context
        else:
            system_context = base_context

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Send user message and get response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": chat_msg.message}
            ],
            max_tokens=1000
        )
        
        bot_response = response.choices[0].message.content
        
        return {"response": bot_response}
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ==================== AI KNOWLEDGE MANAGEMENT ====================

class AIKnowledgeEntry(BaseModel):
    title: str
    content: str
    category: str  # general, chain_of_command, bylaws, meetings, admin_only
    is_active: bool = True
    admin_only: bool = False

class AIKnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    admin_only: Optional[bool] = None

def check_ai_admin_access(current_user: dict):
    """Check if user has access to AI knowledge management (Nationals chapter only)"""
    chapter = current_user.get('chapter', '')
    
    # Only users in National chapter can access AI knowledge
    return chapter == 'National'

@api_router.get("/ai-knowledge")
async def get_ai_knowledge(current_user: dict = Depends(verify_token)):
    """Get all AI knowledge entries - restricted to NPrez, NVP, NSEC"""
    if not check_ai_admin_access(current_user):
        raise HTTPException(status_code=403, detail="Only National President, Vice President, or Secretary can manage AI knowledge")
    
    entries = await db.ai_knowledge.find({}, {"_id": 0}).to_list(length=None)
    return entries

@api_router.post("/ai-knowledge")
async def create_ai_knowledge(entry: AIKnowledgeEntry, current_user: dict = Depends(verify_token)):
    """Create a new AI knowledge entry - restricted to NPrez, NVP, NSEC"""
    if not check_ai_admin_access(current_user):
        raise HTTPException(status_code=403, detail="Only National President, Vice President, or Secretary can manage AI knowledge")
    
    new_entry = {
        "id": str(uuid.uuid4()),
        "title": entry.title,
        "content": entry.content,
        "category": entry.category,
        "is_active": entry.is_active,
        "admin_only": entry.admin_only,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get('username'),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get('username')
    }
    
    await db.ai_knowledge.insert_one(new_entry)
    return {"message": "Knowledge entry created", "id": new_entry["id"]}

@api_router.put("/ai-knowledge/{entry_id}")
async def update_ai_knowledge(entry_id: str, update: AIKnowledgeUpdate, current_user: dict = Depends(verify_token)):
    """Update an AI knowledge entry - restricted to NPrez, NVP, NSEC"""
    if not check_ai_admin_access(current_user):
        raise HTTPException(status_code=403, detail="Only National President, Vice President, or Secretary can manage AI knowledge")
    
    existing = await db.ai_knowledge.find_one({"id": entry_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get('username')
    
    await db.ai_knowledge.update_one({"id": entry_id}, {"$set": update_data})
    return {"message": "Knowledge entry updated"}

@api_router.delete("/ai-knowledge/{entry_id}")
async def delete_ai_knowledge(entry_id: str, current_user: dict = Depends(verify_token)):
    """Delete an AI knowledge entry - restricted to NPrez, NVP, NSEC"""
    if not check_ai_admin_access(current_user):
        raise HTTPException(status_code=403, detail="Only National President, Vice President, or Secretary can manage AI knowledge")
    
    result = await db.ai_knowledge.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return {"message": "Knowledge entry deleted"}

@api_router.post("/ai-knowledge/initialize")
async def initialize_ai_knowledge(current_user: dict = Depends(verify_token)):
    """Initialize AI knowledge from existing hardcoded content - one time setup"""
    if not check_ai_admin_access(current_user):
        raise HTTPException(status_code=403, detail="Only National President, Vice President, or Secretary can manage AI knowledge")
    
    # Check if already initialized
    existing_count = await db.ai_knowledge.count_documents({})
    if existing_count > 0:
        return {"message": f"Knowledge base already has {existing_count} entries. Clear first to reinitialize."}
    
    # Default knowledge entries based on existing hardcoded content
    default_entries = [
        {
            "id": str(uuid.uuid4()),
            "title": "Organization Overview",
            "content": """Brothers of the Highway TC is a men-only trucking organization
Mission: Support and unite professional truck drivers
Requirements: Must have Class A CDL, cannot be in 1% MC clubs
Structure: National Board oversees Chapters (National, AD, HA, HS)
Legal Status: 501(c)(3) non-profit organization""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Mission Statement",
            "content": """"We are a Trucker Club that is family oriented, community minded and dedicated to shaping the future while honoring the past. We are a Trucker Club working on bringing back the old school ways of trucking. We are committed to doing what it takes to bring back the respect to the industry by bringing a brotherhood to the industry again.""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Core Values & Activities",
            "content": """- Respect To Others While Driving
- Help Other Drivers In Need
- Doing Trash Pick Ups To Keep Lots Clean
- Creating The Family Away From Family
- Donating To Various Charities
- Create A Brotherhood
- Showing All Around Respect
- Doing What It Takes To Make A Change
- Most Of All Bring The Respect Back To Drivers""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Logo Elements & Meanings",
            "content": """- Phoenix Wings: Represents "Rise of The Old School Brotherhood from the Ashes"
- Old School Truck: Represents Old School Trucking Ways
- Chains: Represents Unity among members
- Tombstones: Represents Our Fallen Brothers
- Truck Number (2158): Alphanumeric identifier for BOH
- TC: Truckers Club designation""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "National Officers Chain of Command",
            "content": """- National President (NPrez): Q-Ball - CEO, Chairman of National Board, handles external relations
- National Vice President (NVP): Keltic Reaper - Second in command, assumes NPrez duties in absence
- National Sergeant at Arms (NS@A): Repo - "Legal office" of organization, enforces and interprets By-laws
- National Enforcer (NENF): Gear Jammer - Prospect management oversight
- National Treasurer (NT): California Kid - Budget Committee member, handles finances
- National Secretary (NSEC): Lonestar - Budget Committee member, administrative duties
- National Chapter Director (NCD): Shooter - Administrative position (not in Chain of Command)""",
            "category": "chain_of_command",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Additional National Positions",
            "content": """- Club Chaplain (CC): Sancho
- Club Media Director (CMD): Grizz
- Club Counselor & Life Coach (CCLC): Scar""",
            "category": "chain_of_command",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Highway Asylum (HA) Chapter Officers",
            "content": """- HA President (HAPrez): Chap
- HA Vice President (HAVP): Sancho
- HA Sergeant at Arms (HAS@A): Tapeworm
- HA Enforcer (HAENF): *Vacant*
- HA Secretary (HASEC): Hee Haw
- HA Prospect Manager (HAPM): Phantom""",
            "category": "chain_of_command",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Highway Souls (HS) Chapter Officers",
            "content": """- HS President (HSPrez): Bobkat
- HS Vice President (HSVP): Graveyard
- HS Sergeant at Arms (HSS@A): Trucker Dave
- HS Enforcer (HSENF): Rainwater
- HS Secretary (HSSEC): Sodbuster""",
            "category": "chain_of_command",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Asphalt Demons (AD) Chapter Officers",
            "content": """- AD President (ADPrez): Hotshot
- AD Vice President (ADVP): Clutch
- AD Sergeant at Arms (ADS@A): *Vacant*
- AD Enforcer (ADENF): Rookie
- AD Secretary (ADSEC): Two Stacks""",
            "category": "chain_of_command",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Membership Process",
            "content": """1. Open Enrollment - Public recruiting phase
2. Vetting - Initial interview with Training Chapter
3. Hangaround Phase - Test commitment, chat activity
4. Prospect Phase - 4-6 weeks with assignments, weekly meetings
5. Brother - Full member after vote""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Prospect Requirements",
            "content": """- Attend weekly meetings (Thursdays 4pm CST - MANDATORY)
- Complete weekly assignments (essays, trash pickup, meet-ups)
- Purchase 2 supporter gear items before membering
- Learn: Mission Statement, Logo Elements, Chain of Command
- 100% meeting attendance required
- Active chat participation in Discord
- Must memorize Chain of Command structure""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Key Bylaws",
            "content": """- No criminal activity, discrimination, or harassment
- Respect all officers, members, prospects at all times
- Follow Chain of Command always - MUST follow CoC without deviation
- No 1% MC affiliation while in BOH
- Class A CDL required (students with permit may prospect)
- No sex offenders, no drug use/possession
- No reckless driving or property damage""",
            "category": "bylaws",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Meet-ups & Events",
            "content": """- 3 annual sanctioned meet-ups
- Driver appreciation events
- Family days
- Community service (trash pickups)""",
            "category": "meetings",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Social Media & Communications",
            "content": """- Discord: Primary platform for voice/text chat
- Facebook Family Page: Public outreach, professional posts only
- TikTok: Recruiting tool, PG-level content, 21+ only
- Respect and professional presentation required on all platforms""",
            "category": "general",
            "is_active": True,
            "admin_only": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Officer Rules & Governance (Admin Only)",
            "content": """ARTICLE I: GENERAL RULES OF ORDER
- Voting: Officers cannot vote for themselves for promotion/demotion/removal
- Service: Officers serve at pleasure of NPrez and National Board
- Observation Period: 7 days, new officers have no authority during this time
- Probation: 90 days with training and evaluation, can be removed for poor performance

ARTICLE II: OFFICER DUTIES & RESPONSIBILITIES
- Officers must fulfill duties while upholding Member By-laws
- Chain of Command must always be followed
- Officer Meetings: National (Wed 3pm EST), Chapter (Wed 5pm EST)
- 100% attendance required unless approved by CoC

ARTICLE IV: OFFICER NON-PERFORMANCE
- Dereliction of Duty: Can result in sanction up to removal
- 2/3 vote required to discipline (majority for National Board)
- Officers can be voted out except National Committee officers (NPrez removes them)""",
            "category": "admin_only",
            "is_active": True,
            "admin_only": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Disciplinary Process (Admin Only)",
            "content": """ARTICLE V: OFFICER DISCIPLINARY PROCESS
- Sanction requests must be submitted within 72 hours to NENF
- Investigation begins within 72 hours by Chapter President
- NS@A drafts Notification of Sanction
- NRC convenes Disciplinary Hearing (with NVP, NS@A, NRC)
- Officer receives notification within 7 days for signature
- Appeals: Submit within 72 hours to NENF, committee reviews within 72 hours
- Officers limited to 2 strikes (vs 3 for members)
- Strikes remain 90 days on record

SANCTIONS (Progressive Discipline):
1. Verbal Warning - Least severe, discussion with Officer
2. Written Warning - Progressive step, documented in Member file
3. Strike - Most severe (3 strikes for members = removal, 2 strikes for Officers = removal)""",
            "category": "admin_only",
            "is_active": True,
            "admin_only": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "National Governing Bodies (Admin Only)",
            "content": """NATIONAL GOVERNING BODIES:
- National Budget Committee: Oversees quarterly/annual budget, maintains IRS compliance
  Members: National President (Q-Ball), National Treasurer (California Kid), National Secretary (Lonestar)
- National Board: All National Officers (sans National President for voting to maintain odd number)
  Includes: National Vice President (Keltic Reaper), National Sergeant at Arms (Repo), National Enforcer (Gear Jammer), National Treasurer (California Kid), National Secretary (Lonestar)
  Responsible for: Policy creation, membership roll, general operating orders""",
            "category": "admin_only",
            "is_active": True,
            "admin_only": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Meeting Schedule (Admin Only)",
            "content": """MEETINGS:
- National Officer: Wednesdays 3pm EST
- Chapter Officer: Wednesdays 5pm EST  
- Prospect: Thursdays 4pm CST (mandatory, 100% attendance)
- Member meetings vary by chapter
- Meeting rules: Microphones muted in app, cameras on (when <20 people), follow Robert's Rules of Order""",
            "category": "admin_only",
            "is_active": True,
            "admin_only": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get('username'),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get('username')
        }
    ]
    
    await db.ai_knowledge.insert_many(default_entries)
    return {"message": f"Initialized {len(default_entries)} knowledge entries"}


# ==================== OFFICER TRACKING (Attendance & Dues) ====================

OFFICER_TITLES = ['Prez', 'VP', 'S@A', 'Enf', 'SEC', 'CD', 'T', 'ENF', 'PM', 'CC', 'CMD', 'CCLC', 'NVP', 'NPrez']
# Note: A&D editing is now controlled by edit_dues permission, not hardcoded titles
AD_EDIT_TITLES = ['SEC', 'NVP', 'NPrez', 'Prez', 'VP', 'T']  # Fallback list - actual control via permissions
CHAPTERS = ['National', 'AD', 'HA', 'HS']

async def check_edit_dues_permission(user: dict) -> bool:
    """Check if user has edit_dues permission from Permission Panel"""
    chapter = user.get('chapter', 'National')
    title = user.get('title', '')
    
    # Check permission from database
    perms = await db.role_permissions.find_one(
        {"chapter": chapter, "title": title},
        {"_id": 0, "edit_dues": 1}
    )
    
    if perms and perms.get('edit_dues'):
        return True
    
    return False

async def check_edit_attendance_permission(user: dict) -> bool:
    """Check if user has edit_attendance permission from Permission Panel"""
    chapter = user.get('chapter', 'National')
    title = user.get('title', '')
    
    # Check permission from database
    perms = await db.role_permissions.find_one(
        {"chapter": chapter, "title": title},
        {"_id": 0, "edit_attendance": 1}
    )
    
    if perms and perms.get('edit_attendance'):
        return True
    
    return False

def is_secretary(user: dict) -> bool:
    """Legacy check - now uses AD_EDIT_TITLES as fallback. Real control via permissions."""
    user_title = user.get('title', '')
    # Include Prez in the list for backward compatibility
    return user_title in AD_EDIT_TITLES

def is_any_officer(user: dict) -> bool:
    """Check if user is any officer (can view)"""
    return user.get('title') in OFFICER_TITLES or user.get('role') == 'admin'

def can_access_ad(user: dict) -> bool:
    """Check if user can access A&D page - reads from database permissions"""
    user_title = user.get('title', '')
    user_role = user.get('role', '')
    
    # Admins always have access
    if user_role == 'admin':
        return True
    
    # For now, use sync check - will be updated to async in endpoint
    # This is a fallback for sync contexts
    if user_title in ['CC', 'CCLC']:
        return False
    
    return user_title in OFFICER_TITLES


async def check_ad_access(user: dict) -> bool:
    """Async check if user can access A&D page from database (no admin bypass)"""
    return await check_permission(user, "ad_page_access")


async def check_view_full_member_info(user: dict) -> bool:
    """Check if user can view full member info from database (no admin bypass)"""
    return await check_permission(user, "view_full_member_info")


async def check_manage_system_users(user: dict) -> bool:
    """Check if user can manage system users from database (no admin bypass)"""
    return await check_permission(user, "manage_system_users")

class AttendanceRecord(BaseModel):
    member_id: str
    meeting_date: str  # YYYY-MM-DD
    meeting_type: str  # 'national_officer', 'chapter_officer', 'prospect', 'member'
    status: str  # 'present', 'absent', 'excused'
    notes: Optional[str] = None

class DuesRecord(BaseModel):
    member_id: str
    month: str  # 'Jan_2026', 'Feb_2026', etc. or just current month
    status: str  # 'paid', 'late', 'unpaid'
    notes: Optional[str] = None

@api_router.get("/officer-tracking/members")
async def get_members_by_chapter(current_user: dict = Depends(verify_token)):
    """Get all members organized by chapter - officers can view based on permissions"""
    user_title = current_user.get('title', '')
    user_role = current_user.get('role', '')
    
    # Log for debugging
    logger.info(f"A&D access attempt - User: {current_user.get('username')}, Title: {user_title}, Role: {user_role}")
    
    # Check permission from database
    if not await check_ad_access(current_user):
        logger.warning(f"A&D access denied - User: {current_user.get('username')}, Title: {user_title}")
        raise HTTPException(status_code=403, detail="You don't have permission to access this page")
    
    # Check if user can view National chapter A&D
    can_view_national = can_view_national_ad(current_user)
    
    result = {}
    for chapter in CHAPTERS:
        # Skip National chapter if user can't view it
        if chapter == "National" and not can_view_national:
            continue
            
        # Get ALL members in this chapter (not just officers)
        query = {"chapter": chapter}
        members = await db.members.find(query, {"_id": 0}).to_list(length=None)
        
        # Sort by title importance, then by handle
        title_order = {t: i for i, t in enumerate(OFFICER_TITLES)}
        members.sort(key=lambda x: (title_order.get(x.get('title', ''), 999), x.get('handle', '')))
        
        result[chapter] = [{
            "id": m.get("id"),
            "handle": m.get("handle"),
            "name": m.get("name"),
            "title": m.get("title"),
            "chapter": m.get("chapter"),
            "email": m.get("email"),
            "meeting_attendance": m.get("meeting_attendance", []),
            "dues_history": m.get("dues_history", []),
            "non_dues_paying": m.get("non_dues_paying", False)
        } for m in members]
    
    return result

@api_router.get("/officer-tracking/officers")
async def get_officers_by_chapter(current_user: dict = Depends(verify_token)):
    """Get all officers organized by chapter - based on permissions"""
    if not await check_ad_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to access this page")
    
    # Check if user can view National chapter A&D
    can_view_national = can_view_national_ad(current_user)
    
    result = {}
    for chapter in CHAPTERS:
        # Skip National chapter if user can't view it
        if chapter == "National" and not can_view_national:
            continue
            
        # Get members who are officers in this chapter
        query = {
            "chapter": chapter,
            "title": {"$in": OFFICER_TITLES}
        }
        officers = await db.members.find(query, {"_id": 0}).to_list(length=None)
        
        # Sort by title importance
        title_order = {t: i for i, t in enumerate(OFFICER_TITLES)}
        officers.sort(key=lambda x: title_order.get(x.get('title', ''), 999))
        
        result[chapter] = [{
            "id": o.get("id"),
            "handle": o.get("handle"),
            "name": o.get("name"),
            "title": o.get("title"),
            "chapter": o.get("chapter"),
            "email": o.get("email"),
            "meeting_attendance": o.get("meeting_attendance", []),
            "dues_history": o.get("dues_history", [])
        } for o in officers]
    
    return result

@api_router.get("/officer-tracking/attendance")
async def get_attendance_records(
    chapter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Get attendance records - based on permissions"""
    if not await check_ad_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to access this page")
    
    query = {}
    if chapter:
        # Get member IDs for this chapter
        chapter_members = await db.members.find({"chapter": chapter}, {"id": 1}).to_list(length=None)
        member_ids = [m.get("id") for m in chapter_members]
        query["member_id"] = {"$in": member_ids}
    
    if start_date:
        query["meeting_date"] = {"$gte": start_date}
    if end_date:
        if "meeting_date" in query:
            query["meeting_date"]["$lte"] = end_date
        else:
            query["meeting_date"] = {"$lte": end_date}
    
    records = await db.officer_attendance.find(query, {"_id": 0}).to_list(length=None)
    return records

@api_router.post("/officer-tracking/attendance")
async def record_attendance(record: AttendanceRecord, current_user: dict = Depends(verify_token)):
    """Record attendance - requires edit_attendance permission"""
    has_permission = await check_edit_attendance_permission(current_user)
    if not has_permission and not is_secretary(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to edit attendance")
    
    # Check for existing record in officer_attendance collection
    existing = await db.officer_attendance.find_one({
        "member_id": record.member_id,
        "meeting_date": record.meeting_date,
        "meeting_type": record.meeting_type
    })
    
    record_data = {
        "id": existing.get("id") if existing else str(uuid.uuid4()),
        "member_id": record.member_id,
        "meeting_date": record.meeting_date,
        "meeting_type": record.meeting_type,
        "status": record.status,
        "notes": record.notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get('username')
    }
    
    if existing:
        await db.officer_attendance.update_one(
            {"id": existing.get("id")},
            {"$set": record_data}
        )
    else:
        record_data["created_at"] = datetime.now(timezone.utc).isoformat()
        record_data["created_by"] = current_user.get('username')
        await db.officer_attendance.insert_one(record_data)
    
    # Update member's meeting_attendance in the member database
    # Format: {"2026": [{date: "2026-01-07", status: 0|1|2, note: ""}, ...]}
    try:
        year_str = record.meeting_date.split('-')[0]  # Extract year from "2026-01-07"
        
        # Map status string to number: present=1, absent=0, excused=2
        status_map = {'present': 1, 'absent': 0, 'excused': 2}
        status_num = status_map.get(record.status, 0)
        
        # Get the member's current attendance data
        member = await db.members.find_one({"id": record.member_id})
        if member:
            attendance = member.get('meeting_attendance', {})
            
            # Initialize year array if it doesn't exist
            if year_str not in attendance or not isinstance(attendance.get(year_str), list):
                attendance[year_str] = []
            
            # Check if meeting for this date already exists
            year_meetings = attendance[year_str]
            existing_idx = None
            for i, m in enumerate(year_meetings):
                if isinstance(m, dict) and m.get('date') == record.meeting_date:
                    existing_idx = i
                    break
            
            meeting_entry = {
                "date": record.meeting_date,
                "status": status_num,
                "note": record.notes or ""
            }
            
            if existing_idx is not None:
                # Update existing meeting
                year_meetings[existing_idx] = meeting_entry
            else:
                # Add new meeting and sort by date
                year_meetings.append(meeting_entry)
                year_meetings.sort(key=lambda x: x.get('date', '') if isinstance(x, dict) else '')
            
            attendance[year_str] = year_meetings
            
            # Save back to member document
            await db.members.update_one(
                {"id": record.member_id},
                {"$set": {"meeting_attendance": attendance}}
            )
            logger.info(f"Updated member {record.member_id} attendance for {record.meeting_date}: {record.status}")
    except Exception as e:
        logger.error(f"Failed to update member attendance field: {str(e)}")
    
    return {"message": "Attendance recorded and member updated", "id": record_data["id"]}

@api_router.delete("/officer-tracking/attendance/{record_id}")
async def delete_attendance(record_id: str, current_user: dict = Depends(verify_token)):
    """Delete attendance record - requires edit_attendance permission"""
    has_permission = await check_edit_attendance_permission(current_user)
    if not has_permission and not is_secretary(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to delete attendance")
    
    # Get the record first to update member
    record = await db.officer_attendance.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Remove from member's meeting_attendance (format: {year: [{date, status, note}, ...]})
    try:
        year_str = record["meeting_date"].split('-')[0]
        member = await db.members.find_one({"id": record["member_id"]})
        if member:
            attendance = member.get('meeting_attendance', {})
            if year_str in attendance and isinstance(attendance[year_str], list):
                # Filter out the meeting with matching date
                attendance[year_str] = [
                    m for m in attendance[year_str] 
                    if not (isinstance(m, dict) and m.get('date') == record["meeting_date"])
                ]
                await db.members.update_one(
                    {"id": record["member_id"]},
                    {"$set": {"meeting_attendance": attendance}}
                )
    except Exception as e:
        logger.error(f"Failed to update member attendance on delete: {str(e)}")
    
    result = await db.officer_attendance.delete_one({"id": record_id})
    return {"message": "Attendance record deleted"}

# Endpoint to delete attendance from member side (syncs to officer_attendance)
@api_router.delete("/members/{member_id}/attendance")
async def delete_member_attendance(
    member_id: str, 
    meeting_date: str,
    current_user: dict = Depends(verify_token)
):
    """Delete a meeting from member's attendance - syncs to officer_attendance collection"""
    # Check permission
    has_permission = await check_edit_attendance_permission(current_user)
    if not has_permission and not is_secretary(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to delete attendance")
    
    # Remove from officer_attendance collection
    result = await db.officer_attendance.delete_many({
        "member_id": member_id,
        "meeting_date": meeting_date
    })
    logger.info(f"Deleted {result.deleted_count} records from officer_attendance for member {member_id}, date {meeting_date}")
    
    # Remove from member's meeting_attendance
    try:
        year_str = meeting_date.split('-')[0]
        member = await db.members.find_one({"id": member_id})
        if member:
            attendance = member.get('meeting_attendance', {})
            if year_str in attendance and isinstance(attendance[year_str], list):
                attendance[year_str] = [
                    m for m in attendance[year_str] 
                    if not (isinstance(m, dict) and m.get('date') == meeting_date)
                ]
                await db.members.update_one(
                    {"id": member_id},
                    {"$set": {"meeting_attendance": attendance}}
                )
    except Exception as e:
        logger.error(f"Failed to update member attendance on delete: {str(e)}")
    
    return {"message": "Attendance record deleted from both locations"}

@api_router.get("/officer-tracking/dues")
async def get_dues_records(
    chapter: Optional[str] = None,
    quarter: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Get dues records - based on permissions"""
    if not await check_ad_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to access this page")
    
    query = {}
    if chapter:
        chapter_members = await db.members.find({"chapter": chapter}, {"id": 1}).to_list(length=None)
        member_ids = [m.get("id") for m in chapter_members]
        query["member_id"] = {"$in": member_ids}
    
    if quarter:
        query["quarter"] = quarter
    
    records = await db.officer_dues.find(query, {"_id": 0}).to_list(length=None)
    
    # Enrich with forgiven and extension status from members collection
    now = datetime.now(timezone.utc)
    current_month = f"{now.strftime('%b')}_{now.year}"  # Format: "Jan_2026"
    
    # Get all active extensions
    extensions = await db.dues_extensions.find({}).to_list(100)
    active_extensions = {}
    for ext in extensions:
        try:
            ext_date = datetime.fromisoformat(ext.get("extension_until", "").replace("Z", "+00:00"))
            if ext_date > now:
                active_extensions[ext.get("member_id")] = ext.get("extension_until")
        except:
            pass
    
    # Get all members to check for forgiven dues
    all_members = await db.members.find({}, {"_id": 0, "id": 1, "dues": 1}).to_list(500)
    year_str = str(now.year)
    month_idx = now.month - 1
    
    forgiven_members = {}
    for member in all_members:
        member_id = member.get("id")
        dues = member.get("dues", {})
        if year_str in dues:
            year_dues = dues[year_str]
            if isinstance(year_dues, list) and len(year_dues) > month_idx:
                month_data = year_dues[month_idx]
                if isinstance(month_data, dict) and month_data.get("forgiven"):
                    forgiven_members[member_id] = {
                        "forgiven_by": month_data.get("forgiven_by"),
                        "note": month_data.get("note", "")
                    }
    
    # Add extension and forgiven status to records for current month
    enriched_records = []
    for record in records:
        record_copy = dict(record)
        member_id = record.get("member_id")
        
        # Check if member has active extension
        if member_id in active_extensions:
            record_copy["has_extension"] = True
            record_copy["extension_until"] = active_extensions[member_id]
        
        # Check if dues were forgiven for current month
        if record.get("month") == current_month and member_id in forgiven_members:
            record_copy["status"] = "forgiven"
            record_copy["forgiven"] = True
            record_copy["forgiven_by"] = forgiven_members[member_id].get("forgiven_by")
            record_copy["notes"] = forgiven_members[member_id].get("note", record.get("notes", ""))
        
        enriched_records.append(record_copy)
    
    # Also add records for members with extensions or forgiven dues who don't have records yet
    existing_member_months = {(r.get("member_id"), r.get("month")) for r in records}
    
    for member_id, ext_until in active_extensions.items():
        if (member_id, current_month) not in existing_member_months:
            enriched_records.append({
                "id": str(uuid.uuid4()),
                "member_id": member_id,
                "month": current_month,
                "status": "extended",
                "has_extension": True,
                "extension_until": ext_until,
                "notes": f"Extended until {ext_until[:10]}"
            })
    
    for member_id, forgive_info in forgiven_members.items():
        if (member_id, current_month) not in existing_member_months and member_id not in active_extensions:
            enriched_records.append({
                "id": str(uuid.uuid4()),
                "member_id": member_id,
                "month": current_month,
                "status": "forgiven",
                "forgiven": True,
                "forgiven_by": forgive_info.get("forgiven_by"),
                "notes": forgive_info.get("note", "")
            })
    
    return enriched_records

@api_router.post("/officer-tracking/dues")
async def record_dues(record: DuesRecord, current_user: dict = Depends(verify_token)):
    """Record dues status - requires edit_dues permission"""
    has_permission = await check_edit_dues_permission(current_user)
    if not has_permission and not is_secretary(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to edit dues")
    
    # Check for existing record in officer_dues collection
    existing = await db.officer_dues.find_one({
        "member_id": record.member_id,
        "month": record.month
    })
    
    record_data = {
        "id": existing.get("id") if existing else str(uuid.uuid4()),
        "member_id": record.member_id,
        "month": record.month,
        "status": record.status,  # 'paid', 'late', 'unpaid'
        "notes": record.notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get('username')
    }
    
    if existing:
        await db.officer_dues.update_one(
            {"id": existing.get("id")},
            {"$set": record_data}
        )
    else:
        record_data["created_at"] = datetime.now(timezone.utc).isoformat()
        record_data["created_by"] = current_user.get('username')
        await db.officer_dues.insert_one(record_data)
    
    # Parse month format "Mon_YYYY" (e.g., "Jan_2026") to get year and month index
    try:
        month_abbr, year_str = record.month.split('_')
        month_map = {'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                     'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11}
        month_index = month_map.get(month_abbr, 0)
        
        # Get the member's current dues data
        member = await db.members.find_one({"id": record.member_id})
        if member:
            dues = member.get('dues', {})
            
            # Initialize year array if it doesn't exist or is invalid
            if year_str not in dues or not isinstance(dues.get(year_str), list) or len(dues.get(year_str, [])) < 12:
                dues[year_str] = [{"status": "unpaid", "note": ""} for _ in range(12)]
            
            # Ensure each month entry is a proper dict (fix any invalid entries)
            for i in range(12):
                if not isinstance(dues[year_str][i], dict):
                    dues[year_str][i] = {"status": "unpaid", "note": ""}
            
            # Update the specific month
            dues[year_str][month_index] = {
                "status": record.status,
                "note": record.notes or ""
            }
            
            # Build update document
            update_doc = {"dues": dues}
            
            # If marking as paid, clear any dues suspension and restore Discord permissions
            if record.status == "paid":
                update_doc["dues_suspended"] = False
                update_doc["dues_suspended_at"] = None
                
                # Restore Discord permissions if they were suspended
                discord_result = await restore_discord_member(record.member_id)
                if discord_result.get("success"):
                    logger.info(f"Discord permissions restored for {record.member_id}")
            
            # Save back to member document
            await db.members.update_one(
                {"id": record.member_id},
                {"$set": update_doc}
            )
            logger.info(f"Updated member {record.member_id} dues for {record.month}: {record.status}")
    except Exception as e:
        logger.error(f"Failed to update member dues field: {str(e)}")
    
    return {"message": "Dues recorded and member updated", "id": record_data["id"]}


@api_router.get("/officer-tracking/dues/history/{member_id}")
async def get_member_dues_history(member_id: str, current_user: dict = Depends(verify_token)):
    """Get dues payment history for a member including Square transaction info"""
    if not await check_ad_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view dues history")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get subscription link info (for Square customer ID)
    subscription_link = await db.member_subscriptions.find_one(
        {"member_id": member_id}, {"_id": 0}
    )
    
    # Get Square payment history via invoices for subscription
    square_payments = []
    if subscription_link and square_client:
        subscription_id = subscription_link.get("square_subscription_id")
        
        # First try to get invoices from the subscription directly
        if subscription_id:
            try:
                # Get subscription details to find invoice_ids
                sub_result = square_client.subscriptions.get(subscription_id=subscription_id)
                if sub_result and sub_result.subscription:
                    subscription = sub_result.subscription
                    invoice_ids = getattr(subscription, 'invoice_ids', None) or []
                    
                    # Fetch invoice details for each invoice_id
                    for invoice_id in invoice_ids:
                        try:
                            inv_result = square_client.invoices.get(invoice_id=invoice_id)
                            if inv_result and inv_result.invoice:
                                invoice = inv_result.invoice
                                # Get invoice payment info
                                status = getattr(invoice, 'status', 'UNKNOWN')
                                order_id = getattr(invoice, 'order_id', None)
                                
                                payment_info = {
                                    "invoice_id": invoice.id,
                                    "subscription_id": subscription_id,
                                    "amount": 0,
                                    "currency": "USD",
                                    "invoice_date": getattr(invoice, 'created_at', None),
                                    "due_date": getattr(invoice, 'due_date', None),
                                    "status": status,
                                    "payment_id": None,
                                    "paid_at": None,
                                    "receipt_url": None,
                                    "order_id": order_id
                                }
                                
                                # Get payment amount from payment_requests
                                if hasattr(invoice, 'payment_requests') and invoice.payment_requests:
                                    req = invoice.payment_requests[0]
                                    if hasattr(req, 'computed_amount_money') and req.computed_amount_money:
                                        payment_info["amount"] = req.computed_amount_money.amount / 100
                                        payment_info["currency"] = req.computed_amount_money.currency or "USD"
                                
                                # If invoice is paid and has an order_id, get the payment_id from the order
                                if status == "PAID" and order_id:
                                    try:
                                        # Get the order to find the tender and payment_id
                                        order_result = square_client.orders.get(order_id=order_id)
                                        if order_result and order_result.order:
                                            order = order_result.order
                                            # Get payment info from tenders
                                            tenders = getattr(order, 'tenders', None) or []
                                            for tender in tenders:
                                                if hasattr(tender, 'payment_id') and tender.payment_id:
                                                    payment_info["payment_id"] = tender.payment_id
                                                    payment_info["paid_at"] = getattr(tender, 'created_at', None) or getattr(invoice, 'updated_at', None)
                                                    break
                                    except Exception as order_err:
                                        logger.warning(f"Failed to fetch order {order_id}: {order_err}")
                                    
                                    # Fallback: use invoice updated_at as paid_at if we still don't have it
                                    if not payment_info["paid_at"]:
                                        payment_info["paid_at"] = getattr(invoice, 'updated_at', None)
                                
                                square_payments.append(payment_info)
                        except Exception as inv_err:
                            logger.warning(f"Failed to fetch invoice {invoice_id}: {inv_err}")
                            continue
            except Exception as sub_err:
                logger.warning(f"Failed to fetch subscription {subscription_id}: {sub_err}")
        
        # Fallback: Try to get payments directly by customer_id
        if not square_payments:
            try:
                customer_id = subscription_link.get("square_customer_id")
                if customer_id:
                    result = square_client.payments.list(
                        customer_id=customer_id,
                        limit=20
                    )
                    if result and result.payments:
                        for payment in result.payments:
                            if payment.status == "COMPLETED":
                                square_payments.append({
                                    "invoice_id": None,
                                    "subscription_id": subscription_id,
                                    "payment_id": payment.id,
                                    "amount": payment.amount_money.amount / 100 if payment.amount_money else 0,
                                    "currency": payment.amount_money.currency if payment.amount_money else "USD",
                                    "invoice_date": None,
                                    "due_date": None,
                                    "paid_at": payment.created_at,
                                    "status": payment.status,
                                    "receipt_url": payment.receipt_url,
                                    "order_id": None
                                })
            except Exception as pay_err:
                logger.warning(f"Failed to fetch payments for member {member_id}: {pay_err}")
    
    # Get dues records from officer_dues collection
    dues_records = await db.officer_dues.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get dues from member record
    member_dues = member.get("dues", {})
    
    # Find last paid date
    last_paid = None
    last_paid_note = None
    
    # Check member dues array for most recent paid status
    for year in sorted(member_dues.keys(), reverse=True):
        year_dues = member_dues[year]
        if isinstance(year_dues, list):
            for month_idx in range(len(year_dues) - 1, -1, -1):
                month_data = year_dues[month_idx]
                if isinstance(month_data, dict) and month_data.get("status") == "paid":
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    last_paid = f"{month_names[month_idx]} {year}"
                    last_paid_note = month_data.get("note", "")
                    break
        if last_paid:
            break
    
    return {
        "member_id": member_id,
        "member_handle": member.get("handle"),
        "member_name": member.get("name"),
        "last_paid": last_paid,
        "last_paid_note": last_paid_note,
        "subscription_info": subscription_link,
        "square_payments": square_payments,
        "dues_records": dues_records,
        "member_dues": member_dues
    }


@api_router.delete("/officer-tracking/dues/{record_id}")
async def delete_dues(record_id: str, current_user: dict = Depends(verify_token)):
    """Delete dues record - requires edit_dues permission"""
    has_permission = await check_edit_dues_permission(current_user)
    if not has_permission and not is_secretary(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to delete dues records")
    
    # Get the record first to update member
    record = await db.officer_dues.find_one({"id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Dues record not found")
    
    # Remove from member's dues_history array
    await db.members.update_one(
        {"id": record["member_id"]},
        {"$pull": {"dues_history": {"quarter": record["quarter"]}}}
    )
    
    result = await db.officer_dues.delete_one({"id": record_id})
    return {"message": "Dues record deleted"}


@api_router.get("/dues/debug-payment-orders")
async def debug_payment_orders(current_user: dict = Depends(verify_token)):
    """Debug endpoint to see dues-related orders and their data"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    # Search payments directly (not orders) around July 5, 2025
    start_date = "2025-07-01T00:00:00Z"
    end_date = "2025-07-10T00:00:00Z"
    
    # Get payments
    payments_result = square_client.payments.list(
        begin_time=start_date,
        end_time=end_date,
        limit=100
    )
    
    payments_list = []
    # Handle pager response
    payments_data = list(payments_result) if payments_result else []
    for payment in payments_data:
        payment_info = {
            "payment_id": payment.id,
            "created_at": payment.created_at,
            "amount": payment.amount_money.amount/100 if payment.amount_money else 0,
            "status": payment.status,
            "order_id": getattr(payment, 'order_id', None),
            "customer_id": getattr(payment, 'customer_id', None),
            "note": getattr(payment, 'note', None),
            "receipt_url": getattr(payment, 'receipt_url', None),
            "buyer_email": getattr(payment, 'buyer_email_address', None)
        }
        
        # Get customer details if available
        cust_id = getattr(payment, 'customer_id', None)
        if cust_id:
            try:
                cust_result = square_client.customers.get(customer_id=cust_id)
                if cust_result and cust_result.customer:
                    c = cust_result.customer
                    payment_info["customer_name"] = f"{getattr(c, 'given_name', '') or ''} {getattr(c, 'family_name', '') or ''}".strip()
                    payment_info["customer_email"] = getattr(c, 'email_address', None)
                    payment_info["customer_nickname"] = getattr(c, 'nickname', None)
                    payment_info["customer_note"] = getattr(c, 'note', None)
            except:
                pass
        
        payments_list.append(payment_info)
    
    # Also search orders
    orders_result = square_client.orders.search(
        location_ids=[SQUARE_LOCATION_ID],
        limit=100,
        query={
            "filter": {
                "date_time_filter": {
                    "created_at": {
                        "start_at": start_date,
                        "end_at": end_date
                    }
                }
            },
            "sort": {"sort_field": "CREATED_AT", "sort_order": "ASC"}
        }
    )
    
    orders_list = []
    for order in (orders_result.orders or []):
        line_items = getattr(order, 'line_items', None) or []
        items_info = [{"name": getattr(item, 'name', ''), "amount": getattr(item, 'total_money', None).amount/100 if getattr(item, 'total_money', None) else 0} for item in line_items]
        
        order_info = {
            "order_id": order.id,
            "created_at": order.created_at,
            "state": getattr(order, 'state', None),
            "total_amount": getattr(order, 'total_money', None).amount/100 if getattr(order, 'total_money', None) else 0,
            "customer_id": getattr(order, 'customer_id', None),
            "items": items_info
        }
        orders_list.append(order_info)
    
    return {
        "payments": payments_list, 
        "payments_count": len(payments_list),
        "orders": orders_list,
        "orders_count": len(orders_list),
        "date_range": f"{start_date} to {end_date}"
    }


@api_router.get("/officer-tracking/summary")
async def get_tracking_summary(current_user: dict = Depends(verify_token)):
    """Get summary of attendance and dues by chapter - based on permissions"""
    if not await check_ad_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to access this page")
    
    # Check if user can view National chapter A&D
    can_view_national = can_view_national_ad(current_user)
    
    # Get current month info
    now = datetime.now()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_month = f"{month_names[now.month - 1]}_{now.year}"  # e.g., "Jan_2026"
    
    summary = {}
    
    # Get all active dues extensions (extension_until >= today)
    today_str = now.strftime("%Y-%m-%d")
    active_extensions = await db.dues_extensions.find({
        "extension_until": {"$gte": today_str}
    }).to_list(length=None)
    extended_member_ids = set(ext.get("member_id") for ext in active_extensions)
    
    for chapter in CHAPTERS:
        # Skip National chapter if user can't view it
        if chapter == "National" and not can_view_national:
            continue
            
        # Get ALL members in chapter (include non_dues_paying field)
        members = await db.members.find(
            {"chapter": chapter},
            {"id": 1, "dues": 1, "non_dues_paying": 1}
        ).to_list(length=None)
        
        # Separate dues-paying members from non-dues-paying (exempt) members
        dues_paying_members = [m for m in members if not m.get("non_dues_paying", False)]
        non_dues_paying_members = [m for m in members if m.get("non_dues_paying", False)]
        
        member_ids = [m.get("id") for m in members]
        dues_paying_member_ids = [m.get("id") for m in dues_paying_members]
        
        # Get attendance stats for last 30 days (all members)
        thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        attendance = await db.officer_attendance.find({
            "member_id": {"$in": member_ids},
            "meeting_date": {"$gte": thirty_days_ago}
        }).to_list(length=None)
        
        present_count = sum(1 for a in attendance if a.get("status") == "present")
        total_attendance = len(attendance)
        
        # Count dues paid for current month from officer_dues collection
        # Include both 'paid' and 'extended' status as paid
        dues_from_officer_dues = await db.officer_dues.find({
            "member_id": {"$in": dues_paying_member_ids},
            "month": current_month,
            "status": {"$in": ["paid", "extended"]}
        }).to_list(length=None)
        
        # Count UNIQUE members who have paid (avoid duplicate records)
        members_paid_in_officer_dues = set(d.get("member_id") for d in dues_from_officer_dues)
        paid_from_officer_dues = len(members_paid_in_officer_dues)
        
        year_str = str(now.year)
        month_idx = now.month - 1  # 0-indexed
        
        paid_count = paid_from_officer_dues
        for m in dues_paying_members:
            member_id = m.get("id")
            # Skip if already counted from officer_dues collection
            if member_id in members_paid_in_officer_dues:
                continue
                
            # Check if member has an active extension (not already recorded) - count as paid
            if member_id in extended_member_ids:
                paid_count += 1
                continue
                
            # Fallback: check members.dues field
            dues = m.get("dues", {})
            if year_str in dues and isinstance(dues[year_str], list) and len(dues[year_str]) > month_idx:
                month_data = dues[year_str][month_idx]
                # Handle different formats: dict with status, or just a status string/bool
                if isinstance(month_data, dict):
                    if month_data.get("status") in ["paid", "extended"]:
                        paid_count += 1
                elif month_data == "paid" or month_data is True:
                    paid_count += 1
        
        # Dues total only counts dues-paying members (excludes exempt/non-dues-paying)
        dues_total = len(dues_paying_members)
        
        summary[chapter] = {
            "member_count": len(member_ids),
            "attendance_rate": round(present_count / total_attendance * 100, 1) if total_attendance > 0 else 0,
            "meetings_tracked": total_attendance,
            "dues_paid": paid_count,
            "dues_total": dues_total,
            "current_month": current_month
        }
    
    return summary


# ==================== MY DUES ENDPOINT ====================

@api_router.get("/my-dues")
async def get_my_dues(current_user: dict = Depends(verify_token)):
    """Get dues payment history for the logged-in user's linked member profile"""
    
    # Get user's linked member_id
    user = await db.users.find_one({"username": current_user.get("username")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    member_id = user.get("member_id")
    
    # If no member_id linked, try to find by matching username to handle
    if not member_id:
        member = await db.members.find_one({"handle": current_user.get("username")}, {"_id": 0})
        if member:
            member_id = member.get("id")
            # Link for future use
            await db.users.update_one(
                {"username": current_user.get("username")},
                {"$set": {"member_id": member_id}}
            )
    
    if not member_id:
        return {
            "linked": False,
            "message": "Your account is not linked to a member profile. Please contact an administrator.",
            "dues": None
        }
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        return {
            "linked": False,
            "message": "Linked member profile not found. Please contact an administrator.",
            "dues": None
        }
    
    # Get subscription info if available
    subscription_link = await db.member_subscriptions.find_one(
        {"member_id": member_id}, {"_id": 0}
    )
    
    # Get Square payment history if we have subscription info
    square_payments = []
    if subscription_link and square_client:
        subscription_id = subscription_link.get("square_subscription_id")
        
        if subscription_id:
            try:
                sub_result = square_client.subscriptions.get(subscription_id=subscription_id)
                if sub_result and sub_result.subscription:
                    subscription = sub_result.subscription
                    invoice_ids = getattr(subscription, 'invoice_ids', None) or []
                    
                    for invoice_id in invoice_ids[:12]:  # Limit to last 12 invoices
                        try:
                            inv_result = square_client.invoices.get(invoice_id=invoice_id)
                            if inv_result and inv_result.invoice:
                                invoice = inv_result.invoice
                                status = getattr(invoice, 'status', 'UNKNOWN')
                                order_id = getattr(invoice, 'order_id', None)
                                
                                payment_info = {
                                    "invoice_id": invoice.id,
                                    "amount": 0,
                                    "currency": "USD",
                                    "invoice_date": getattr(invoice, 'created_at', None),
                                    "status": status,
                                    "payment_id": None,
                                    "paid_at": None
                                }
                                
                                if hasattr(invoice, 'payment_requests') and invoice.payment_requests:
                                    req = invoice.payment_requests[0]
                                    if hasattr(req, 'computed_amount_money') and req.computed_amount_money:
                                        payment_info["amount"] = req.computed_amount_money.amount / 100
                                        payment_info["currency"] = req.computed_amount_money.currency or "USD"
                                
                                if status == "PAID" and order_id:
                                    try:
                                        order_result = square_client.orders.get(order_id=order_id)
                                        if order_result and order_result.order:
                                            tenders = getattr(order_result.order, 'tenders', None) or []
                                            for tender in tenders:
                                                if hasattr(tender, 'payment_id') and tender.payment_id:
                                                    payment_info["payment_id"] = tender.payment_id
                                                    payment_info["paid_at"] = getattr(tender, 'created_at', None)
                                                    break
                                    except:
                                        pass
                                    
                                    if not payment_info["paid_at"]:
                                        payment_info["paid_at"] = getattr(invoice, 'updated_at', None)
                                
                                square_payments.append(payment_info)
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Failed to fetch subscription for my-dues: {e}")
    
    # Also get one-time payment links for this member
    synced_payments = await db.synced_payment_links.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("payment_date", -1).limit(20).to_list(20)
    
    # Get dues status from member record (legacy format)
    member_dues = member.get("dues", {})
    
    # Also get dues from member_dues collection (new format with payment_info)
    dues_records = await db.member_dues.find(
        {"member_id": member_id},
        {"_id": 0}
    ).to_list(10)
    
    # Build payment_info map from dues records
    payment_info_by_year = {}
    for record in dues_records:
        year = str(record.get("year"))
        payment_info_by_year[year] = record.get("payment_info", {})
        # Also merge the months data if available
        if record.get("months"):
            if year not in member_dues:
                member_dues[year] = []
            months_data = record.get("months", {})
            month_names_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for idx, month_name in enumerate(month_names_list):
                status = months_data.get(month_name, "unpaid")
                if isinstance(member_dues[year], list) and len(member_dues[year]) > idx:
                    # Update existing entry if the new data shows paid
                    if status == "paid":
                        member_dues[year][idx] = True
                elif isinstance(member_dues[year], list):
                    # Extend list if needed
                    while len(member_dues[year]) <= idx:
                        member_dues[year].append(False)
                    member_dues[year][idx] = status == "paid"
    
    # Also extract payment notes from member's dues field (legacy format)
    month_names_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for year_str, year_data in member_dues.items():
        if isinstance(year_data, list) and year_str not in payment_info_by_year:
            payment_info_by_year[year_str] = {}
        if isinstance(year_data, list):
            for idx, month_data in enumerate(year_data):
                if idx < len(month_names_list):
                    month_name = month_names_list[idx]
                    # Check if month_data has a note field
                    if isinstance(month_data, dict) and month_data.get("note"):
                        if year_str not in payment_info_by_year:
                            payment_info_by_year[year_str] = {}
                        payment_info_by_year[year_str][month_name] = month_data.get("note")
    
    # Calculate current status
    now = datetime.now(timezone.utc)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    year_str = str(now.year)
    month_idx = now.month - 1
    
    current_month_status = "unpaid"
    if year_str in member_dues and isinstance(member_dues[year_str], list) and len(member_dues[year_str]) > month_idx:
        month_data = member_dues[year_str][month_idx]
        if isinstance(month_data, dict):
            current_month_status = month_data.get("status", "unpaid")
        elif month_data is True or month_data == "paid":
            current_month_status = "paid"
    
    return {
        "linked": True,
        "member_id": member_id,
        "member_handle": member.get("handle"),
        "member_name": member.get("name"),
        "current_month": f"{month_names[month_idx]} {now.year}",
        "current_month_status": current_month_status,
        "has_subscription": subscription_link is not None,
        "subscription_info": {
            "customer_name": subscription_link.get("customer_name") if subscription_link else None,
            "last_synced": subscription_link.get("last_synced") if subscription_link else None
        } if subscription_link else None,
        "square_payments": square_payments,
        "one_time_payments": synced_payments,
        "dues_by_year": member_dues,
        "payment_info_by_year": payment_info_by_year
    }


# ==================== ROLE PERMISSIONS ENDPOINTS ====================

# Permission definitions
AVAILABLE_PERMISSIONS = [
    {"key": "ad_page_access", "label": "A&D Page Access", "description": "Can view Attendance & Dues page"},
    {"key": "edit_attendance", "label": "Edit Attendance", "description": "Can record and edit attendance on A&D page"},
    {"key": "edit_dues", "label": "Edit Dues", "description": "Can update dues status on A&D page"},
    {"key": "view_promotions", "label": "View Promotions Page", "description": "Can access Promotions page to manage Discord roles and member titles"},
    {"key": "view_full_member_info", "label": "View Full Member Info", "description": "Can see all member details (address, DOB, etc.)"},
    {"key": "view_private_personal_email", "label": "View Private Personal Email", "description": "Can see personal emails even if marked private"},
    {"key": "edit_members", "label": "Edit Members", "description": "Can add/edit/delete members"},
    {"key": "view_prospects", "label": "View Prospects", "description": "Can access Prospects page"},
    {"key": "manage_store", "label": "Manage Store", "description": "Can add/edit store products"},
    {"key": "view_reports", "label": "View Reports", "description": "Can access Reports page"},
    {"key": "manage_events", "label": "Manage Events", "description": "Can add/edit events"},
    {"key": "manage_system_users", "label": "Manage System Users", "description": "Can add/edit system user accounts"},
    {"key": "manage_dues_reminders", "label": "Manage Dues Reminders", "description": "Can view/edit dues reminder emails and run checks"},
]

# All manageable titles
MANAGEABLE_TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM", "(pm)", "Brother", "Honorary"]

def can_manage_permissions(user: dict) -> bool:
    """Check if user can manage role permissions - National Prez, VP, SEC, T only"""
    user_chapter = user.get("chapter", "")
    user_title = user.get("title", "")
    user_role = user.get("role", "")
    
    if user_chapter != "National":
        return False
    
    if user_role == "admin":
        return True
    
    return user_title in ["Prez", "VP", "SEC", "T"]


async def get_title_permissions(title: str, chapter: str = None) -> dict:
    """Get permissions for a specific title and chapter from database"""
    if chapter:
        record = await db.role_permissions.find_one({"title": title, "chapter": chapter}, {"_id": 0})
    else:
        # Fallback: try to find any matching title (for backwards compatibility)
        record = await db.role_permissions.find_one({"title": title}, {"_id": 0})
    
    if record:
        return record.get("permissions", {})
    return {}


async def check_permission(user: dict, permission_key: str) -> bool:
    """Check if user has a specific permission based on their title and chapter (no admin bypass)"""
    user_title = user.get("title", "")
    user_chapter = user.get("chapter", "")
    username = user.get("username", "")
    
    # Check if user/member is suspended for unpaid dues
    # First try to get the user's linked member_id
    user_record = await db.users.find_one({"username": username}, {"member_id": 1})
    if user_record and user_record.get("member_id"):
        member = await db.members.find_one({"id": user_record.get("member_id")}, {"dues_suspended": 1})
        if member and member.get("dues_suspended"):
            # User is suspended - deny all permissions except basic viewing
            if permission_key not in ["view_suggestions", "submit_suggestions"]:
                return False
    
    # Get permissions from database (chapter-specific)
    perms = await get_title_permissions(user_title, user_chapter)
    return perms.get(permission_key, False)


@api_router.get("/permissions/definitions")
async def get_permission_definitions(current_user: dict = Depends(verify_token)):
    """Get list of available permissions, titles, and chapters"""
    if not can_manage_permissions(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, SEC, and T can manage permissions")
    
    return {
        "permissions": AVAILABLE_PERMISSIONS,
        "titles": MANAGEABLE_TITLES,
        "chapters": CHAPTERS
    }


@api_router.get("/permissions/all")
async def get_all_permissions(current_user: dict = Depends(verify_token)):
    """Get all role permissions organized by chapter"""
    if not can_manage_permissions(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, SEC, and T can manage permissions")
    
    records = await db.role_permissions.find({}, {"_id": 0}).to_list(500)
    
    # Organize by chapter -> title -> permissions
    result = {}
    for chapter in CHAPTERS:
        result[chapter] = {}
        for record in records:
            if record.get("chapter") == chapter:
                result[chapter][record.get("title")] = record.get("permissions", {})
    
    return {
        "permissions_by_chapter": result,
        "available_permissions": AVAILABLE_PERMISSIONS,
        "titles": MANAGEABLE_TITLES,
        "chapters": CHAPTERS
    }


class PermissionUpdate(BaseModel):
    chapter: str
    title: str
    permission_key: str
    value: bool


@api_router.put("/permissions/update")
async def update_permission(update: PermissionUpdate, current_user: dict = Depends(verify_token)):
    """Update a single permission for a chapter + title"""
    if not can_manage_permissions(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, SEC, and T can manage permissions")
    
    if update.chapter not in CHAPTERS:
        raise HTTPException(status_code=400, detail=f"Invalid chapter: {update.chapter}")
    
    if update.title not in MANAGEABLE_TITLES:
        raise HTTPException(status_code=400, detail=f"Invalid title: {update.title}")
    
    valid_keys = [p["key"] for p in AVAILABLE_PERMISSIONS]
    if update.permission_key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Invalid permission key: {update.permission_key}")
    
    # Update the permission
    result = await db.role_permissions.update_one(
        {"chapter": update.chapter, "title": update.title},
        {
            "$set": {
                f"permissions.{update.permission_key}": update.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.get("username")
            }
        },
        upsert=True
    )
    
    logger.info(f"Permission updated: {update.chapter}/{update.title}.{update.permission_key} = {update.value} by {current_user.get('username')}")
    
    return {"success": True, "message": f"Updated {update.chapter}/{update.title}.{update.permission_key} to {update.value}"}


class BulkPermissionUpdate(BaseModel):
    chapter: str
    title: str
    permissions: dict


@api_router.put("/permissions/bulk-update")
async def bulk_update_permissions(update: BulkPermissionUpdate, current_user: dict = Depends(verify_token)):
    """Update all permissions for a chapter + title at once"""
    if not can_manage_permissions(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, SEC, and T can manage permissions")
    
    if update.chapter not in CHAPTERS:
        raise HTTPException(status_code=400, detail=f"Invalid chapter: {update.chapter}")
    
    if update.title not in MANAGEABLE_TITLES:
        raise HTTPException(status_code=400, detail=f"Invalid title: {update.title}")
    
    # Validate permission keys
    valid_keys = [p["key"] for p in AVAILABLE_PERMISSIONS]
    for key in update.permissions.keys():
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid permission key: {key}")
    
    # Update all permissions
    await db.role_permissions.update_one(
        {"chapter": update.chapter, "title": update.title},
        {
            "$set": {
                "permissions": update.permissions,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.get("username")
            }
        },
        upsert=True
    )
    
    logger.info(f"Bulk permissions updated for {update.chapter}/{update.title} by {current_user.get('username')}")
    
    return {"success": True, "message": f"Updated all permissions for {update.chapter}/{update.title}"}


# ==================== DUES REMINDER EMAIL ENDPOINTS ====================

class DuesEmailTemplateUpdate(BaseModel):
    subject: str
    body: str
    is_active: bool = True


@api_router.get("/dues-reminders/templates")
async def get_dues_email_templates(current_user: dict = Depends(verify_token)):
    """Get all dues reminder email templates"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to manage dues reminders")
    
    templates = await db.dues_email_templates.find({}, {"_id": 0}).sort("day_trigger", 1).to_list(10)
    return {"templates": templates}


@api_router.put("/dues-reminders/templates/{template_id}")
async def update_dues_email_template(
    template_id: str,
    update: DuesEmailTemplateUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update a dues reminder email template"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to manage dues reminders")
    
    result = await db.dues_email_templates.update_one(
        {"id": template_id},
        {
            "$set": {
                "subject": update.subject,
                "body": update.body,
                "is_active": update.is_active,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.get("username")
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"success": True, "message": "Template updated"}


@api_router.get("/dues-reminders/status")
async def get_dues_reminder_status(current_user: dict = Depends(verify_token)):
    """Get current dues reminder status - who has been sent what"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to view dues reminder status")
    
    from zoneinfo import ZoneInfo
    cst = ZoneInfo("America/Chicago")
    now = datetime.now(cst)
    month = now.month
    year = now.year
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Get all members
    members = await db.members.find({}, {"_id": 0, "id": 1, "handle": 1, "name": 1, "email": 1, "chapter": 1, "dues": 1, "non_dues_paying": 1}).to_list(1000)
    
    # Get sent reminders for this month
    sent_reminders = await db.dues_reminder_sent.find(
        {"month": month, "year": year},
        {"_id": 0}
    ).to_list(10000)
    
    sent_by_member = {}
    for sr in sent_reminders:
        mid = sr.get("member_id")
        if mid not in sent_by_member:
            sent_by_member[mid] = []
        sent_by_member[mid].append(sr)
    
    # Determine who hasn't paid
    unpaid_members = []
    for member in members:
        # Skip non-dues paying members (honorary, exempt, etc.)
        if member.get("non_dues_paying", False):
            continue
        
        dues = member.get("dues", {})
        year_str = str(year)
        month_idx = month - 1
        
        is_paid = False
        if year_str in dues:
            year_dues = dues[year_str]
            if isinstance(year_dues, list) and len(year_dues) > month_idx:
                month_data = year_dues[month_idx]
                if month_data is True or (isinstance(month_data, dict) and month_data.get("status") == "paid"):
                    is_paid = True
        
        if not is_paid:
            member_sent = sent_by_member.get(member.get("id"), [])
            # Decrypt email for display
            decrypted_email = decrypt_data(member.get("email", "")) if member.get("email") else "No email"
            
            # Check for active extension
            member_id = member.get("id")
            extension = await db.dues_extensions.find_one({"member_id": member_id})
            has_extension = False
            extension_until = None
            if extension:
                try:
                    ext_date = datetime.fromisoformat(extension.get("extension_until", "").replace("Z", "+00:00"))
                    if ext_date > now:
                        has_extension = True
                        extension_until = extension.get("extension_until")
                except:
                    pass
            
            unpaid_members.append({
                "id": member_id,
                "handle": member.get("handle"),
                "name": member.get("name"),
                "email": decrypted_email,
                "chapter": member.get("chapter"),
                "reminders_sent": [s.get("template_id") for s in member_sent],
                "last_reminder_date": max([s.get("sent_at") for s in member_sent]) if member_sent else None,
                "has_extension": has_extension,
                "extension_until": extension_until
            })
    
    # Get suspended members (those who received day 10 notice)
    suspended_members = [m for m in unpaid_members if "dues_reminder_day10" in m.get("reminders_sent", [])]
    
    return {
        "current_month": f"{month_names[month - 1]} {year}",
        "day_of_month": now.day,
        "unpaid_count": len(unpaid_members),
        "suspended_count": len(suspended_members),
        "unpaid_members": unpaid_members
    }


@api_router.get("/dues-reminders/settings")
async def get_dues_reminder_settings(current_user: dict = Depends(verify_token)):
    """Get dues reminder system settings"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to manage dues reminder settings")
    
    settings = await db.dues_reminder_settings.find_one({"id": "main"}, {"_id": 0})
    if not settings:
        # Return defaults
        settings = {
            "id": "main",
            "suspension_enabled": True,
            "discord_kick_enabled": True,
            "email_reminders_enabled": True
        }
    return settings


@api_router.put("/dues-reminders/settings")
async def update_dues_reminder_settings(
    settings: dict,
    current_user: dict = Depends(verify_token)
):
    """Update dues reminder system settings"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to manage dues reminder settings")
    
    # Only allow updating specific fields
    allowed_fields = ["suspension_enabled", "discord_kick_enabled", "email_reminders_enabled"]
    update_data = {k: v for k, v in settings.items() if k in allowed_fields}
    update_data["id"] = "main"
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("username")
    
    await db.dues_reminder_settings.update_one(
        {"id": "main"},
        {"$set": update_data},
        upsert=True
    )
    
    return {"success": True, "message": "Settings updated", "settings": update_data}


@api_router.post("/dues-reminders/send-test")
async def send_test_dues_reminder(
    template_id: str,
    email: str,
    current_user: dict = Depends(verify_token)
):
    """Send a test dues reminder email"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to send test emails")
    
    # Get template
    template = await db.dues_email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    now = datetime.now(timezone.utc)
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Replace placeholders
    subject = template.get("subject", "")
    body = template.get("body", "")
    body = body.replace("{{member_name}}", "Test Member")
    body = body.replace("{{month}}", month_names[now.month - 1])
    body = body.replace("{{year}}", str(now.year))
    
    # Convert plain text body to HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            {body.replace(chr(10), '<br>')}
        </div>
    </body>
    </html>
    """
    
    # Send actual test email if SendGrid is configured
    if smtp_configured:
        email_result = await send_email_smtp(email, subject, html_body, body)
        if email_result.get("success"):
            return {
                "success": True,
                "message": f"Test email sent to {email}",
                "preview": {
                    "to": email,
                    "subject": subject,
                    "body": body
                }
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send: {email_result.get('message')}",
                "preview": {
                    "to": email,
                    "subject": subject,
                    "body": body
                }
            }
    else:
        # Fallback to preview only if SendGrid not configured
        logger.info(f"TEST EMAIL preview for {email}:\nSubject: {subject}")
        return {
            "success": True,
            "message": "SendGrid not configured - showing preview only",
            "preview": {
                "to": email,
                "subject": subject,
                "body": body
            }
        }


@api_router.post("/dues-reminders/run-check")
async def run_dues_reminder_check(current_user: dict = Depends(verify_token)):
    """Manually trigger dues reminder check and send emails"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to run dues checks")
    
    result = await check_and_send_dues_reminders()
    return result


# ==================== DUES EXTENSION ENDPOINTS ====================

class DuesExtensionCreate(BaseModel):
    member_id: str
    extension_until: str  # ISO date string (YYYY-MM-DD)
    reason: str = ""

class DuesExtensionUpdate(BaseModel):
    extension_until: str
    reason: str = ""


@api_router.get("/dues-reminders/extensions")
async def get_dues_extensions(current_user: dict = Depends(verify_token)):
    """Get all active dues extensions"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to view dues extensions")
    
    now = datetime.now(timezone.utc)
    
    # Get all extensions (including expired for history)
    extensions = await db.dues_extensions.find({}, {"_id": 0}).sort("extension_until", -1).to_list(100)
    
    # Enrich with member info
    enriched = []
    for ext in extensions:
        member = await db.members.find_one({"id": ext.get("member_id")}, {"_id": 0, "handle": 1, "name": 1, "chapter": 1})
        if member:
            ext["member_handle"] = member.get("handle")
            ext["member_name"] = member.get("name")
            ext["member_chapter"] = member.get("chapter")
        
        # Check if still active
        try:
            ext_date = datetime.fromisoformat(ext.get("extension_until", "").replace("Z", "+00:00"))
            ext["is_active"] = ext_date > now
        except:
            ext["is_active"] = False
        
        enriched.append(ext)
    
    return {"extensions": enriched}


@api_router.post("/dues-reminders/extensions")
async def create_dues_extension(
    extension: DuesExtensionCreate,
    current_user: dict = Depends(verify_token)
):
    """Grant a dues payment extension to a member"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to grant extensions")
    
    # Verify member exists
    member = await db.members.find_one({"id": extension.member_id}, {"_id": 0, "handle": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Parse and validate the extension date
    try:
        ext_date = datetime.fromisoformat(extension.extension_until)
        if ext_date.tzinfo is None:
            ext_date = ext_date.replace(tzinfo=timezone.utc)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    now = datetime.now(timezone.utc)
    if ext_date <= now:
        raise HTTPException(status_code=400, detail="Extension date must be in the future")
    
    # Create or update the extension
    extension_data = {
        "member_id": extension.member_id,
        "extension_until": ext_date.isoformat(),
        "reason": extension.reason,
        "granted_by": current_user.get("username"),
        "granted_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.dues_extensions.update_one(
        {"member_id": extension.member_id},
        {"$set": extension_data},
        upsert=True
    )
    
    logger.info(f"Dues extension granted to {member.get('handle')} until {ext_date.date()} by {current_user.get('username')}")
    
    return {
        "success": True,
        "message": f"Extension granted to {member.get('handle')} until {ext_date.strftime('%B %d, %Y')}",
        "extension": extension_data
    }


@api_router.put("/dues-reminders/extensions/{member_id}")
async def update_dues_extension(
    member_id: str,
    update: DuesExtensionUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update an existing dues extension"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to update extensions")
    
    # Check if extension exists
    existing = await db.dues_extensions.find_one({"member_id": member_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    # Parse the new date
    try:
        ext_date = datetime.fromisoformat(update.extension_until)
        if ext_date.tzinfo is None:
            ext_date = ext_date.replace(tzinfo=timezone.utc)
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    await db.dues_extensions.update_one(
        {"member_id": member_id},
        {"$set": {
            "extension_until": ext_date.isoformat(),
            "reason": update.reason,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get("username")
        }}
    )
    
    return {"success": True, "message": "Extension updated"}


@api_router.delete("/dues-reminders/extensions/{member_id}")
async def revoke_dues_extension(
    member_id: str,
    current_user: dict = Depends(verify_token)
):
    """Revoke a dues extension"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to revoke extensions")
    
    result = await db.dues_extensions.delete_one({"member_id": member_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    logger.info(f"Dues extension revoked for member {member_id} by {current_user.get('username')}")
    
    return {"success": True, "message": "Extension revoked"}


class SuspendMemberRequest(BaseModel):
    reason: str = "Manual suspension"


@api_router.post("/members/{member_id}/suspend")
async def suspend_member(
    member_id: str,
    request: SuspendMemberRequest,
    current_user: dict = Depends(verify_token)
):
    """Manually suspend a member - remove Discord roles and mark as suspended"""
    has_access = await check_permission(current_user, "edit_dues")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to suspend members")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if already suspended
    if member.get("dues_suspended"):
        raise HTTPException(status_code=400, detail="Member is already suspended")
    
    # Suspend in Discord
    discord_result = await suspend_discord_member(
        member.get("handle"),
        member_id,
        request.reason
    )
    
    # Update member record
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "dues_suspended": True,
            "dues_suspended_at": datetime.now(timezone.utc).isoformat(),
            "suspended_by": current_user.get("username"),
            "suspension_reason": request.reason
        }}
    )
    
    logger.info(f"Member {member.get('handle')} suspended by {current_user.get('username')}: {request.reason}")
    
    return {
        "success": True,
        "message": f"Member {member.get('handle')} has been suspended",
        "discord_suspended": discord_result.get("success", False),
        "discord_message": discord_result.get("message", "")
    }


@api_router.post("/members/{member_id}/unsuspend")
async def unsuspend_member(
    member_id: str,
    current_user: dict = Depends(verify_token)
):
    """Manually unsuspend a member - restore Discord roles and clear suspension"""
    has_access = await check_permission(current_user, "edit_dues")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to unsuspend members")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if actually suspended
    if not member.get("dues_suspended"):
        raise HTTPException(status_code=400, detail="Member is not suspended")
    
    # Restore Discord roles
    discord_result = await restore_discord_member(member_id)
    
    # Clear suspension from member record
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "dues_suspended": False,
            "dues_suspended_at": None,
            "reinstated_by": current_user.get("username"),
            "reinstated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"Member {member.get('handle')} unsuspended by {current_user.get('username')}")
    
    return {
        "success": True,
        "message": f"Member {member.get('handle')} has been unsuspended",
        "discord_restored": discord_result.get("success", False),
        "discord_message": discord_result.get("message", "")
    }


@api_router.post("/dues-reminders/reinstate/{member_id}")
async def reinstate_member(
    member_id: str,
    current_user: dict = Depends(verify_token)
):
    """Manually reinstate a suspended member - restore Discord permissions and clear suspension"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to reinstate members")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0, "handle": 1, "dues_suspended": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Clear the dues_suspended flag
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "dues_suspended": False,
            "dues_suspended_at": None,
            "reinstated_by": current_user.get("username"),
            "reinstated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Restore Discord permissions
    discord_result = await restore_discord_member(member_id)
    
    logger.info(f"Member {member.get('handle')} reinstated by {current_user.get('username')}")
    
    return {
        "success": True,
        "message": f"Member {member.get('handle')} has been reinstated",
        "discord_restored": discord_result.get("success", False),
        "discord_message": discord_result.get("message", "")
    }


class ForgiveDuesRequest(BaseModel):
    member_id: str
    reason: str = ""


@api_router.post("/dues-reminders/forgive")
async def forgive_dues(
    request: ForgiveDuesRequest,
    current_user: dict = Depends(verify_token)
):
    """Forgive/waive dues for a member for the current month"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to forgive dues")
    
    # Get member info
    member = await db.members.find_one({"id": request.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    now = datetime.now(timezone.utc)
    year = now.year
    month = now.month
    year_str = str(year)
    month_idx = month - 1
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Get current dues structure
    dues = member.get("dues", {})
    
    # Initialize year if needed
    if year_str not in dues:
        dues[year_str] = [None] * 12
    
    # Ensure it's a list
    if not isinstance(dues[year_str], list):
        dues[year_str] = [None] * 12
    
    # Mark as forgiven with note
    dues[year_str][month_idx] = {
        "status": "paid",
        "note": f"Forgiven by {current_user.get('username')}" + (f": {request.reason}" if request.reason else ""),
        "forgiven": True,
        "forgiven_by": current_user.get("username"),
        "forgiven_at": now.isoformat()
    }
    
    # Update member record - also clear any suspension
    await db.members.update_one(
        {"id": request.member_id},
        {"$set": {
            "dues": dues,
            "dues_suspended": False,
            "dues_suspended_at": None,
            "updated_at": now.isoformat()
        }}
    )
    
    # Restore Discord permissions if they were suspended
    discord_result = await restore_discord_member(request.member_id)
    
    logger.info(f"Dues forgiven for {member.get('handle')} ({month_names[month_idx]} {year}) by {current_user.get('username')}")
    
    return {
        "success": True,
        "message": f"Dues forgiven for {member.get('handle')} for {month_names[month_idx]} {year}",
        "discord_restored": discord_result.get("success", False)
    }


async def has_active_extension(member_id: str) -> bool:
    """Check if a member has an active dues extension"""
    extension = await db.dues_extensions.find_one({"member_id": member_id})
    if not extension:
        return False
    
    try:
        ext_date = datetime.fromisoformat(extension.get("extension_until", "").replace("Z", "+00:00"))
        return ext_date > datetime.now(timezone.utc)
    except:
        return False


async def check_and_send_dues_reminders():
    """Check for unpaid dues and send appropriate reminder emails"""
    from zoneinfo import ZoneInfo
    
    # Use Central Standard Time for date calculations
    cst = ZoneInfo("America/Chicago")
    now = datetime.now(cst)
    day = now.day
    month = now.month
    year = now.year
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Get settings
    settings = await db.dues_reminder_settings.find_one({"id": "main"}, {"_id": 0})
    if not settings:
        settings = {"suspension_enabled": True, "discord_kick_enabled": True, "email_reminders_enabled": True}
    
    suspension_enabled = settings.get("suspension_enabled", True)
    discord_kick_enabled = settings.get("discord_kick_enabled", True)
    email_reminders_enabled = settings.get("email_reminders_enabled", True)
    
    # If email reminders are disabled, skip everything
    if not email_reminders_enabled:
        return {"message": "Email reminders are disabled", "emails_sent": 0}
    
    # Get active templates
    templates = await db.dues_email_templates.find({"is_active": True}, {"_id": 0}).to_list(10)
    
    # Determine which template to use based on day
    template_to_send = None
    for template in templates:
        if template.get("day_trigger") == day:
            template_to_send = template
            break
    
    # Also check if we're past certain days and haven't sent those notices
    if not template_to_send:
        if day >= 30:
            template_to_send = next((t for t in templates if t.get("day_trigger") == 30), None)
        elif day >= 10:
            template_to_send = next((t for t in templates if t.get("day_trigger") == 10), None)
    
    if not template_to_send:
        return {"message": f"No reminder scheduled for day {day}", "emails_sent": 0}
    
    # Get all members with email
    members = await db.members.find(
        {"email": {"$exists": True, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    emails_sent = 0
    errors = []
    
    for member in members:
        member_id = member.get("id")
        dues = member.get("dues", {})
        year_str = str(year)
        month_idx = month - 1
        
        # Skip non-dues paying members (honorary, exempt, etc.)
        if member.get("non_dues_paying", False):
            sys.stderr.write(f"⏭️ [DUES] Skipping {member.get('handle')} - non-dues paying member\n")
            sys.stderr.flush()
            continue
        
        # Check if member has an active extension
        if await has_active_extension(member_id):
            sys.stderr.write(f"⏭️ [DUES] Skipping {member.get('handle')} - has active extension\n")
            sys.stderr.flush()
            continue
        
        # Check if paid
        is_paid = False
        if year_str in dues:
            year_dues = dues[year_str]
            if isinstance(year_dues, list) and len(year_dues) > month_idx:
                month_data = year_dues[month_idx]
                if month_data is True or (isinstance(month_data, dict) and month_data.get("status") == "paid"):
                    is_paid = True
        
        if is_paid:
            continue
        
        # Check if we already sent this template to this member this month
        already_sent = await db.dues_reminder_sent.find_one({
            "member_id": member_id,
            "month": month,
            "year": year,
            "template_id": template_to_send.get("id")
        })
        
        if already_sent:
            continue
        
        # Prepare email content
        subject = template_to_send.get("subject", "")
        body = template_to_send.get("body", "")
        member_name = member.get("name") or member.get("handle", "Member")
        body = body.replace("{{member_name}}", member_name)
        body = body.replace("{{month}}", month_names[month - 1])
        body = body.replace("{{year}}", str(year))
        
        # Get decrypted email address
        encrypted_email = member.get("email")
        email_addr = decrypt_data(encrypted_email) if encrypted_email else None
        
        if not email_addr:
            logger.warning(f"No email address for member {member.get('handle')}")
            continue
        
        # Convert plain text body to HTML (preserve line breaks)
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {body.replace(chr(10), '<br>')}
            </div>
        </body>
        </html>
        """
        
        # Send email via SendGrid
        email_result = await send_email_smtp(email_addr, subject, html_body, body)
        
        if email_result.get("success"):
            logger.info(f"DUES REMINDER sent to {email_addr} ({member.get('handle')}): {subject}")
        else:
            logger.warning(f"DUES REMINDER failed for {email_addr}: {email_result.get('message')}")
        
        # Record that we sent this reminder (even if email failed, to avoid spam)
        try:
            await db.dues_reminder_sent.insert_one({
                "member_id": member_id,
                "member_handle": member.get("handle"),
                "email": encrypted_email,  # Store encrypted
                "month": month,
                "year": year,
                "template_id": template_to_send.get("id"),
                "sent_at": now.isoformat(),
                "subject": subject,
                "email_sent": email_result.get("success", False)
            })
            emails_sent += 1
            
            day_trigger = template_to_send.get("day_trigger")
            
            # If day 10 notice, mark member as suspended and suspend Discord permissions (if enabled)
            if day_trigger == 10 and suspension_enabled:
                await db.members.update_one(
                    {"id": member_id},
                    {"$set": {"dues_suspended": True, "dues_suspended_at": now.isoformat()}}
                )
                
                # Also suspend their Discord permissions
                discord_result = await suspend_discord_member(
                    member_handle=member.get("handle", "Unknown"),
                    member_id=member_id,
                    reason=f"Dues suspension - Day 10+ overdue for {current_month}"
                )
                if discord_result.get("success"):
                    sys.stderr.write(f"🚫 [DUES] Discord suspended for {member.get('handle')}\n")
                    sys.stderr.flush()
                else:
                    sys.stderr.write(f"⚠️ [DUES] Discord suspension failed for {member.get('handle')}: {discord_result.get('message')}\n")
                    sys.stderr.flush()
            elif day_trigger == 10 and not suspension_enabled:
                sys.stderr.write(f"⏭️ [DUES] Suspension disabled - skipping suspension for {member.get('handle')}\n")
                sys.stderr.flush()
            
            # If day 30 notice, kick member from Discord server (if enabled)
            elif day_trigger == 30 and discord_kick_enabled:
                # Kick from Discord
                discord_result = await kick_discord_member(
                    member_handle=member.get("handle", "Unknown"),
                    member_id=member_id,
                    reason=f"Dues removal - 30+ days overdue for {current_month}"
                )
                if discord_result.get("success"):
                    sys.stderr.write(f"🚫 [DUES] Discord REMOVED for {member.get('handle')}\n")
                    sys.stderr.flush()
                else:
                    sys.stderr.write(f"⚠️ [DUES] Discord removal failed for {member.get('handle')}: {discord_result.get('message')}\n")
                    sys.stderr.flush()
            elif day_trigger == 30 and not discord_kick_enabled:
                sys.stderr.write(f"⏭️ [DUES] Discord kick disabled - skipping removal for {member.get('handle')}\n")
                sys.stderr.flush()
                    
        except Exception as e:
            errors.append(f"Failed for {member.get('handle')}: {str(e)}")
    
    return {
        "message": f"Dues reminder check complete for day {day}",
        "template_used": template_to_send.get("name"),
        "emails_sent": emails_sent,
        "suspension_enabled": suspension_enabled,
        "discord_kick_enabled": discord_kick_enabled,
        "errors": errors if errors else None
    }


def run_dues_reminder_job():
    """Wrapper to run async dues reminder check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"💰 [SCHEDULER] Starting dues reminder check job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(check_and_send_dues_reminders())
            print(f"✅ [SCHEDULER] Dues reminder check completed: {result}", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running dues reminder check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


def run_square_sync_job():
    """Wrapper to run async Square dues sync in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"💳 [SCHEDULER] Starting Square dues sync job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(auto_sync_square_dues())
            print(f"✅ [SCHEDULER] Square dues sync completed: {result}", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running Square dues sync: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


async def auto_sync_square_dues():
    """Automated Square subscription sync - runs without user context"""
    import sys
    from motor.motor_asyncio import AsyncIOMotorClient
    
    if not square_client:
        return {"success": False, "message": "Square client not configured"}
    
    MONTHLY_DUES_AMOUNT = 30  # $30 per month
    
    try:
        # Create a new MongoDB connection for this thread
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        thread_db = client[db_name]
        
        sys.stderr.write("💳 [SQUARE SYNC] Starting auto-sync...\n")
        sys.stderr.flush()
        
        # Get active subscriptions
        subscriptions = []
        cursor = None
        
        while True:
            result = square_client.subscriptions.search(
                cursor=cursor,
                limit=100,
                query={
                    "filter": {
                        "location_ids": [SQUARE_LOCATION_ID]
                    }
                }
            )
            
            subs = result.subscriptions or []
            # Filter to ACTIVE subscriptions that are NOT scheduled for cancellation
            active_subs = [s for s in subs if s.status == "ACTIVE" and not s.canceled_date]
            subscriptions.extend(active_subs)
            
            cursor = result.cursor
            if not cursor:
                break
        
        sys.stderr.write(f"💳 [SQUARE SYNC] Found {len(subscriptions)} active subscriptions\n")
        sys.stderr.flush()
        
        # Batch retrieve customers for subscriptions
        customer_ids = list(set(sub.customer_id for sub in subscriptions if sub.customer_id))
        customer_map = {}
        
        for i in range(0, len(customer_ids), 100):
            batch_ids = customer_ids[i:i+100]
            try:
                batch_result = square_client.customers.bulk_retrieve_customers(
                    customer_ids=batch_ids
                )
                if batch_result.responses:
                    for cust_id, response in batch_result.responses.items():
                        if response.customer:
                            cust = response.customer
                            given_name = cust.given_name or ''
                            family_name = cust.family_name or ''
                            customer_map[cust_id] = f"{given_name} {family_name}".strip()
            except Exception as e:
                logger.warning(f"Batch customer fetch failed: {e}")
        
        # Get all members and manual links using thread-local db
        members = await thread_db.members.find({}, {"_id": 0}).to_list(1000)
        manual_links = await thread_db.member_subscriptions.find({}, {"_id": 0}).to_list(1000)
        manual_link_map = {link.get("square_customer_id"): link.get("member_id") for link in manual_links if link.get("square_customer_id")}
        
        # Create name-to-member map for fuzzy matching
        name_to_member = {}
        for member in members:
            name = member.get("name", "").lower().strip()
            if name:
                name_to_member[name] = member
            handle = member.get("handle", "").lower().strip()
            if handle:
                name_to_member[handle] = member
        
        synced_count = 0
        payment_months_updated = 0
        
        for sub in subscriptions:
            customer_id = sub.customer_id
            customer_name = customer_map.get(customer_id, "Unknown")
            
            # Try to find matching member
            member = None
            
            # Check manual link first
            if customer_id in manual_link_map:
                member_id = manual_link_map[customer_id]
                member = next((m for m in members if m.get("id") == member_id), None)
            
            # Try fuzzy match by name
            if not member:
                customer_name_lower = customer_name.lower().strip()
                if customer_name_lower in name_to_member:
                    member = name_to_member[customer_name_lower]
                else:
                    for name_key, m in name_to_member.items():
                        if customer_name_lower in name_key or name_key in customer_name_lower:
                            member = m
                            break
            
            if not member:
                continue
            
            member_id = member.get("id")
            
            # Get payments for this subscription
            try:
                payments_result = square_client.payments.list(
                    location_id=SQUARE_LOCATION_ID,
                    limit=100
                )
                
                # Handle both pager and direct response
                all_payments = []
                if hasattr(payments_result, 'payments') and payments_result.payments:
                    all_payments = payments_result.payments
                elif hasattr(payments_result, '__iter__'):
                    all_payments = list(payments_result)
                
                # Filter payments for this customer
                customer_payments = [p for p in all_payments 
                                   if hasattr(p, 'customer_id') and p.customer_id == customer_id 
                                   and hasattr(p, 'status') and p.status == "COMPLETED"
                                   and hasattr(p, 'source_type') and p.source_type == "CARD"]
                
                for payment in customer_payments:
                    amount_cents = payment.amount_money.amount if payment.amount_money else 0
                    amount_dollars = amount_cents / 100
                    
                    # Parse payment date
                    payment_date_str = payment.created_at
                    try:
                        payment_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
                    except:
                        continue
                    
                    payment_year = payment_date.year
                    payment_month = payment_date.month - 1  # 0-indexed
                    
                    # Determine months covered
                    if amount_dollars >= 300:
                        months_to_cover = 12
                    else:
                        months_to_cover = max(1, int(amount_dollars / MONTHLY_DUES_AMOUNT))
                    
                    # Update member dues for covered months
                    for i in range(months_to_cover):
                        target_month = (payment_month + i) % 12
                        target_year = payment_year + ((payment_month + i) // 12)
                        
                        # Check if this payment was already synced
                        existing_sync = await thread_db.synced_payments.find_one({
                            "payment_id": payment.id,
                            "member_id": member_id,
                            "year": target_year,
                            "month": target_month
                        })
                        
                        if existing_sync:
                            continue  # Already synced this payment
                        
                        # Update dues record
                        dues_record = await thread_db.member_dues.find_one({
                            "member_id": member_id,
                            "year": target_year
                        })
                        
                        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_key = month_names[target_month]
                        
                        if dues_record:
                            update_data = {
                                f"months.{month_key}": "paid",
                                f"payment_info.{month_key}": f"Square payment ${amount_dollars:.2f} on {payment_date.strftime('%m/%d/%Y')}",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                            await thread_db.member_dues.update_one(
                                {"member_id": member_id, "year": target_year},
                                {"$set": update_data}
                            )
                        else:
                            # Create new dues record
                            new_record = {
                                "member_id": member_id,
                                "year": target_year,
                                "months": {m: "unpaid" for m in month_names},
                                "payment_info": {},
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "created_by": "square_sync"
                            }
                            new_record["months"][month_key] = "paid"
                            new_record["payment_info"][month_key] = f"Square payment ${amount_dollars:.2f} on {payment_date.strftime('%m/%d/%Y')}"
                            await thread_db.member_dues.insert_one(new_record)
                        
                        # Record this payment as synced
                        await thread_db.synced_payments.insert_one({
                            "payment_id": payment.id,
                            "member_id": member_id,
                            "year": target_year,
                            "month": target_month,
                            "amount": amount_dollars,
                            "synced_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        payment_months_updated += 1
                        sys.stderr.write(f"   ✅ Updated {member.get('handle', 'Unknown')}: {month_key} {target_year} = paid\n")
                        sys.stderr.flush()
                    
                    # Check if this member was suspended and should be restored
                    member_data = await thread_db.members.find_one({"id": member_id})
                    if member_data and member_data.get("dues_suspended"):
                        # Check if current month is now paid
                        now = datetime.now(timezone.utc)
                        current_year = now.year
                        current_month_idx = now.month - 1
                        current_month_name = month_names[current_month_idx]
                        
                        current_dues = await thread_db.member_dues.find_one({
                            "member_id": member_id,
                            "year": current_year
                        })
                        
                        if current_dues and current_dues.get("months", {}).get(current_month_name) == "paid":
                            # Clear suspension
                            await thread_db.members.update_one(
                                {"id": member_id},
                                {"$set": {"dues_suspended": False, "dues_suspended_at": None}}
                            )
                            sys.stderr.write(f"   🔓 Cleared suspension for {member.get('handle', 'Unknown')} - dues paid\n")
                            sys.stderr.flush()
                            
                            # Try to restore Discord permissions
                            try:
                                discord_result = await restore_discord_member(member_id)
                                if discord_result.get("success"):
                                    sys.stderr.write(f"   ✅ Discord permissions restored for {member.get('handle', 'Unknown')}\n")
                                    sys.stderr.flush()
                            except Exception as discord_err:
                                sys.stderr.write(f"   ⚠️ Could not restore Discord: {discord_err}\n")
                                sys.stderr.flush()
                
                synced_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to get payments for subscription {sub.id}: {e}")
                continue
        
        # Close the thread-local connection
        client.close()
        
        sys.stderr.write(f"💳 [SQUARE SYNC] Synced {synced_count} subscriptions, updated {payment_months_updated} month records\n")
        sys.stderr.flush()
        
        return {
            "success": True,
            "subscriptions_synced": synced_count,
            "payment_months_updated": payment_months_updated
        }
        
    except Exception as e:
        logger.error(f"Square auto-sync failed: {str(e)}")
        return {"success": False, "message": str(e)}


@api_router.post("/dues/trigger-auto-sync")
async def trigger_auto_sync(current_user: dict = Depends(verify_token)):
    """Manually trigger the automatic Square dues sync (admin/secretary only)"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can trigger sync")
    
    result = await auto_sync_square_dues()
    return result


@api_router.post("/dues-reminders/test-discord-suspension")
async def test_discord_suspension(
    member_id: str,
    action: str = "suspend",  # "suspend" or "restore"
    current_user: dict = Depends(verify_token)
):
    """Test Discord suspension/restoration for a member (admin only)"""
    has_access = await check_permission(current_user, "manage_dues_reminders")
    if not has_access:
        raise HTTPException(status_code=403, detail="You don't have permission to manage dues reminders")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0, "handle": 1, "id": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if action == "suspend":
        result = await suspend_discord_member(
            member_handle=member.get("handle", "Unknown"),
            member_id=member_id,
            reason="Manual test suspension"
        )
    elif action == "restore":
        result = await restore_discord_member(member_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'suspend' or 'restore'")
    
    return result


# ==================== SUGGESTION BOX ENDPOINTS ====================

class SuggestionCreate(BaseModel):
    title: str
    description: str
    is_anonymous: bool = False

class SuggestionStatusUpdate(BaseModel):
    status: str  # "new", "reviewed", "in_progress", "implemented", "declined"

class SuggestionVote(BaseModel):
    vote_type: str  # "upvote" or "downvote"

def can_manage_suggestions(user: dict) -> bool:
    """Check if user is a National Officer (except Honorary) who can manage suggestion statuses"""
    NATIONAL_OFFICER_TITLES = ['Prez', 'VP', 'S@A', 'ENF', 'CD', 'T', 'SEC', 'NPrez', 'NVP']
    user_chapter = user.get('chapter', '')
    user_title = user.get('title', '')
    return user_chapter == "National" and user_title in NATIONAL_OFFICER_TITLES

@api_router.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(verify_token)):
    """Get all suggestions - all logged-in members can view"""
    suggestions = await db.suggestions.find({}, {"_id": 0}).to_list(1000)
    
    # Sort by created_at descending (newest first)
    suggestions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Calculate net votes for each suggestion
    for s in suggestions:
        upvotes = len(s.get("upvotes", []))
        downvotes = len(s.get("downvotes", []))
        s["vote_count"] = upvotes - downvotes
        s["upvote_count"] = upvotes
        s["downvote_count"] = downvotes
        # Check if current user has voted
        user_id = current_user.get("member_id") or current_user.get("id")
        s["user_vote"] = None
        if user_id in s.get("upvotes", []):
            s["user_vote"] = "upvote"
        elif user_id in s.get("downvotes", []):
            s["user_vote"] = "downvote"
        # Remove vote arrays from response (privacy)
        s.pop("upvotes", None)
        s.pop("downvotes", None)
    
    return suggestions

@api_router.post("/suggestions")
async def create_suggestion(
    suggestion: SuggestionCreate,
    current_user: dict = Depends(verify_token)
):
    """Create a new suggestion - all logged-in members can submit"""
    user_handle = current_user.get("handle") or current_user.get("username")
    user_id = current_user.get("member_id") or current_user.get("id")
    
    new_suggestion = {
        "id": str(uuid.uuid4()),
        "title": suggestion.title,
        "description": suggestion.description,
        "submitted_by": "Anonymous" if suggestion.is_anonymous else user_handle,
        "submitter_id": user_id,  # Track even if anonymous (for voting)
        "is_anonymous": suggestion.is_anonymous,
        "status": "new",
        "upvotes": [],
        "downvotes": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.suggestions.insert_one(new_suggestion)
    
    # Return without internal fields
    response = {k: v for k, v in new_suggestion.items() if k not in ["_id", "upvotes", "downvotes", "submitter_id"]}
    response["vote_count"] = 0
    response["upvote_count"] = 0
    response["downvote_count"] = 0
    response["user_vote"] = None
    
    return response

@api_router.post("/suggestions/{suggestion_id}/vote")
async def vote_suggestion(
    suggestion_id: str,
    vote: SuggestionVote,
    current_user: dict = Depends(verify_token)
):
    """Vote on a suggestion - upvote or downvote"""
    user_id = current_user.get("member_id") or current_user.get("id")
    
    suggestion = await db.suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    upvotes = suggestion.get("upvotes", [])
    downvotes = suggestion.get("downvotes", [])
    
    if vote.vote_type == "upvote":
        # Remove from downvotes if present
        if user_id in downvotes:
            downvotes.remove(user_id)
        # Toggle upvote
        if user_id in upvotes:
            upvotes.remove(user_id)
            new_vote = None
        else:
            upvotes.append(user_id)
            new_vote = "upvote"
    elif vote.vote_type == "downvote":
        # Remove from upvotes if present
        if user_id in upvotes:
            upvotes.remove(user_id)
        # Toggle downvote
        if user_id in downvotes:
            downvotes.remove(user_id)
            new_vote = None
        else:
            downvotes.append(user_id)
            new_vote = "downvote"
    else:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    
    await db.suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "vote_count": len(upvotes) - len(downvotes),
        "upvote_count": len(upvotes),
        "downvote_count": len(downvotes),
        "user_vote": new_vote
    }

@api_router.patch("/suggestions/{suggestion_id}/status")
async def update_suggestion_status(
    suggestion_id: str,
    status_update: SuggestionStatusUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update suggestion status - National Officers only (except Honorary)"""
    if not can_manage_suggestions(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only National Officers can update suggestion status")
    
    valid_statuses = ["new", "reviewed", "in_progress", "implemented", "declined"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    suggestion = await db.suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    user_handle = current_user.get("handle") or current_user.get("username")
    
    await db.suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {
            "status": status_update.status,
            "status_updated_by": user_handle,
            "status_updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"Status updated to {status_update.status}", "status": status_update.status}

@api_router.delete("/suggestions/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: str,
    current_user: dict = Depends(verify_token)
):
    """Delete a suggestion - National Officers or the original submitter can delete"""
    suggestion = await db.suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    user_id = current_user.get("member_id") or current_user.get("id")
    is_submitter = suggestion.get("submitter_id") == user_id
    is_officer = can_manage_suggestions(current_user) or current_user.get('role') == 'admin'
    
    if not is_submitter and not is_officer:
        raise HTTPException(status_code=403, detail="You can only delete your own suggestions")
    
    await db.suggestions.delete_one({"id": suggestion_id})
    
    return {"message": "Suggestion deleted"}


# ==================== EVENT ENDPOINTS ====================

@api_router.get("/events")
async def get_events(
    chapter: Optional[str] = None,
    title_filter: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Get all events, optionally filtered by chapter and title"""
    query = {}
    
    # Filter by chapter if specified
    if chapter:
        query["$or"] = [{"chapter": chapter}, {"chapter": None}]
    
    # Filter by title if specified
    if title_filter:
        if "$or" not in query:
            query["$or"] = []
        query["$or"].append({"title_filter": title_filter})
        query["$or"].append({"title_filter": None})
    
    events = await db.events.find(query, {"_id": 0}).to_list(length=None)
    
    # Convert datetime objects to ISO strings
    for event in events:
        if isinstance(event.get('created_at'), datetime):
            event['created_at'] = event['created_at'].isoformat()
    
    # Sort by date (newest first)
    events.sort(key=lambda x: x.get('date', ''), reverse=False)
    
    return events

@api_router.get("/events/upcoming-count")
async def get_upcoming_events_count(current_user: dict = Depends(verify_token)):
    """Get count of upcoming events for badge"""
    from datetime import date
    today = date.today().isoformat()
    
    # Build query based on user's chapter and title
    query = {"date": {"$gte": today}}
    
    # If user has a chapter, show events for their chapter or all chapters
    user_chapter = current_user.get("chapter")
    if user_chapter:
        query["$or"] = [{"chapter": user_chapter}, {"chapter": None}]
    
    count = await db.events.count_documents(query)
    return {"count": count}

@api_router.post("/events")
async def create_event(event_data: EventCreate, current_user: dict = Depends(verify_token)):
    """Create a new event - permission based"""
    # Check permission
    if not await can_manage_events_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to manage events")
    
    from dateutil.relativedelta import relativedelta
    
    # Get creator's chapter and title from current_user
    creator_chapter = current_user.get("chapter")
    creator_title = current_user.get("title")
    
    # Find creator's handle from members collection
    creator_handle = None
    member = await db.members.find_one({"email": current_user.get("email")}, {"_id": 0, "handle": 1})
    if member:
        creator_handle = member.get("handle")
    
    # Helper function to create a single event
    def create_single_event(event_date: str, parent_id: str = None, is_instance: bool = False) -> dict:
        event = Event(
            title=event_data.title,
            description=event_data.description,
            date=event_date,
            time=event_data.time,
            location=event_data.location,
            chapter=event_data.chapter,
            title_filter=event_data.title_filter,
            discord_notifications_enabled=event_data.discord_notifications_enabled,
            discord_channel=event_data.discord_channel,
            created_by=current_user["username"],
            creator_chapter=creator_chapter,
            creator_title=creator_title,
            creator_handle=creator_handle,
            repeat_type=event_data.repeat_type if not is_instance else None,
            repeat_interval=event_data.repeat_interval if not is_instance else None,
            repeat_end_date=event_data.repeat_end_date if not is_instance else None,
            repeat_count=event_data.repeat_count if not is_instance else None,
            repeat_days=event_data.repeat_days if not is_instance else None,
            parent_event_id=parent_id,
            is_recurring_instance=is_instance
        )
        doc = event.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        return doc
    
    created_events = []
    
    # Check if this is a recurring event
    if event_data.repeat_type and event_data.repeat_type != "none":
        start_date = datetime.strptime(event_data.date, "%Y-%m-%d")
        
        # Determine end condition
        max_occurrences = event_data.repeat_count or 52  # Default max 52 occurrences (1 year of weekly)
        end_date = None
        if event_data.repeat_end_date:
            end_date = datetime.strptime(event_data.repeat_end_date, "%Y-%m-%d")
        
        # Create the parent event first
        parent_doc = create_single_event(event_data.date, None, False)
        parent_id = parent_doc['id']
        await db.events.insert_one(parent_doc)
        created_events.append(parent_doc)
        
        # Generate recurring instances
        current_date = start_date
        occurrences = 1
        interval = event_data.repeat_interval or 1
        
        while occurrences < max_occurrences:
            # Calculate next date based on repeat type
            if event_data.repeat_type == "daily":
                current_date = current_date + timedelta(days=interval)
            elif event_data.repeat_type == "weekly":
                if event_data.repeat_days and len(event_data.repeat_days) > 0:
                    # Custom weekly - specific days of week
                    found_next = False
                    check_date = current_date + timedelta(days=1)
                    days_checked = 0
                    while not found_next and days_checked < 14:  # Check up to 2 weeks
                        if check_date.weekday() in event_data.repeat_days:
                            current_date = check_date
                            found_next = True
                        else:
                            check_date = check_date + timedelta(days=1)
                        days_checked += 1
                    if not found_next:
                        break
                else:
                    # Standard weekly - same day each week
                    current_date = current_date + timedelta(weeks=interval)
            elif event_data.repeat_type == "monthly":
                current_date = current_date + relativedelta(months=interval)
            elif event_data.repeat_type == "custom":
                # Custom interval in days
                current_date = current_date + timedelta(days=interval)
            else:
                break
            
            # Check end conditions
            if end_date and current_date > end_date:
                break
            
            # Create the recurring instance
            instance_date = current_date.strftime("%Y-%m-%d")
            instance_doc = create_single_event(instance_date, parent_id, True)
            await db.events.insert_one(instance_doc)
            created_events.append(instance_doc)
            occurrences += 1
        
        # Log activity
        await log_activity(
            username=current_user["username"],
            action="event_create",
            details=f"Created recurring event: {event_data.title} ({event_data.repeat_type}) - {len(created_events)} occurrences"
        )
        
        return {
            "message": f"Recurring event created successfully ({len(created_events)} occurrences)",
            "id": parent_id,
            "occurrences": len(created_events)
        }
    else:
        # Single event (non-recurring)
        doc = create_single_event(event_data.date, None, False)
        await db.events.insert_one(doc)
        
        # Log activity
        await log_activity(
            username=current_user["username"],
            action="event_create",
            details=f"Created event: {event_data.title} on {event_data.date}"
        )
        
        return {"message": "Event created successfully", "id": doc['id']}

@api_router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update an event - permission based"""
    # Check permission
    if not await can_manage_events_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to manage events")
    
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = {}
    if event_data.title:
        update_data['title'] = event_data.title
    if event_data.description is not None:
        update_data['description'] = event_data.description
    if event_data.date:
        update_data['date'] = event_data.date
    if event_data.time is not None:
        update_data['time'] = event_data.time
    if event_data.location is not None:
        update_data['location'] = event_data.location
    if event_data.chapter is not None:
        update_data['chapter'] = event_data.chapter
    if event_data.title_filter is not None:
        update_data['title_filter'] = event_data.title_filter
    if event_data.discord_notifications_enabled is not None:
        update_data['discord_notifications_enabled'] = event_data.discord_notifications_enabled
    if event_data.discord_channel is not None:
        update_data['discord_channel'] = event_data.discord_channel
    
    if update_data:
        await db.events.update_one({"id": event_id}, {"$set": update_data})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="event_update",
        details=f"Updated event: {event.get('title', event_id)}"
    )
    
    return {"message": "Event updated successfully"}

@api_router.get("/events/discord-channels")
async def get_discord_channels(current_user: dict = Depends(verify_admin)):
    """Get available Discord channels based on user's chapter and title"""
    chapter = current_user.get("chapter", "")
    title = current_user.get("title", "")
    
    # Check if user has a title that can schedule events
    if title not in EVENT_SCHEDULER_TITLES:
        return {"channels": [], "can_schedule": False, "message": "Your title does not have permission to schedule events"}
    
    # Get available channels for the user's chapter
    channels = get_available_discord_channels(chapter)
    
    # Format channel list with display names
    channel_list = []
    for ch in channels:
        display_name = ch.replace("-", " ").title()
        channel_list.append({
            "id": ch,
            "name": display_name,
            "available": DISCORD_CHANNEL_WEBHOOKS.get(ch) is not None
        })
    
    return {
        "channels": channel_list,
        "can_schedule": True,
        "chapter": chapter,
        "title": title
    }

@api_router.post("/events/{event_id}/send-discord-notification")
async def send_event_discord_notification_now(event_id: str, current_user: dict = Depends(verify_admin)):
    """Manually send Discord notification for an event immediately (admin only)"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if Discord notifications are enabled for this event
    if not event.get('discord_notifications_enabled', True):
        raise HTTPException(status_code=400, detail="Discord notifications are disabled for this event")
    
    # Send notification immediately (0 means "now")
    success = await send_discord_notification(event, 0)
    
    if success:
        # Log activity
        await log_activity(
            username=current_user["username"],
            action="event_discord_manual",
            details=f"Manually sent Discord notification for event: {event.get('title', event_id)}"
        )
        return {"message": "Discord notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Discord notification")

@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: dict = Depends(verify_token)):
    """Delete an event - permission based"""
    # Check permission
    if not await can_manage_events_async(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to manage events")
    
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await db.events.delete_one({"id": event_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="event_delete",
        details=f"Deleted event: {event.get('title', event_id)}"
    )
    
    return {"message": "Event deleted successfully"}


@api_router.post("/events/trigger-notification-check")
async def trigger_notification_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the scheduler's notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_notification_check)
    thread.start()
    
    return {"message": "Notification check triggered. Check backend logs for results."}


@api_router.post("/birthdays/trigger-check")
async def trigger_birthday_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the birthday notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_birthday_check)
    thread.start()
    
    return {"message": "Birthday check triggered. Check backend logs for results."}


@api_router.post("/anniversaries/trigger-check")
async def trigger_anniversary_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the anniversary notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_anniversary_check)
    thread.start()
    
    return {"message": "Anniversary check triggered. Check backend logs for results."}


@api_router.get("/anniversaries/this-month")
async def get_anniversaries_this_month(current_user: dict = Depends(verify_token)):
    """Get list of members with anniversaries this month"""
    from datetime import datetime
    
    today = datetime.now()
    current_month = today.strftime("%m")
    current_year = today.year
    
    # Fetch all members with join_date
    members = await db.members.find(
        {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    anniversary_members = []
    for member in members:
        join_date = member.get('join_date', '')
        if not join_date or '/' not in join_date:
            continue
        
        try:
            join_month = join_date.split('/')[0].zfill(2)
            join_year_str = join_date.split('/')[1]
            
            if join_month == current_month:
                try:
                    join_year = int(join_year_str)
                    years = current_year - join_year
                    
                    if years >= 1:
                        # Decrypt member data
                        decrypted = decrypt_member_sensitive_data(member.copy())
                        anniversary_members.append({
                            "id": member.get('id'),
                            "handle": decrypted.get('handle'),
                            "name": decrypted.get('name'),
                            "chapter": decrypted.get('chapter'),
                            "title": decrypted.get('title'),
                            "join_date": join_date,
                            "years": years
                        })
                except ValueError:
                    continue
        except Exception:
            continue
    
    # Sort by years (longest first)
    anniversary_members.sort(key=lambda x: x["years"], reverse=True)
    
    return {
        "month": today.strftime("%B %Y"),
        "count": len(anniversary_members),
        "members": anniversary_members
    }


@api_router.get("/anniversaries/upcoming")
async def get_upcoming_anniversaries(months: int = 3, current_user: dict = Depends(verify_token)):
    """Get list of members with anniversaries in the next N months"""
    from datetime import datetime
    
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Fetch all members with join_date
    members = await db.members.find(
        {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    upcoming_anniversaries = []
    for member in members:
        join_date = member.get('join_date', '')
        if not join_date or '/' not in join_date:
            continue
        
        try:
            join_month = int(join_date.split('/')[0])
            join_year_str = join_date.split('/')[1]
            join_year = int(join_year_str)
            
            # Calculate months until anniversary
            if join_month >= current_month:
                months_until = join_month - current_month
                anniversary_year = current_year
            else:
                months_until = (12 - current_month) + join_month
                anniversary_year = current_year + 1
            
            # Check if within range
            if months_until <= months:
                years = anniversary_year - join_year
                
                if years >= 1:
                    # Decrypt member data
                    decrypted = decrypt_member_sensitive_data(member.copy())
                    upcoming_anniversaries.append({
                        "id": member.get('id'),
                        "handle": decrypted.get('handle'),
                        "name": decrypted.get('name'),
                        "chapter": decrypted.get('chapter'),
                        "title": decrypted.get('title'),
                        "join_date": join_date,
                        "years": years,
                        "months_until": months_until
                    })
        except (ValueError, IndexError):
            continue
    
    # Sort by months_until (soonest first)
    upcoming_anniversaries.sort(key=lambda x: x["months_until"])
    
    return {
        "from_date": today.strftime("%Y-%m-%d"),
        "months_ahead": months,
        "count": len(upcoming_anniversaries),
        "members": upcoming_anniversaries
    }


@api_router.get("/birthdays/today")
async def get_todays_birthdays(current_user: dict = Depends(verify_token)):
    """Get list of members with birthdays today"""
    from datetime import datetime
    
    today = datetime.now()
    today_mm_dd = today.strftime("%m-%d")
    
    # Fetch all members with DOB set
    members = await db.members.find(
        {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    birthday_members = []
    for member in members:
        dob = member.get('dob', '')
        if not dob:
            continue
        try:
            dob_mm_dd = dob[5:10]  # Gets MM-DD portion
            if dob_mm_dd == today_mm_dd:
                birthday_members.append({
                    "id": member.get("id"),
                    "handle": member.get("handle"),
                    "name": member.get("name"),
                    "chapter": member.get("chapter"),
                    "title": member.get("title"),
                    "dob": dob
                })
        except:
            pass
    
    return {
        "date": today.strftime("%Y-%m-%d"),
        "count": len(birthday_members),
        "members": birthday_members
    }


@api_router.get("/birthdays/upcoming")
async def get_upcoming_birthdays(days: int = 30, current_user: dict = Depends(verify_token)):
    """Get list of members with birthdays in the next N days"""
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # Fetch all members with DOB set
    members = await db.members.find(
        {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    upcoming_birthdays = []
    for member in members:
        dob = member.get('dob', '')
        if not dob:
            continue
        try:
            # Parse DOB and calculate this year's birthday
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            this_year_birthday = dob_date.replace(year=today.year)
            
            # If birthday already passed this year, check next year
            if this_year_birthday.date() < today.date():
                this_year_birthday = dob_date.replace(year=today.year + 1)
            
            # Check if within the next N days
            days_until = (this_year_birthday.date() - today.date()).days
            
            if 0 <= days_until <= days:
                upcoming_birthdays.append({
                    "id": member.get("id"),
                    "handle": member.get("handle"),
                    "name": member.get("name"),
                    "chapter": member.get("chapter"),
                    "title": member.get("title"),
                    "dob": dob,
                    "birthday_date": this_year_birthday.strftime("%Y-%m-%d"),
                    "days_until": days_until
                })
        except:
            pass
    
    # Sort by days_until
    upcoming_birthdays.sort(key=lambda x: x["days_until"])
    
    return {
        "from_date": today.strftime("%Y-%m-%d"),
        "to_date": (today + timedelta(days=days)).strftime("%Y-%m-%d"),
        "count": len(upcoming_birthdays),
        "members": upcoming_birthdays
    }


@api_router.get("/birthdays/monthly")
async def get_monthly_birthdays(month: int, year: int, current_user: dict = Depends(verify_token)):
    """Get all members with birthdays in a specific month"""
    from datetime import datetime
    
    user_chapter = current_user.get('chapter')
    is_national_member = user_chapter == 'National'
    
    # Fetch all members with DOB set
    members = await db.members.find(
        {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    # Filter out National members for non-National users
    if not is_national_member:
        members = [m for m in members if m.get('chapter') != 'National']
    
    monthly_birthdays = []
    for member in members:
        dob = member.get('dob', '')
        if not dob:
            continue
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            # Check if birthday is in the requested month
            if dob_date.month == month:
                birthday_this_year = dob_date.replace(year=year)
                monthly_birthdays.append({
                    "id": member.get("id"),
                    "handle": member.get("handle"),
                    "name": member.get("name"),
                    "chapter": member.get("chapter"),
                    "title": member.get("title"),
                    "dob": dob,
                    "birthday_date": birthday_this_year.strftime("%Y-%m-%d"),
                    "day": dob_date.day
                })
        except:
            pass
    
    # Sort by day of month
    monthly_birthdays.sort(key=lambda x: x["day"])
    
    return {
        "month": month,
        "year": year,
        "count": len(monthly_birthdays),
        "members": monthly_birthdays
    }


@api_router.get("/anniversaries/monthly")
async def get_monthly_anniversaries(month: int, year: int, current_user: dict = Depends(verify_token)):
    """Get all members with anniversaries in a specific month"""
    from datetime import datetime
    
    user_chapter = current_user.get('chapter')
    is_national_member = user_chapter == 'National'
    
    # Fetch all members with join_date set
    members = await db.members.find(
        {"join_date": {"$exists": True, "$ne": None, "$ne": "", "$ne": "None"}},
        {"_id": 0}
    ).to_list(1000)
    
    # Filter out National members for non-National users
    if not is_national_member:
        members = [m for m in members if m.get('chapter') != 'National']
    
    monthly_anniversaries = []
    for member in members:
        join_date_str = member.get('join_date', '')
        if not join_date_str or join_date_str == 'None':
            continue
        try:
            # join_date can be stored as "MM/YYYY" or "MM/YY" format
            parts = join_date_str.split('/')
            if len(parts) == 2:
                join_month = int(parts[0])
                join_year_str = parts[1]
                
                # Handle both 2-digit and 4-digit years
                if len(join_year_str) == 4:
                    join_year = int(join_year_str)
                else:
                    join_year_short = int(join_year_str)
                    join_year = 2000 + join_year_short if join_year_short < 50 else 1900 + join_year_short
                
                if join_month == month:
                    years_member = year - join_year
                    if years_member > 0:  # Only show if at least 1 year
                        monthly_anniversaries.append({
                            "id": member.get("id"),
                            "handle": member.get("handle"),
                            "name": member.get("name"),
                            "chapter": member.get("chapter"),
                            "title": member.get("title"),
                            "join_date": join_date_str,
                            "years": years_member,
                            "anniversary_date": f"{year}-{str(month).zfill(2)}-01"
                        })
        except:
            pass
    
    # Sort by years (longest members first)
    monthly_anniversaries.sort(key=lambda x: x["years"], reverse=True)
    
    return {
        "month": month,
        "year": year,
        "count": len(monthly_anniversaries),
        "members": monthly_anniversaries
    }


# ==================== DISCORD NOTIFICATION SYSTEM ====================

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta

# Discord channel webhook configuration
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Discord channel webhooks mapping
DISCORD_CHANNEL_WEBHOOKS = {
    "member-chat": os.environ.get('DISCORD_WEBHOOK_MEMBER_CHAT'),
    "officers": os.environ.get('DISCORD_WEBHOOK_OFFICERS'),
    "hapm": os.environ.get('DISCORD_WEBHOOK_HAPM'),
    "ha-coc": os.environ.get('DISCORD_WEBHOOK_HA_COC'),
    "ad-coc": os.environ.get('DISCORD_WEBHOOK_AD_COC'),
    "hs-coc": os.environ.get('DISCORD_WEBHOOK_HS_COC'),
    "ncd-coc": os.environ.get('DISCORD_WEBHOOK_NCD_COC'),
    "national-board": os.environ.get('DISCORD_WEBHOOK_NATIONAL_BOARD'),
    "national-aoh-boh": os.environ.get('DISCORD_WEBHOOK_NATIONAL_AOH_BOH'),
    "national-budget-cmte": os.environ.get('DISCORD_WEBHOOK_NATIONAL_BUDGET'),
}

# Channels available per chapter
# Officers with titles: Prez, VP, S@A, ENF, SEC, T, CD can schedule events
DISCORD_CHANNELS_BY_CHAPTER = {
    "National": list(DISCORD_CHANNEL_WEBHOOKS.keys()),  # National can post anywhere
    "HA": ["member-chat", "hapm", "ha-coc", "officers"],
    "AD": ["member-chat", "ad-coc", "officers"],
    "HS": ["member-chat", "hs-coc", "officers"],
}

# Titles that can schedule events
EVENT_SCHEDULER_TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD"]

def get_available_discord_channels(chapter: str) -> list:
    """Get list of Discord channels available for a chapter"""
    return DISCORD_CHANNELS_BY_CHAPTER.get(chapter, ["member-chat"])

def get_discord_webhook_url(channel: str) -> str:
    """Get webhook URL for a specific channel"""
    return DISCORD_CHANNEL_WEBHOOKS.get(channel, DISCORD_WEBHOOK_URL)

async def send_discord_notification(event: dict, hours_before: int, channel: str = None):
    """Send Discord notification for an event
    
    Args:
        event: Event dictionary
        hours_before: 24, 3, or 0 (0 = send now/manual trigger)
        channel: Discord channel to send to (defaults to event's discord_channel or member-chat)
    """
    # Get the channel from event or parameter
    target_channel = channel or event.get('discord_channel', 'member-chat')
    webhook_url = get_discord_webhook_url(target_channel)
    
    if not webhook_url:
        print(f"⚠️  Discord webhook URL not configured for channel: {target_channel}")
        return False
    
    try:
        # Format the event time with Central Time indicator
        event_datetime_str = f"{event['date']}"
        if event.get('time'):
            event_datetime_str += f" at {event['time']} CST"
        else:
            event_datetime_str += " (Time TBD)"
        
        # Determine color and footer based on hours_before
        if hours_before == 0:
            color = 0x0099ff  # Blue for manual/immediate
            footer_text = "Manual notification"
            content = f"@everyone **Event Announcement!** 🚛"
        elif hours_before == 24:
            color = 0x00ff00  # Green for 24h
            footer_text = "Tomorrow!"
            content = f"@everyone **Reminder: Event tomorrow!** 🚛"
        else:  # 3 hours
            color = 0xff9900  # Orange for 3h
            footer_text = "Starting soon!"
            content = f"@everyone **Event starting in 3 hours!** ⏰"
        
        # Create embed for Discord
        embed = {
            "title": f"🚛 {event['title']}",
            "description": event.get('description', 'No description provided'),
            "color": color,
            "fields": [
                {
                    "name": "📅 Date & Time",
                    "value": event_datetime_str,
                    "inline": True
                }
            ],
            "footer": {
                "text": footer_text
            }
        }
        
        # Add location if available
        if event.get('location'):
            embed["fields"].append({
                "name": "📍 Location",
                "value": event['location'],
                "inline": True
            })
        
        # Add chapter filter if specified
        if event.get('chapter'):
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": event['chapter'],
                "inline": True
            })
        
        # Add title filter if specified
        if event.get('title_filter'):
            embed["fields"].append({
                "name": "👥 For",
                "value": event['title_filter'],
                "inline": True
            })
        
        # Add creator information
        creator_parts = []
        if event.get('creator_chapter'):
            creator_parts.append(event['creator_chapter'])
        if event.get('creator_title'):
            creator_parts.append(event['creator_title'])
        if event.get('creator_handle'):
            creator_parts.append(event['creator_handle'])
        
        if creator_parts:
            embed["fields"].append({
                "name": "📋 Created By",
                "value": " | ".join(creator_parts),
                "inline": False
            })
        
        # Add channel info to footer
        channel_display = target_channel.replace("-", " ").title()
        
        payload = {
            "content": content,
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            hours_text = "now" if hours_before == 0 else f"{hours_before}h before"
            print(f"✅ Discord notification sent to #{target_channel} for event: {event['title']} ({hours_text})")
            return True
        else:
            print(f"❌ Discord notification failed to #{target_channel}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Discord notification: {str(e)}")
        return False

async def check_and_send_event_notifications():
    """Check for upcoming events and send notifications"""
    import sys
    from motor.motor_asyncio import AsyncIOMotorClient
    
    try:
        # Create a fresh MongoDB client for this thread's event loop
        scheduler_client = AsyncIOMotorClient(mongo_url)
        scheduler_db = scheduler_client[os.environ['DB_NAME']]
        
        # Use Central Time for all event calculations
        import pytz
        central = pytz.timezone('America/Chicago')
        now = datetime.now(central)
        
        print(f"🔍 [SCHEDULER] Running notification check at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}", file=sys.stderr, flush=True)
        
        # Get all events
        events = await scheduler_db.events.find({}, {"_id": 0}).to_list(length=None)
        print(f"📋 [SCHEDULER] Found {len(events)} total events", file=sys.stderr, flush=True)
        
        for event in events:
            try:
                # Parse event date and time in Central Time
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                
                # If time is specified, add it
                if event.get('time'):
                    time_parts = event['time'].split(':')
                    event_date = event_date.replace(
                        hour=int(time_parts[0]),
                        minute=int(time_parts[1])
                    )
                else:
                    # Default to noon if no time specified
                    event_date = event_date.replace(hour=12, minute=0)
                
                # Make timezone aware as Central Time
                event_date = central.localize(event_date)
                
                # Calculate time until event
                time_until_event = event_date - now
                hours_until_event = time_until_event.total_seconds() / 3600
                
                print(f"  📅 Event '{event.get('title')}': {hours_until_event:.2f}h away (Discord enabled: {event.get('discord_notifications_enabled', True)})", file=sys.stderr, flush=True)
                
                # Skip if Discord notifications are disabled for this event
                if not event.get('discord_notifications_enabled', True):
                    print(f"  ⏭️  Skipping - Discord notifications disabled", file=sys.stderr, flush=True)
                    continue
                
                # Skip past events
                if hours_until_event < 0:
                    print(f"  ⏭️  Skipping - Event is in the past", file=sys.stderr, flush=True)
                    continue
                
                # Check for 24-hour notification (between 23.5 and 24.5 hours)
                if 23.5 <= hours_until_event <= 24.5 and not event.get('notification_24h_sent'):
                    print(f"📢 [SCHEDULER] Sending 24h notification for: {event['title']}", file=sys.stderr, flush=True)
                    success = await send_discord_notification(event, 24)
                    if success:
                        await scheduler_db.events.update_one(
                            {"id": event['id']},
                            {"$set": {"notification_24h_sent": True}}
                        )
                        print(f"✅ [SCHEDULER] 24h notification sent successfully", file=sys.stderr, flush=True)
                    else:
                        print(f"❌ [SCHEDULER] 24h notification failed", file=sys.stderr, flush=True)
                
                # Check for 3-hour notification (between 2.5 and 3.5 hours)
                elif 2.5 <= hours_until_event <= 3.5 and not event.get('notification_3h_sent'):
                    print(f"📢 [SCHEDULER] Sending 3h notification for: {event['title']}", file=sys.stderr, flush=True)
                    success = await send_discord_notification(event, 3)
                    if success:
                        await scheduler_db.events.update_one(
                            {"id": event['id']},
                            {"$set": {"notification_3h_sent": True}}
                        )
                        print(f"✅ [SCHEDULER] 3h notification sent successfully", file=sys.stderr, flush=True)
                    else:
                        print(f"❌ [SCHEDULER] 3h notification failed", file=sys.stderr, flush=True)
                        
            except Exception as e:
                print(f"❌ [SCHEDULER] Error processing event {event.get('id')}: {str(e)}", file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
                continue
        
        print(f"✅ [SCHEDULER] Notification check completed", file=sys.stderr, flush=True)
        
        # Close the scheduler-specific client
        scheduler_client.close()
                
    except Exception as e:
        print(f"❌ [SCHEDULER] Error in check_and_send_event_notifications: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Ensure client is closed even on error
        try:
            scheduler_client.close()
        except:
            pass

def run_notification_check():
    """Wrapper to run async notification check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🚀 [SCHEDULER] Starting notification check job...", file=sys.stderr, flush=True)
        
        # APScheduler runs this in a separate thread, so we need a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_event_notifications())
            print(f"✅ [SCHEDULER] Notification check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running notification check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


# ==================== BIRTHDAY NOTIFICATIONS ====================

async def send_birthday_notification(member: dict):
    """Send Discord notification for a member's birthday to member-chat channel"""
    # Always use member-chat webhook for birthday notifications
    webhook_url = get_discord_webhook_url("member-chat")
    if not webhook_url:
        print("⚠️  Discord webhook URL not configured for member-chat channel (birthday notification)")
        return False
    
    try:
        # Get member details
        member_name = member.get('name', member.get('handle', 'Brother'))
        member_handle = member.get('handle', '')
        member_chapter = member.get('chapter', '')
        member_title = member.get('title', '')
        
        # Create a festive birthday embed
        embed = {
            "title": "🎂 Happy Birthday! 🎉",
            "description": f"Today we celebrate **{member_name}**!\n\nWishing you a fantastic birthday filled with joy and many great drives ahead! 🚛",
            "color": 0xFFD700,  # Gold color for birthday
            "fields": [],
            "footer": {
                "text": "Brothers of the Highway | Birthday Wishes"
            }
        }
        
        # Add member info
        if member_handle:
            embed["fields"].append({
                "name": "🏷️ Handle",
                "value": member_handle,
                "inline": True
            })
        
        if member_chapter:
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": member_chapter,
                "inline": True
            })
        
        if member_title:
            embed["fields"].append({
                "name": "👤 Title",
                "value": member_title,
                "inline": True
            })
        
        # Add call to action
        embed["fields"].append({
            "name": "🎊 Join the Celebration!",
            "value": "All Brothers are invited to wish them a Happy Birthday!",
            "inline": False
        })
        
        payload = {
            "content": f"@everyone **🎂 Birthday Alert!** 🎂\n\nLet's all wish **{member_name}** a very Happy Birthday! 🎉",
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            print(f"✅ Birthday notification sent to #member-chat for: {member_name}")
            return True
        else:
            print(f"❌ Birthday notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending birthday notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def check_and_send_birthday_notifications():
    """Check for members with birthdays today and send Discord notifications"""
    import sys
    from datetime import datetime
    
    try:
        print(f"🎂 [BIRTHDAY] Checking for birthdays today...", file=sys.stderr, flush=True)
        
        # Get today's date in MM-DD format for comparison
        today = datetime.now()
        today_mm_dd = today.strftime("%m-%d")
        today_key = today.strftime("%Y-%m-%d")
        
        # Create a new MongoDB connection for this thread
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        thread_db = client[db_name]
        
        # Try to acquire a distributed lock for this job run
        # This prevents multiple instances from running the same job simultaneously
        import uuid
        lock_id = str(uuid.uuid4())
        lock_result = await thread_db.scheduler_locks.update_one(
            {
                "job_name": "birthday_check",
                "lock_date": today_key,
                "completed": False
            },
            {
                "$setOnInsert": {
                    "job_name": "birthday_check",
                    "lock_date": today_key,
                    "lock_id": lock_id,
                    "locked_at": datetime.now(),
                    "completed": False
                }
            },
            upsert=True
        )
        
        # If we didn't get the lock (another instance got it), exit early
        if not lock_result.upserted_id:
            # Check if already completed
            existing_lock = await thread_db.scheduler_locks.find_one({
                "job_name": "birthday_check",
                "lock_date": today_key
            })
            if existing_lock and existing_lock.get("completed"):
                print(f"🎂 [BIRTHDAY] Already completed by another instance today, skipping.", file=sys.stderr, flush=True)
            else:
                print(f"🎂 [BIRTHDAY] Another instance is running this job, skipping.", file=sys.stderr, flush=True)
            client.close()
            return
        
        print(f"🎂 [BIRTHDAY] Acquired job lock: {lock_id}", file=sys.stderr, flush=True)
        
        # Ensure unique index exists to prevent duplicates
        await thread_db.birthday_notifications.create_index(
            [("member_id", 1), ("notification_date", 1)],
            unique=True
        )
        
        # Fetch all members with DOB set
        members = await thread_db.members.find(
            {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0}
        ).to_list(1000)
        
        print(f"🎂 [BIRTHDAY] Found {len(members)} members with DOB records", file=sys.stderr, flush=True)
        
        # Check today's date key to avoid duplicate notifications
        today_key = today.strftime("%Y-%m-%d")
        
        birthday_count = 0
        for member in members:
            dob = member.get('dob', '')
            if not dob:
                continue
            
            try:
                # DOB format: YYYY-MM-DD, extract MM-DD
                dob_mm_dd = dob[5:10]  # Gets MM-DD portion
                
                if dob_mm_dd == today_mm_dd:
                    member_id = member.get('id', member.get('handle', ''))
                    
                    # First check if already notified (faster than upsert for most cases)
                    existing = await thread_db.birthday_notifications.find_one({
                        "member_id": member_id,
                        "notification_date": today_key
                    })
                    
                    if existing:
                        print(f"   ⏭️ Already notified for {member.get('name', member.get('handle'))}", file=sys.stderr, flush=True)
                        continue
                    
                    # Use upsert to atomically check and insert - prevents race condition
                    try:
                        result = await thread_db.birthday_notifications.update_one(
                            {
                                "member_id": member_id,
                                "notification_date": today_key
                            },
                            {
                                "$setOnInsert": {
                                    "member_id": member_id,
                                    "member_name": member.get('name', member.get('handle', '')),
                                    "notification_date": today_key,
                                    "sent_at": datetime.now()
                                }
                            },
                            upsert=True
                        )
                        
                        # Only send notification if this was a new insert (not already exists)
                        if result.upserted_id:
                            print(f"   🎉 Birthday found: {member.get('name', member.get('handle'))} - {dob}", file=sys.stderr, flush=True)
                            success = await send_birthday_notification(member)
                            
                            if not success:
                                # If notification failed, remove the record so it can retry
                                await thread_db.birthday_notifications.delete_one({
                                    "member_id": member_id,
                                    "notification_date": today_key
                                })
                            else:
                                birthday_count += 1
                        else:
                            print(f"   ⏭️ Already notified (race) for {member.get('name', member.get('handle'))}", file=sys.stderr, flush=True)
                    except Exception as dup_error:
                        # Duplicate key error means another instance already inserted
                        if "duplicate key" in str(dup_error).lower() or "E11000" in str(dup_error):
                            print(f"   ⏭️ Already notified (dup key) for {member.get('name', member.get('handle'))}", file=sys.stderr, flush=True)
                        else:
                            raise dup_error
                        
            except Exception as e:
                print(f"   ❌ Error processing DOB for {member.get('handle', 'unknown')}: {str(e)}", file=sys.stderr, flush=True)
        
        # Mark the job as completed
        await thread_db.scheduler_locks.update_one(
            {"job_name": "birthday_check", "lock_date": today_key},
            {"$set": {"completed": True, "completed_at": datetime.now(), "notifications_sent": birthday_count}}
        )
        
        print(f"🎂 [BIRTHDAY] Sent {birthday_count} birthday notification(s) today", file=sys.stderr, flush=True)
        client.close()
        
    except Exception as e:
        print(f"❌ [BIRTHDAY] Error checking birthdays: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


def run_birthday_check():
    """Wrapper to run async birthday check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🎂 [SCHEDULER] Starting birthday check job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_birthday_notifications())
            print(f"✅ [SCHEDULER] Birthday check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running birthday check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)

# ==================== ANNIVERSARY NOTIFICATIONS ====================

async def send_anniversary_notification(member: dict, years: int):
    """Send Discord notification for a member's anniversary to member-chat channel"""
    # Always use member-chat webhook for anniversary notifications
    webhook_url = get_discord_webhook_url("member-chat")
    if not webhook_url:
        print("⚠️  Discord webhook URL not configured for member-chat channel (anniversary notification)")
        return False
    
    try:
        # Get member details
        member_name = member.get('name', member.get('handle', 'Brother'))
        member_handle = member.get('handle', '')
        member_chapter = member.get('chapter', '')
        member_title = member.get('title', '')
        
        # Create trucker-themed anniversary message
        year_text = "year" if years == 1 else "years"
        
        # Milestone messages based on years
        if years >= 10:
            milestone_msg = "A true road warrior and pillar of the Brotherhood! 🏆"
        elif years >= 5:
            milestone_msg = "A seasoned veteran of the highway! Keep on truckin'! 🛣️"
        elif years >= 3:
            milestone_msg = "Rolling strong through the years! 💪"
        else:
            milestone_msg = "Keep those wheels turning, Brother! 🚛"
        
        # Create a festive anniversary embed
        embed = {
            "title": "🎉 Member Anniversary! 🎊",
            "description": f"**{member_name}** is celebrating **{years} {year_text}** as a Brother of the Highway!\n\n{milestone_msg}",
            "color": 0x4169E1,  # Royal blue for anniversary
            "fields": [],
            "footer": {
                "text": "Brothers of the Highway | Anniversary Celebration"
            }
        }
        
        # Add member info
        if member_handle:
            embed["fields"].append({
                "name": "🏷️ Handle",
                "value": member_handle,
                "inline": True
            })
        
        if member_chapter:
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": member_chapter,
                "inline": True
            })
        
        if member_title:
            embed["fields"].append({
                "name": "👤 Title",
                "value": member_title,
                "inline": True
            })
        
        # Add years milestone
        embed["fields"].append({
            "name": "📅 Years of Brotherhood",
            "value": f"**{years}** {year_text} on the road together!",
            "inline": False
        })
        
        # Add call to action
        embed["fields"].append({
            "name": "🎊 Congratulations!",
            "value": "All Brothers are invited to congratulate them on their anniversary!",
            "inline": False
        })
        
        payload = {
            "content": f"@everyone **🎉 Anniversary Alert!** 🎉\n\nLet's all congratulate **{member_name}** on **{years} {year_text}** with the Brotherhood! 🚛💨",
            "embeds": [embed]
        }
        
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            print(f"✅ Anniversary notification sent to #member-chat for: {member_name} ({years} years)")
            return True
        else:
            print(f"❌ Anniversary notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending anniversary notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def check_and_send_anniversary_notifications():
    """Check for members with anniversaries this month and send Discord notifications (runs on 1st of month)"""
    import sys
    from datetime import datetime
    
    try:
        print(f"🎉 [ANNIVERSARY] Checking for member anniversaries this month...", file=sys.stderr, flush=True)
        
        # Get current month and year
        today = datetime.now()
        current_month = today.strftime("%m")  # MM format
        current_year = today.year
        
        # Create a new MongoDB connection for this thread
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        thread_db = client[db_name]
        
        # Check today's date key to avoid duplicate notifications (use year-month)
        month_key = today.strftime("%Y-%m")
        
        # Try to acquire a distributed lock for this job run
        # This prevents multiple instances from running the same job simultaneously
        import uuid
        lock_id = str(uuid.uuid4())
        lock_result = await thread_db.scheduler_locks.update_one(
            {
                "job_name": "anniversary_check",
                "lock_date": month_key,
                "completed": False
            },
            {
                "$setOnInsert": {
                    "job_name": "anniversary_check",
                    "lock_date": month_key,
                    "lock_id": lock_id,
                    "locked_at": datetime.now(),
                    "completed": False
                }
            },
            upsert=True
        )
        
        # If we didn't get the lock (another instance got it), exit early
        if not lock_result.upserted_id:
            # Check if already completed
            existing_lock = await thread_db.scheduler_locks.find_one({
                "job_name": "anniversary_check",
                "lock_date": month_key
            })
            if existing_lock and existing_lock.get("completed"):
                print(f"🎉 [ANNIVERSARY] Already completed by another instance this month, skipping.", file=sys.stderr, flush=True)
            else:
                print(f"🎉 [ANNIVERSARY] Another instance is running this job, skipping.", file=sys.stderr, flush=True)
            client.close()
            return
        
        print(f"🎉 [ANNIVERSARY] Acquired job lock: {lock_id}", file=sys.stderr, flush=True)
        
        # Ensure unique index exists to prevent duplicate anniversary notifications
        await thread_db.anniversary_notifications.create_index(
            [("member_id", 1), ("notification_month", 1)],
            unique=True
        )
        
        # Fetch all members with join_date set
        members = await thread_db.members.find(
            {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0}
        ).to_list(1000)
        
        print(f"🎉 [ANNIVERSARY] Found {len(members)} members with join_date records", file=sys.stderr, flush=True)
        
        anniversary_count = 0
        for member in members:
            join_date = member.get('join_date', '')
            if not join_date:
                continue
            
            try:
                # join_date format: MM/YYYY, extract MM portion
                if '/' in join_date:
                    join_month = join_date.split('/')[0].zfill(2)  # Get MM, pad with 0 if needed
                    join_year_str = join_date.split('/')[1]
                    
                    # Check if this member's anniversary is this month
                    if join_month == current_month:
                        # Calculate years of membership
                        try:
                            join_year = int(join_year_str)
                            years = current_year - join_year
                            
                            # Skip if less than 1 year or join year is in the future
                            if years < 1:
                                continue
                                
                        except ValueError:
                            print(f"   ⚠️ Invalid year in join_date for {member.get('handle', 'unknown')}: {join_date}", file=sys.stderr, flush=True)
                            continue
                        
                        member_id = member.get('id', member.get('handle', ''))
                        
                        # Check if we already sent notification this month (with unique index backup)
                        existing = await thread_db.anniversary_notifications.find_one({
                            "member_id": member_id,
                            "notification_month": month_key
                        })
                        
                        if existing:
                            print(f"   ⏭️ Already notified for {member.get('name', member.get('handle'))} this month", file=sys.stderr, flush=True)
                            continue
                        
                        # Decrypt sensitive data for the notification
                        decrypted_member = decrypt_member_sensitive_data(member.copy())
                        
                        # Send anniversary notification
                        print(f"   🎉 Anniversary found: {decrypted_member.get('name', decrypted_member.get('handle'))} - {years} year(s) (joined {join_date})", file=sys.stderr, flush=True)
                        success = await send_anniversary_notification(decrypted_member, years)
                        
                        if success:
                            # Record that we sent the notification (use upsert for safety with unique index)
                            try:
                                await thread_db.anniversary_notifications.update_one(
                                    {
                                        "member_id": member_id,
                                        "notification_month": month_key
                                    },
                                    {
                                        "$setOnInsert": {
                                            "member_id": member_id,
                                            "member_name": decrypted_member.get('name', decrypted_member.get('handle', '')),
                                            "notification_month": month_key,
                                            "years": years,
                                            "sent_at": datetime.now()
                                        }
                                    },
                                    upsert=True
                                )
                                anniversary_count += 1
                            except Exception as dup_err:
                                # Duplicate key error means another instance already recorded it
                                print(f"   ⚠️ Duplicate notification prevented for {member.get('handle')}", file=sys.stderr, flush=True)
                            
            except Exception as e:
                print(f"   ❌ Error processing join_date for {member.get('handle', 'unknown')}: {str(e)}", file=sys.stderr, flush=True)
        
        # Mark job as completed
        await thread_db.scheduler_locks.update_one(
            {
                "job_name": "anniversary_check",
                "lock_date": month_key
            },
            {
                "$set": {
                    "completed": True,
                    "completed_at": datetime.now(),
                    "notifications_sent": anniversary_count
                }
            }
        )
        
        print(f"🎉 [ANNIVERSARY] Sent {anniversary_count} anniversary notification(s) this month", file=sys.stderr, flush=True)
        client.close()
        
    except Exception as e:
        print(f"❌ [ANNIVERSARY] Error checking anniversaries: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


def run_anniversary_check():
    """Wrapper to run async anniversary check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🎉 [SCHEDULER] Starting anniversary check job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_anniversary_notifications())
            print(f"✅ [SCHEDULER] Anniversary check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running anniversary check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


# Initialize scheduler variable (will be started in startup event)
import sys
scheduler = None


# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ==================== STORE API ENDPOINTS ====================

@api_router.get("/store/products")
async def get_store_products(category: Optional[str] = None, current_user: dict = Depends(verify_token)):
    """Get all active store products"""
    try:
        query = {"is_active": True}
        if category:
            query["category"] = category
        
        products = await db.store_products.find(query, {"_id": 0}).to_list(1000)
        
        # Check if user is a member for member pricing
        is_member = current_user.get("role") == "admin" or await db.members.find_one({"email": current_user.get("email")})
        
        # Check if user can manage store (async to check delegated admins)
        user_can_manage = await can_manage_store_async(current_user)
        
        for product in products:
            if isinstance(product.get('created_at'), str):
                product['created_at'] = datetime.fromisoformat(product['created_at'])
            if isinstance(product.get('updated_at'), str):
                product['updated_at'] = datetime.fromisoformat(product['updated_at'])
            # Apply member pricing if applicable
            if is_member and product.get('member_price'):
                product['display_price'] = product['member_price']
                product['is_member_price'] = True
            else:
                product['display_price'] = product['price']
                product['is_member_price'] = False
            # Add management permission flag
            product['can_manage'] = user_can_manage
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/store/public/products")
async def get_public_store_products():
    """Get supporter-available store products (no authentication required)"""
    try:
        # Get only merchandise products that are marked for supporter store
        query = {
            "is_active": True,
            "category": "merchandise",
            "show_in_supporter_store": True  # Only show products marked for supporter store
        }
        
        products = await db.store_products.find(query, {"_id": 0}).to_list(1000)
        
        for product in products:
            if isinstance(product.get('created_at'), str):
                product['created_at'] = datetime.fromisoformat(product['created_at'])
            if isinstance(product.get('updated_at'), str):
                product['updated_at'] = datetime.fromisoformat(product['updated_at'])
            # Public store always shows regular price
            product['display_price'] = product.get('price', 0)
            product['is_member_price'] = False
            product['can_manage'] = False
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/store/products/{product_id}")
async def get_store_product(product_id: str, current_user: dict = Depends(verify_token)):
    """Get a single store product"""
    product = await db.store_products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/store/products", response_model=StoreProduct)
async def create_store_product(product_data: StoreProductCreate, current_user: dict = Depends(verify_token)):
    """Create a new store product (Store admins only)"""
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can add store products")
    
    product = StoreProduct(**product_data.model_dump())
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.store_products.insert_one(doc)
    
    await log_activity(
        current_user["username"],
        "create_product",
        f"Created store product: {product.name}"
    )
    
    return product

@api_router.put("/store/products/{product_id}")
async def update_store_product(product_id: str, product_data: StoreProductUpdate, current_user: dict = Depends(verify_token)):
    """Update a store product (Store admins only)"""
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can edit store products")
    
    product = await db.store_products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.store_products.update_one({"id": product_id}, {"$set": update_data})
    
    updated_product = await db.store_products.find_one({"id": product_id}, {"_id": 0})
    return updated_product

@api_router.delete("/store/products/{product_id}")
async def delete_store_product(product_id: str, current_user: dict = Depends(verify_token)):
    """Delete a store product (Store admins only)"""
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can delete store products")
    
    result = await db.store_products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

# Shopping Cart Endpoints
@api_router.get("/store/cart")
async def get_cart(current_user: dict = Depends(verify_token)):
    """Get the current user's shopping cart"""
    cart = await db.store_carts.find_one({"user_id": current_user["username"]}, {"_id": 0})
    if not cart:
        return {"items": [], "total": 0, "item_count": 0}
    
    total = sum(item["price"] * item["quantity"] for item in cart.get("items", []))
    item_count = sum(item["quantity"] for item in cart.get("items", []))
    
    return {
        "items": cart.get("items", []),
        "total": round(total, 2),
        "item_count": item_count
    }

@api_router.post("/store/cart/add")
async def add_to_cart(
    product_id: str, 
    quantity: int = 1, 
    variation_id: Optional[str] = None,
    customization: Optional[str] = None,
    add_on_price: float = 0,
    current_user: dict = Depends(verify_token)
):
    """Add a product to the shopping cart with optional variation and customization"""
    product = await db.store_products.find_one({"id": product_id, "is_active": True}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get price and inventory based on variation if provided
    price = product['price']
    variation_name = None
    variation_inventory = product.get("inventory_count", 0)
    
    if product.get("has_variations") and product.get("variations"):
        if not variation_id:
            raise HTTPException(status_code=400, detail="Please select a size/option")
        
        # Find the selected variation
        selected_var = None
        for var in product["variations"]:
            if var["id"] == variation_id:
                selected_var = var
                break
        
        if not selected_var:
            raise HTTPException(status_code=400, detail="Invalid size/option selected")
        
        if selected_var.get("sold_out") or selected_var.get("inventory_count", 0) < quantity:
            raise HTTPException(status_code=400, detail=f"Size {selected_var['name']} is out of stock")
        
        price = selected_var["price"]
        variation_name = selected_var["name"]
        variation_inventory = selected_var.get("inventory_count", 0)
    else:
        # Check inventory for non-variation products
        if product.get("inventory_count", 0) < quantity and product.get("category") == "merchandise":
            raise HTTPException(status_code=400, detail="Insufficient inventory")
    
    # Check if user is a member for pricing
    is_member = current_user.get("role") == "admin" or await db.members.find_one({"email": current_user.get("email")})
    if is_member and product.get('member_price'):
        price = product['member_price']
    
    # Add customization add-on price
    price += add_on_price
    
    # Build cart item name with variation and customization
    item_name = product["name"]
    if variation_name:
        item_name += f" ({variation_name})"
    if customization:
        item_name += f" - {customization}"
    
    cart_item = {
        "product_id": product_id,
        "name": item_name,
        "price": price,
        "quantity": quantity,
        "image_url": product.get("image_url"),
        "variation_id": variation_id,
        "variation_name": variation_name,
        "customization": customization
    }
    
    # Check if item already in cart (same product, variation, and customization)
    existing_cart = await db.store_carts.find_one({"user_id": current_user["username"]})
    
    if existing_cart:
        items = existing_cart.get("items", [])
        found = False
        for item in items:
            # Match on product_id, variation_id, AND customization
            if (item["product_id"] == product_id and 
                item.get("variation_id") == variation_id and 
                item.get("customization") == customization):
                item["quantity"] += quantity
                found = True
                break
        
        if not found:
            items.append(cart_item)
        
        await db.store_carts.update_one(
            {"user_id": current_user["username"]},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        cart = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["username"],
            "items": [cart_item],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.store_carts.insert_one(cart)
    
    return {"message": "Item added to cart", "item": cart_item}

@api_router.put("/store/cart/update")
async def update_cart_item(product_id: str, quantity: int, variation_id: Optional[str] = None, customization: Optional[str] = None, current_user: dict = Depends(verify_token)):
    """Update quantity of an item in cart"""
    cart = await db.store_carts.find_one({"user_id": current_user["username"]})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = cart.get("items", [])
    found = False
    
    if quantity <= 0:
        # Remove item matching product_id, variation_id, and customization
        items = [item for item in items if not (
            item["product_id"] == product_id and 
            item.get("variation_id") == variation_id and
            item.get("customization") == customization
        )]
        found = True
    else:
        for item in items:
            # Match on product_id, variation_id, and customization
            if (item["product_id"] == product_id and 
                item.get("variation_id") == variation_id and
                item.get("customization") == customization):
                item["quantity"] = quantity
                found = True
                break
    
    if not found:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    await db.store_carts.update_one(
        {"user_id": current_user["username"]},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Cart updated"}

@api_router.delete("/store/cart/clear")
async def clear_cart(current_user: dict = Depends(verify_token)):
    """Clear the shopping cart"""
    await db.store_carts.delete_one({"user_id": current_user["username"]})
    return {"message": "Cart cleared"}

# Order Endpoints
@api_router.post("/store/orders/create")
async def create_order(shipping_address: Optional[str] = None, notes: Optional[str] = None, current_user: dict = Depends(verify_token)):
    """Create an order from the current cart (legacy endpoint - use /store/checkout for hosted checkout)"""
    cart = await db.store_carts.find_one({"user_id": current_user["username"]})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    items = cart["items"]
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    tax = round(subtotal * 0.0825, 2)  # 8.25% tax
    total = round(subtotal + tax, 2)
    
    order = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["username"],
        "user_name": current_user.get("username", "Unknown"),
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": "pending",
        "shipping_address": shipping_address,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.store_orders.insert_one(order)
    
    return {"order_id": order["id"], "total": total, "total_cents": int(total * 100)}

@api_router.post("/store/checkout")
async def create_hosted_checkout(shipping_address: Optional[str] = None, notes: Optional[str] = None, current_user: dict = Depends(verify_token)):
    """Create a Square hosted checkout link and redirect URL"""
    cart = await db.store_carts.find_one({"user_id": current_user["username"]})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    items = cart["items"]
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    tax = round(subtotal * 0.0825, 2)  # 8.25% tax
    total = round(subtotal + tax, 2)
    
    # Create local order first with pending status
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "user_id": current_user["username"],
        "user_name": current_user.get("username", "Unknown"),
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": "pending",
        "shipping_address": shipping_address,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.store_orders.insert_one(order)
    
    try:
        # Generate idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # Build line items for Square order
        line_items = []
        for item in items:
            # Calculate item price including any add-ons
            item_price_cents = int(item["price"] * 100)
            
            line_item = {
                "name": item["name"],
                "quantity": str(item["quantity"]),
                "base_price_money": {
                    "amount": item_price_cents,
                    "currency": "USD"
                }
            }
            
            # Add variation name if present
            if item.get("variation_name"):
                line_item["variation_name"] = item["variation_name"]
            
            # Add customization as note if present
            if item.get("customization"):
                line_item["note"] = item["customization"]
            
            line_items.append(line_item)
        
        # Create order object for Square
        square_order = {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": line_items,
            "reference_id": order_id  # Link to our local order
        }
        
        # Get frontend URL for redirect after payment
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000').replace('/api', '').rstrip('/')
        redirect_url = f"{frontend_url}/store?payment=success&order_id={order_id}"
        
        # Create checkout options
        checkout_options = {
            "redirect_url": redirect_url,
            "ask_for_shipping_address": True if shipping_address else False,
        }
        
        # Call Square API to create payment link
        result = square_client.checkout.payment_links.create(
            idempotency_key=idempotency_key,
            description=f"BOHTC Store Order #{order_id[:8]}",
            order=square_order,
            checkout_options=checkout_options
        )
        
        if result and hasattr(result, 'payment_link') and result.payment_link:
            payment_link = result.payment_link
            
            # Update order with Square payment link info
            await db.store_orders.update_one(
                {"id": order_id},
                {"$set": {
                    "square_payment_link_id": payment_link.id,
                    "square_order_id": payment_link.order_id,
                    "checkout_url": payment_link.url,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Clear the cart after successful checkout link creation
            await db.store_carts.delete_one({"user_id": current_user["username"]})
            
            # Log activity
            await log_activity(
                current_user["username"],
                "checkout_started",
                f"Checkout started for order {order_id}, total ${total:.2f}"
            )
            
            return {
                "success": True,
                "checkout_url": payment_link.url,
                "order_id": order_id,
                "square_order_id": payment_link.order_id,
                "total": total
            }
        else:
            # If Square API returns an error, delete the pending order
            await db.store_orders.delete_one({"id": order_id})
            error_detail = "Failed to create checkout link"
            if hasattr(result, 'errors') and result.errors:
                error_detail = result.errors[0].get('detail', error_detail)
            raise HTTPException(status_code=400, detail=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        # Clean up the order if Square API call fails
        await db.store_orders.delete_one({"id": order_id})
        logger.error(f"Square checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Checkout error: {str(e)}")

class SupporterCheckoutRequest(BaseModel):
    items: list
    customer_email: str
    customer_name: str
    shipping_address: Optional[str] = None

@api_router.post("/store/public/checkout")
async def create_supporter_checkout(checkout_data: SupporterCheckoutRequest):
    """Create a Square hosted checkout link for supporter store (no authentication required)"""
    if not checkout_data.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    # Calculate totals from items
    subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in checkout_data.items)
    tax = round(subtotal * 0.0825, 2)  # 8.25% tax
    total = round(subtotal + tax, 2)
    
    # Create local order with pending status
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "user_id": f"supporter_{checkout_data.customer_email}",
        "user_name": checkout_data.customer_name,
        "customer_email": checkout_data.customer_email,
        "items": checkout_data.items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": "pending",
        "shipping_address": checkout_data.shipping_address,
        "order_type": "supporter",  # Mark as supporter order
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.store_orders.insert_one(order)
    
    try:
        # Generate idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # Build line items for Square order
        line_items = []
        for item in checkout_data.items:
            item_price_cents = int(item.get("price", 0) * 100)
            
            line_item = {
                "name": item.get("name", "Product"),
                "quantity": str(item.get("quantity", 1)),
                "base_price_money": {
                    "amount": item_price_cents,
                    "currency": "USD"
                }
            }
            
            if item.get("variation_name"):
                line_item["variation_name"] = item["variation_name"]
            
            if item.get("customization"):
                line_item["note"] = item["customization"]
            
            line_items.append(line_item)
        
        # Create order object for Square
        square_order = {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": line_items,
            "reference_id": order_id
        }
        
        # Get frontend URL for redirect after payment
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000').replace('/api', '').rstrip('/')
        redirect_url = f"{frontend_url}/supporter-store?payment=success&order_id={order_id}"
        
        # Create checkout options
        checkout_options = {
            "redirect_url": redirect_url,
            "ask_for_shipping_address": True,
        }
        
        # Call Square API to create payment link
        result = square_client.checkout.payment_links.create(
            idempotency_key=idempotency_key,
            description=f"BOHTC Supporter Store Order #{order_id[:8]}",
            order=square_order,
            checkout_options=checkout_options
        )
        
        if result and hasattr(result, 'payment_link') and result.payment_link:
            payment_link = result.payment_link
            
            # Update order with Square payment link info
            await db.store_orders.update_one(
                {"id": order_id},
                {"$set": {
                    "square_payment_link_id": payment_link.id,
                    "square_order_id": payment_link.order_id,
                    "checkout_url": payment_link.url,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {
                "success": True,
                "checkout_url": payment_link.url,
                "order_id": order_id,
                "total": total
            }
        else:
            await db.store_orders.delete_one({"id": order_id})
            raise HTTPException(status_code=400, detail="Failed to create checkout link")
            
    except HTTPException:
        raise
    except Exception as e:
        await db.store_orders.delete_one({"id": order_id})
        logger.error(f"Supporter checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Checkout error: {str(e)}")

@api_router.post("/store/orders/{order_id}/pay")
async def process_payment(order_id: str, payment: PaymentRequest, current_user: dict = Depends(verify_token)):
    """Process payment for an order using Square"""
    order = await db.store_orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        # Create payment with Square
        idempotency_key = str(uuid.uuid4())
        
        payment_body = {
            "source_id": payment.source_id,
            "amount_money": {
                "amount": payment.amount_cents,
                "currency": "USD"
            },
            "idempotency_key": idempotency_key,
            "location_id": SQUARE_LOCATION_ID,
            "autocomplete": True
        }
        
        if payment.customer_email:
            payment_body["buyer_email_address"] = payment.customer_email
        
        result = square_client.payments.create(**payment_body)
        
        if result and result.payment:
            square_payment = result.payment
            
            # Update order status
            await db.store_orders.update_one(
                {"id": order_id},
                {"$set": {
                    "status": "paid",
                    "square_payment_id": square_payment.id,
                    "payment_method": "card",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Update inventory for merchandise items
            for item in order["items"]:
                product = await db.store_products.find_one({"id": item["product_id"]})
                if product and product.get("category") == "merchandise":
                    await db.store_products.update_one(
                        {"id": item["product_id"]},
                        {"$inc": {"inventory_count": -item["quantity"]}}
                    )
            
            # Update member dues status if this is a dues payment
            dues_info = order.get("dues_info")
            if dues_info and dues_info.get("member_id"):
                member_id = dues_info["member_id"]
                year = str(dues_info["year"])
                month = dues_info["month"]
                
                # Get current member dues
                member = await db.members.find_one({"id": member_id})
                if member:
                    dues = member.get("dues", {})
                    
                    # Initialize year if not exists
                    if year not in dues:
                        dues[year] = [{"status": "unpaid", "note": ""} for _ in range(12)]
                    
                    # Update the specific month to paid
                    if isinstance(dues[year], list) and len(dues[year]) > month:
                        dues[year][month] = {"status": "paid", "note": f"Paid via store on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"}
                    
                    # Update member record
                    await db.members.update_one(
                        {"id": member_id},
                        {"$set": {
                            "dues": dues,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    # Log the dues update
                    await log_activity(
                        current_user["username"],
                        "dues_paid",
                        f"Dues paid for {year}-{month+1:02d} via store payment"
                    )
            
            # Clear cart
            await db.store_carts.delete_one({"user_id": current_user["username"]})
            
            # Log activity
            await log_activity(
                current_user["username"],
                "payment_completed",
                f"Payment of ${order['total']:.2f} completed for order {order_id}"
            )
            
            return {
                "success": True,
                "payment_id": square_payment.id,
                "amount": square_payment.amount_money.amount / 100 if square_payment.amount_money else 0,
                "status": square_payment.status,
                "order_id": order_id
            }
        else:
            raise HTTPException(status_code=400, detail="Payment failed")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")

@api_router.get("/store/orders")
async def get_orders(current_user: dict = Depends(verify_token)):
    """Get orders for the current user (or all orders for admin)"""
    if current_user.get("role") == "admin":
        orders = await db.store_orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    else:
        orders = await db.store_orders.find({"user_id": current_user["username"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return orders

@api_router.get("/store/orders/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(verify_token)):
    """Get a specific order"""
    order = await db.store_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only allow access to own orders unless admin
    if current_user.get("role") != "admin" and order["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order

@api_router.put("/store/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, current_user: dict = Depends(verify_token)):
    """Update order status (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    valid_statuses = ["pending", "paid", "shipped", "completed", "cancelled", "refunded"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db.store_orders.update_one(
        {"id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated", "status": status}

# Dues-specific endpoint
@api_router.post("/store/dues/pay")
async def pay_dues(amount: float, year: int, month: int = 0, handle: str = None, current_user: dict = Depends(verify_token)):
    """Create a dues payment order and update member dues status"""
    # Validate month (0-11)
    if month < 0 or month > 11:
        raise HTTPException(status_code=400, detail="Invalid month. Must be 0-11")
    
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    
    # Find or create dues product for this month/year
    product_name = f"{month_names[month]} {year} Monthly Dues"
    dues_product = await db.store_products.find_one({"category": "dues", "name": product_name})
    
    if not dues_product:
        dues_product = {
            "id": str(uuid.uuid4()),
            "name": product_name,
            "description": f"Monthly membership dues for {month_names[month]} {year}",
            "price": amount,
            "category": "dues",
            "is_active": True,
            "inventory_count": 9999,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.store_products.insert_one(dues_product)
    
    # Find the member record for this user - try handle first, then username/email
    member = None
    if handle:
        # Sanitize handle for regex to prevent NoSQL injection
        safe_handle = sanitize_for_regex(sanitize_string_input(handle))
        member = await db.members.find_one({"handle": {"$regex": f"^{safe_handle}$", "$options": "i"}})
    
    if not member:
        member = await db.members.find_one({"$or": [
            {"name": current_user.get("username")},
            {"email": current_user.get("email")},
            {"user_id": current_user.get("id")}
        ]})
    
    # Create order with member info for dues update after payment
    order = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["username"],
        "user_name": current_user.get("username", "Unknown"),
        "member_handle": handle,  # Store the handle for reference
        "items": [{
            "product_id": dues_product["id"],
            "name": dues_product["name"],
            "price": amount,
            "quantity": 1
        }],
        "subtotal": amount,
        "tax": 0,  # No tax on dues
        "total": amount,
        "status": "pending",
        "notes": f"Monthly dues payment for {month_names[month]} {year}" + (f" - Handle: {handle}" if handle else ""),
        "dues_info": {  # Store dues info to update member record after payment
            "year": year,
            "month": month,
            "month_name": month_names[month],
            "member_id": member["id"] if member else None,
            "member_handle": handle
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.store_orders.insert_one(order)
    
    return {"order_id": order["id"], "total": amount, "total_cents": int(amount * 100)}

@api_router.get("/store/dues/payments")
async def get_dues_payments(current_user: dict = Depends(verify_token)):
    """Get all dues payments (Store admins only)"""
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can view dues payments")
    
    # Find all orders that have dues_info
    dues_orders = await db.store_orders.find(
        {"dues_info": {"$exists": True, "$ne": None}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return dues_orders

@api_router.post("/store/sync-square-catalog")
async def sync_square_catalog(current_user: dict = Depends(verify_token)):
    """Sync products from Square catalog to local store (Store admins only)"""
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can sync store products")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    try:
        # Fetch catalog items from Square - iterate through the pager
        result = square_client.catalog.list(types="ITEM")
        items = list(result)  # Convert pager to list
        
        if not items:
            return {"message": "No items found in Square catalog", "count": 0}
        
        # Collect all variation IDs to fetch inventory in batch
        all_variation_ids = []
        for item in items:
            item_data = item.item_data
            if not item_data:
                continue
            for var in (item_data.variations or []):
                all_variation_ids.append(var.id)
        
        # Fetch inventory counts for all variations
        inventory_map = {}
        if all_variation_ids:
            try:
                inv_result = square_client.inventory.batch_get_counts(
                    catalog_object_ids=all_variation_ids,
                    location_ids=[SQUARE_LOCATION_ID]
                )
                inv_items = list(inv_result)
                for count in inv_items:
                    qty = int(count.quantity) if count.quantity else 0
                    inventory_map[count.catalog_object_id] = qty
            except Exception as inv_e:
                print(f"Warning: Could not fetch inventory: {inv_e}", file=sys.stderr)
        
        synced_count = 0
        
        for item in items:
            item_data = item.item_data
            if not item_data:
                continue
            item_id = item.id
            name = item_data.name or "Unknown"
            description = item_data.description or ""
            
            # Get ecom image URLs if available
            image_url = None
            if item_data.ecom_image_uris and len(item_data.ecom_image_uris) > 0:
                image_url = item_data.ecom_image_uris[0]
            
            # Get variations with inventory
            variations_list = item_data.variations or []
            if not variations_list:
                continue
            
            # Build variations data with inventory
            product_variations = []
            total_inventory = 0
            min_price = float('inf')
            has_size_variations = False
            
            # Check if this is a shirt/hoodie (allows customization)
            # Specific exclusions per user requirements:
            # - Hi-Viz shirts (any Hi-Viz product)
            # - Member Long Sleeve Shirt - Black (Original Logo Design)
            # - Ladiez T-Shirt
            name_lower = name.lower()
            is_apparel = any(word in name_lower for word in ['shirt', 'hoodie', 'tee', 'jersey', 'long sleeve'])
            
            # Check specific exclusions
            is_excluded = (
                'hi-viz' in name_lower or 
                'hiviz' in name_lower or
                'hi viz' in name_lower or
                'ladiez' in name_lower or
                ('member long sleeve' in name_lower and 'original logo design' in name_lower)
            )
            
            allows_customization = is_apparel and not is_excluded
            
            for var in variations_list:
                var_data = var.item_variation_data
                if not var_data:
                    continue
                
                price_money = var_data.price_money
                if not price_money:
                    continue
                    
                price = price_money.amount / 100
                if price <= 0:
                    continue
                
                if price < min_price:
                    min_price = price
                
                var_name = var_data.name or "Default"
                var_id = var.id
                
                # Get inventory from our map
                inv_count = inventory_map.get(var_id, 0)
                total_inventory += inv_count
                
                # Check sold_out from location overrides
                sold_out = inv_count == 0
                if var_data.location_overrides:
                    for lo in var_data.location_overrides:
                        if lo.sold_out:
                            sold_out = True
                            break
                
                # Check if this looks like a size
                size_indicators = ['S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', 'XS', 'XXL', 'LT', 'XLT', '2XLT', '3XLT']
                if var_name.upper() in size_indicators or any(s in var_name.upper() for s in size_indicators):
                    has_size_variations = True
                
                product_variations.append({
                    "id": str(uuid.uuid4()),
                    "name": var_name,
                    "price": price,
                    "square_variation_id": var_id,
                    "inventory_count": inv_count,
                    "sold_out": sold_out
                })
            
            if min_price == float('inf'):
                continue
            
            # Sort variations by size order
            size_order = {'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'LT': 4, 'XL': 5, 'XLT': 6, '2XL': 7, '2XLT': 8, '3XL': 9, '3XLT': 10, '4XL': 11, '5XL': 12, 'Regular': 0}
            product_variations.sort(key=lambda x: size_order.get(x['name'], 99))
            
            # Determine if product should be shown in supporter store
            # Default: show everything EXCEPT member-only items
            is_member_only = (
                'member' in name_lower and 
                'supporter' not in name_lower
            )
            # NEW ITEMS: Default to NOT showing in supporter store
            # Store admins must manually enable each item for supporter store
            show_in_supporter = False  # Always false for new items
            
            # Check if product already exists
            existing = await db.store_products.find_one({"square_catalog_id": item_id})
            
            product_data = {
                "name": name,
                "description": description[:500] if description else "",
                "price": min_price,
                "image_url": image_url,
                "variations": product_variations,
                "has_variations": len(product_variations) > 1 or has_size_variations,
                "allows_customization": allows_customization,
                "inventory_count": total_inventory,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                # Update existing product - preserve show_in_supporter_store setting
                # Admins control this manually
                await db.store_products.update_one(
                    {"square_catalog_id": item_id},
                    {"$set": product_data}
                )
            else:
                # Create new product - default to NOT in supporter store
                product_data.update({
                    "id": str(uuid.uuid4()),
                    "category": "merchandise",
                    "square_catalog_id": item_id,
                    "is_active": True,
                    "show_in_supporter_store": show_in_supporter,  # Default FALSE for new items
                    "allows_customization": False,  # Default FALSE, admin must enable
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                await db.store_products.insert_one(product_data)
                logger.info(f"New product synced: {name} (supporter store: {show_in_supporter})")
            
            synced_count += 1
        
        return {"message": f"Successfully synced {synced_count} products from Square catalog with inventory", "count": synced_count}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

# ==================== SQUARE WEBHOOK ENDPOINT ====================

@api_router.post("/webhooks/square")
async def handle_square_webhook(request: Request):
    """
    Handle webhook events from Square.
    
    Events handled:
    - payment.completed: Update order status to 'paid'
    - payment.updated: Handle payment status changes
    - order.updated: Handle order status changes
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Get signature header
        signature = request.headers.get('x-square-hmacsha256-signature', '')
        
        # Get the notification URL (must match what's configured in Square Dashboard)
        notification_url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/webhooks/square"
        
        # Verify signature if key is configured
        if SQUARE_WEBHOOK_SIGNATURE_KEY:
            try:
                is_valid = square_verify_signature(
                    request_body=body_str,
                    signature_header=signature,
                    signature_key=SQUARE_WEBHOOK_SIGNATURE_KEY,
                    notification_url=notification_url
                )
                if not is_valid:
                    logger.warning("Square webhook signature verification failed")
                    raise HTTPException(status_code=401, detail="Invalid signature")
            except NameError:
                # square_verify_signature not imported (Square SDK issue)
                logger.warning("Square signature verification not available, skipping...")
        else:
            logger.info("Square webhook signature key not configured, skipping verification")
        
        # Parse the event
        import json
        event_data = json.loads(body_str)
        
        event_type = event_data.get('type', '')
        event_id = event_data.get('event_id', '')
        
        logger.info(f"Square webhook received: {event_type} (event_id: {event_id})")
        
        # Handle different event types
        if event_type == 'payment.completed':
            await handle_payment_completed(event_data)
        elif event_type == 'payment.updated':
            await handle_payment_updated(event_data)
        elif event_type == 'order.updated':
            await handle_order_updated(event_data)
        else:
            logger.info(f"Unhandled Square webhook event type: {event_type}")
        
        # Return 200 to acknowledge receipt (Square requires this)
        return {"status": "ok", "event_id": event_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Square webhook error: {str(e)}")
        # Still return 200 to prevent Square from retrying
        return {"status": "error", "message": str(e)}

async def handle_payment_completed(event_data: dict):
    """Handle payment.completed webhook event"""
    try:
        payment = event_data.get('data', {}).get('object', {}).get('payment', {})
        payment_id = payment.get('id')
        order_id = payment.get('order_id')
        status_value = payment.get('status')
        amount_money = payment.get('amount_money', {})
        amount_cents = amount_money.get('amount', 0)
        amount_dollars = amount_cents / 100 if amount_cents else 0
        
        logger.info(f"Payment completed: payment_id={payment_id}, order_id={order_id}, status={status_value}, amount=${amount_dollars}")
        
        # Try to find local order first (for in-app store purchases)
        local_order = None
        if order_id:
            local_order = await db.store_orders.find_one({"square_order_id": order_id})
            
            if not local_order:
                reference_id = payment.get('reference_id')
                if reference_id:
                    local_order = await db.store_orders.find_one({"id": reference_id})
        
        if local_order:
            # Handle in-app store order
            if local_order.get('status') != 'paid':
                update_data = {
                    "status": "paid",
                    "square_payment_id": payment_id,
                    "payment_completed_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.store_orders.update_one(
                    {"id": local_order["id"]},
                    {"$set": update_data}
                )
                
                logger.info(f"Order {local_order['id']} updated to 'paid' via webhook")
                
                # Update member dues if this is a dues payment
                dues_info = local_order.get("dues_info")
                if dues_info and dues_info.get("member_id"):
                    await update_member_dues_from_webhook(dues_info)
                
                await log_activity(
                    local_order.get("user_id", "webhook"),
                    "order_paid_webhook",
                    f"Order {local_order['id']} marked as paid via Square webhook"
                )
        else:
            # No local order - this might be a direct Square payment (payment link, POS, etc.)
            # Try to match to a member for automatic dues tracking
            await try_match_external_payment_to_dues(payment, payment_id, amount_dollars)
            
    except Exception as e:
        logger.error(f"Error handling payment.completed: {str(e)}")


async def try_match_external_payment_to_dues(payment: dict, payment_id: str, amount: float):
    """Try to match an external Square payment to a member for dues tracking"""
    try:
        # Get customer info from payment
        customer_id = payment.get('customer_id')
        buyer_email = payment.get('buyer_email_address')
        note = payment.get('note', '')
        
        customer_name = None
        
        # Try to get customer name from Square
        if customer_id and square_client:
            try:
                result = square_client.customers.retrieve_customer(customer_id=customer_id)
                if result.is_success():
                    customer = result.body.get('customer', {})
                    given_name = customer.get('given_name', '')
                    family_name = customer.get('family_name', '')
                    customer_name = f"{given_name} {family_name}".strip()
                    if not customer_name:
                        customer_name = customer.get('company_name')
            except Exception as e:
                logger.warning(f"Failed to get customer from Square: {e}")
        
        if not customer_name:
            logger.info(f"External payment {payment_id}: No customer name found, skipping dues match")
            return
        
        logger.info(f"External payment {payment_id}: Trying to match customer '{customer_name}' to member")
        
        # Try to find matching member by name (fuzzy match)
        members = await db.members.find({}, {"_id": 0}).to_list(1000)
        
        matched_member = None
        best_score = 0
        
        customer_name_lower = customer_name.lower().strip()
        
        for member in members:
            member_name = member.get('name', '').lower().strip()
            member_handle = member.get('handle', '').lower().strip()
            
            # Exact match on name
            if customer_name_lower == member_name:
                matched_member = member
                best_score = 100
                break
            
            # Exact match on handle
            if customer_name_lower == member_handle:
                matched_member = member
                best_score = 100
                break
            
            # Partial match (name contains or is contained)
            if customer_name_lower in member_name or member_name in customer_name_lower:
                score = 80
                if score > best_score:
                    best_score = score
                    matched_member = member
            
            # Check if handle matches part of customer name
            if member_handle and (member_handle in customer_name_lower or customer_name_lower in member_handle):
                score = 75
                if score > best_score:
                    best_score = score
                    matched_member = member
        
        if matched_member and best_score >= 75:
            logger.info(f"External payment {payment_id}: Matched to member '{matched_member.get('handle')}' (score: {best_score})")
            
            # Mark current month as paid
            now = datetime.now(timezone.utc)
            year = str(now.year)
            month = now.month - 1  # 0-indexed
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            dues_info = {
                "member_id": matched_member["id"],
                "year": int(year),
                "month": month,
                "month_name": month_names[month]
            }
            
            await update_member_dues_from_webhook(dues_info)
            
            # Log the external payment for tracking
            external_payment_record = {
                "id": str(uuid.uuid4()),
                "square_payment_id": payment_id,
                "customer_name": customer_name,
                "member_id": matched_member["id"],
                "member_handle": matched_member.get("handle"),
                "amount": amount,
                "year": year,
                "month": month,
                "month_name": month_names[month],
                "match_score": best_score,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "external_square_payment"
            }
            await db.external_dues_payments.insert_one(external_payment_record)
            
            logger.info(f"External payment {payment_id}: Dues updated for {matched_member.get('handle')} - {month_names[month]} {year}")
        else:
            # Log unmatched payment for manual review
            unmatched_record = {
                "id": str(uuid.uuid4()),
                "square_payment_id": payment_id,
                "customer_name": customer_name,
                "buyer_email": buyer_email,
                "amount": amount,
                "note": note,
                "status": "unmatched",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.unmatched_payments.insert_one(unmatched_record)
            logger.info(f"External payment {payment_id}: No member match found for '{customer_name}', saved for review")
            
    except Exception as e:
        logger.error(f"Error matching external payment to dues: {str(e)}")

async def handle_payment_updated(event_data: dict):
    """Handle payment.updated webhook event"""
    try:
        payment = event_data.get('data', {}).get('object', {}).get('payment', {})
        payment_id = payment.get('id')
        status_value = payment.get('status')
        
        logger.info(f"Payment updated: payment_id={payment_id}, status={status_value}")
        
        # If payment failed or was cancelled, update order
        if status_value in ['FAILED', 'CANCELED']:
            order_id = payment.get('order_id')
            if order_id:
                local_order = await db.store_orders.find_one({"square_order_id": order_id})
                if local_order and local_order.get('status') == 'pending':
                    await db.store_orders.update_one(
                        {"id": local_order["id"]},
                        {"$set": {
                            "status": "cancelled",
                            "cancellation_reason": f"Payment {status_value.lower()}",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    logger.info(f"Order {local_order['id']} cancelled due to payment {status_value}")
    except Exception as e:
        logger.error(f"Error handling payment.updated: {str(e)}")

async def handle_order_updated(event_data: dict):
    """Handle order.updated webhook event"""
    try:
        order = event_data.get('data', {}).get('object', {}).get('order', {})
        square_order_id = order.get('id')
        state = order.get('state')
        
        logger.info(f"Order updated: square_order_id={square_order_id}, state={state}")
        
        # Find local order
        local_order = await db.store_orders.find_one({"square_order_id": square_order_id})
        
        if not local_order:
            reference_id = order.get('reference_id')
            if reference_id:
                local_order = await db.store_orders.find_one({"id": reference_id})
        
        if not local_order:
            logger.warning(f"Local order not found for Square order: {square_order_id}")
            return
        
        # Map Square order states to our statuses
        status_map = {
            'OPEN': 'pending',
            'COMPLETED': 'paid',
            'CANCELED': 'cancelled'
        }
        
        new_status = status_map.get(state)
        if new_status and local_order.get('status') != new_status:
            await db.store_orders.update_one(
                {"id": local_order["id"]},
                {"$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Order {local_order['id']} status updated to '{new_status}' via order.updated webhook")
    except Exception as e:
        logger.error(f"Error handling order.updated: {str(e)}")

async def update_member_dues_from_webhook(dues_info: dict):
    """Update member dues status when payment is confirmed via webhook"""
    try:
        member_id = dues_info.get("member_id")
        year = str(dues_info.get("year"))
        month = dues_info.get("month")
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        if not member_id:
            return
        
        member = await db.members.find_one({"id": member_id})
        if not member:
            logger.warning(f"Member not found for dues update: {member_id}")
            return
        
        dues = member.get("dues", {})
        
        # Initialize year if not exists
        if year not in dues:
            dues[year] = [{"status": "unpaid", "note": ""} for _ in range(12)]
        
        # Update the specific month to paid
        payment_note = f"Paid via Square on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        if isinstance(dues[year], list) and len(dues[year]) > month:
            dues[year][month] = {
                "status": "paid",
                "note": payment_note
            }
        
        # Update member record
        await db.members.update_one(
            {"id": member_id},
            {"$set": {
                "dues": dues,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Also update officer_dues collection (for A & D page sync)
        month_str = f"{month_names[month]}_{year}"  # e.g., "Jan_2026"
        existing = await db.officer_dues.find_one({
            "member_id": member_id,
            "month": month_str
        })
        
        dues_record = {
            "id": existing.get("id") if existing else str(uuid.uuid4()),
            "member_id": member_id,
            "month": month_str,
            "status": "paid",
            "notes": payment_note,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "square_webhook"
        }
        
        if existing:
            await db.officer_dues.update_one(
                {"id": existing.get("id")},
                {"$set": dues_record}
            )
        else:
            dues_record["created_at"] = datetime.now(timezone.utc).isoformat()
            dues_record["created_by"] = "square_webhook"
            await db.officer_dues.insert_one(dues_record)
        
        logger.info(f"Member {member_id} dues updated for {year}-{int(month)+1:02d} via webhook (synced to A&D)")
        
    except Exception as e:
        logger.error(f"Error updating member dues from webhook: {str(e)}")

@api_router.get("/webhooks/square/info")
async def get_square_webhook_info(current_user: dict = Depends(verify_token)):
    """Get Square webhook configuration info (Store admins only)"""
    # Check if user can manage store
    if not await can_manage_store_async(current_user):
        raise HTTPException(status_code=403, detail="Only store admins can view webhook info")
    
    webhook_url = f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/webhooks/square"
    signature_configured = bool(SQUARE_WEBHOOK_SIGNATURE_KEY)
    
    return {
        "webhook_url": webhook_url,
        "signature_key_configured": signature_configured,
        "events_to_subscribe": [
            "payment.completed",
            "payment.updated",
            "order.updated"
        ],
        "instructions": {
            "step1": "Go to Square Developer Dashboard (https://developer.squareup.com/apps)",
            "step2": "Select your application",
            "step3": "Click on 'Webhooks' in the left menu",
            "step4": f"Add a new webhook subscription with URL: {webhook_url}",
            "step5": "Subscribe to events: payment.completed, payment.updated, order.updated",
            "step6": "Copy the Signature Key and add it to your .env as SQUARE_WEBHOOK_SIGNATURE_KEY",
            "step7": "Save and test the webhook"
        }
    }

# ==================== SQUARE SUBSCRIPTION SYNC ENDPOINTS ====================

# Fuzzy matching helper for Square subscription matching
def fuzzy_match_member(customer_name: str, members: list, threshold: int = 75) -> tuple:
    """
    Match customer name to member using fuzzy string matching.
    Returns (matched_member, match_score, match_type) or (None, 0, None)
    """
    from rapidfuzz import fuzz, process
    
    if not customer_name:
        return None, 0, None
    
    customer_name_lower = customer_name.lower().strip()
    best_match = None
    best_score = 0
    match_type = None
    
    for member in members:
        member_name = member.get('name', '').lower().strip()
        member_handle = member.get('handle', '').lower().strip()
        
        # Exact match - highest priority
        if customer_name_lower == member_name:
            return member, 100, "exact_name"
        if customer_name_lower == member_handle:
            return member, 100, "exact_handle"
        
        # Fuzzy match on name
        if member_name:
            name_score = fuzz.token_sort_ratio(customer_name_lower, member_name)
            if name_score > best_score and name_score >= threshold:
                best_score = name_score
                best_match = member
                match_type = "fuzzy_name"
        
        # Fuzzy match on handle
        if member_handle:
            handle_score = fuzz.token_sort_ratio(customer_name_lower, member_handle)
            if handle_score > best_score and handle_score >= threshold:
                best_score = handle_score
                best_match = member
                match_type = "fuzzy_handle"
        
        # Partial match - check if one contains the other
        if member_name and (customer_name_lower in member_name or member_name in customer_name_lower):
            partial_score = 85  # Give partial matches a good score
            if partial_score > best_score:
                best_score = partial_score
                best_match = member
                match_type = "partial_name"
    
    return best_match, best_score, match_type


@api_router.get("/dues/subscriptions")
async def get_square_subscriptions(current_user: dict = Depends(verify_token)):
    """Get active Square subscriptions and match to members using batch API calls and fuzzy matching"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can view subscriptions")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    try:
        # Get all subscriptions from Square using new SDK format
        subscriptions = []
        cursor = None
        
        while True:
            result = square_client.subscriptions.search(
                cursor=cursor,
                limit=100,
                query={
                    "filter": {
                        "location_ids": [SQUARE_LOCATION_ID]
                    }
                }
            )
            
            subs = result.subscriptions or []
            # Filter to ACTIVE subscriptions that are NOT scheduled for cancellation
            # (canceled_date being set means cancellation is scheduled)
            active_subs = [s for s in subs if s.status == "ACTIVE" and not s.canceled_date]
            subscriptions.extend(active_subs)
            
            cursor = result.cursor
            if not cursor:
                break
        
        # Collect all customer IDs for batch retrieval
        customer_ids = list(set(sub.customer_id for sub in subscriptions if sub.customer_id))
        
        # Batch retrieve customers (up to 100 per call)
        customer_map = {}
        for i in range(0, len(customer_ids), 100):
            batch_ids = customer_ids[i:i+100]
            try:
                batch_result = square_client.customers.bulk_retrieve_customers(
                    customer_ids=batch_ids
                )
                if batch_result.responses:
                    for cust_id, response in batch_result.responses.items():
                        if response.customer:
                            cust = response.customer
                            given_name = cust.given_name or ''
                            family_name = cust.family_name or ''
                            customer_map[cust_id] = {
                                "name": f"{given_name} {family_name}".strip(),
                                "email": cust.email_address
                            }
            except Exception as e:
                logger.warning(f"Batch customer fetch failed: {e}")
                # Fallback to individual fetches for this batch
                for cust_id in batch_ids:
                    try:
                        cust_result = square_client.customers.get(customer_id=cust_id)
                        if cust_result.customer:
                            cust = cust_result.customer
                            given_name = cust.given_name or ''
                            family_name = cust.family_name or ''
                            customer_map[cust_id] = {
                                "name": f"{given_name} {family_name}".strip(),
                                "email": cust.email_address
                            }
                    except:
                        pass
        
        # Get all members for matching
        members = await db.members.find({}, {"_id": 0, "id": 1, "name": 1, "handle": 1}).to_list(1000)
        
        # Get manual subscription links
        manual_links = await db.member_subscriptions.find({}, {"_id": 0}).to_list(1000)
        manual_link_map = {link.get("square_customer_id"): link for link in manual_links if link.get("square_customer_id")}
        
        # Process and match subscriptions
        matched_subs = []
        unmatched_subs = []
        
        for sub in subscriptions:
            customer_id = sub.customer_id
            sub_id = sub.id
            status = sub.status
            charged_through_date = sub.charged_through_date
            
            customer_info = customer_map.get(customer_id, {})
            customer_name = customer_info.get("name")
            customer_email = customer_info.get("email")
            
            matched_member = None
            match_score = 0
            match_type = None
            
            # First check for manual link
            if customer_id in manual_link_map:
                link = manual_link_map[customer_id]
                member_id = link.get("member_id")
                matched_member = next((m for m in members if m.get("id") == member_id), None)
                if matched_member:
                    match_score = 100
                    match_type = "manual_link"
            
            # If no manual link, use fuzzy matching
            if not matched_member and customer_name:
                matched_member, match_score, match_type = fuzzy_match_member(customer_name, members)
            
            sub_data = {
                "subscription_id": sub_id,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "status": status,
                "charged_through_date": charged_through_date,
                "matched_member_id": matched_member.get("id") if matched_member else None,
                "matched_member_handle": matched_member.get("handle") if matched_member else None,
                "match_score": match_score,
                "match_type": match_type
            }
            
            if matched_member:
                matched_subs.append(sub_data)
            else:
                unmatched_subs.append(sub_data)
        
        return {
            "total": len(subscriptions),
            "matched": matched_subs,
            "unmatched": unmatched_subs,
            "customer_fetch_method": "batch"
        }
        
    except Exception as e:
        logger.error(f"Error fetching Square subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch subscriptions: {str(e)}")


@api_router.post("/dues/sync-subscriptions")
async def sync_subscriptions_to_dues(current_user: dict = Depends(verify_token)):
    """Sync active Square subscriptions to member dues using actual payment history.
    Payment amount determines months covered:
    - $30 = 1 month
    - $300-$330 = 12 months (yearly - $300 if annual sub on Jan 1, $330 otherwise)
    Payment date determines which month(s) get marked as paid.
    """
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can sync subscriptions")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    MONTHLY_DUES_AMOUNT = 30  # $30 per month
    
    try:
        # Get active subscriptions
        subscriptions = []
        cursor = None
        
        while True:
            result = square_client.subscriptions.search(
                cursor=cursor,
                limit=100,
                query={
                    "filter": {
                        "location_ids": [SQUARE_LOCATION_ID]
                    }
                }
            )
            
            subs = result.subscriptions or []
            # Filter to ACTIVE subscriptions that are NOT scheduled for cancellation
            active_subs = [s for s in subs if s.status == "ACTIVE" and not s.canceled_date]
            subscriptions.extend(active_subs)
            
            cursor = result.cursor
            if not cursor:
                break
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Batch retrieve customers for subscriptions
        customer_ids = list(set(sub.customer_id for sub in subscriptions if sub.customer_id))
        customer_map = {}
        
        for i in range(0, len(customer_ids), 100):
            batch_ids = customer_ids[i:i+100]
            try:
                batch_result = square_client.customers.bulk_retrieve_customers(
                    customer_ids=batch_ids
                )
                if batch_result.responses:
                    for cust_id, response in batch_result.responses.items():
                        if response.customer:
                            cust = response.customer
                            given_name = cust.given_name or ''
                            family_name = cust.family_name or ''
                            customer_map[cust_id] = f"{given_name} {family_name}".strip()
            except Exception as e:
                logger.warning(f"Batch customer fetch failed: {e}")
                for cust_id in batch_ids:
                    try:
                        cust_result = square_client.customers.get(customer_id=cust_id)
                        if cust_result.customer:
                            cust = cust_result.customer
                            given_name = cust.given_name or ''
                            family_name = cust.family_name or ''
                            customer_map[cust_id] = f"{given_name} {family_name}".strip()
                    except:
                        pass
        
        # Get all members and manual links
        members = await db.members.find({}, {"_id": 0}).to_list(1000)
        manual_links = await db.member_subscriptions.find({}, {"_id": 0}).to_list(1000)
        manual_link_map = {link.get("square_customer_id"): link.get("member_id") for link in manual_links if link.get("square_customer_id")}
        
        synced_count = 0
        months_marked_paid = 0
        skipped_count = 0
        errors = []
        
        for sub in subscriptions:
            customer_id = sub.customer_id
            customer_name = customer_map.get(customer_id)
            
            if not customer_name and customer_id not in manual_link_map:
                skipped_count += 1
                continue
            
            matched_member = None
            
            # First check manual link
            if customer_id in manual_link_map:
                member_id = manual_link_map[customer_id]
                matched_member = next((m for m in members if m.get("id") == member_id), None)
            
            # Then try fuzzy matching
            if not matched_member and customer_name:
                matched_member, score, match_type = fuzzy_match_member(customer_name, members)
            
            if not matched_member:
                skipped_count += 1
                continue
            
            # Get actual payment history from subscription invoices
            try:
                invoice_ids = getattr(sub, 'invoice_ids', None) or []
                payments_processed = set()  # Track processed payments to avoid duplicates
                
                for invoice_id in invoice_ids:
                    try:
                        inv_result = square_client.invoices.get(invoice_id=invoice_id)
                        if not inv_result or not inv_result.invoice:
                            continue
                        
                        invoice = inv_result.invoice
                        status = getattr(invoice, 'status', 'UNKNOWN')
                        
                        if status != "PAID":
                            continue
                        
                        # Get payment amount
                        amount = 0
                        if hasattr(invoice, 'payment_requests') and invoice.payment_requests:
                            req = invoice.payment_requests[0]
                            if hasattr(req, 'computed_amount_money') and req.computed_amount_money:
                                amount = req.computed_amount_money.amount / 100  # Convert cents to dollars
                        
                        if amount <= 0:
                            continue
                        
                        # Get payment date from order
                        order_id = getattr(invoice, 'order_id', None)
                        payment_date = None
                        payment_id = None
                        
                        if order_id:
                            try:
                                order_result = square_client.orders.get(order_id=order_id)
                                if order_result and order_result.order:
                                    tenders = getattr(order_result.order, 'tenders', None) or []
                                    for tender in tenders:
                                        if hasattr(tender, 'payment_id') and tender.payment_id:
                                            payment_id = tender.payment_id
                                            # Skip if we've already processed this payment
                                            if payment_id in payments_processed:
                                                break
                                            payments_processed.add(payment_id)
                                            payment_date = getattr(tender, 'created_at', None)
                                            break
                            except Exception as order_err:
                                logger.warning(f"Failed to fetch order {order_id}: {order_err}")
                        
                        # Fallback to invoice date
                        if not payment_date:
                            payment_date = getattr(invoice, 'updated_at', None) or getattr(invoice, 'created_at', None)
                        
                        if not payment_date:
                            continue
                        
                        # Parse payment date
                        try:
                            if isinstance(payment_date, str):
                                # Parse ISO format date
                                payment_dt = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
                            else:
                                payment_dt = payment_date
                        except Exception:
                            continue
                        
                        # Calculate number of months covered by this payment
                        # Special handling for yearly payments:
                        # - $300 = 12 months (annual subscription discount)
                        # - $330 = 12 months (standard yearly)
                        # - Otherwise: $30 per month
                        if amount >= 300 and amount <= 330:
                            num_months = 12  # Yearly payment
                        else:
                            num_months = max(1, int(amount / MONTHLY_DUES_AMOUNT))
                        
                        # Mark dues as paid for each month covered
                        for month_offset in range(num_months):
                            # Calculate target month/year
                            target_month = payment_dt.month - 1 + month_offset  # 0-indexed
                            target_year = payment_dt.year
                            
                            # Handle year rollover
                            while target_month >= 12:
                                target_month -= 12
                                target_year += 1
                            
                            # Update dues for this month
                            payment_note = f"Paid via Square on {payment_dt.strftime('%Y-%m-%d')}"
                            if payment_id:
                                payment_note += f" (Trans: {payment_id[:12]}...)"
                            
                            await update_member_dues_with_payment_info(
                                member_id=matched_member["id"],
                                year=target_year,
                                month=target_month,
                                payment_note=payment_note,
                                payment_id=payment_id
                            )
                            months_marked_paid += 1
                        
                    except Exception as inv_err:
                        logger.warning(f"Failed to process invoice {invoice_id}: {inv_err}")
                        continue
                
                synced_count += 1
                
                # Save/update subscription link
                await db.member_subscriptions.update_one(
                    {"member_id": matched_member["id"]},
                    {"$set": {
                        "member_id": matched_member["id"],
                        "member_handle": matched_member.get("handle"),
                        "square_customer_id": customer_id,
                        "square_subscription_id": sub.id,
                        "customer_name": customer_name,
                        "last_synced": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
                
            except Exception as e:
                errors.append(f"Failed to update {matched_member.get('handle')}: {str(e)}")
        
        return {
            "message": "Subscription sync complete - based on actual payment history",
            "members_synced": synced_count,
            "months_marked_paid": months_marked_paid,
            "skipped": skipped_count,
            "total_subscriptions": len(subscriptions),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error syncing subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync subscriptions: {str(e)}")


@api_router.post("/dues/sync-payment-links")
async def sync_payment_links_to_dues(current_user: dict = Depends(verify_token)):
    """Sync dues from Square payments (one-time dues payments via payment links).
    Uses the Payments API and matches customers to members by name using fuzzy matching.
    Looks for orders with dues-related items.
    """
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can sync payment links")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    MONTHLY_DUES_AMOUNT = 30
    DUES_ITEM_KEYWORDS = [
        "dues",
        "dues annual",
        "annual dues",
        "member dues",
        "monthly member dues",
        "monthly dues",
        "lump sum dues",
        "lump sum",
        "past due",
        "late fee",
        "one time payment",
        "one-time",
        "membership",
        "national dues",
        "chapter dues"
    ]
    
    try:
        # Get all completed payments from last 12 months
        start_date = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        
        payments_result = square_client.payments.list(
            begin_time=start_date,
            limit=200
        )
        
        all_payments = list(payments_result) if payments_result else []
        
        # Filter to completed payments only
        completed_payments = [p for p in all_payments if p.status == "COMPLETED"]
        
        # Get all members for matching
        members = await db.members.find({}, {"_id": 0}).to_list(1000)
        
        # Track processed payments to avoid duplicates
        processed_payments = set()
        existing_synced = await db.synced_payment_links.find({}, {"payment_id": 1}).to_list(10000)
        for doc in existing_synced:
            if doc.get("payment_id"):
                processed_payments.add(doc["payment_id"])
        
        # Also exclude payments that are from subscriptions (already synced via subscription sync)
        subscription_payment_ids = set()
        sub_links = await db.member_subscriptions.find({}, {"_id": 0}).to_list(1000)
        # We'll check order_ids instead since subscription payments are tied to subscription orders
        
        synced_count = 0
        months_marked_paid = 0
        skipped_no_match = 0
        skipped_not_dues = 0
        errors = []
        
        for payment in completed_payments:
            try:
                payment_id = payment.id
                
                # Skip if already processed
                if payment_id in processed_payments:
                    continue
                
                order_id = getattr(payment, 'order_id', None)
                if not order_id:
                    continue
                
                # Get the order to check if it's a dues payment
                try:
                    order_result = square_client.orders.get(order_id=order_id)
                    if not order_result or not order_result.order:
                        continue
                    order = order_result.order
                except Exception:
                    continue
                
                # Check if this order has dues-related items
                line_items = getattr(order, 'line_items', None) or []
                is_dues_order = False
                total_amount = 0
                
                # Debug: Log item names for troubleshooting
                item_names_found = []
                
                for item in line_items:
                    item_name = (getattr(item, 'name', '') or '').lower()
                    item_names_found.append(item_name)
                    if any(keyword in item_name for keyword in DUES_ITEM_KEYWORDS):
                        is_dues_order = True
                        if hasattr(item, 'total_money') and item.total_money:
                            total_amount += item.total_money.amount / 100
                
                # Also check order note/reference for dues keywords
                order_note = (getattr(order, 'reference_id', '') or '').lower()
                order_source = (getattr(order, 'source', None) or {})
                if hasattr(order_source, 'name'):
                    order_source_name = (order_source.name or '').lower()
                else:
                    order_source_name = ''
                
                if not is_dues_order:
                    # Check if any dues keyword in order note or source
                    if any(keyword in order_note for keyword in DUES_ITEM_KEYWORDS):
                        is_dues_order = True
                    elif any(keyword in order_source_name for keyword in DUES_ITEM_KEYWORDS):
                        is_dues_order = True
                
                if not is_dues_order:
                    skipped_not_dues += 1
                    continue
                
                # Use payment amount if we couldn't get it from items
                if total_amount == 0 and payment.amount_money:
                    total_amount = payment.amount_money.amount / 100
                
                # Get customer name from payment
                customer_name = None
                customer_id = getattr(payment, 'customer_id', None)
                
                if customer_id:
                    try:
                        cust_result = square_client.customers.get(customer_id=customer_id)
                        if cust_result and cust_result.customer:
                            c = cust_result.customer
                            given_name = getattr(c, 'given_name', '') or ''
                            family_name = getattr(c, 'family_name', '') or ''
                            customer_name = f"{given_name} {family_name}".strip()
                    except Exception:
                        pass
                
                if not customer_name:
                    skipped_no_match += 1
                    continue
                
                # Use fuzzy matching to find member
                matched_member, score, match_type = fuzzy_match_member(customer_name, members)
                
                if not matched_member:
                    skipped_no_match += 1
                    continue
                
                # Parse payment date
                payment_date = getattr(payment, 'created_at', None)
                if payment_date:
                    try:
                        if isinstance(payment_date, str):
                            payment_dt = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
                        else:
                            payment_dt = payment_date
                    except Exception:
                        payment_dt = datetime.now(timezone.utc)
                else:
                    payment_dt = datetime.now(timezone.utc)
                
                # Calculate months covered
                if total_amount >= 300 and total_amount <= 330:
                    num_months = 12
                else:
                    num_months = max(1, int(total_amount / MONTHLY_DUES_AMOUNT))
                
                # Mark dues as paid
                for month_offset in range(num_months):
                    target_month = payment_dt.month - 1 + month_offset
                    target_year = payment_dt.year
                    
                    while target_month >= 12:
                        target_month -= 12
                        target_year += 1
                    
                    payment_note = f"Paid via Square on {payment_dt.strftime('%Y-%m-%d')}"
                    if payment_id:
                        payment_note += f" (Trans: {payment_id[:12]}...)"
                    
                    await update_member_dues_with_payment_info(
                        member_id=matched_member["id"],
                        year=target_year,
                        month=target_month,
                        payment_note=payment_note,
                        payment_id=payment_id
                    )
                    months_marked_paid += 1
                
                # Mark as processed
                await db.synced_payment_links.update_one(
                    {"payment_id": payment_id},
                    {"$set": {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "member_id": matched_member["id"],
                        "member_handle": matched_member.get("handle"),
                        "customer_name": customer_name,
                        "amount": total_amount,
                        "months_covered": num_months,
                        "payment_date": payment_dt.isoformat(),
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                        "match_score": score,
                        "match_type": match_type
                    }},
                    upsert=True
                )
                
                synced_count += 1
                
            except Exception as e:
                errors.append(f"Failed to process payment {payment.id}: {str(e)}")
        
        return {
            "message": "Payment link sync complete",
            "payments_synced": synced_count,
            "months_marked_paid": months_marked_paid,
            "skipped_no_member_match": skipped_no_match,
            "skipped_not_dues": skipped_not_dues,
            "total_payments_checked": len(completed_payments),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error syncing payment links: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync payment links: {str(e)}")


@api_router.post("/dues/cleanup-duplicate-notes")
async def cleanup_duplicate_payment_notes(current_user: dict = Depends(verify_token)):
    """Clean up duplicate payment notes in officer_dues records.
    This fixes cases where the same transaction was recorded multiple times.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        # Get all officer_dues records with notes
        records = await db.officer_dues.find(
            {"notes": {"$exists": True, "$ne": ""}},
            {"_id": 0}
        ).to_list(10000)
        
        cleaned_count = 0
        
        for record in records:
            notes = record.get("notes", "")
            if not notes or "|" not in notes:
                continue
            
            # Split by | separator
            parts = notes.split("|")
            
            # Extract unique transaction IDs
            seen_trans = set()
            unique_parts = []
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Extract transaction ID if present
                trans_id = None
                if "(Trans:" in part:
                    try:
                        start = part.index("(Trans:") + 7
                        end = part.index("...", start)
                        trans_id = part[start:end].strip()
                    except:
                        pass
                
                # If we have a transaction ID, check for duplicates
                if trans_id:
                    if trans_id in seen_trans:
                        continue  # Skip duplicate
                    seen_trans.add(trans_id)
                
                unique_parts.append(part)
            
            # If we removed duplicates, update the record
            if len(unique_parts) < len(parts):
                new_notes = " | ".join(unique_parts)
                await db.officer_dues.update_one(
                    {"id": record.get("id")},
                    {"$set": {"notes": new_notes}}
                )
                cleaned_count += 1
        
        # Also clean up member dues records
        members = await db.members.find(
            {"dues": {"$exists": True}},
            {"_id": 0, "id": 1, "dues": 1}
        ).to_list(10000)
        
        member_cleaned = 0
        for member in members:
            member_id = member.get("id")
            dues = member.get("dues", {})
            updated = False
            
            for year_str, months in dues.items():
                if not isinstance(months, list):
                    continue
                
                for i, month_data in enumerate(months):
                    if not isinstance(month_data, dict):
                        continue
                    
                    note = month_data.get("note", "")
                    if not note or "|" not in note:
                        continue
                    
                    # Split and dedupe
                    parts = note.split("|")
                    seen_trans = set()
                    unique_parts = []
                    
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        
                        trans_id = None
                        if "(Trans:" in part:
                            try:
                                start = part.index("(Trans:") + 7
                                end = part.index("...", start)
                                trans_id = part[start:end].strip()
                            except:
                                pass
                        
                        if trans_id:
                            if trans_id in seen_trans:
                                continue
                            seen_trans.add(trans_id)
                        
                        unique_parts.append(part)
                    
                    if len(unique_parts) < len(parts):
                        dues[year_str][i]["note"] = " | ".join(unique_parts)
                        updated = True
            
            if updated:
                await db.members.update_one(
                    {"id": member_id},
                    {"$set": {"dues": dues}}
                )
                member_cleaned += 1
        
        return {
            "message": "Duplicate payment notes cleaned up",
            "officer_dues_cleaned": cleaned_count,
            "members_cleaned": member_cleaned
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up duplicate notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up duplicate notes: {str(e)}")


@api_router.post("/dues/reapply-payment-notes")
async def reapply_payment_notes(current_user: dict = Depends(verify_token)):
    """Re-apply Square payment notes from synced_payment_links to officer_dues.
    This fixes cases where a month was manually marked as paid before the Square sync ran.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        # Get all synced payment links
        synced_payments = await db.synced_payment_links.find({}, {"_id": 0}).to_list(10000)
        
        updated_count = 0
        errors = []
        
        for payment in synced_payments:
            try:
                member_id = payment.get("member_id")
                payment_date_str = payment.get("payment_date")
                payment_id = payment.get("payment_id")
                amount = payment.get("amount", 0)
                months_covered = payment.get("months_covered", 1)
                
                if not member_id or not payment_date_str:
                    continue
                
                # Parse payment date
                try:
                    payment_dt = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
                except:
                    continue
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                # Update each month covered by this payment
                for month_offset in range(months_covered):
                    target_month = payment_dt.month - 1 + month_offset
                    target_year = payment_dt.year
                    
                    while target_month >= 12:
                        target_month -= 12
                        target_year += 1
                    
                    month_str = f"{month_names[target_month]}_{target_year}"
                    payment_note = f"Paid via Square on {payment_dt.strftime('%Y-%m-%d')}"
                    if payment_id:
                        payment_note += f" (Trans: {payment_id[:12]}...)"
                    if amount:
                        payment_note += f" - ${amount:.2f}"
                    
                    # Find and update officer_dues record
                    existing = await db.officer_dues.find_one({
                        "member_id": member_id,
                        "month": month_str
                    })
                    
                    if existing:
                        existing_notes = existing.get("notes", "")
                        # Only update if Square payment info not already present
                        if payment_id and payment_id[:12] not in existing_notes:
                            new_notes = f"{existing_notes} | {payment_note}" if existing_notes and existing_notes.strip() else payment_note
                            await db.officer_dues.update_one(
                                {"id": existing.get("id")},
                                {"$set": {
                                    "notes": new_notes,
                                    "square_payment_id": payment_id,
                                    "updated_at": datetime.now(timezone.utc).isoformat()
                                }}
                            )
                            updated_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing payment {payment.get('payment_id', 'unknown')}: {str(e)}")
        
        return {
            "message": "Payment notes re-applied",
            "records_updated": updated_count,
            "total_synced_payments": len(synced_payments),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error re-applying payment notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to re-apply payment notes: {str(e)}")


@api_router.get("/dues/debug-recent-payments")
async def debug_recent_payments(current_user: dict = Depends(verify_token)):
    """Debug endpoint to see recent Square payments and their item names"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    try:
        # Get recent payments
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        
        payments_result = square_client.payments.list(
            begin_time=start_date,
            limit=50
        )
        
        all_payments = list(payments_result) if payments_result else []
        completed_payments = [p for p in all_payments if p.status == "COMPLETED"]
        
        debug_info = []
        
        for payment in completed_payments[:20]:  # Limit to 20 for debug
            payment_info = {
                "payment_id": payment.id,
                "amount": payment.amount_money.amount / 100 if payment.amount_money else 0,
                "created_at": str(payment.created_at),
                "customer_id": getattr(payment, 'customer_id', None),
                "order_id": getattr(payment, 'order_id', None),
                "items": []
            }
            
            # Get customer name
            if payment_info["customer_id"]:
                try:
                    cust_result = square_client.customers.get(customer_id=payment_info["customer_id"])
                    if cust_result and cust_result.customer:
                        c = cust_result.customer
                        payment_info["customer_name"] = f"{c.given_name or ''} {c.family_name or ''}".strip()
                except:
                    pass
            
            # Get order items
            if payment_info["order_id"]:
                try:
                    order_result = square_client.orders.get(order_id=payment_info["order_id"])
                    if order_result and order_result.order:
                        order = order_result.order
                        line_items = getattr(order, 'line_items', None) or []
                        for item in line_items:
                            payment_info["items"].append({
                                "name": getattr(item, 'name', 'Unknown'),
                                "amount": item.total_money.amount / 100 if item.total_money else 0
                            })
                except:
                    pass
            
            debug_info.append(payment_info)
        
        return {"payments": debug_info, "total_recent": len(completed_payments)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_member_dues_with_payment_info(member_id: str, year: int, month: int, payment_note: str, payment_id: str = None):
    """Update member dues status for a specific month based on actual payment"""
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    year_str = str(year)
    
    try:
        member = await db.members.find_one({"id": member_id})
        if not member:
            return
        
        dues = member.get("dues", {})
        
        # Initialize year if not exists
        if year_str not in dues:
            dues[year_str] = [{"status": "unpaid", "note": ""} for _ in range(12)]
        
        # Check current status
        current_status = None
        current_note = ""
        if isinstance(dues[year_str], list) and len(dues[year_str]) > month:
            if isinstance(dues[year_str][month], dict):
                current_status = dues[year_str][month].get("status")
                current_note = dues[year_str][month].get("note", "") or ""
            elif dues[year_str][month] == True:
                current_status = "paid"
        
        # Use first 12 chars of payment_id for duplicate detection (matches the note format)
        payment_id_short = payment_id[:12] if payment_id else None
        
        # Update to paid - even if already paid, we want to add the Square payment info
        should_update_member = False
        if current_status != "paid":
            # Not yet paid - do full update
            dues[year_str][month] = {
                "status": "paid",
                "note": payment_note
            }
            should_update_member = True
        elif payment_id_short and payment_id_short not in current_note:
            # Already paid but we have new Square payment info to add
            new_note = f"{current_note} | {payment_note}" if current_note else payment_note
            dues[year_str][month] = {
                "status": "paid",
                "note": new_note
            }
            should_update_member = True
        # If payment_id is already in the note, skip (duplicate)
        
        if should_update_member:
            # Update member record - also clear any dues suspension
            await db.members.update_one(
                {"id": member_id},
                {"$set": {
                    "dues": dues,
                    "dues_suspended": False,
                    "dues_suspended_at": None,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Restore Discord permissions if they were suspended
            await restore_discord_member(member_id)
        
        # Also update officer_dues collection (for A & D page sync)
        month_str = f"{month_names[month]}_{year_str}"
        existing = await db.officer_dues.find_one({
            "member_id": member_id,
            "month": month_str
        })
        
        if existing:
            # Check for duplicate payment before updating
            existing_notes = existing.get("notes", "") or ""
            existing_payment_id = existing.get("square_payment_id", "") or ""
            
            # Skip if this payment is already recorded (check both full ID and short ID)
            if payment_id and (payment_id == existing_payment_id or (payment_id_short and payment_id_short in existing_notes)):
                # Already have this payment recorded, skip
                return
            
            should_update = False
            new_notes = payment_note
            
            if existing.get("status") != "paid":
                # Not yet paid - do full update
                should_update = True
            elif payment_id_short and payment_id_short not in existing_notes:
                # Already paid but we have new Square payment info to add
                new_notes = f"{existing_notes} | {payment_note}" if existing_notes else payment_note
                should_update = True
            
            if should_update:
                await db.officer_dues.update_one(
                    {"id": existing.get("id")},
                    {"$set": {
                        "status": "paid",
                        "notes": new_notes,
                        "square_payment_id": payment_id,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "updated_by": "square_sync"
                    }}
                )
        else:
            # Create new record
            dues_record = {
                "id": str(uuid.uuid4()),
                "member_id": member_id,
                "month": month_str,
                "status": "paid",
                "notes": payment_note,
                "square_payment_id": payment_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "square_sync"
            }
            await db.officer_dues.insert_one(dues_record)
        
        logger.info(f"Member {member_id} dues updated for {month_names[month]} {year_str} via sync")
        
    except Exception as e:
        logger.error(f"Error updating member dues: {str(e)}")


class LinkSubscriptionRequest(BaseModel):
    member_id: str
    square_customer_id: str


@api_router.post("/dues/link-subscription")
async def link_member_to_subscription(
    request: LinkSubscriptionRequest,
    current_user: dict = Depends(verify_token)
):
    """Manually link a member to a Square customer for subscription tracking"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can link subscriptions")
    
    member = await db.members.find_one({"id": request.member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    await db.member_subscriptions.update_one(
        {"square_customer_id": request.square_customer_id},
        {"$set": {
            "member_id": request.member_id,
            "member_handle": member.get("handle"),
            "square_customer_id": request.square_customer_id,
            "linked_by": current_user.get("username"),
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "link_type": "manual"
        }},
        upsert=True
    )
    
    return {"message": f"Member {member.get('handle')} linked to Square customer", "success": True}


@api_router.delete("/dues/link-subscription/{customer_id}")
async def unlink_subscription(
    customer_id: str,
    current_user: dict = Depends(verify_token)
):
    """Remove a manual subscription link"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can unlink subscriptions")
    
    result = await db.member_subscriptions.delete_one({"square_customer_id": customer_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {"message": "Subscription link removed", "success": True}


@api_router.delete("/dues/cancel-square-subscription/{subscription_id}")
async def cancel_square_subscription(
    subscription_id: str,
    current_user: dict = Depends(verify_token)
):
    """Cancel a Square subscription directly (for unmatched/orphaned subscriptions)"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can cancel subscriptions")
    
    if not square_client:
        raise HTTPException(status_code=500, detail="Square client not configured")
    
    try:
        # Get subscription details first to find customer info
        sub_result = square_client.subscriptions.get(subscription_id=subscription_id)
        
        if not sub_result.subscription:
            raise HTTPException(status_code=404, detail="Subscription not found in Square")
        
        subscription = sub_result.subscription
        customer_id = subscription.customer_id
        
        # Check if subscription is already cancelled
        if subscription.status == "CANCELED":
            # Just clean up our local link if any
            await db.member_subscriptions.delete_one({"square_customer_id": customer_id})
            return {
                "message": "Subscription was already cancelled",
                "subscription_id": subscription_id,
                "status": "CANCELED",
                "success": True
            }
        
        # Cancel the subscription
        cancel_result = square_client.subscriptions.cancel(
            subscription_id=subscription_id
        )
        
        if cancel_result.subscription:
            # Clean up any local subscription link
            await db.member_subscriptions.delete_one({"square_customer_id": customer_id})
            
            logger.info(f"Cancelled Square subscription {subscription_id} by {current_user.get('username')}")
            
            return {
                "message": "Square subscription cancelled successfully",
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "canceled_date": cancel_result.subscription.canceled_date,
                "success": True
            }
        else:
            errors = cancel_result.errors if cancel_result.errors else "Unknown error"
            raise HTTPException(status_code=400, detail=f"Failed to cancel subscription: {errors}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling Square subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling subscription: {str(e)}")


@api_router.get("/dues/all-members-for-linking")
async def get_members_for_linking(current_user: dict = Depends(verify_token)):
    """Get all members for the subscription linking dropdown"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can access this")
    
    members = await db.members.find({}, {"_id": 0, "id": 1, "name": 1, "handle": 1, "chapter": 1}).to_list(1000)
    return members


# ==================== DUES PAYMENT MANAGEMENT ENDPOINTS ====================

@api_router.get("/dues/unmatched-payments")
async def get_unmatched_payments(current_user: dict = Depends(verify_token)):
    """Get unmatched Square payments for manual review (SEC, NVP, NPrez, or admin)"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can view unmatched payments")
    
    payments = await db.unmatched_payments.find(
        {"status": "unmatched"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return payments


@api_router.get("/dues/matched-payments")
async def get_matched_payments(current_user: dict = Depends(verify_token)):
    """Get external payments that were auto-matched to members"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can view matched payments")
    
    payments = await db.external_dues_payments.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return payments


@api_router.post("/dues/match-payment")
async def match_payment_to_member(
    payment_id: str,
    member_id: str,
    year: int,
    month: int,
    current_user: dict = Depends(verify_token)
):
    """Manually match an unmatched payment to a member"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can match payments")
    
    # Find the unmatched payment
    payment = await db.unmatched_payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Find the member
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Update dues
    dues_info = {
        "member_id": member_id,
        "year": year,
        "month": month
    }
    await update_member_dues_from_webhook(dues_info)
    
    # Move payment to matched
    matched_record = {
        "id": str(uuid.uuid4()),
        "square_payment_id": payment.get("square_payment_id"),
        "customer_name": payment.get("customer_name"),
        "member_id": member_id,
        "member_handle": member.get("handle"),
        "amount": payment.get("amount"),
        "year": str(year),
        "month": month,
        "month_name": month_names[month],
        "match_score": 100,
        "matched_by": current_user.get("username"),
        "created_at": payment.get("created_at"),
        "matched_at": datetime.now(timezone.utc).isoformat(),
        "source": "manual_match"
    }
    await db.external_dues_payments.insert_one(matched_record)
    
    # Mark original as matched
    await db.unmatched_payments.update_one(
        {"id": payment_id},
        {"$set": {"status": "matched", "matched_to": member_id, "matched_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Payment matched to {member.get('handle')} for {month_names[month]} {year}"}


@api_router.delete("/dues/unmatched-payments/{payment_id}")
async def dismiss_unmatched_payment(payment_id: str, current_user: dict = Depends(verify_token)):
    """Dismiss/ignore an unmatched payment (not a dues payment)"""
    if not is_secretary(current_user) and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only Secretaries can dismiss payments")
    
    result = await db.unmatched_payments.update_one(
        {"id": payment_id},
        {"$set": {"status": "dismissed", "dismissed_by": current_user.get("username"), "dismissed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {"message": "Payment dismissed"}


# ==================== STORE ADMIN MANAGEMENT ENDPOINTS ====================

@api_router.get("/store/admins/status")
async def get_store_admin_status(current_user: dict = Depends(verify_token)):
    """Get current user's store admin status"""
    is_primary = is_primary_store_admin(current_user)
    is_delegated = False
    
    if not is_primary:
        # Check if delegated admin
        delegated = await db.store_admins.find_one({"username": current_user.get("username", "")})
        is_delegated = delegated is not None
    
    return {
        "can_manage_store": is_primary or is_delegated,
        "is_primary_admin": is_primary,
        "is_delegated_admin": is_delegated,
        "can_manage_admins": is_primary  # Only primary admins can manage the admin list
    }

@api_router.get("/store/admins")
async def get_store_admins(current_user: dict = Depends(verify_token)):
    """Get list of store admins (Primary admins only)"""
    # Only primary admins can view/manage store admin list
    if not is_primary_store_admin(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can manage store admins")
    
    # Get all delegated store admins
    delegated_admins = await db.store_admins.find({}, {"_id": 0}).to_list(100)
    
    # Get user info for each delegated admin
    admin_list = []
    for admin in delegated_admins:
        user = await db.users.find_one({"username": admin["username"]}, {"_id": 0, "password_hash": 0})
        if user:
            admin_list.append({
                "id": admin["id"],
                "username": admin["username"],
                "granted_by": admin["granted_by"],
                "created_at": admin["created_at"],
                "user_info": {
                    "title": user.get("title", ""),
                    "chapter": user.get("chapter", ""),
                    "role": user.get("role", "")
                }
            })
    
    return admin_list

@api_router.get("/store/admins/eligible")
async def get_eligible_store_admins(current_user: dict = Depends(verify_token)):
    """Get list of National users who can be granted store admin access (Primary admins only)"""
    if not is_primary_store_admin(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can manage store admins")
    
    # Get all current store admins usernames
    current_admins = await db.store_admins.find({}, {"username": 1}).to_list(100)
    current_admin_usernames = {a["username"] for a in current_admins}
    
    # Primary admin titles - these users don't need to be added (they already have access)
    primary_titles = ["Prez", "VP", "SEC"]
    
    # Get all National chapter admins who are not already delegated admins and not primary admins
    users = await db.users.find(
        {"role": "admin", "chapter": "National"},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    eligible = []
    for user in users:
        # Skip if already a delegated admin
        if user["username"] in current_admin_usernames:
            continue
        # Skip if a primary admin (they already have access)
        if user.get("title", "") in primary_titles:
            continue
        eligible.append({
            "username": user["username"],
            "title": user.get("title", ""),
            "chapter": user.get("chapter", "")
        })
    
    return eligible

@api_router.post("/store/admins")
async def add_store_admin(admin_data: StoreAdminCreate, current_user: dict = Depends(verify_token)):
    """Grant store admin access to a user (Primary admins only)"""
    if not is_primary_store_admin(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can grant store admin access")
    
    # Verify the user exists and is a National admin
    user = await db.users.find_one({"username": admin_data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("role") != "admin" or user.get("chapter") != "National":
        raise HTTPException(status_code=400, detail="Only National chapter admins can be granted store access")
    
    # Check if already a store admin
    existing = await db.store_admins.find_one({"username": admin_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="User is already a store admin")
    
    # Check if they're a primary admin (don't need to add them)
    primary_titles = ["Prez", "VP", "SEC"]
    if user.get("title", "") in primary_titles:
        raise HTTPException(status_code=400, detail="This user already has store access as a primary admin")
    
    # Create the store admin record
    store_admin = StoreAdmin(
        username=admin_data.username,
        granted_by=current_user["username"]
    )
    
    doc = store_admin.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.store_admins.insert_one(doc)
    
    await log_activity(
        current_user["username"],
        "grant_store_admin",
        f"Granted store admin access to {admin_data.username}"
    )
    
    return {"message": f"Store admin access granted to {admin_data.username}", "id": store_admin.id}

@api_router.delete("/store/admins/{admin_id}")
async def remove_store_admin(admin_id: str, current_user: dict = Depends(verify_token)):
    """Remove store admin access from a user (Primary admins only)"""
    if not is_primary_store_admin(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can remove store admin access")
    
    # Find and delete the store admin
    admin = await db.store_admins.find_one({"id": admin_id})
    if not admin:
        raise HTTPException(status_code=404, detail="Store admin not found")
    
    await db.store_admins.delete_one({"id": admin_id})
    
    await log_activity(
        current_user["username"],
        "revoke_store_admin",
        f"Revoked store admin access from {admin['username']}"
    )
    
    return {"message": f"Store admin access revoked from {admin['username']}"}

# ==================== END STORE ADMIN MANAGEMENT ENDPOINTS ====================

# ==================== STORE SETTINGS ENDPOINTS ====================

@api_router.get("/store/settings")
async def get_store_settings(current_user: dict = Depends(verify_token)):
    """Get store settings - check if stores are open or closed"""
    settings = await db.store_settings.find_one({"id": "store_status"}, {"_id": 0})
    
    if not settings:
        # Default settings - both stores open
        settings = {
            "id": "store_status",
            "supporter_store_open": True,
            "member_store_open": True,
            "supporter_store_message": "Under Construction - Check back soon!",
            "member_store_message": "Under Construction - Check back soon!"
        }
    
    # Check if user can bypass store closure (National Prez, VP, SEC)
    can_bypass = is_primary_store_admin(current_user)
    
    return {
        **settings,
        "can_bypass": can_bypass
    }

@api_router.get("/store/settings/public")
async def get_store_settings_public():
    """Public endpoint to get store settings - for login page and supporter store"""
    settings = await db.store_settings.find_one({"id": "store_status"}, {"_id": 0})
    
    if not settings:
        # Default settings - both stores open
        settings = {
            "supporter_store_open": True,
            "member_store_open": True,
            "supporter_store_message": "Under Construction - Check back soon!",
            "member_store_message": "Under Construction - Check back soon!"
        }
    
    return {
        "supporter_store_open": settings.get("supporter_store_open", True),
        "member_store_open": settings.get("member_store_open", True),
        "supporter_store_message": settings.get("supporter_store_message", "Under Construction - Check back soon!"),
        "member_store_message": settings.get("member_store_message", "Under Construction - Check back soon!")
    }

@api_router.get("/stats/experience")
async def get_total_experience():
    """Public endpoint to get total years of trucking experience across all members"""
    members = await db.members.find({}, {"experience_start": 1, "_id": 0}).to_list(10000)
    
    total_years = 0.0
    members_with_experience = 0
    now = datetime.now(timezone.utc)
    
    for member in members:
        exp_start = member.get("experience_start")
        if exp_start:
            try:
                # Parse MM/YYYY format
                parts = exp_start.split("/")
                if len(parts) == 2:
                    month = int(parts[0])
                    year = int(parts[1])
                    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
                    years = (now - start_date).days / 365.25
                    if years > 0:
                        total_years += years
                        members_with_experience += 1
            except (ValueError, IndexError):
                continue
    
    return {
        "total_years": round(total_years, 1),
        "total_years_formatted": f"{int(total_years):,}",
        "members_with_experience": members_with_experience
    }

@api_router.put("/store/settings")
async def update_store_settings(
    supporter_store_open: bool = None,
    member_store_open: bool = None,
    supporter_store_message: str = None,
    member_store_message: str = None,
    current_user: dict = Depends(verify_token)
):
    """Update store settings - only National Prez, VP, SEC can update"""
    if not is_primary_store_admin(current_user):
        raise HTTPException(status_code=403, detail="Only National Prez, VP, or SEC can update store settings")
    
    # Get current settings (exclude _id)
    settings = await db.store_settings.find_one({"id": "store_status"}, {"_id": 0})
    
    if not settings:
        settings = {
            "id": "store_status",
            "supporter_store_open": True,
            "member_store_open": True,
            "supporter_store_message": "Under Construction - Check back soon!",
            "member_store_message": "Under Construction - Check back soon!"
        }
    
    # Update only provided fields
    if supporter_store_open is not None:
        settings["supporter_store_open"] = supporter_store_open
    if member_store_open is not None:
        settings["member_store_open"] = member_store_open
    if supporter_store_message is not None:
        settings["supporter_store_message"] = supporter_store_message
    if member_store_message is not None:
        settings["member_store_message"] = member_store_message
    
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    settings["updated_by"] = current_user.get("username", "unknown")
    
    # Upsert the settings
    await db.store_settings.update_one(
        {"id": "store_status"},
        {"$set": settings},
        upsert=True
    )
    
    # Log the activity
    changes = []
    if supporter_store_open is not None:
        changes.append(f"Supporter Store: {'Open' if supporter_store_open else 'Closed'}")
    if member_store_open is not None:
        changes.append(f"Member Store: {'Open' if member_store_open else 'Closed'}")
    
    await log_activity(
        current_user["username"],
        "update_store_settings",
        f"Updated store settings: {', '.join(changes)}"
    )
    
    return {"message": "Store settings updated", "settings": settings}

# ==================== END STORE SETTINGS ENDPOINTS ====================

# ==================== AUTO-SYNC ON LOGIN ====================

async def trigger_catalog_sync_background():
    """Background task to sync Square catalog"""
    try:
        if not square_client:
            logger.warning("Square client not configured, skipping auto-sync")
            return
        
        # Fetch catalog items from Square
        result = square_client.catalog.list(types="ITEM")
        items = list(result)
        
        if not items:
            logger.info("No items found in Square catalog during auto-sync")
            return
        
        # Collect all variation IDs for inventory fetch
        all_variation_ids = []
        for item in items:
            item_data = item.item_data
            if not item_data:
                continue
            for var in (item_data.variations or []):
                all_variation_ids.append(var.id)
        
        # Fetch inventory counts
        inventory_map = {}
        if all_variation_ids:
            try:
                inv_result = square_client.inventory.batch_get_counts(
                    catalog_object_ids=all_variation_ids,
                    location_ids=[SQUARE_LOCATION_ID]
                )
                inv_items = list(inv_result)
                for count in inv_items:
                    qty = int(count.quantity) if count.quantity else 0
                    inventory_map[count.catalog_object_id] = qty
            except Exception as inv_e:
                logger.warning(f"Could not fetch inventory during auto-sync: {inv_e}")
        
        synced_count = 0
        new_count = 0
        
        for item in items:
            item_data = item.item_data
            if not item_data:
                continue
            
            item_id = item.id
            name = item_data.name or "Unknown"
            description = item_data.description or ""
            
            # Get ecom image URLs
            image_url = None
            if item_data.ecom_image_uris and len(item_data.ecom_image_uris) > 0:
                image_url = item_data.ecom_image_uris[0]
            
            variations_list = item_data.variations or []
            if not variations_list:
                continue
            
            # Build variations data
            product_variations = []
            total_inventory = 0
            min_price = float('inf')
            has_size_variations = False
            
            name_lower = name.lower()
            is_apparel = any(word in name_lower for word in ['shirt', 'hoodie', 'tee', 'jersey', 'long sleeve'])
            is_excluded = (
                'hi-viz' in name_lower or 
                'hiviz' in name_lower or
                'hi viz' in name_lower or
                'ladiez' in name_lower or
                ('member long sleeve' in name_lower and 'original logo design' in name_lower)
            )
            allows_customization = is_apparel and not is_excluded
            
            for var in variations_list:
                var_data = var.item_variation_data
                if not var_data:
                    continue
                
                price_money = var_data.price_money
                if not price_money:
                    continue
                
                price = price_money.amount / 100
                if price <= 0:
                    continue
                
                if price < min_price:
                    min_price = price
                
                var_name = var_data.name or "Default"
                var_id = var.id
                inv_count = inventory_map.get(var_id, 0)
                total_inventory += inv_count
                
                sold_out = inv_count == 0
                if var_data.location_overrides:
                    for lo in var_data.location_overrides:
                        if lo.sold_out:
                            sold_out = True
                            break
                
                size_indicators = ['S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', 'XS', 'XXL', 'LT', 'XLT', '2XLT', '3XLT']
                if var_name.upper() in size_indicators or any(s in var_name.upper() for s in size_indicators):
                    has_size_variations = True
                
                product_variations.append({
                    "id": str(uuid.uuid4()),
                    "name": var_name,
                    "price": price,
                    "square_variation_id": var_id,
                    "inventory_count": inv_count,
                    "sold_out": sold_out
                })
            
            if min_price == float('inf'):
                continue
            
            # Sort variations by size order
            size_order = {'XS': 0, 'S': 1, 'M': 2, 'L': 3, 'LT': 4, 'XL': 5, 'XLT': 6, '2XL': 7, '2XLT': 8, '3XL': 9, '3XLT': 10, '4XL': 11, '5XL': 12, 'Regular': 0}
            product_variations.sort(key=lambda x: size_order.get(x['name'], 99))
            
            # Check if product already exists
            existing = await db.store_products.find_one({"square_catalog_id": item_id})
            
            product_data = {
                "name": name,
                "description": description[:500] if description else "",
                "price": min_price,
                "image_url": image_url,
                "variations": product_variations,
                "has_variations": len(product_variations) > 1 or has_size_variations,
                "allows_customization": allows_customization,
                "inventory_count": total_inventory,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                # Update existing - preserve admin-controlled settings
                await db.store_products.update_one(
                    {"square_catalog_id": item_id},
                    {"$set": product_data}
                )
            else:
                # New product - default to NOT showing in supporter store
                product_data.update({
                    "id": str(uuid.uuid4()),
                    "category": "merchandise",
                    "square_catalog_id": item_id,
                    "is_active": True,
                    "show_in_supporter_store": False,  # NEW items default to hidden from supporter store
                    "allows_customization": False,  # Default FALSE, admin must enable
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                await db.store_products.insert_one(product_data)
                new_count += 1
                logger.info(f"Auto-sync: New product added: {name} (hidden from supporter store)")
            
            synced_count += 1
        
        logger.info(f"Auto-sync completed: {synced_count} products synced, {new_count} new products added")
    
    except Exception as e:
        logger.error(f"Auto-sync error: {str(e)}")

# ==================== END AUTO-SYNC ====================

# ==================== END STORE API ENDPOINTS ====================


# ==================== FORMS MANAGEMENT ENDPOINTS ====================

FORMS_UPLOAD_DIR = Path("/app/uploads/forms")
FORMS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@api_router.get("/forms")
async def get_forms(current_user: dict = Depends(verify_token)):
    """Get all available forms"""
    forms = await db.forms.find({}, {"_id": 0}).sort("uploaded_at", -1).to_list(100)
    return {"forms": forms}


@api_router.post("/forms/upload")
async def upload_form(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    current_user: dict = Depends(verify_token)
):
    """Upload a new form (admin or users with manage_forms permission)"""
    has_access = await check_permission(current_user, "manage_forms")
    if not has_access and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="You don't have permission to upload forms")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size (10MB max)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
    
    # Generate unique filename
    import uuid
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.png', '.jpg', '.jpeg', '.gif', '.webp']
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = FORMS_UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create form record
    form_id = str(uuid.uuid4())
    form_record = {
        "id": form_id,
        "name": name or file.filename,
        "description": description or "",
        "filename": file.filename,
        "stored_filename": unique_filename,
        "file_size": len(file_content),
        "file_type": file_ext,
        "uploaded_by": current_user.get("username"),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.forms.insert_one(form_record)
    
    return {"success": True, "message": "Form uploaded successfully", "form_id": form_id}


@api_router.get("/forms/{form_id}/download")
async def download_form(form_id: str, current_user: dict = Depends(verify_token)):
    """Download a form"""
    form = await db.forms.find_one({"id": form_id}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    file_path = FORMS_UPLOAD_DIR / form.get("stored_filename", "")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Form file not found")
    
    # Determine content type
    content_types = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    file_ext = form.get("file_type", "").lower()
    content_type = content_types.get(file_ext, 'application/octet-stream')
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=form.get("filename", "download"),
        media_type=content_type
    )


@api_router.delete("/forms/{form_id}")
async def delete_form(form_id: str, current_user: dict = Depends(verify_token)):
    """Delete a form (admin or users with manage_forms permission)"""
    has_access = await check_permission(current_user, "manage_forms")
    if not has_access and current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="You don't have permission to delete forms")
    
    form = await db.forms.find_one({"id": form_id}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Delete file
    file_path = FORMS_UPLOAD_DIR / form.get("stored_filename", "")
    if file_path.exists():
        file_path.unlink()
    
    # Delete record
    await db.forms.delete_one({"id": form_id})
    
    return {"success": True, "message": "Form deleted successfully"}

# ==================== END FORMS ENDPOINTS ====================


# ==================== DISCORD PROMOTION ENDPOINTS ====================

class UpdateRolesRequest(BaseModel):
    role_ids: List[str]


class UpdateNicknameRequest(BaseModel):
    nickname: str


@api_router.get("/discord/roles")
async def get_discord_roles(current_user: dict = Depends(verify_token)):
    """Get all Discord roles from the server"""
    global discord_bot
    
    sys.stderr.write(f"[PROMO] /discord/roles called - bot={discord_bot is not None}, guild_id={DISCORD_GUILD_ID}\n")
    sys.stderr.flush()
    
    if not discord_bot or not DISCORD_GUILD_ID:
        sys.stderr.write(f"[PROMO] Discord not configured - returning empty\n")
        sys.stderr.flush()
        return {"roles": [], "message": "Discord bot not configured"}
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        sys.stderr.write(f"[PROMO] Guild lookup result: {guild is not None}\n")
        sys.stderr.flush()
        
        if not guild:
            return {"roles": [], "message": "Guild not found"}
        
        roles = []
        for role in guild.roles:
            if role.name != "@everyone" and not role.is_bot_managed():
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "color": f"#{role.color.value:06x}" if role.color.value else None,
                    "position": role.position,
                    "permissions": str(role.permissions.value)
                })
        
        sys.stderr.write(f"[PROMO] Returning {len(roles)} roles\n")
        sys.stderr.flush()
        return {"roles": roles}
    except Exception as e:
        sys.stderr.write(f"[PROMO] Error: {e}\n")
        sys.stderr.flush()
        return {"roles": [], "message": str(e)}


@api_router.get("/discord/member/{member_id}/roles")
async def get_member_discord_roles(member_id: str, current_user: dict = Depends(verify_token)):
    """Get a member's current Discord roles"""
    global discord_bot
    
    if not discord_bot or not DISCORD_GUILD_ID:
        return {"roles": [], "nickname": None, "message": "Discord bot not configured"}
    
    # Get member from database
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_handle = member.get("handle", "")
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            return {"roles": [], "nickname": None, "message": "Guild not found"}
        
        # Find Discord member by handle
        discord_member = None
        for dm in guild.members:
            display_name = dm.nick or dm.display_name or dm.name
            if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                discord_member = dm
                break
        
        if not discord_member:
            return {"roles": [], "nickname": None, "message": f"Member '{member_handle}' not found in Discord"}
        
        roles = []
        for role in discord_member.roles:
            if role.name != "@everyone":
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "color": f"#{role.color.value:06x}" if role.color.value else None,
                    "position": role.position
                })
        
        return {
            "roles": roles,
            "nickname": discord_member.nick or discord_member.display_name,
            "discord_id": str(discord_member.id)
        }
    except Exception as e:
        return {"roles": [], "nickname": None, "message": str(e)}


@api_router.post("/discord/member/{member_id}/roles")
async def update_member_discord_roles(
    member_id: str, 
    request: UpdateRolesRequest,
    current_user: dict = Depends(verify_token)
):
    """Update a member's Discord roles"""
    global discord_bot
    
    if not discord_bot or not DISCORD_GUILD_ID:
        raise HTTPException(status_code=503, detail="Discord bot not configured")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_handle = member.get("handle", "")
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        # Find Discord member by handle
        discord_member = None
        for dm in guild.members:
            display_name = dm.nick or dm.display_name or dm.name
            if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                discord_member = dm
                break
        
        if not discord_member:
            raise HTTPException(status_code=404, detail=f"Member '{member_handle}' not found in Discord")
        
        # Get current roles and requested roles
        current_role_ids = {str(r.id) for r in discord_member.roles if r.name != "@everyone"}
        requested_role_ids = set(request.role_ids)
        
        # Roles to add and remove
        roles_to_add = requested_role_ids - current_role_ids
        roles_to_remove = current_role_ids - requested_role_ids
        
        added = 0
        removed = 0
        
        # Add new roles
        for role_id in roles_to_add:
            role = guild.get_role(int(role_id))
            if role:
                await discord_member.add_roles(role, reason=f"Promotion by {current_user.get('username')}")
                added += 1
        
        # Remove old roles
        for role_id in roles_to_remove:
            role = guild.get_role(int(role_id))
            if role and not role.is_bot_managed():
                await discord_member.remove_roles(role, reason=f"Role update by {current_user.get('username')}")
                removed += 1
        
        return {"success": True, "message": f"Updated roles: {added} added, {removed} removed", "added": added, "removed": removed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/discord/member/{member_id}/nickname")
async def update_member_discord_nickname(
    member_id: str,
    request: UpdateNicknameRequest,
    current_user: dict = Depends(verify_token)
):
    """Update a member's Discord nickname"""
    global discord_bot
    
    sys.stderr.write(f"[PROMO] /discord/member/{member_id}/nickname called\n")
    sys.stderr.flush()
    
    if not discord_bot or not DISCORD_GUILD_ID:
        sys.stderr.write(f"[PROMO] Discord not configured - bot={discord_bot is not None}, guild_id={DISCORD_GUILD_ID}\n")
        sys.stderr.flush()
        raise HTTPException(status_code=503, detail="Discord bot not configured")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_handle = member.get("handle", "")
    sys.stderr.write(f"[PROMO] Looking up Discord member for: {member_handle}\n")
    sys.stderr.flush()
    
    try:
        guild = discord_bot.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")
        
        # Find Discord member by handle
        discord_member = None
        for dm in guild.members:
            display_name = dm.nick or dm.display_name or dm.name
            if display_name.lower() == member_handle.lower() or member_handle.lower() in display_name.lower():
                discord_member = dm
                break
        
        if not discord_member:
            raise HTTPException(status_code=404, detail=f"Member '{member_handle}' not found in Discord")
        
        sys.stderr.write(f"[PROMO] Found Discord member, updating nickname to: {request.nickname}\n")
        sys.stderr.flush()
        
        await discord_member.edit(nick=request.nickname, reason=f"Nickname update by {current_user.get('username')}")
        
        sys.stderr.write(f"[PROMO] Nickname updated successfully\n")
        sys.stderr.flush()
        
        return {"success": True, "message": f"Nickname updated to '{request.nickname}'"}
    except HTTPException:
        raise
    except Exception as e:
        sys.stderr.write(f"[PROMO] Error updating nickname: {e}\n")
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END DISCORD PROMOTION ENDPOINTS ====================


# Include the router in the main app
app.include_router(api_router)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Get allowed origins from environment variable
cors_origins_str = os.environ.get('CORS_ORIGINS', '')
cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

# If no origins specified or only '*', use a restrictive default
if not cors_origins or cors_origins == ['*']:
    cors_origins = [
        "https://member-manager-26.preview.emergentagent.com",
        "https://boh-tracker.emergent.host",
        "https://www.bohhub.com",
        "https://bohhub.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop scheduler if it's running
    global scheduler
    if scheduler and scheduler.running:
        try:
            scheduler.shutdown()
            print("✅ [SCHEDULER] Discord event notification scheduler stopped", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"⚠️ [SCHEDULER] Error stopping scheduler: {str(e)}", file=sys.stderr, flush=True)
    
    # Close MongoDB client
    client.close()


sys.stderr.write("✅ [INIT] Server module fully loaded and ready\n")
sys.stderr.flush()

