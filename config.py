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
OBS_PASSWORD = None     # Set to "your_password" if you enabled authentication in OBS

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