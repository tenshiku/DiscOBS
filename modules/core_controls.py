"""
Core Controls Module
Provides the main !obs command and control panel interface
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CoreControlsModule:
   def __init__(self, bot, obs_controller):
       self.bot = bot
       self.obs = obs_controller
       
   async def setup(self):
       """Setup the core controls module"""
       # Add commands using decorator syntax
       @commands.command(name='obs')
       async def obs_control_cmd(ctx):
           await show_main_panel(ctx, self.bot, self.obs)
       
       @commands.command(name='panel')
       async def obs_panel_cmd(ctx):
           await show_main_panel(ctx, self.bot, self.obs)
       
       self.bot.add_command(obs_control_cmd)
       self.bot.add_command(obs_panel_cmd)
       
       # Add persistent view
       self.bot.add_view(OBSControlView(self.bot, self.obs))
       
       logger.info("Core Controls module setup complete")
   
   async def cleanup(self):
       """Cleanup when module is disabled"""
       logger.info("Core Controls module cleanup complete")

class OBSControlView(discord.ui.View):
    def __init__(self, bot, obs_controller):
        super().__init__(timeout=None)
        self.bot = bot
        self.obs = obs_controller
    
    @discord.ui.button(label='🎬 Scenes', style=discord.ButtonStyle.primary, custom_id='scenes_button')
    async def scenes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if scene controls module is loaded
        if 'scene_controls' in self.bot.loaded_modules:
            scene_module = self.bot.loaded_modules['scene_controls']
            await scene_module.show_scenes_panel(interaction, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Scene Controls module is not enabled. Check modules_config.py",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(label='🔴 Stream Control', style=discord.ButtonStyle.secondary, custom_id='stream_button')
    async def stream_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await show_stream_panel(interaction, self.obs, edit=True)
    
    @discord.ui.button(label='🔊 Audio', style=discord.ButtonStyle.secondary, custom_id='audio_button')
    async def audio_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if audio controls module is loaded
        if 'audio_controls' in self.bot.loaded_modules:
            audio_module = self.bot.loaded_modules['audio_controls']
            await audio_module.show_audio_panel(interaction, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Audio Controls module is not enabled. Check modules_config.py",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(label='⚡ Quick Actions', style=discord.ButtonStyle.success, custom_id='quick_button')
    async def quick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if quick actions module is loaded
        if 'quick_actions' in self.bot.loaded_modules:
            quick_module = self.bot.loaded_modules['quick_actions']
            await quick_module.show_quick_actions_panel(interaction, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Quick Actions module is not enabled. Check modules_config.py",
                color=0xff0000
            )
            await interaction.edit_original_response(embed=embed, view=None)

class StreamControlView(discord.ui.View):
    def __init__(self, obs_controller, is_streaming):
        super().__init__(timeout=300)
        self.obs = obs_controller
        self.is_streaming = is_streaming
        
        # Separate Start and Stop buttons
        start_button = discord.ui.Button(label="🚀 Start Stream", style=discord.ButtonStyle.success, custom_id="start_stream")
        start_button.callback = self.start_callback
        self.add_item(start_button)
        
        stop_button = discord.ui.Button(label="🛑 Stop Stream", style=discord.ButtonStyle.danger, custom_id="stop_stream")
        stop_button.callback = self.stop_callback
        self.add_item(stop_button)
        
        # Status button
        status_button = discord.ui.Button(label="📊 Check Status", style=discord.ButtonStyle.secondary, custom_id="check_status")
        status_button.callback = self.status_callback
        self.add_item(status_button)
        
        # Back button
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.secondary, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def start_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Check if already streaming
        current_status = await self.obs.get_stream_status()
        if current_status:
            embed = discord.Embed(
                title="ℹ️ Already Streaming",
                description="Stream is already running! 🔴",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await self.obs.start_streaming()
        if success:
            embed = discord.Embed(
                title="🚀 Stream Started",
                description="You are now **LIVE**! 🔴\n\n*Note: May take a few seconds to fully connect*",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Start",
                description="Could not start stream. Check OBS settings.",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def stop_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Check if already stopped
        current_status = await self.obs.get_stream_status()
        if not current_status:
            embed = discord.Embed(
                title="ℹ️ Already Stopped",
                description="Stream is not currently running. ⭕",
                color=0x808080
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await self.obs.stop_streaming()
        if success:
            embed = discord.Embed(
                title="🛑 Stream Stopped",
                description="You are now **OFFLINE**. ⭕",
                color=0xff0000
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Stop",
                description="Could not stop stream.",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def status_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        is_streaming = await self.obs.get_stream_status()
        status = "🔴 **LIVE**" if is_streaming else "⭕ **OFFLINE**"
        
        embed = discord.Embed(
            title="📊 Stream Status",
            description=f"Current Status: {status}",
            color=0x00ff00 if is_streaming else 0x808080
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Get bot instance from interaction
        bot = interaction.client
        await show_main_panel(interaction, bot, self.obs, edit=True)

# Panel display functions
async def show_main_panel(ctx_or_interaction, bot, obs_controller, edit=False):
    """Show the main OBS control panel"""
    embed = discord.Embed(
        title="🎮 DiscOBS Control Center",
        description="Choose a control panel below:",
        color=0x5865F2
    )
    
    # Add fields based on enabled modules
    if 'scene_controls' in bot.loaded_modules:
        embed.add_field(name="🎬 Scenes", value="Switch between OBS scenes", inline=True)
    
    embed.add_field(name="🔴 Stream", value="Start/stop your stream", inline=True)
    
    if 'audio_controls' in bot.loaded_modules:
        embed.add_field(name="🔊 Audio", value="Control audio sources", inline=True)
    
    if 'quick_actions' in bot.loaded_modules:
        embed.add_field(name="⚡ Quick Actions", value="Emergency controls", inline=True)
    
    # Add info about available standalone commands
    standalone_commands = []
    if 'stream_stats' in bot.loaded_modules:
        standalone_commands.append("`!stats` - Stream statistics")
    if 'recording_controls' in bot.loaded_modules:
        standalone_commands.append("`!record` - Recording controls")
    if 'connection_monitor' in bot.loaded_modules:
        standalone_commands.append("`!monitor` - Connection monitoring")
    
    if standalone_commands:
        embed.add_field(
            name="📱 Standalone Commands",
            value="\n".join(standalone_commands),
            inline=False
        )
    
    view = OBSControlView(bot, obs_controller)
    
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

async def show_stream_panel(ctx_or_interaction, obs_controller, edit=False):
    """Show the stream control panel"""
    is_streaming = await obs_controller.get_stream_status()
    
    status_emoji = "🔴" if is_streaming else "⭕"
    status_text = "LIVE" if is_streaming else "OFFLINE"
    color = 0x00ff00 if is_streaming else 0x808080
    
    embed = discord.Embed(
        title="🔴 Stream Control",
        description=f"**Status:** {status_emoji} {status_text}",
        color=color
    )
    
    # Add stream stats if available
    if is_streaming:
        stats = await obs_controller.get_stream_stats()
        if stats:
            embed.add_field(name="⏱️ Duration", value=stats.get('time_code', '00:00:00'), inline=True)
            embed.add_field(name="📊 FPS", value=f"{stats.get('fps', 0):.1f}", inline=True)
            
            # Calculate dropped percentage
            dropped = stats.get('dropped_frames', 0)
            total = stats.get('total_frames', 1)
            dropped_percent = (dropped / total * 100) if total > 0 else 0
            embed.add_field(name="📉 Dropped", value=f"{dropped_percent:.1f}%", inline=True)
    
    view = StreamControlView(obs_controller, is_streaming)
    
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)