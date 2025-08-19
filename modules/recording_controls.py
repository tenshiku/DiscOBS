"""
Recording Controls Module
Provides the !record command with persistent recording interface
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RecordingControlsModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        self.persistent_messages = {}  # Track persistent recording messages
        self.update_task = None
        
    async def setup(self):
        """Setup the recording controls module"""
        # Add commands using decorator syntax
        @commands.command(name='record')
        async def record_cmd(ctx):
            await self.update_recording_embed(ctx)
        
        self.bot.add_command(record_cmd)
        
        # Add persistent view
        self.bot.add_view(RecordingView(self))
        
        # Start auto-update task
        self.update_task = asyncio.create_task(self.auto_update_recording())
        
        logger.info("Recording Controls module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        if self.update_task:
            self.update_task.cancel()
        logger.info("Recording Controls module cleanup complete")
    
    async def update_recording_embed(self, ctx_or_interaction, edit=False):
        """Update the persistent recording embed"""
        recording_status = await self.obs.get_recording_status()
        
        is_recording = recording_status['active']
        status_emoji = "🎥" if is_recording else "⭕"
        status_text = "Recording" if is_recording else "Not Recording"
        color = 0xff0000 if is_recording else 0x808080
        
        embed = discord.Embed(
            title="🎥 Recording Manager",
            description=f"**Status:** {status_emoji} {status_text}",
            color=color
        )
        
        if is_recording:
            # Recording active - show details
            embed.add_field(name="⏱️ Duration", value=recording_status.get('time_code', '00:00:00'), inline=True)
            
            # Estimate file size (rough calculation)
            bytes_recorded = recording_status.get('bytes', 0)
            if bytes_recorded > 0:
                if bytes_recorded >= 1073741824:  # 1GB
                    file_size_str = f"~{bytes_recorded / 1073741824:.2f} GB"
                elif bytes_recorded >= 1048576:  # 1MB
                    file_size_str = f"~{bytes_recorded / 1048576:.1f} MB"
                else:
                    file_size_str = f"~{bytes_recorded / 1024:.0f} KB"
            else:
                file_size_str = "Calculating..."
            
            embed.add_field(name="💾 File Size", value=file_size_str, inline=True)
            
            # Check if paused
            if recording_status.get('paused', False):
                embed.add_field(name="⏸️ Status", value="Paused", inline=True)
            else:
                embed.add_field(name="📄 Format", value="MP4 (H.264)", inline=True)
            
            # Add performance info
            obs_stats = await self.obs.get_obs_stats()
            if obs_stats:
                embed.add_field(name="📊 FPS", value=f"{obs_stats.get('fps', 0):.1f}", inline=True)
                embed.add_field(name="💾 CPU", value=f"{obs_stats.get('cpu_usage', 0):.1f}%", inline=True)
                
                # Show available disk space
                free_disk = obs_stats.get('free_disk_space', 0)
                if free_disk >= 1024:
                    disk_str = f"{free_disk/1024:.1f} TB free"
                elif free_disk >= 1:
                    disk_str = f"{free_disk:.1f} GB free"
                else:
                    disk_str = f"{free_disk*1024:.0f} MB free"
                embed.add_field(name="💽 Disk Space", value=disk_str, inline=True)
        else:
            # Recording not active - show ready state
            embed.add_field(name="ℹ️ Ready to Record", value="Click Start Recording to begin capturing", inline=False)
            
            # Show current scene that will be recorded
            current_scene = await self.obs.get_current_scene()
            if current_scene:
                embed.add_field(name="🎬 Current Scene", value=current_scene, inline=True)
            
            # Show available disk space
            obs_stats = await self.obs.get_obs_stats()
            if obs_stats:
                free_disk = obs_stats.get('free_disk_space', 0)
                if free_disk >= 1024:
                    disk_str = f"{free_disk/1024:.1f} TB available"
                elif free_disk >= 1:
                    disk_str = f"{free_disk:.1f} GB available"
                else:
                    disk_str = f"{free_disk*1024:.0f} MB available"
                embed.add_field(name="💽 Storage", value=disk_str, inline=True)
        
        embed.timestamp = datetime.now()
        embed.set_footer(text="Updates every 30 seconds")
        
        view = RecordingView(self)
        
        if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
            if edit:
                await ctx_or_interaction.edit_original_response(embed=embed, view=view)
            else:
                message = await ctx_or_interaction.followup.send(embed=embed, view=view)
                # Store message for auto-updates
                self.persistent_messages[message.channel.id] = message.id
        else:  # It's a context (from text command)
            message = await ctx_or_interaction.send(embed=embed, view=view)
            # Store message for auto-updates
            self.persistent_messages[message.channel.id] = message.id
    
    async def auto_update_recording(self):
        """Automatically update persistent recording embeds every 30 seconds"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Update all persistent recording messages
                for channel_id, message_id in list(self.persistent_messages.items()):
                    try:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            message = await channel.fetch_message(message_id)
                            
                            # Create a mock interaction for the update
                            class MockInteraction:
                                def __init__(self, message):
                                    self.message = message
                                
                                async def edit_original_response(self, embed=None, view=None):
                                    await self.message.edit(embed=embed, view=view)
                            
                            mock_interaction = MockInteraction(message)
                            await self.update_recording_embed(mock_interaction, edit=True)
                    except Exception as e:
                        logger.error(f"Error updating recording embed {message_id}: {e}")
                        # Remove invalid message ID
                        del self.persistent_messages[channel_id]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-update recording task: {e}")

