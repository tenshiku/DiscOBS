#!/usr/bin/env python3
"""
DiscOBS - Discord OBS Control Bot
Main entry point for the bot
"""

import discord
from discord.ext import commands
import asyncio
import logging
import sys
import os

# Add modules directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import configuration
try:
    from config import DISCORD_TOKEN, OBS_HOST, OBS_PORT, OBS_PASSWORD
    from modules_config import ENABLED_MODULES
except ImportError as e:
    print(f"❌ ERROR: Configuration file not found!")
    print(f"Missing: {e}")
    print("Please make sure config.py and modules_config.py are in the same folder as discobs.py")
    exit(1)

# Import core OBS controller
from modules.obs_controller import OBSController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiscOBS(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize OBS controller
        self.obs_controller = OBSController(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        
        # Module storage
        self.loaded_modules = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up DiscOBS...")
        
        # Connect to OBS
        obs_connected = await self.obs_controller.connect()
        if not obs_connected:
            logger.error("Failed to connect to OBS. Some features may not work.")
        else:
            logger.info("Successfully connected to OBS!")
        
        # Load enabled modules
        await self.load_modules()
        
        logger.info("DiscOBS setup complete!")
    
    async def load_modules(self):
        """Load all enabled modules"""
        logger.info("Loading modules...")
        
        # Core Control Module (always loaded)
        if ENABLED_MODULES.get("core_controls", True):
            try:
                from modules.core_controls import CoreControlsModule
                core_module = CoreControlsModule(self, self.obs_controller)
                await core_module.setup()
                self.loaded_modules["core_controls"] = core_module
                logger.info("✅ Core Controls module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Core Controls module: {e}")
        
        # Stream Stats Module
        if ENABLED_MODULES.get("stream_stats", True):
            try:
                from modules.stream_stats import StreamStatsModule
                stats_module = StreamStatsModule(self, self.obs_controller)
                await stats_module.setup()
                self.loaded_modules["stream_stats"] = stats_module
                logger.info("✅ Stream Stats module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Stream Stats module: {e}")
        
        # Recording Controls Module
        if ENABLED_MODULES.get("recording_controls", True):
            try:
                from modules.recording_controls import RecordingControlsModule
                recording_module = RecordingControlsModule(self, self.obs_controller)
                await recording_module.setup()
                self.loaded_modules["recording_controls"] = recording_module
                logger.info("✅ Recording Controls module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Recording Controls module: {e}")
        
        # Connection Monitor Module
        if ENABLED_MODULES.get("connection_monitor", True):
            try:
                from modules.connection_monitor import ConnectionMonitorModule
                monitor_module = ConnectionMonitorModule(self, self.obs_controller)
                await monitor_module.setup()
                self.loaded_modules["connection_monitor"] = monitor_module
                logger.info("✅ Connection Monitor module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Connection Monitor module: {e}")
        
        # Audio Controls Module
        if ENABLED_MODULES.get("audio_controls", True):
            try:
                from modules.audio_controls import AudioControlsModule
                audio_module = AudioControlsModule(self, self.obs_controller)
                await audio_module.setup()
                self.loaded_modules["audio_controls"] = audio_module
                logger.info("✅ Audio Controls module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Audio Controls module: {e}")
        
        # Scene Controls Module
        if ENABLED_MODULES.get("scene_controls", True):
            try:
                from modules.scene_controls import SceneControlsModule
                scene_module = SceneControlsModule(self, self.obs_controller)
                await scene_module.setup()
                self.loaded_modules["scene_controls"] = scene_module
                logger.info("✅ Scene Controls module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Scene Controls module: {e}")
        
        # Quick Actions Module
        if ENABLED_MODULES.get("quick_actions", True):
            try:
                from modules.quick_actions import QuickActionsModule
                quick_module = QuickActionsModule(self, self.obs_controller)
                await quick_module.setup()
                self.loaded_modules["quick_actions"] = quick_module
                logger.info("✅ Quick Actions module loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load Quick Actions module: {e}")
        
        logger.info(f"Loaded {len(self.loaded_modules)} modules successfully")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"🎮 DiscOBS is online! Logged in as {self.user}")
        logger.info(f"📊 Loaded modules: {', '.join(self.loaded_modules.keys())}")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        logger.info("Shutting down DiscOBS...")
        
        # Cleanup modules
        for module_name, module in self.loaded_modules.items():
            try:
                if hasattr(module, 'cleanup'):
                    await module.cleanup()
                logger.info(f"✅ Cleaned up {module_name}")
            except Exception as e:
                logger.error(f"❌ Error cleaning up {module_name}: {e}")
        
        # Disconnect from OBS
        self.obs_controller.disconnect()
        
        await super().close()
        logger.info("DiscOBS shutdown complete")

# Error handling
@commands.Cog.listener()
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `!help` for command help.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred while executing the command.")

def main():
    """Main entry point"""
    logger.info("Starting DiscOBS...")
    
    # Validate Discord token
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.error("❌ Discord token not configured! Please edit config.py")
        return
    
    # Create and run bot
    bot = DiscOBS()
    
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        logger.info("DiscOBS terminated")

if __name__ == "__main__":
    main()