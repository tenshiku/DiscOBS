# =========================================
# DISCOBS MODULES CONFIGURATION
# =========================================
# Enable or disable specific modules
# Set to True to enable, False to disable

ENABLED_MODULES = {
    # Core OBS control panel (!obs command)
    # This provides the main control interface
    "core_controls": True,
    
    # Stream statistics display (!stats command) 
    # Shows bitrate, FPS, dropped frames, etc.
    "stream_stats": True,
    
    # Recording controls (!record command)
    # Start/stop recording independently from streaming
    "recording_controls": True,
    
    # Connection monitoring (!monitor command)
    # Automatic scene switching when encoder disconnects
    # Recommended for IRL streamers using Belabox/bonding
    "connection_monitor": False,
    
    # Audio source controls (part of !obs)
    # Mute/unmute audio sources
    "audio_controls": True,
    
    # Scene switching controls (part of !obs)
    # Switch between OBS scenes
    "scene_controls": True,
    
    # Quick action buttons (part of !obs)
    # BRB, Intro, Outro, Emergency stop
    "quick_actions": True,
}

# =========================================
# CONFIGURATION PRESETS
# =========================================
"""
DESKTOP STREAMING (Default - works out of the box):
ENABLED_MODULES = {
    "core_controls": True,
    "stream_stats": True,
    "recording_controls": True,
    "connection_monitor": False,  # Not needed for desktop streaming
    "audio_controls": True,
    "scene_controls": True,
    "quick_actions": True,
}

IRL STREAMING (Enable connection monitoring):
ENABLED_MODULES = {
    "core_controls": True,
    "stream_stats": True,
    "recording_controls": True,
    "connection_monitor": True,   # Enable for automatic failover
    "audio_controls": True,
    "scene_controls": True,
    "quick_actions": True,
}

MINIMAL SETUP (Basic functionality only):
ENABLED_MODULES = {
    "core_controls": True,
    "stream_stats": False,
    "recording_controls": False,
    "connection_monitor": False,
    "audio_controls": True,
    "scene_controls": True,
    "quick_actions": False,
}
"""

# =========================================
# MODULE DESCRIPTIONS
# =========================================
"""
CORE_CONTROLS:
- Main !obs command with control panel
- Stream start/stop buttons
- Navigation between other modules
- Required for basic functionality

STREAM_STATS:
- !stats command for real-time statistics
- Performance metrics (CPU, memory, FPS)
- Auto-updating every 30 seconds
- Useful for monitoring stream health

RECORDING_CONTROLS:
- !record command for recording management
- Independent recording controls
- File size estimation and duration tracking
- Great for creating highlights/content

CONNECTION_MONITOR:
- !monitor command for encoder monitoring
- Automatic scene switching on connection loss
- Belabox Cloud integration for IRL streaming
- Requires Belabox setup in config.py
- Desktop streamers typically don't need this

AUDIO_CONTROLS:
- Audio source mute/unmute buttons
- Volume level indicators
- Part of the main !obs panel
- Essential for stream audio management

SCENE_CONTROLS:
- Scene switching interface
- Visual current scene indicator
- Part of the main !obs panel
- Core functionality for scene management

QUICK_ACTIONS:
- Emergency scene shortcuts (BRB, Intro, Outro)
- Emergency stream stop button
- Customizable quick scene buttons
- Great for rapid scene changes during streams
"""