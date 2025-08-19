"""
Quick Actions Module
Provides quick scene switching and emergency controls
"""

import discord
import logging
from typing import Dict, Any

# Import configuration
from config import QUICK_ACTIONS, CUSTOM_QUICK_ACTIONS, EMERGENCY_STOP_STREAM

logger = logging.getLogger(__name__)

class QuickActionsModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        
    async def setup(self):
        """Setup the quick actions module"""
        # Add persistent view with timeout=None
        self.bot.add_view(QuickActionsView(self))
        
        logger.info("Quick Actions module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        logger.info("Quick Actions module cleanup complete")
    
    async def show_quick_actions_panel(self, ctx_or_interaction, edit=False):
        """Show the quick actions panel"""
        embed = discord.Embed(
            title="⚡ Quick Actions",
            description="Emergency controls and scene shortcuts:",
            color=0xffa500
        )
        
        # Add fields for configured actions
        action_count = 0
        for action_key, action_config in QUICK_ACTIONS.items():
            if action_key == "emergency" and not action_config.get("enabled", False):
                continue
            embed.add_field(
                name=action_config["button_label"],
                value=action_config["description"],
                inline=True
            )
            action_count += 1
        
        # Add custom actions
        for action_key, action_config in CUSTOM_QUICK_ACTIONS.items():
            embed.add_field(
                name=action_config["button_label"],
                value=action_config["description"],
                inline=True
            )
            action_count += 1
        
        # Add emergency stop if enabled
        if EMERGENCY_STOP_STREAM:
            embed.add_field(name="🚨 Emergency Stop", value="Stop stream immediately", inline=True)
            action_count += 1
        
        if action_count == 0:
            embed.add_field(
                name="ℹ️ No Actions Configured",
                value="Configure quick actions in config.py to use this panel",
                inline=False
            )
        
        view = QuickActionsView(self)
        
        if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
            if edit:
                await ctx_or_interaction.edit_original_response(embed=embed, view=view)
            else:
                await ctx_or_interaction.followup.send(embed=embed, view=view)
        else:  # It's a context (from text command)
            await ctx_or_interaction.send(embed=embed, view=view)

class QuickActionsView(discord.ui.View):
    def __init__(self, quick_actions_module):
        super().__init__(timeout=None)  # Set timeout=None for persistent views
        self.quick_actions_module = quick_actions_module
        self.obs = quick_actions_module.obs
        
        # Add configured quick action buttons
        for action_key, action_config in QUICK_ACTIONS.items():
            if action_key == "emergency" and not action_config.get("enabled", False):
                continue  # Skip emergency scene if not enabled
                
            button = discord.ui.Button(
                label=action_config["button_label"],
                style=discord.ButtonStyle.primary if action_key != "emergency" else discord.ButtonStyle.danger,
                custom_id=f"quick_{action_key}"
            )
            button.callback = self.create_quick_callback(action_key, action_config)
            self.add_item(button)
        
        # Add custom quick actions
        for action_key, action_config in CUSTOM_QUICK_ACTIONS.items():
            button = discord.ui.Button(
                label=action_config["button_label"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"custom_{action_key}"
            )
            button.callback = self.create_quick_callback(action_key, action_config)
            self.add_item(button)
        
        # Add emergency stop button if enabled
        if EMERGENCY_STOP_STREAM:
            emergency_button = discord.ui.Button(
                label="🚨 Emergency Stop",
                style=discord.ButtonStyle.danger,
                custom_id="emergency_stop"
            )
            emergency_button.callback = self.emergency_stop_callback
            self.add_item(emergency_button)
        
        # Back button
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.secondary, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    def create_quick_callback(self, action_key, action_config):
        """Create a callback function for a quick action"""
        async def quick_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            
            scene_name = action_config["scene_name"]
            success = await self.obs.switch_scene(scene_name)
            
            if success:
                embed = discord.Embed(
                    title="🎬 Scene Switched",
                    description=action_config["success_message"],
                    color=0x00ff00
                )
                logger.info(f"Quick action {action_key}: Switched to scene {scene_name}")
            else:
                embed = discord.Embed(
                    title="❌ Scene Not Found",
                    description=f"Create a scene named **{scene_name}** in OBS",
                    color=0xff0000
                )
                logger.warning(f"Quick action {action_key}: Scene {scene_name} not found")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        return quick_callback
    
    async def emergency_stop_callback(self, interaction: discord.Interaction):
        """Handle emergency stop button"""
        await interaction.response.defer()
        
        # Stop stream immediately
        success = await self.obs.stop_streaming()
        
        if success:
            embed = discord.Embed(
                title="🚨 EMERGENCY STOP",
                description="Stream has been stopped immediately!",
                color=0xff0000
            )
            logger.warning("Emergency stop activated - stream stopped")
        else:
            embed = discord.Embed(
                title="❌ Emergency Stop Failed",
                description="Failed to stop stream! Check OBS connection.",
                color=0xff0000
            )
            logger.error("Emergency stop failed - could not stop stream")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        """Handle back button"""
        await interaction.response.defer()
        
        # Check if core controls module is loaded
        if 'core_controls' in self.quick_actions_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.quick_actions_module.bot, self.quick_actions_module.obs, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)