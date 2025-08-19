"""
Connection Monitor Module
Provides automatic scene switching when encoder connection is lost
"""

import discord
from discord.ext import commands
import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Import configuration
from config import CONNECTION_MONITORING, BELABOX_MONITORING

logger = logging.getLogger(__name__)

class ConnectionMonitorModule:
    def __init__(self, bot, obs_controller):
        self.bot = bot
        self.obs = obs_controller
        self.monitoring_active = False
        self.last_scene_before_switch = None
        self.current_encoder_status = {}
        self.monitoring_task = None
        self.failure_counts = {}
        self.current_scene_cache = None
        
    async def setup(self):
        """Setup the connection monitor module"""
        @commands.command(name='monitor')
        async def monitor_cmd(ctx):
            await self.show_connection_monitor(ctx)
        
        @commands.command(name='debug_belabox')
        async def debug_belabox_cmd(ctx):
            await self.debug_belabox_connection(ctx)
        
        self.bot.add_command(monitor_cmd)
        self.bot.add_command(debug_belabox_cmd)
        
        # Add persistent view
        self.bot.add_view(ConnectionMonitorView(self))
        
        # Start monitoring if enabled
        if CONNECTION_MONITORING.get("enabled", False):
            await self.start_monitoring()
        
        logger.info("Connection Monitor module setup complete")
    
    async def cleanup(self):
        """Cleanup when module is disabled"""
        await self.stop_monitoring()
        logger.info("Connection Monitor module cleanup complete")
    
    async def start_monitoring(self):
        """Start connection monitoring"""
        if not CONNECTION_MONITORING.get("enabled", False):
            logger.info("Connection monitoring is disabled in config")
            return
            
        if not BELABOX_MONITORING.get("enabled", False):
            logger.warning("Connection monitoring enabled but no monitoring method configured")
            return
            
        logger.info("Starting connection monitoring...")
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self):
        """Stop connection monitoring"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Connection monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        check_interval = CONNECTION_MONITORING.get("check_interval", 15)
        
        while self.monitoring_active:
            try:
                encoder_status = await self._check_belabox()
                should_switch, reason = self._should_switch_scene(encoder_status)
                
                if should_switch:
                    await self._handle_connection_lost(reason)
                elif await self._is_currently_in_fallback_scene() and encoder_status.get("online", False):
                    await self._handle_connection_restored()
                    
                self.current_encoder_status = encoder_status
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def _check_belabox(self) -> Dict[str, Any]:
        """Check Belabox Cloud stats"""
        if not BELABOX_MONITORING.get("enabled", False):
            return {"online": True, "error": "Monitoring disabled"}
            
        config = BELABOX_MONITORING
        stats_url = config.get("stats_url", "")
        
        if not stats_url:
            return {"online": False, "error": "No stats URL configured"}
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(stats_url, timeout=10) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            publishers = data.get("publishers", {})
                            live_publisher = publishers.get("live", {})
                            
                            connected = live_publisher.get("connected", False)
                            if not connected:
                                return {"online": False, "error": "Publisher not connected", "enabled": True}
                            
                            bitrate = live_publisher.get("bitrate", 0)
                            rtt = live_publisher.get("rtt", 0)
                            dropped_pkts = live_publisher.get("dropped_pkts", 0)
                            
                            bitrate_threshold = config.get("bitrate_threshold", 500)
                            rtt_threshold = config.get("rtt_threshold", 2000)
                            dropped_threshold = config.get("dropped_threshold", 100)
                            
                            bitrate_ok = bitrate >= bitrate_threshold
                            rtt_ok = rtt <= rtt_threshold
                            dropped_ok = dropped_pkts <= dropped_threshold
                            
                            online = bitrate_ok and rtt_ok and dropped_ok
                            
                            return {
                                "online": online,
                                "bitrate": bitrate,
                                "rtt": rtt,
                                "dropped": 0,
                                "dropped_pkts": dropped_pkts,
                                "connected": connected,
                                "bitrate_ok": bitrate_ok,
                                "rtt_ok": rtt_ok,
                                "dropped_ok": dropped_ok,
                                "enabled": True
                            }
                        except Exception as json_error:
                            return {"online": False, "error": f"JSON parse error: {json_error}", "enabled": True}
                    else:
                        return {"online": False, "error": f"HTTP {response.status}", "enabled": True}
                        
        except asyncio.TimeoutError:
            return {"online": False, "error": "Request timeout", "enabled": True}
        except Exception as e:
            return {"online": False, "error": str(e), "enabled": True}
    
    def _should_switch_scene(self, encoder_status: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if we should switch to fallback scene"""
        timeout_threshold = CONNECTION_MONITORING.get("timeout_threshold", 30)
        
        if encoder_status.get("online", False):
            if self.failure_counts:
                logger.info("Connection back online, resetting failure counts")
            self.failure_counts = {}
            return False, ""
            
        current_time = time.time()
        if "last_failure_time" not in self.failure_counts:
            self.failure_counts["last_failure_time"] = current_time
        else:
            time_since_first_failure = current_time - self.failure_counts["last_failure_time"]
            
            if time_since_first_failure >= timeout_threshold:
                reason = encoder_status.get("error", "Connection failed")
                return True, reason
                
        return False, ""
        
    async def _is_currently_in_fallback_scene(self) -> bool:
        """Check if we're currently in the fallback scene"""
        fallback_scene = CONNECTION_MONITORING.get("fallback_scene", "BRB")
        try:
            current_scene = await self.obs.get_current_scene()
            self.current_scene_cache = current_scene
            return current_scene == fallback_scene
        except Exception as e:
            logger.error(f"Error checking current scene: {e}")
            return False
            
    async def _handle_connection_lost(self, reason: str):
        """Handle when connection is lost"""
        fallback_scene = CONNECTION_MONITORING.get("fallback_scene", "BRB")
        
        if not await self._is_currently_in_fallback_scene():
            try:
                current_scene = await self.obs.get_current_scene()
                if current_scene:
                    self.last_scene_before_switch = current_scene
            except Exception as e:
                logger.error(f"Error saving current scene: {e}")
                
        success = await self.obs.switch_scene(fallback_scene)
        
        if success:
            logger.warning(f"Connection lost! Switched to {fallback_scene}. Reason: {reason}")
            
            if CONNECTION_MONITORING.get("discord_notifications", True):
                await self._send_discord_notification(
                    f"🔌 **Connection Lost!**\nSwitched to **{fallback_scene}** scene.\n\n**Reason:** {reason}",
                    color=0xff0000
                )
        else:
            logger.error(f"Failed to switch to fallback scene: {fallback_scene}")
    
    async def _handle_connection_restored(self):
        """Handle when connection is restored"""
        return_behavior = CONNECTION_MONITORING.get("return_behavior", "previous")
        
        target_scene = None
        if return_behavior == "previous" and self.last_scene_before_switch:
            target_scene = self.last_scene_before_switch
        elif return_behavior != "manual" and return_behavior != "previous":
            target_scene = return_behavior
            
        if target_scene:
            success = await self.obs.switch_scene(target_scene)
            if success:
                logger.info(f"Connection restored! Switched back to {target_scene}")
                
                if CONNECTION_MONITORING.get("discord_notifications", True):
                    await self._send_discord_notification(
                        f"✅ **Connection Restored!**\nSwitched back to **{target_scene}** scene.",
                        color=0x00ff00
                    )
                    
                self.last_scene_before_switch = None
        else:
            logger.info("Connection restored! Manual scene control required.")
            
            if CONNECTION_MONITORING.get("discord_notifications", True):
                await self._send_discord_notification(
                    f"✅ **Connection Restored!**\nManual scene control required.",
                    color=0xffa500
                )
    
    async def _send_discord_notification(self, message: str, color: int = 0x5865f2):
        """Send notification to Discord channels that have used the bot recently"""
        try:
            logger.info(f"Discord notification: {message}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    async def debug_belabox_connection(self, ctx):
        """Debug command to test Belabox connection and show raw response"""
        embed = discord.Embed(
            title="🔍 Belabox Debug",
            description="Testing your Belabox connection...",
            color=0x5865f2
        )
        await ctx.send(embed=embed)
        
        config = BELABOX_MONITORING
        stats_url = config.get("stats_url", "")
        
        if not stats_url:
            embed = discord.Embed(
                title="❌ No URL Configured",
                description="No Belabox stats URL found in config.py",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(stats_url, timeout=10) as response:
                    if response.status == 200:
                        raw_data = await response.text()
                        
                        try:
                            data = await response.json()
                            
                            embed = discord.Embed(
                                title="✅ Connection Successful",
                                description=f"**HTTP Status:** {response.status}\n**Raw Data:**\n```json\n{str(data)[:1800]}\n```",
                                color=0x00ff00
                            )
                            
                            publishers = data.get("publishers", {})
                            live_publisher = publishers.get("live", {})
                            
                            bitrate = live_publisher.get("bitrate", "NOT FOUND")
                            rtt = live_publisher.get("rtt", "NOT FOUND") 
                            dropped_pkts = live_publisher.get("dropped_pkts", "NOT FOUND")
                            connected = live_publisher.get("connected", "NOT FOUND")
                            
                            embed.add_field(name="Parsed Fields", 
                                          value=f"connected: {connected}\nbitrate: {bitrate}\nrtt: {rtt}\ndropped_pkts: {dropped_pkts}", 
                                          inline=False)
                            
                        except Exception as json_error:
                            embed = discord.Embed(
                                title="⚠️ JSON Parse Error",
                                description=f"**HTTP Status:** {response.status} (Success)\n**Error:** {str(json_error)}\n**Raw Response:**\n```\n{raw_data[:1500]}\n```",
                                color=0xffa500
                            )
                    else:
                        error_text = await response.text()
                        embed = discord.Embed(
                            title="❌ HTTP Error",
                            description=f"**Status:** {response.status}\n**Response:**\n```\n{error_text[:1500]}\n```",
                            color=0xff0000
                        )
                        
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏰ Timeout Error",
                description="Request timed out after 10 seconds. Your Belabox might be offline or the URL is incorrect.",
                color=0xff0000
            )
        except Exception as e:
            embed = discord.Embed(
                title="❌ Connection Error", 
                description=f"**Error:** {str(e)}\n\nThis could mean:\n• Belabox is offline\n• URL is incorrect\n• Network connectivity issues",
                color=0xff0000
            )
        
        await ctx.send(embed=embed)

    async def get_encoder_status(self) -> Dict[str, Any]:
        """Get current encoder status for other modules"""
        return self.current_encoder_status
    
    async def show_connection_monitor(self, ctx_or_interaction, edit=False):
        """Show connection monitoring status"""
        enabled = CONNECTION_MONITORING.get("enabled", False)
        
        if not enabled:
            embed = discord.Embed(
                title="❌ Monitor Disabled",
                description="Connection monitoring is disabled. Edit `config.py` to enable:\n\n```python\nCONNECTION_MONITORING = {\n    \"enabled\": True,\n    \"fallback_scene\": \"BRB\"\n}\n```",
                color=0xff0000
            )
            view = None
        else:
            active = self.monitoring_active
            belabox_enabled = BELABOX_MONITORING.get("enabled", False)
            
            status_emoji = "🛡️" if active else "⚪"
            status_text = "Active" if active else "Stopped"
            color = 0x00ff00 if active else 0x808080
            
            embed = discord.Embed(
                title="🛡️ Connection Monitor",
                description=f"**Status:** {status_emoji} {status_text}",
                color=color
            )
            
            embed.add_field(name="⚙️ Fallback Scene", value=CONNECTION_MONITORING.get("fallback_scene", "BRB"), inline=True)
            embed.add_field(name="⏱️ Check Interval", value=f"{CONNECTION_MONITORING.get('check_interval', 15)}s", inline=True)
            embed.add_field(name="⏲️ Timeout", value=f"{CONNECTION_MONITORING.get('timeout_threshold', 30)}s", inline=True)
            
            if belabox_enabled:
                embed.add_field(name="📊 Bitrate Threshold", value=f"{BELABOX_MONITORING.get('bitrate_threshold', 500)} kbps", inline=True)
                embed.add_field(name="⏱️ RTT Threshold", value=f"{BELABOX_MONITORING.get('rtt_threshold', 2000)} ms", inline=True)
                embed.add_field(name="📉 Dropped Threshold", value=f"{BELABOX_MONITORING.get('dropped_threshold', 100)} pkts", inline=True)
            
            if belabox_enabled:
                embed.add_field(name="📡 Method", value="Belabox Cloud", inline=True)
                stats_url = BELABOX_MONITORING.get("stats_url", "")
                if stats_url:
                    from urllib.parse import urlparse
                    domain = urlparse(stats_url).netloc
                    embed.add_field(name="🌐 Endpoint", value=domain, inline=True)
            else:
                embed.add_field(name="📡 Method", value="❌ Not Configured", inline=True)
            
            embed.add_field(name="📢 Notifications", value="✅ Enabled" if CONNECTION_MONITORING.get("discord_notifications", True) else "❌ Disabled", inline=True)
            
            if self.current_encoder_status and belabox_enabled:
                status = self.current_encoder_status
                if status.get("online", False):
                    embed.add_field(
                        name="📊 Encoder Status",
                        value=f"✅ Connected\n{status.get('bitrate', 0)} kbps • {status.get('rtt', 0)}ms RTT\n{status.get('dropped_pkts', 0)} pkts dropped",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="📊 Encoder Status",
                        value=f"❌ Disconnected\n{status.get('error', 'Unknown error')}",
                        inline=False
                    )
            elif not belabox_enabled:
                embed.add_field(
                    name="ℹ️ Setup Required",
                    value="Configure Belabox monitoring in config.py to enable connection monitoring",
                    inline=False
                )
            
            embed.timestamp = datetime.now()
            view = ConnectionMonitorView(self)
        
        if hasattr(ctx_or_interaction, 'followup'):
            if edit:
                await ctx_or_interaction.edit_original_response(embed=embed, view=view)
            else:
                await ctx_or_interaction.followup.send(embed=embed, view=view)
        else:
            await ctx_or_interaction.send(embed=embed, view=view)

class ConnectionMonitorView(discord.ui.View):
    def __init__(self, monitor_module):
        super().__init__(timeout=None)
        self.monitor_module = monitor_module
    
    @discord.ui.button(label='🔄 Refresh', style=discord.ButtonStyle.secondary, custom_id='refresh_monitor')
    async def refresh_monitor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.monitor_module.show_connection_monitor(interaction, edit=True)
    
    @discord.ui.button(label='🧪 Test Connection', style=discord.ButtonStyle.primary, custom_id='test_connection')
    async def test_connection(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if BELABOX_MONITORING.get("enabled", False):
            status = await self.monitor_module._check_belabox()
            if status.get("online", False):
                embed = discord.Embed(
                    title="✅ Connection Test Passed",
                    description=f"**Belabox Status:** Connected\n**Bitrate:** {status.get('bitrate', 0)} kbps\n**RTT:** {status.get('rtt', 0)}ms\n**Dropped:** {status.get('dropped_pkts', 0)} pkts",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ Connection Test Failed",
                    description=f"**Error:** {status.get('error', 'Unknown error')}",
                    color=0xff0000
                )
        else:
            embed = discord.Embed(
                title="❌ No Monitoring Configured",
                description="Belabox monitoring is not enabled. Check your config.py file.",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='🔍 Debug Belabox', style=discord.ButtonStyle.secondary, custom_id='debug_belabox')
    async def debug_belabox(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.monitor_module.debug_belabox_connection(interaction)
    
    @discord.ui.button(label='⚙️ Toggle Monitor', style=discord.ButtonStyle.success, custom_id='toggle_monitor')
    async def toggle_monitor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if not CONNECTION_MONITORING.get("enabled", False):
            embed = discord.Embed(
                title="❌ Monitor Disabled in Config",
                description="Connection monitoring is disabled in config.py. Enable it first:\n\n```python\nCONNECTION_MONITORING = {\n    \"enabled\": True\n}\n```",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if self.monitor_module.monitoring_active:
            await self.monitor_module.stop_monitoring()
            embed = discord.Embed(
                title="⏹️ Monitor Stopped",
                description="Connection monitoring has been stopped.",
                color=0xffa500
            )
        else:
            await self.monitor_module.start_monitoring()
            embed = discord.Embed(
                title="▶️ Monitor Started", 
                description="Connection monitoring has been started.",
                color=0x00ff00
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        await self.monitor_module.show_connection_monitor(interaction, edit=True)
    
    @discord.ui.button(label='📱 Main Panel', style=discord.ButtonStyle.secondary, custom_id='main_panel')
    async def main_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if 'core_controls' in self.monitor_module.bot.loaded_modules:
            from modules.core_controls import show_main_panel
            await show_main_panel(interaction, self.monitor_module.bot, self.monitor_module.obs)
        else:
            embed = discord.Embed(
                title="❌ Module Disabled",
                description="Core Controls module is not enabled.",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)