class RecordingView(discord.ui.View):
    def __init__(self, recording_module):
        super().__init__(timeout=None)
        self.recording_module = recording_module
        self.obs = recording_module.obs
    
    @discord.ui.button(label='🎥 Start Recording', style=discord.ButtonStyle.success, custom_id='start_recording')
    async def start_recording(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if already recording
        current_status = await self.obs.get_recording_status()
        if current_status['active']:
            embed = discord.Embed(
                title="ℹ️ Already Recording",
                description="Recording is already active! 🎥",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await self.obs.start_recording()
        if success:
            embed = discord.Embed(
                title="🎥 Recording Started",
                description="Recording started successfully!\n\n*File will be saved to your OBS recording folder*",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Start Recording",
                description="Could not start recording. Check OBS settings and storage space.",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        await self.recording_module.update_recording_embed(interaction, edit=True)
    
    @discord.ui.button(label='🛑 Stop Recording', style=discord.ButtonStyle.danger, custom_id='stop_recording')
    async def stop_recording(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if actually recording
        current_status = await self.obs.get_recording_status()
        if not current_status['active']:
            embed = discord.Embed(
                title="ℹ️ Not Recording",
                description="Recording is not currently active. ⭕",
                color=0x808080
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await self.obs.stop_recording()
        if success:
            embed = discord.Embed(
                title="🛑 Recording Stopped",
                description="Recording stopped successfully!\n\n*File has been saved to your recording folder*",
                color=0xff0000
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Stop Recording",
                description="Could not stop recording.",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        await self.recording_module.update_recording_embed(interaction, edit=True)
    
    @discord.ui.button(label='🔄 Refresh', style=discord.ButtonStyle.secondary, custom_id='refresh_recording')
    async def refresh_recording(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.recording_module.update_recording_embed(interaction, edit=True)
    
    @discord.ui.button(label='📁 Open Folder', style=discord.ButtonStyle.secondary, custom_id='open_folder')
    async def open_folder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📁 Recording Folder",
            description="Your recordings are saved to the folder configured in:\n\n**OBS Settings** → **Output** → **Recording Path**\n\nCheck your OBS settings to see the exact location.",
            color=0x5865F2
        )
        embed.add_field(
            name="💡 Tip",
            value="You can change the recording folder in OBS Settings → Output → Recording",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='📱 Main Panel', style=discord.ButtonStyle.secondary, custom_id='main_panel')
    async def main_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if core controls module is loaded
        if 'core_controls' in self.recording_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.recording_module.bot, self.recording_module.obs)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)