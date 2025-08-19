"""
Audio Controls Module
Provides audio source muting and volume controls
"""

import discord
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AudioControlsModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        
    async def setup(self):
        """Setup the audio controls module"""
        logger.info("Audio Controls module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        logger.info("Audio Controls module cleanup complete")
    
    async def show_audio_panel(self, ctx_or_interaction, edit=False):
        """Show the audio control panel"""
        audio_sources = await self.obs.get_audio_sources()
        
        if not audio_sources:
            embed = discord.Embed(
                title="❌ No Audio Sources",
                description="No audio sources found in OBS. Make sure you have audio inputs configured.",
                color=0xff0000
            )
            view = None
        else:
            embed = discord.Embed(
                title="🔊 Audio Control",
                description="Click a source to toggle mute/unmute:",
                color=0x5865F2
            )
            
            # Add current status field
            status_text = ""
            for source in audio_sources[:10]:  # Limit to 10 for embed readability
                emoji = "🔇" if source['muted'] else "🔊"
                volume_db = source.get('volume_db', 0)
                if volume_db == -100:  # -100dB is typically silent/muted
                    volume_str = "Silent"
                elif volume_db >= 0:
                    volume_str = f"+{volume_db:.0f}dB"
                else:
                    volume_str = f"{volume_db:.0f}dB"
                
                status_text += f"{emoji} **{source['name']}** ({volume_str})\n"
            
            if status_text:
                embed.add_field(name="Current Status", value=status_text, inline=False)
            
            if len(audio_sources) > 20:
                embed.add_field(
                    name="⚠️ Note",
                    value="Only showing first 20 audio sources",
                    inline=False
                )
            
            view = AudioControlView(self, audio_sources)
        
        if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
            if edit:
                await ctx_or_interaction.edit_original_response(embed=embed, view=view)
            else:
                await ctx_or_interaction.followup.send(embed=embed, view=view)
        else:  # It's a context (from text command)
            await ctx_or_interaction.send(embed=embed, view=view)

class AudioControlView(discord.ui.View):
    def __init__(self, audio_module, audio_sources: List[Dict[str, Any]]):
        super().__init__(timeout=300)
        self.audio_module = audio_module
        self.obs = audio_module.obs
        self.audio_sources = audio_sources
        
        # Add audio source buttons (max 20 to fit Discord limits)
        for i, source in enumerate(audio_sources[:20]):
            emoji = "🔇" if source['muted'] else "🔊"
            style = discord.ButtonStyle.secondary if source['muted'] else discord.ButtonStyle.success
            
            # Truncate long source names to fit button labels
            label = source['name']
            if len(label) > 70:  # Leave room for emoji
                label = label[:67] + "..."
            
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=style,
                custom_id=f"audio_{i}"
            )
            button.callback = self.audio_callback
            self.add_item(button)
        
        # Add control buttons
        refresh_button = discord.ui.Button(label="🔄 Refresh", style=discord.ButtonStyle.primary, custom_id="refresh_audio")
        refresh_button.callback = self.refresh_callback
        self.add_item(refresh_button)
        
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.danger, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def audio_callback(self, interaction: discord.Interaction):
        """Handle audio source mute toggle"""
        source_index = int(interaction.data['custom_id'].split('_')[1])
        source = self.audio_sources[source_index]
        source_name = source['name']
        current_muted = source['muted']
        
        await interaction.response.defer()
        
        # Toggle mute status
        new_mute_state = not current_muted
        success = await self.obs.mute_source(source_name, new_mute_state)
        
        if success:
            action = "Muted" if new_mute_state else "Unmuted"
            emoji = "🔇" if new_mute_state else "🔊"
            color = 0xffa500 if new_mute_state else 0x00ff00
            
            embed = discord.Embed(
                title=f"{emoji} Audio {action}",
                description=f"**{source_name}** is now {action.lower()}",
                color=color
            )
            logger.info(f"Audio control: {action} {source_name}")
            
            # Refresh the audio panel to show updated status
            await self.refresh_audio_panel(interaction)
        else:
            embed = discord.Embed(
                title="❌ Audio Control Failed",
                description=f"Failed to toggle **{source_name}**\n\nCheck OBS connection and source name.",
                color=0xff0000
            )
            logger.error(f"Failed to toggle audio source: {source_name}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh button"""
        await interaction.response.defer()
        await self.refresh_audio_panel(interaction)
    
    async def refresh_audio_panel(self, interaction: discord.Interaction):
        """Refresh the audio panel with current data"""
        await self.audio_module.show_audio_panel(interaction, edit=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button"""
        await interaction.response.defer()
        
        # Check if core controls module is loaded
        if 'core_controls' in self.audio_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.audio_module.bot, self.audio_module.obs, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)