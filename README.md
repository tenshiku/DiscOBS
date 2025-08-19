# 🎮 DiscOBS - Discord OBS Control Bot

![Python](https://img.shields.io/badge/python-3.7+-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg) ![Discord](https://img.shields.io/badge/discord-bot-7289da.svg) ![OBS](https://img.shields.io/badge/OBS-WebSocket-purple.svg) ![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**Control your OBS Studio remotely through Discord with an easy-to-use button interface.**

I created this bot to solve a problem I had while IRL streaming. When traveling with my streaming setup, I needed a way to control OBS remotely without dealing with port forwarding at hotels or Airbnbs. The solution was simple, run a Discord bot locally that connects to OBS WebSocket, then control everything from my phone through Discord.

## ✨ Features

- 🎬 **Scene Switching** - Visual scene controls with current scene highlighting
- 🔴 **Stream Control** - Start/stop streaming with status monitoring
- 🔊 **Audio Management** - One-click mute/unmute for all audio sources
- ⚡ **Quick Actions** - Customizable emergency buttons (BRB, Intro, Outro, etc.)
- 📊 **Stream Statistics** - Real-time performance monitoring with auto-updating displays
- 🛡️ **Connection Monitoring** - Automatic scene switching when encoder connection fails (Belabox integration)
- 🎥 **Recording Control** - Independent recording management with file size tracking
- 📱 **Mobile Friendly** - Perfect for controlling from your phone
- 🧩 **Modular Design** - Enable/disable features based on your needs

## 🎯 Perfect For

- **📱 IRL Streamers** using mobile encoders (Belabox, Radxa Rock, etc.)
- **🌐 Remote Streaming** setups where OBS runs on a different computer
- **💻 Multi-PC Streamers** who want to control streaming PC from gaming PC
- **👥 Team Streams** where moderators need emergency controls
- **🎮 Mobile Control** when you need to manage your stream away from your desk

## 🎮 Commands

| Command    | Description                                                   |
| ---------- | ------------------------------------------------------------- |
| `!obs`     | 🎛️ Main control panel with scene, stream, and audio controls |
| `!stats`   | 📊 Persistent stream statistics with auto-updates             |
| `!record`  | 🎥 Recording management with duration and file size tracking  |
| `!monitor` | 🛡️ Connection monitoring and encoder status                  |

All controls use interactive buttons - no need to remember complex commands.

## 📚 Documentation

- [🏠 Wiki Home](https://github.com/tenshiku/DiscOBS/wiki) - Complete documentation and setup instructions
- [📖 Setup Guide](https://github.com/tenshiku/DiscOBS/wiki/Setup-Guide) - Get started in 10 minutes
- [⚙️ Configuration](https://github.com/tenshiku/DiscOBS/wiki/Configuration) - Customize your bot
- [🔧 Troubleshooting](https://github.com/tenshiku/DiscOBS/wiki/Troubleshooting) - Fix common issues

## 📋 Requirements

- **Python 3.7+**
- **OBS Studio** with WebSocket enabled
- **Discord Bot** with message permissions
- **Internet Connection** for Discord communication

## 🆘 Support

Having issues? Check the [🔧 Troubleshooting](https://github.com/tenshiku/DiscOBS/wiki/Troubleshooting) page or [create an issue](https://github.com/tenshiku/DiscOBS/issues).

## 📄 License

This project is open source. Feel free to modify and distribute.

---

**Ready to get started? Head to the [📚 Wiki](https://github.com/tenshiku/DiscOBS/wiki) for complete setup instructions!**

*If this bot helps your stream, consider starring the repository or donating to my ko-fi! ⭐*
