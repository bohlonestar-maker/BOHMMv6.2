import discord
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend path for imports
sys.path.append('/app/backend')

# Discord Analytics Bot with Voice and Text Tracking
class DiscordActivityBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.voice_sessions = {}
        
        # MongoDB connection
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client[db_name]
        
    async def on_ready(self):
        print(f'✅ Discord Analytics Bot logged in as {self.user}')
        print(f'   Connected to {len(self.guilds)} guild(s)')
        for guild in self.guilds:
            print(f'   - {guild.name} ({guild.id}) - {guild.member_count} members')

    async def on_voice_state_update(self, member, before, after):
        """Track voice channel activity"""
        if member.bot:
            return
            
        user_id = str(member.id)
        now = datetime.now(timezone.utc)
        
        try:
            # User joined voice channel
            if before.channel is None and after.channel is not None:
                self.voice_sessions[user_id] = {
                    'joined_at': now,
                    'channel_id': str(after.channel.id),
                    'channel_name': after.channel.name
                }
                print(f"🎤 {member.display_name} joined {after.channel.name}")
                
            # User left voice channel
            elif before.channel is not None and after.channel is None:
                if user_id in self.voice_sessions:
                    session = self.voice_sessions[user_id]
                    duration = (now - session['joined_at']).total_seconds()
                    
                    voice_activity = {
                        'id': str(uuid.uuid4()),
                        'discord_user_id': user_id,
                        'channel_id': session['channel_id'],
                        'channel_name': session['channel_name'],
                        'joined_at': session['joined_at'],
                        'left_at': now,
                        'duration_seconds': int(duration),
                        'date': now.date().isoformat()
                    }
                    
                    await self.db.discord_voice_activity.insert_one(voice_activity)
                    print(f"💾 Saved {member.display_name} voice session: {duration/60:.1f} min")
                    del self.voice_sessions[user_id]
                    
            # User moved between channels
            elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                if user_id in self.voice_sessions:
                    session = self.voice_sessions[user_id]
                    duration = (now - session['joined_at']).total_seconds()
                    
                    voice_activity = {
                        'id': str(uuid.uuid4()),
                        'discord_user_id': user_id,
                        'channel_id': session['channel_id'],
                        'channel_name': session['channel_name'],
                        'joined_at': session['joined_at'],
                        'left_at': now,
                        'duration_seconds': int(duration),
                        'date': now.date().isoformat()
                    }
                    
                    await self.db.discord_voice_activity.insert_one(voice_activity)
                
                # Start new session
                self.voice_sessions[user_id] = {
                    'joined_at': now,
                    'channel_id': str(after.channel.id),
                    'channel_name': after.channel.name
                }
                print(f"🎤 {member.display_name} moved to {after.channel.name}")
        
        except Exception as e:
            print(f"❌ Voice tracking error: {str(e)}")
                    
    async def on_message(self, message):
        """Track text message activity"""
        if message.author.bot or not message.guild:
            return
            
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        channel_name = message.channel.name
        today = datetime.now(timezone.utc).date().isoformat()
        
        try:
            # Check existing record for today
            existing_record = await self.db.discord_text_activity.find_one({
                'discord_user_id': user_id,
                'channel_id': channel_id,
                'date': today
            })
            
            if existing_record:
                await self.db.discord_text_activity.update_one(
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
                await self.db.discord_text_activity.insert_one(text_activity)
        
        except Exception as e:
            print(f"❌ Text tracking error: {str(e)}")

# Run the Discord bot
async def run_discord_bot():
    """Run the Discord analytics bot"""
    try:
        print("🚀 Starting Discord Analytics Bot...")
        
        token = os.environ.get('DISCORD_BOT_TOKEN')
        if not token:
            print("❌ DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        bot = DiscordActivityBot()
        await bot.start(token)
        
    except Exception as e:
        print(f"❌ Error starting Discord bot: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('/app/backend/.env')
    
    # Run the bot
    asyncio.run(run_discord_bot())
