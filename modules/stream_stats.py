"""
Stream Stats Module
Provides the !stats command with persistent statistics display
"""

import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StreamStatsModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        self.persistent_messages = {}  # Track persistent stat messages
        self.update_task = None
        
    async def setup(self):
        """Setup the stream stats module"""
        # Add commands using decorator syntax
        @commands.command(name='stats')
        async def stats_cmd(ctx):
            await self.update_stats_embed(ctx)
        
        self.bot.add_command(stats_cmd)
        
        # Add persistent view
        self.bot.add_view(StatsView(self))
        
        # Start auto-update task
        self.update_task = asyncio.create_task(self.auto_update_stats())
        
        logger.info("Stream Stats module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        if self.update_task:
            self.update_task.cancel()
        logger.info("Stream Stats module cleanup complete")
    
    async def update_stats_embed(self, ctx_or_interaction, edit=False):
        """Update the persistent stats embed"""
        stats = await self.obs.get_stream_stats()
        
        if not stats:
            embed = discord.Embed(
                title="❌ Stats Unavailable",
                description="Could not retrieve OBS statistics. Make sure OBS is running and connected.",
                color=0xff0000
            )
        else:
            is_streaming = stats['active']
            status_emoji = "🔴" if is_streaming else "⭕"
            status_text = "LIVE" if is_streaming else "OFFLINE"
            color = 0x00ff00 if is_streaming else 0x808080
            
            embed = discord.Embed(
                title="📊 Stream Statistics",
                description=f"**Status:** {status_emoji} {status_text}",
                color=color
            )
            
            if is_streaming:
                # Stream-specific stats
                embed.add_field(name="⏱️ Stream Time", value=stats.get('time_code', '00:00:00'), inline=True)
                embed.add_field(name="📊 FPS", value=f"{stats.get('fps', 0):.1f} fps", inline=True)
                
                # Calculate bitrate in a more readable format
                bitrate = stats.get('bitrate', 0)
                if bitrate >= 1000:
                    bitrate_str = f"{bitrate/1000:.1f} Mbps"
                else:
                    bitrate_str = f"{bitrate:.0f} kbps"
                embed.add_field(name="📡 Bitrate", value=bitrate_str, inline=True)
                
                # Dropped frames calculation
                dropped = stats.get('dropped_frames', 0)
                total = stats.get('total_frames', 1)
                dropped_percent = (dropped / total * 100) if total > 0 else 0
                
                embed.add_field(name="📉 Dropped Frames", value=f"{dropped} ({dropped_percent:.1f}%)", inline=True)
                embed.add_field(name="💾 CPU Usage", value=f"{stats.get('cpu_usage', 0):.1f}%", inline=True)
                embed.add_field(name="💿 Memory", value=f"{stats.get('memory_usage', 0):.1f} MB", inline=True)
                
                # Disk space
                free_disk = stats.get('free_disk_space', 0)
                if free_disk >= 1024:
                    disk_str = f"{free_disk/1024:.1f} TB"
                elif free_disk >= 1:
                    disk_str = f"{free_disk:.1f} GB"
                else:
                    disk_str = f"{free_disk*1024:.0f} MB"
                embed.add_field(name="💽 Free Disk", value=disk_str, inline=True)
            else:
                # When not streaming, show basic OBS stats
                embed.add_field(name="📊 OBS FPS", value=f"{stats.get('fps', 0):.1f} fps", inline=True)
                embed.add_field(name="💾 CPU Usage", value=f"{stats.get('cpu_usage', 0):.1f}%", inline=True)
                embed.add_field(name="💿 Memory", value=f"{stats.get('memory_usage', 0):.1f} MB", inline=True)
        
        # Add connection monitor info if available
        if 'connection_monitor' in self.bot.loaded_modules:
            monitor_module = self.bot.loaded_modules['connection_monitor']
            if hasattr(monitor_module, 'get_encoder_status'):
                encoder_status = await monitor_module.get_encoder_status()
                if encoder_status and encoder_status.get('enabled', False):
                    if encoder_status.get('online', False):
                        embed.add_field(
                            name="🛡️ Encoder Status",
                            value=f"✅ Connected\n{encoder_status.get('bitrate', 0)} kbps • {encoder_status.get('rtt', 0)}ms RTT",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="🛡️ Encoder Status", 
                            value=f"❌ Disconnected\n{encoder_status.get('error', 'Unknown error')}",
                            inline=False
                        )
        
        embed.timestamp = datetime.now()
        embed.set_footer(text="Updates every 30 seconds")
        
        view = StatsView(self)
        
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
    
    async def auto_update_stats(self):
        """Automatically update persistent stats embeds every 30 seconds"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Update all persistent stats messages
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
                            await self.update_stats_embed(mock_interaction, edit=True)
                    except Exception as e:
                        logger.error(f"Error updating stats embed {message_id}: {e}")
                        # Remove invalid message ID
                        del self.persistent_messages[channel_id]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-update stats task: {e}")

class StatsView(discord.ui.View):
    def __init__(self, stats_module):
        super().__init__(timeout=None)
        self.stats_module = stats_module
    
    @discord.ui.button(label='🔄 Refresh', style=discord.ButtonStyle.secondary, custom_id='refresh_stats')
    async def refresh_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.stats_module.update_stats_embed(interaction, edit=True)
    
    @discord.ui.button(label='🛡️ Monitor', style=discord.ButtonStyle.primary, custom_id='show_monitor')
    async def show_monitor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if connection monitor module is loaded
        if 'connection_monitor' in self.stats_module.bot.loaded_modules:
            monitor_module = self.stats_module.bot.loaded_modules['connection_monitor']
            await monitor_module.show_connection_monitor(interaction)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Connection Monitor module is not enabled. Check modules_config.py",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='📱 Main Panel', style=discord.ButtonStyle.secondary, custom_id='main_panel')
    async def main_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Check if core controls module is loaded
        if 'core_controls' in self.stats_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.stats_module.bot, self.stats_module.obs)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)