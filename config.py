# =========================================
# DISCOBS CONFIGURATION FILE
# =========================================
# Edit this file to customize your DiscOBS bot
# No need to touch the main discobs.py file!

# =========================================
# DISCORD & OBS SETTINGS
# =========================================

# DISCORD BOT TOKEN
# Get this from: https://discord.com/developers/applications
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# OBS WEBSOCKET SETTINGS
# Configure these in OBS: Tools → WebSocket Server Settings
OBS_HOST = "localhost"  # Don't change this unless OBS is on another computer
OBS_PORT = 4455         # Default OBS WebSocket port
OBS_PASSWORD = "your_obs_password"     # Set to your OBS WebSocket password, or "" if disabled

# =========================================
# QUICK ACTIONS CONFIGURATION
# =========================================
# Customize the buttons in the Quick Actions panel
# Change scene_name to match YOUR OBS scenes exactly!

QUICK_ACTIONS = {
    # BRB (Be Right Back) Scene
    "brb": {
        "scene_name": "BRB",                    # YOUR OBS scene name (case-sensitive!)
        "button_label": "⏸️ BRB",               # Button text (you can change the emoji/text)
        "description": "Be Right Back scene",   # Description shown in embed
        "success_message": "⏸️ **Be Right Back** - Switched to BRB scene"
    },
    
    # Stream Intro Scene
    "intro": {
        "scene_name": "Intro",                  # YOUR OBS scene name
        "button_label": "🎬 Intro",             # Button text
        "description": "Stream intro scene",    # Description
        "success_message": "🎬 **Intro** - Switched to intro scene"
    },
    
    # Stream Outro Scene
    "outro": {
        "scene_name": "Outro",                  # YOUR OBS scene name
        "button_label": "👋 Outro",             # Button text
        "description": "Stream outro scene",    # Description
        "success_message": "👋 **Outro** - Switched to outro scene"
    },
    
    # Emergency Scene (Optional)
    "emergency": {
        "scene_name": "Emergency",              # YOUR OBS scene name
        "button_label": "🚨 Emergency Scene",   # Button text
        "description": "Emergency backup scene", # Description
        "success_message": "🚨 **Emergency** - Switched to emergency scene",
        "enabled": False                        # Set to True to enable this button
    }
}

# =========================================
# EMERGENCY STOP SETTING
# =========================================
# Choose what the emergency button does:
# True = Stop stream immediately (recommended)
# False = Switch to emergency scene above
EMERGENCY_STOP_STREAM = True

# =========================================
# CUSTOM QUICK ACTIONS (Optional)
# =========================================
# Add your own custom scene buttons here!
# You can add as many as you want.

CUSTOM_QUICK_ACTIONS = {
    # Example custom scene - uncomment and customize:
    # "gaming": {
    #     "scene_name": "Gaming Setup",           # YOUR OBS scene name
    #     "button_label": "🎮 Gaming",            # Button text
    #     "description": "Switch to gaming scene", # Description
    #     "success_message": "🎮 **Gaming Mode** - Ready to game!"
    # },
    
    # Another example - IRL streaming scene:
    # "irl": {
    #     "scene_name": "IRL Camera",
    #     "button_label": "📱 IRL",
    #     "description": "IRL streaming setup",
    #     "success_message": "📱 **IRL Mode** - Going mobile!"
    # },
    
    # Chatting scene example:
    # "chat": {
    #     "scene_name": "Just Chatting",
    #     "button_label": "💬 Chat",
    #     "description": "Just chatting scene",
    #     "success_message": "💬 **Chat Time** - Let's talk!"
    # }
}

# =========================================
# CONNECTION MONITORING CONFIGURATION
# =========================================
CONNECTION_MONITORING = {
    "enabled": False,  # Set to True for IRL streaming with Belabox
    "check_interval": 15,  # Check every 15 seconds
    "timeout_threshold": 60,  # Switch to failover after 60 seconds of failure
    "fallback_scene": "BRB",  # Scene to switch to when connection fails
    "return_behavior": "previous",  # "previous", "manual", or specific scene name
    "discord_notifications": True  # Send Discord notifications on connection changes
}

# =========================================
# BELABOX CLOUD MONITORING (Optional)
# =========================================
BELABOX_MONITORING = {
    "enabled": False,  # Set to True if you use Belabox Cloud
    "stats_url": "",  # Your Belabox Cloud stats URL from your account
    "bitrate_threshold": 1000,  # Minimum bitrate (kbps) before considering connection failed
    "rtt_threshold": 2000,  # Maximum RTT (ms) before considering connection failed
    "dropped_threshold": 100  # Maximum dropped packets before considering connection failed
}

# =========================================
# SETUP INSTRUCTIONS
# =========================================
"""
QUICK SETUP GUIDE:

1. DISCORD BOT:
   - Go to https://discord.com/developers/applications
   - Create a new application and bot
   - Copy the bot token and paste it in DISCORD_TOKEN above
   - Invite bot to your server with Send Messages permission

2. OBS WEBSOCKET:
   - In OBS: Tools → WebSocket Server Settings
   - Enable WebSocket Server
   - Note the port (usually 4455)
   - Set a password or leave blank, update OBS_PASSWORD above

3. CUSTOMIZE SCENES:
   - Look at your OBS scene names
   - Update the "scene_name" values above to match exactly
   - Scene names are case-sensitive!

4. BELABOX SETUP (Optional):
   - If you use Belabox Cloud, set enabled to True
   - Get your stats URL from your Belabox Cloud account
   - Adjust thresholds based on your connection quality

5. RUN THE BOT:
   - Save this file
   - Run: python discobs.py
   - In Discord, type: !obs

EXAMPLE SCENE SETUP:
If your OBS scenes are named:
- "Stream Starting"
- "Be Right Back" 
- "Stream Ending"

Then update the config like this:
QUICK_ACTIONS = {
    "brb": {
        "scene_name": "Be Right Back",  # ← Changed to match your scene
        "button_label": "⏸️ BRB",
        # ... rest stays the same
    },
    "intro": {
        "scene_name": "Stream Starting",  # ← Changed to match your scene
        "button_label": "🎬 Start",        # ← You can also change button text
        # ... rest stays the same
    }
}

BELABOX THRESHOLD RECOMMENDATIONS:
For typical IRL streaming (2-5 Mbps):
- bitrate_threshold: 1000 (switch if below 1 Mbps)
- rtt_threshold: 2000 (switch if above 2 seconds latency)
- dropped_threshold: 100 (switch if more than 100 dropped packets)

For high-quality streams (5-10 Mbps):
- bitrate_threshold: 2000 (switch if below 2 Mbps)
- rtt_threshold: 1500 (switch if above 1.5 seconds latency)
- dropped_threshold: 50 (switch if more than 50 dropped packets)

COMMANDS:
- !obs - Main control panel
- !stats - Stream statistics
- !record - Recording controls
- !monitor - Connection monitoring
- !debug_belabox - Test Belabox connection

Need help? Check the README or open an issue on GitHub!
"""