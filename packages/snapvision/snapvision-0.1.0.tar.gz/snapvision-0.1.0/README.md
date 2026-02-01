# 🔍 SnapVision

A cross-platform, local-only vision assistant with OCR and AI analysis.

SnapVision captures screen regions, performs OCR, and uses LLMs to analyze the content — all running locally on your machine.

## ✨ Features

- 🖥️ **Local-only**: No backend, no hosting, runs entirely on your machine
- 🌍 **Cross-platform**: Works on Windows, Linux (X11), and macOS
- ⌨️ **Global hotkeys**: Trigger capture from anywhere
- 🎯 **Drag-select**: Choose exactly what region to capture
- 📝 **Smart OCR**: Extract text from screenshots using Google Vision
- 🤖 **LLM Processing**: Clean and structure OCR output with Groq or OpenAI
- 💬 **ChatGPT Integration**: Continue conversations in your browser

## 📦 Installation

```bash
pip install snapvision
```

**Requirements:**
- Python 3.10 or higher
- Windows, Linux (X11), or macOS

## 🚀 Usage Guide

### 1. Setup (One-time)
Run the configuration wizard to set up your API keys:

```bash
snapvision configure
```

You'll be prompted to enter:
- **OCR Provider**: `google` (Recommended)
- **Google Vision API Key**: [Get it here](https://console.cloud.google.com/)
- **LLM Provider**: `groq` (Fastest) or `openai`
- **LLM API Key**: Get it from [Groq](https://console.groq.com/) or [OpenAI](https://platform.openai.com/)
- **Global Hotkey**: The keyboard shortcut to trigger capture (Default: `Ctrl+Shift+Z`)

### 2. Run
Start SnapVision (runs in background automatically):

```bash
snapvision start
```

That's it! You can close the terminal - SnapVision keeps running.

### 3. Capture & Analyze
1.  Press **`Ctrl+Shift+Z`** (or your custom hotkey).
2.  **Drag your mouse** to select an area on the screen.
3.  SnapVision will analyze it and show a **popup** with:
    *   🤖 **AI Summary**: A concise explanation or answer.
    *   📝 **Extracted Text**: The raw text found in the image.
4.  **Interact**:
    *   Click **"Copy"** to grab the text.
    *   Click **"Analyze with ChatGPT"** to open the topic in your browser for a deeper dive.

### 4. Stop
To stop the application at any time:

```bash
snapvision stop
```

---

## �️ Platform Support

| Platform | Status | Notes |
| :--- | :---: | :--- |
| **Windows** | ✅ Fully Supported | Best experience |
| **Linux (X11)** | ✅ Supported | Works with X11 display server |
| **Linux (Wayland)** | ⚠️ Limited | Global hotkeys may not work |
| **macOS** | ✅ Supported | May need accessibility permissions |

---

## ⚠️ Known Limitations

- **API Keys Required**: You need your own API keys for Google Vision and Groq/OpenAI.
- **Internet Required**: For API calls.
- **Wayland**: On Linux with Wayland, use XWayland for best results.

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
