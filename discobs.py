import discord
from discord.ext import commands
import obswebsocket
from obswebsocket import obsws, requests as obs_requests
import asyncio
import json
import logging
from typing import Optional

# Import configuration
try:
    from config import *
except ImportError:
    print("❌ ERROR: config.py file not found!")
    print("Please make sure config.py is in the same folder as discobs.py")
    print("You can download it from the DiscOBS package.")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OBSController:
    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        
    async def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            logger.info("Connected to OBS WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from OBS WebSocket"""
        if self.ws:
            self.ws.disconnect()
            logger.info("Disconnected from OBS")
    
    async def get_scenes(self):
        """Get list of available scenes"""
        try:
            scenes = self.ws.call(obs_requests.GetSceneList())
            current_scene = self.ws.call(obs_requests.GetCurrentProgramScene())
            scene_list = []
            current_scene_name = current_scene.getCurrentProgramSceneName()
            
            for scene in scenes.getScenes():
                scene_name = scene['sceneName']
                is_current = scene_name == current_scene_name
                scene_list.append({'name': scene_name, 'current': is_current})
            
            return scene_list, current_scene_name
        except Exception as e:
            logger.error(f"Error getting scenes: {e}")
            return [], None
    
    async def switch_scene(self, scene_name: str):
        """Switch to a specific scene"""
        try:
            self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
            return True
        except Exception as e:
            logger.error(f"Error switching to scene '{scene_name}': {e}")
            return False
    
    async def start_streaming(self):
        """Start streaming"""
        try:
            self.ws.call(obs_requests.StartStream())
            return True
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            return False
    
    async def stop_streaming(self):
        """Stop streaming"""
        try:
            self.ws.call(obs_requests.StopStream())
            return True
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return False
    
    async def get_stream_status(self):
        """Get current streaming status"""
        try:
            status = self.ws.call(obs_requests.GetStreamStatus())
            return status.getOutputActive()
        except Exception as e:
            logger.error(f"Error getting stream status: {e}")
            return False
    
    async def get_audio_sources(self):
        """Get list of audio sources with their mute status"""
        try:
            inputs = self.ws.call(obs_requests.GetInputList())
            audio_sources = []
            for input_item in inputs.getInputs():
                try:
                    # Check if input has audio
                    volume_info = self.ws.call(obs_requests.GetInputVolume(inputName=input_item['inputName']))
                    mute_info = self.ws.call(obs_requests.GetInputMute(inputName=input_item['inputName']))
                    
                    audio_sources.append({
                        'name': input_item['inputName'],
                        'muted': mute_info.getInputMuted(),
                        'volume': volume_info.getInputVolumeDb()
                    })
                except:
                    pass  # Not an audio source
            return audio_sources
        except Exception as e:
            logger.error(f"Error getting audio sources: {e}")
            return []
    
    async def mute_source(self, source_name: str, muted: bool = True):
        """Mute or unmute an audio source"""
        try:
            self.ws.call(obs_requests.SetInputMute(inputName=source_name, inputMuted=muted))
            return True
        except Exception as e:
            logger.error(f"Error muting source '{source_name}': {e}")
            return False

# Initialize OBS controller
obs_controller = OBSController(OBS_HOST, OBS_PORT, OBS_PASSWORD)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class OBSControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label='🎬 Scenes', style=discord.ButtonStyle.primary, custom_id='scenes_button')
    async def scenes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await show_scenes_panel(interaction, edit=True)
    
    @discord.ui.button(label='🔴 Stream Control', style=discord.ButtonStyle.secondary, custom_id='stream_button')
    async def stream_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await show_stream_panel(interaction, edit=True)
    
    @discord.ui.button(label='🔊 Audio', style=discord.ButtonStyle.secondary, custom_id='audio_button')
    async def audio_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await show_audio_panel(interaction, edit=True)
    
    @discord.ui.button(label='⚡ Quick Actions', style=discord.ButtonStyle.success, custom_id='quick_button')
    async def quick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await show_quick_actions_panel(interaction, edit=True)

