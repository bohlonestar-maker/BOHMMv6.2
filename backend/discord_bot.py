import discord
import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend path for imports
sys.path.append('/app/backend')

# Discord Bot for Analytics (Simplified - No Recording)
class DiscordActivityBot(discord.Client):
    def __init__(self):
        # Set intents for member access
        intents = discord.Intents.default()
        intents.members = True
        
        super().__init__(intents=intents)
        
        # MongoDB connection
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client[db_name]
        
    async def on_ready(self):
        """Bot is ready and connected to Discord"""
        print(f'✅ Discord Analytics Bot logged in as {self.user}')
        print(f'   Connected to {len(self.guilds)} guild(s)')
        for guild in self.guilds:
            print(f'   - {guild.name} ({guild.id}) - {guild.member_count} members')

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
