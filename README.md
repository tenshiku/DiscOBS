# 🎮 DiscOBS - Discord OBS Control Bot

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![Discord](https://img.shields.io/badge/discord-bot-7289da.svg)
![OBS](https://img.shields.io/badge/OBS-WebSocket-purple.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**I created this bot to solve a problem I had while IRL streaming. When I travel with my streaming setup (laptop + IRL backpack), I needed a way to control OBS remotely without dealing with port forwarding at Airbnbs or hotels.**

**The solution was simple: run a Discord bot locally on my laptop that connects to OBS WebSocket, then control everything from my phone through Discord. No network configuration needed, just start the bot and go live from anywhere.**

## ✨ Features

- 🎬 **Scene Switching** - Visual scene controls with current scene highlighting
- 🔴 **Stream Control** - Start/stop streaming with status monitoring
- 🔊 **Audio Management** - One-click mute/unmute for all audio sources
- ⚡ **Quick Actions** - Customizable emergency buttons (BRB, Intro, Outro, etc.)
- 📱 **Mobile Friendly** - Perfect for controlling from your phone
- ⚙️ **Easy Configuration** - No code editing required

## 📋 What You Need

- **Python 3.7+** installed on your computer
- **OBS Studio** with WebSocket plugin
- **Discord Bot** (free to create)
- **Discord Server** where you have permission to add bots

## 🚀 Quick Setup

### 1. Download DiscOBS

Download these two files and put them in the same folder:

- `discobs.py` (main bot code)
- `config.py` (your settings)

### 2. Install Python Libraries

Open Command Prompt/Terminal and run:

```bash
pip install discord.py obs-websocket-py
```

### 3. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Give it a name
3. Go to "Bot" section → Click "Add Bot"
4. **Copy the Token** (you'll need this)
5. Enable "Message Content Intent"
6. Go to "OAuth2" → "URL Generator"
7. Select: `bot` + `applications.commands`
8. Select permissions: `Send Messages`, `Read Message History`
9. Copy the URL and invite bot to your server

### 4. Configure OBS WebSocket

1. Open OBS Studio
2. Go to **Tools** → **WebSocket Server Settings**
3. Check ✅ **"Enable WebSocket server"**
4. Note the port (usually 4455)
5. Optionally set a password (Recommended)

### 5. Edit Your Configuration

Open `config.py` and update:

```python
# Add your Discord bot token
DISCORD_TOKEN = "your_actual_bot_token_here"

# Set OBS password if you created one
OBS_PASSWORD = "your_obs_password"  # or None if no password

# Update scene names to match YOUR OBS scenes
QUICK_ACTIONS = {
    "brb": {
        "scene_name": "BRB",  # ← Change this to YOUR scene name
        # ... rest can stay the same
    }
}
```

### 6. Run DiscOBS

```bash
python discobs.py
```

You should see:

```
INFO:__main__:DiscOBS has connected to Discord!
INFO:__main__:Connected to OBS WebSocket
INFO:__main__:Bot is ready and connected to OBS!
```

### 7. Use DiscOBS

In Discord, type: `!obs`

You'll get a control panel with buttons for:

- 🎬 Scene control
- 🔴 Stream start/stop
- 🔊 Audio mute/unmute
- ⚡ Quick actions

## ⚙️ Customization

### Adding Custom Quick Actions

Edit `config.py` and add to `CUSTOM_QUICK_ACTIONS`:

```python
CUSTOM_QUICK_ACTIONS = {
    "gaming": {
        "scene_name": "Gaming Setup",     # Your OBS scene name
        "button_label": "🎮 Gaming",      # Button text
        "description": "Gaming scene",    # Description
        "success_message": "🎮 **Gaming Mode** - Ready to game!"
    },
    "irl": {
        "scene_name": "IRL Camera",
        "button_label": "📱 IRL", 
        "description": "IRL streaming",
        "success_message": "📱 **IRL Mode** - Going mobile!"
    }
}
```

### Changing Button Labels

You can customize any button text:

```python
"button_label": "🔄 Away",  # Instead of "⏸️ BRB"
```

### Emergency Button Options

Choose what the emergency button does:

```python
EMERGENCY_STOP_STREAM = True   # Stops stream immediately
EMERGENCY_STOP_STREAM = False  # Switches to emergency scene
```

## 🎯 Perfect For

- **IRL Streamers** - Control OBS from your phone while mobile
- **Remote Streaming** - Control OBS from another room/location
- **Multi-PC Setups** - Control streaming PC from gaming PC
- **Collaborative Streams** - Let moderators help control scenes
- **Backup Control** - Emergency controls when main setup fails

## 📱 Mobile Usage

DiscOBS is designed for mobile use:

1. Open Discord on your phone
2. Type `!obs` once
3. Tap buttons to control everything
4. No typing required after initial setup

## 🔧 Troubleshooting

### Bot won't start

- ❌ Check Discord token is correct
- ❌ Make sure `config.py` is in same folder as `discobs.py`
- ❌ Verify Python libraries are installed

### Can't control OBS

- ❌ Make sure OBS WebSocket is enabled
- ❌ Check port number (4455 by default)
- ❌ Verify password matches (or set to `None`)

### Scene buttons don't work

- ❌ Scene names must match exactly (case-sensitive)
- ❌ Check spelling in `config.py`
- ❌ Make sure scenes exist in OBS

### Commands not responding

- ❌ Bot needs "Send Messages" permission
- ❌ "Message Content Intent" must be enabled
- ❌ Try `!obs` in a channel where bot has permissions

## 🌟 Tips

- **Test everything** before going live
- **Create a dedicated channel** for bot commands
- **Scene names are case-sensitive** - check spelling
- **Keep the command prompt open** while streaming
- **Bot works on any internet connection** - WiFi, mobile hotspot, etc.

## 📄 File Structure

```
DiscOBS/
├── discobs.py     # Main bot code (don't edit this)
├── config.py      # Your settings (edit this)
└── README.md      # This file
```

## 🎮 Commands

| Command  | Description                           |
| -------- | ------------------------------------- |
| `!obs`   | Open the main control panel           |
| `!panel` | Alternative command for control panel |

Everything else is done through the interactive buttons!

## 💡 Support

Having issues? Check that:

1. Discord bot token is correct
2. OBS WebSocket is enabled
3. Scene names match exactly
4. Bot has proper Discord permissions
5. All Python libraries are installed

---

**Created for streamers, by streamers. Happy streaming! 🎬📱**