class ScenesView(discord.ui.View):
    def __init__(self, scenes_data):
        super().__init__(timeout=300)
        self.scenes_data = scenes_data
        
        # Add scene buttons (max 25 components per view)
        for i, scene in enumerate(scenes_data[:20]):  # Limit to 20 scenes
            style = discord.ButtonStyle.success if scene['current'] else discord.ButtonStyle.secondary
            emoji = "▶️" if scene['current'] else "🎬"
            button = discord.ui.Button(
                label=scene['name'][:80],  # Discord label limit
                style=style,
                emoji=emoji,
                custom_id=f"scene_{i}"
            )
            button.callback = self.scene_callback
            self.add_item(button)
        
        # Add back button
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.danger, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def scene_callback(self, interaction: discord.Interaction):
        scene_index = int(interaction.data['custom_id'].split('_')[1])
        scene_name = self.scenes_data[scene_index]['name']
        
        await interaction.response.defer()
        success = await obs_controller.switch_scene(scene_name)
        
        if success:
            embed = discord.Embed(
                title="🎬 Scene Switched",
                description=f"Now showing: **{scene_name}**",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            # Refresh the scenes panel
            await show_scenes_panel(interaction, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to switch to scene: {scene_name}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await show_main_panel(interaction, edit=True)

class StreamControlView(discord.ui.View):
    def __init__(self, is_streaming):
        super().__init__(timeout=300)
        self.is_streaming = is_streaming
        
        # Separate Start and Stop buttons - always show both
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
        
        # Check if already streaming first
        current_status = await obs_controller.get_stream_status()
        if current_status:
            embed = discord.Embed(
                title="ℹ️ Already Streaming",
                description="Stream is already running! 🔴",
                color=0xffa500
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await obs_controller.start_streaming()
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
        
        # Check if already stopped first
        current_status = await obs_controller.get_stream_status()
        if not current_status:
            embed = discord.Embed(
                title="ℹ️ Already Stopped",
                description="Stream is not currently running. ⭕",
                color=0x808080
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        success = await obs_controller.stop_streaming()
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
        is_streaming = await obs_controller.get_stream_status()
        status = "🔴 **LIVE**" if is_streaming else "⭕ **OFFLINE**"
        
        embed = discord.Embed(
            title="📊 Stream Status",
            description=f"Current Status: {status}",
            color=0x00ff00 if is_streaming else 0x808080
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await show_main_panel(interaction, edit=True)

class AudioControlView(discord.ui.View):
    def __init__(self, audio_sources):
        super().__init__(timeout=300)
        self.audio_sources = audio_sources
        
        # Add audio source buttons
        for i, source in enumerate(audio_sources[:20]):  # Limit to 20 sources
            emoji = "🔇" if source['muted'] else "🔊"
            style = discord.ButtonStyle.secondary if source['muted'] else discord.ButtonStyle.success
            
            button = discord.ui.Button(
                label=f"{source['name'][:70]}",  # Limit label length
                emoji=emoji,
                style=style,
                custom_id=f"audio_{i}"
            )
            button.callback = self.audio_callback
            self.add_item(button)
        
        # Back button
        back_button = discord.ui.Button(label="← Back", style=discord.ButtonStyle.danger, custom_id="back_main")
        back_button.callback = self.back_callback
        self.add_item(back_button)
    
    async def audio_callback(self, interaction: discord.Interaction):
        source_index = int(interaction.data['custom_id'].split('_')[1])
        source = self.audio_sources[source_index]
        
        await interaction.response.defer()
        
        # Toggle mute status
        new_mute_state = not source['muted']
        success = await obs_controller.mute_source(source['name'], new_mute_state)
        
        if success:
            action = "Muted" if new_mute_state else "Unmuted"
            emoji = "🔇" if new_mute_state else "🔊"
            embed = discord.Embed(
                title=f"{emoji} Audio {action}",
                description=f"**{source['name']}** is now {action.lower()}",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            # Refresh audio panel
            await show_audio_panel(interaction, edit=True)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to toggle {source['name']}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await show_main_panel(interaction, edit=True)

class QuickActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        
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
        async def quick_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            success = await obs_controller.switch_scene(action_config["scene_name"])
            
            if success:
                embed = discord.Embed(
                    title="Scene Switched",
                    description=action_config["success_message"],
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ Scene Not Found",
                    description=f"Create a scene named **{action_config['scene_name']}** in OBS",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        return quick_callback
    
    async def emergency_stop_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Stop stream immediately
        success = await obs_controller.stop_streaming()
        
        embed = discord.Embed(
            title="🚨 EMERGENCY STOP",
            description="Stream has been stopped immediately!" if success else "Failed to stop stream!",
            color=0xff0000
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await show_main_panel(interaction, edit=True)

# Panel display functions
async def show_main_panel(ctx_or_interaction, edit=False):
    embed = discord.Embed(
        title="🎮 OBS Control Center",
        description="Choose a control panel below:",
        color=0x5865F2
    )
    embed.add_field(name="🎬 Scenes", value="Switch between OBS scenes", inline=True)
    embed.add_field(name="🔴 Stream", value="Start/stop your stream", inline=True)
    embed.add_field(name="🔊 Audio", value="Control audio sources", inline=True)
    embed.add_field(name="⚡ Quick Actions", value="Emergency controls", inline=True)
    
    view = OBSControlView()
    
    # Check if it's an interaction (from button) or context (from command)
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

async def show_scenes_panel(ctx_or_interaction, edit=False):
    scenes_data, current_scene = await obs_controller.get_scenes()
    
    if not scenes_data:
        embed = discord.Embed(
            title="❌ No Scenes Found",
            description="No OBS scenes available",
            color=0xff0000
        )
        view = None
    else:
        embed = discord.Embed(
            title="🎬 Scene Control",
            description=f"**Current Scene:** {current_scene}\n\nClick a scene to switch:",
            color=0x5865F2
        )
        view = ScenesView(scenes_data)
    
    # Check if it's an interaction (from button) or context (from command)
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

async def show_stream_panel(ctx_or_interaction, edit=False):
    is_streaming = await obs_controller.get_stream_status()
    
    status_emoji = "🔴" if is_streaming else "⭕"
    status_text = "LIVE" if is_streaming else "OFFLINE"
    color = 0x00ff00 if is_streaming else 0x808080
    
    embed = discord.Embed(
        title="🔴 Stream Control",
        description=f"**Status:** {status_emoji} {status_text}",
        color=color
    )
    
    view = StreamControlView(is_streaming)
    
    # Check if it's an interaction (from button) or context (from command)
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

async def show_audio_panel(ctx_or_interaction, edit=False):
    audio_sources = await obs_controller.get_audio_sources()
    
    if not audio_sources:
        embed = discord.Embed(
            title="❌ No Audio Sources",
            description="No audio sources found in OBS",
            color=0xff0000
        )
        view = None
    else:
        embed = discord.Embed(
            title="🔊 Audio Control",
            description="Click a source to toggle mute/unmute:",
            color=0x5865F2
        )
        
        # Add field showing current status
        status_text = ""
        for source in audio_sources[:10]:  # Limit to 10 for embed
            emoji = "🔇" if source['muted'] else "🔊"
            status_text += f"{emoji} {source['name']}\n"
        
        if status_text:
            embed.add_field(name="Current Status", value=status_text, inline=False)
        
        view = AudioControlView(audio_sources)
    
    # Check if it's an interaction (from button) or context (from command)
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

async def show_quick_actions_panel(ctx_or_interaction, edit=False):
    embed = discord.Embed(
        title="⚡ Quick Actions",
        description="Emergency controls and scene shortcuts:",
        color=0xffa500
    )
    
    # Add fields for configured actions
    for action_key, action_config in QUICK_ACTIONS.items():
        if action_key == "emergency" and not action_config.get("enabled", False):
            continue
        embed.add_field(
            name=action_config["button_label"], 
            value=action_config["description"], 
            inline=True
        )
    
    # Add custom actions
    for action_key, action_config in CUSTOM_QUICK_ACTIONS.items():
        embed.add_field(
            name=action_config["button_label"], 
            value=action_config["description"], 
            inline=True
        )
    
    # Add emergency stop if enabled
    if EMERGENCY_STOP_STREAM:
        embed.add_field(name="🚨 Emergency", value="Stop stream immediately", inline=True)
    
    view = QuickActionsView()
    
    # Check if it's an interaction (from button) or context (from command)
    if hasattr(ctx_or_interaction, 'followup'):  # It's an interaction
        if edit:
            await ctx_or_interaction.edit_original_response(embed=embed, view=view)
        else:
            await ctx_or_interaction.followup.send(embed=embed, view=view)
    else:  # It's a context (from text command)
        await ctx_or_interaction.send(embed=embed, view=view)

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'{bot.user} has connected to Discord!')
    
    # Connect to OBS
    connected = await obs_controller.connect()
    if not connected:
        logger.error("Failed to connect to OBS. Bot will not function properly.")
    else:
        logger.info("Bot is ready and connected to OBS!")
        
        # Add persistent view
        bot.add_view(OBSControlView())

@bot.command(name='obs')
async def obs_control(ctx):
    """Show OBS control panel: !obs"""
    await show_main_panel(ctx)

# Legacy command support
@bot.command(name='panel')
async def show_panel(ctx):
    """Show OBS control panel: !panel"""
    await show_main_panel(ctx)

# Error handling
@bot.event
async def on_application_command_error(interaction: discord.Interaction, error):
    """Handle application command errors"""
    logger.error(f"Interaction error: {error}")
    
    embed = discord.Embed(
        title="❌ Error",
        description="An error occurred while processing your request.",
        color=0xff0000
    )
    
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            pass

# Graceful shutdown
@bot.event
async def on_disconnect():
    """Handle bot disconnect"""
    obs_controller.disconnect()
    logger.info("Bot disconnected and cleaned up.")

if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        obs_controller.disconnect()