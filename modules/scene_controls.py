"""
Scene Controls Module
Provides scene switching interface
"""

import discord
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SceneControlsModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        
    async def setup(self):
        """Setup the scene controls module"""
        logger.info("Scene Controls module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        logger.info("Scene Controls module cleanup complete")
    
    async def show_scenes_panel(self, ctx_or_interaction, edit=False):
        """Show the scenes control panel"""
        scenes_data, current_scene = await self.obs.get_scenes()
        
        if not scenes_data:
            embed = discord.Embed(
                title="❌ No Scenes Found",
                description="No OBS scenes available. Make sure OBS is running and connected.",
                color=0xff0000
            )
            view = None
        else:
            embed = discord.Embed(
                title="🎬 Scene Control",
                description=f"**Current Scene:** {current_scene}\n\nClick a scene to switch:",
                color=0x5865F2
            )
            
            # Add scene count info
            embed.add_field(
                name="📋 Available Scenes",
                value=f"{len(scenes_data)} scenes found",
                inline=True
            )
            
            if len(scenes_data) > 20:
                embed.add_field(
                    name="⚠️ Note",
                    value="Only showing first 20 scenes",
                    inline=True
                )
            
            view = ScenesView(self, scenes_data)
        
        if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
            if edit:
                await ctx_or_interaction.edit_original_response(embed=embed, view=view)
            else:
                await ctx_or_interaction.followup.send(embed=embed, view=view)
        else:  # It's a context (from text command)
            await ctx_or_interaction.send(embed=embed, view=view)

class ScenesView(discord.ui.View):
    def __init__(self, scene_module, scenes_data: List[Dict[str, Any]]):
        super().__init__(timeout=300)
        self.scene_module = scene_module
        self.obs = scene_module.obs
        self.scenes_data = scenes_data
        
        # Add scene buttons (max 20 to fit Discord limits)
        for i, scene in enumerate(scenes_data[:20]):
            style = discord.ButtonStyle.success if scene['current'] else discord.ButtonStyle.secondary
            emoji = "▶️" if scene['current'] else "🎬"
            
            # Truncate long scene names to fit button labels
            label = scene['name']
            if len(label) > 75:  # Discord button label limit is 80 chars
                label = label[:72] + "..."
            
            button = discord.ui.Button(
                label=label,
                style=style,
                emoji=emoji,
                custom_id=f"scene_{i}"
            )
            button.callback = self.scene_callback
            self.add_item(button)
        
        # Add refresh and back buttons
        refresh_button = discord.ui.Button(label="🔄 Refresh", style=discord.ButtonStyle.primary, custom_id="refresh_scenes")
        refresh_button.callback = self.refresh_callback
        self.add_item(refresh_button)
        
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.danger, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def scene_callback(self, interaction: discord.Interaction):
        """Handle scene selection"""
        scene_index = int(interaction.data['custom_id'].split('_')[1])
        scene_data = self.scenes_data[scene_index]
        scene_name = scene_data['name']
        
        await interaction.response.defer()
        
        # Don't switch if already current scene
        if scene_data['current']:
            embed = discord.Embed(
                title="ℹ️ Already Active",
                description=f"**{scene_name}** is already the current scene.",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await self.obs.switch_scene(scene_name)
        
        if success:
            embed = discord.Embed(
                title="🎬 Scene Switched",
                description=f"Now showing: **{scene_name}**",
                color=0x00ff00
            )
            logger.info(f"Switched to scene: {scene_name}")
            
            # Refresh the scenes panel to show the new current scene
            await self.refresh_scenes_panel(interaction)
        else:
            embed = discord.Embed(
                title="❌ Switch Failed",
                description=f"Failed to switch to scene: **{scene_name}**\n\nCheck OBS connection and scene name.",
                color=0xff0000
            )
            logger.error(f"Failed to switch to scene: {scene_name}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh button"""
        await interaction.response.defer()
        await self.refresh_scenes_panel(interaction)
    
    async def refresh_scenes_panel(self, interaction: discord.Interaction):
        """Refresh the scenes panel with current data"""
        await self.scene_module.show_scenes_panel(interaction, edit=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button"""
        await interaction.response.defer()
        
        # Check if core controls module is loaded
        if 'core_controls' in self.scene_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.scene_module.bot, self.scene_module.obs, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)