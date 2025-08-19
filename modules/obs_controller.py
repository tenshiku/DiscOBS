"""
OBS WebSocket Controller
Handles all communication with OBS Studio
"""

import logging
from typing import Optional, Dict, Any, List
import obswebsocket
from obswebsocket import obsws, requests as obs_requests

logger = logging.getLogger(__name__)

class OBSController:
    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to OBS WebSocket"""
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True
            logger.info(f"Connected to OBS WebSocket at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS WebSocket: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from OBS WebSocket"""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
                logger.info("Disconnected from OBS WebSocket")
            except Exception as e:
                logger.error(f"Error disconnecting from OBS: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to OBS"""
        return self.connected and self.ws is not None
    
    # Scene Management
    async def get_scenes(self) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Get list of available scenes with current scene info"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return [], None
            
        try:
            scenes_response = self.ws.call(obs_requests.GetSceneList())
            current_scene_response = self.ws.call(obs_requests.GetCurrentProgramScene())
            
            scene_list = []
            current_scene_name = current_scene_response.getCurrentProgramSceneName()
            
            for scene in scenes_response.getScenes():
                scene_name = scene['sceneName']
                is_current = scene_name == current_scene_name
                scene_list.append({
                    'name': scene_name,
                    'current': is_current,
                    'index': scene.get('sceneIndex', 0)
                })
            
            return scene_list, current_scene_name
        except Exception as e:
            logger.error(f"Error getting scenes: {e}")
            return [], None
    
    async def switch_scene(self, scene_name: str) -> bool:
        """Switch to a specific scene"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
            logger.info(f"Switched to scene: {scene_name}")
            return True
        except Exception as e:
            logger.error(f"Error switching to scene '{scene_name}': {e}")
            return False
    
    async def get_current_scene(self) -> Optional[str]:
        """Get the currently active scene"""
        if not self.is_connected():
            return None
            
        try:
            response = self.ws.call(obs_requests.GetCurrentProgramScene())
            return response.getCurrentProgramSceneName()
        except Exception as e:
            logger.error(f"Error getting current scene: {e}")
            return None
    
    # Streaming Controls
    async def start_streaming(self) -> bool:
        """Start streaming"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.StartStream())
            logger.info("Started streaming")
            return True
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop streaming"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.StopStream())
            logger.info("Stopped streaming")
            return True
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            return False
    
    async def get_stream_status(self) -> bool:
        """Get current streaming status"""
        if not self.is_connected():
            return False
            
        try:
            status = self.ws.call(obs_requests.GetStreamStatus())
            return status.getOutputActive()
        except Exception as e:
            logger.error(f"Error getting stream status: {e}")
            return False
    
    async def get_stream_stats(self) -> Optional[Dict[str, Any]]:
        """Get detailed stream statistics"""
        if not self.is_connected():
            return None
            
        try:
            stream_status = self.ws.call(obs_requests.GetStreamStatus())
            obs_stats = self.ws.call(obs_requests.GetStats())
            
            # Extract stream-specific stats
            stream_active = stream_status.getOutputActive()
            stream_time = getattr(stream_status, 'getOutputTimecode', lambda: "00:00:00")()
            stream_bytes = getattr(stream_status, 'getOutputBytes', lambda: 0)()
            
            # Extract dropped frames info
            dropped_frames = getattr(stream_status, 'getOutputSkippedFrames', lambda: 0)()
            total_frames = getattr(stream_status, 'getOutputTotalFrames', lambda: 1)()
            
            # Extract OBS performance stats
            fps = getattr(obs_stats, 'getActiveFps', lambda: 60.0)()
            cpu_usage = getattr(obs_stats, 'getCpuUsage', lambda: 0.0)()
            memory_usage = getattr(obs_stats, 'getMemoryUsage', lambda: 0.0)()
            free_disk = getattr(obs_stats, 'getAvailableDiskSpace', lambda: 0.0)()
            
            return {
                'active': stream_active,
                'time_code': stream_time,
                'bytes': stream_bytes,
                'dropped_frames': dropped_frames,
                'total_frames': total_frames,
                'fps': fps,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'free_disk_space': free_disk,
                'bitrate': stream_bytes * 8 / 1000 if stream_bytes > 0 else 0  # Rough bitrate calculation
            }
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            return None
    
    # Recording Controls
    async def start_recording(self) -> bool:
        """Start recording"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.StartRecord())
            logger.info("Started recording")
            return True
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
    
    async def stop_recording(self) -> bool:
        """Stop recording"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.StopRecord())
            logger.info("Stopped recording")
            return True
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False
    
    async def get_recording_status(self) -> Dict[str, Any]:
        """Get current recording status"""
        if not self.is_connected():
            return {'active': False, 'time_code': '00:00:00', 'bytes': 0}
            
        try:
            status = self.ws.call(obs_requests.GetRecordStatus())
            
            return {
                'active': status.getOutputActive(),
                'time_code': getattr(status, 'getOutputTimecode', lambda: "00:00:00")(),
                'bytes': getattr(status, 'getOutputBytes', lambda: 0)(),
                'paused': getattr(status, 'getOutputPaused', lambda: False)()
            }
        except Exception as e:
            logger.error(f"Error getting recording status: {e}")
            return {'active': False, 'time_code': '00:00:00', 'bytes': 0}
    
    # Audio Controls
    async def get_audio_sources(self) -> List[Dict[str, Any]]:
        """Get list of audio sources with their properties"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return []
            
        try:
            inputs_response = self.ws.call(obs_requests.GetInputList())
            audio_sources = []
            
            for input_item in inputs_response.getInputs():
                input_name = input_item['inputName']
                input_kind = input_item.get('inputKind', '')
                
                try:
                    # Check if this input has audio capabilities
                    volume_info = self.ws.call(obs_requests.GetInputVolume(inputName=input_name))
                    mute_info = self.ws.call(obs_requests.GetInputMute(inputName=input_name))
                    
                    audio_sources.append({
                        'name': input_name,
                        'kind': input_kind,
                        'muted': mute_info.getInputMuted(),
                        'volume_db': volume_info.getInputVolumeDb(),
                        'volume_mul': getattr(volume_info, 'getInputVolumeMul', lambda: 1.0)()
                    })
                except Exception:
                    # This input doesn't have audio, skip it
                    continue
            
            return audio_sources
        except Exception as e:
            logger.error(f"Error getting audio sources: {e}")
            return []
    
    async def mute_source(self, source_name: str, muted: bool = True) -> bool:
        """Mute or unmute an audio source"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.SetInputMute(inputName=source_name, inputMuted=muted))
            action = "Muted" if muted else "Unmuted"
            logger.info(f"{action} audio source: {source_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting mute for source '{source_name}': {e}")
            return False
    
    async def set_source_volume(self, source_name: str, volume_db: float) -> bool:
        """Set volume for an audio source (in dB)"""
        if not self.is_connected():
            logger.error("Not connected to OBS")
            return False
            
        try:
            self.ws.call(obs_requests.SetInputVolume(inputName=source_name, inputVolumeDb=volume_db))
            logger.info(f"Set volume for {source_name} to {volume_db}dB")
            return True
        except Exception as e:
            logger.error(f"Error setting volume for source '{source_name}': {e}")
            return False
    
    # Source Management
    async def get_scene_sources(self, scene_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sources in a scene"""
        if not self.is_connected():
            return []
            
        if scene_name is None:
            scene_name = await self.get_current_scene()
            if scene_name is None:
                return []
        
        try:
            response = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
            sources = []
            
            for item in response.getSceneItems():
                sources.append({
                    'name': item.get('sourceName', ''),
                    'id': item.get('sceneItemId', 0),
                    'enabled': item.get('sceneItemEnabled', True),
                    'locked': item.get('sceneItemLocked', False)
                })
            
            return sources
        except Exception as e:
            logger.error(f"Error getting scene sources for '{scene_name}': {e}")
            return []
    
    async def set_source_visibility(self, scene_name: str, source_id: int, visible: bool) -> bool:
        """Set visibility of a source in a scene"""
        if not self.is_connected():
            return False
            
        try:
            self.ws.call(obs_requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=source_id,
                sceneItemEnabled=visible
            ))
            action = "Showed" if visible else "Hidden"
            logger.info(f"{action} source ID {source_id} in scene '{scene_name}'")
            return True
        except Exception as e:
            logger.error(f"Error setting source visibility: {e}")
            return False
    
    # System Information
    async def get_obs_stats(self) -> Optional[Dict[str, Any]]:
        """Get general OBS performance statistics"""
        if not self.is_connected():
            return None
            
        try:
            stats = self.ws.call(obs_requests.GetStats())
            
            return {
                'fps': getattr(stats, 'getActiveFps', lambda: 0.0)(),
                'cpu_usage': getattr(stats, 'getCpuUsage', lambda: 0.0)(),
                'memory_usage': getattr(stats, 'getMemoryUsage', lambda: 0.0)(),
                'free_disk_space': getattr(stats, 'getAvailableDiskSpace', lambda: 0.0)(),
                'average_frame_time': getattr(stats, 'getAverageFrameTime', lambda: 0.0)(),
                'render_skipped_frames': getattr(stats, 'getRenderSkippedFrames', lambda: 0)(),
                'render_total_frames': getattr(stats, 'getRenderTotalFrames', lambda: 1)(),
                'output_skipped_frames': getattr(stats, 'getOutputSkippedFrames', lambda: 0)(),
                'output_total_frames': getattr(stats, 'getOutputTotalFrames', lambda: 1)()
            }
        except Exception as e:
            logger.error(f"Error getting OBS stats: {e}")
            return None
    
    async def get_version_info(self) -> Optional[Dict[str, str]]:
        """Get OBS version information"""
        if not self.is_connected():
            return None
            
        try:
            version = self.ws.call(obs_requests.GetVersion())
            return {
                'obs_version': getattr(version, 'getObsVersion', lambda: 'Unknown')(),
                'obs_web_socket_version': getattr(version, 'getObsWebSocketVersion', lambda: 'Unknown')(),
                'rpc_version': str(getattr(version, 'getRpcVersion', lambda: 'Unknown')()),
                'available_requests': getattr(version, 'getAvailableRequests', lambda: [])()
            }
        except Exception as e:
            logger.error(f"Error getting version info: {e}")
            return None
    
    # Connection Health
    async def test_connection(self) -> Dict[str, Any]:
        """Test the OBS WebSocket connection"""
        if not self.is_connected():
            return {
                'connected': False,
                'error': 'Not connected to OBS WebSocket',
                'host': self.host,
                'port': self.port
            }
        
        try:
            # Try to get version info as a connection test
            version_info = await self.get_version_info()
            if version_info:
                return {
                    'connected': True,
                    'host': self.host,
                    'port': self.port,
                    'obs_version': version_info.get('obs_version', 'Unknown'),
                    'websocket_version': version_info.get('obs_web_socket_version', 'Unknown')
                }
            else:
                return {
                    'connected': False,
                    'error': 'Failed to get OBS version info',
                    'host': self.host,
                    'port': self.port
                }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'host': self.host,
                'port': self.port
            }