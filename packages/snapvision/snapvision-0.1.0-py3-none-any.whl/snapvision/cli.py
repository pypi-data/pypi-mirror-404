"""
CLI entry point for SnapVision.

Provides commands for configuration and running the vision assistant.
"""

import argparse
import sys
from typing import Optional

from snapvision.config import (
    SnapVisionConfig,
    save_config,
    load_config,
    config_exists,
    get_config_path,
)


# Valid modifier keys for hotkey combinations
VALID_MODIFIERS = {"ctrl", "control", "shift", "alt", "cmd", "win"}
# Valid single character keys
VALID_KEYS = set("abcdefghijklmnopqrstuvwxyz0123456789")


def validate_hotkey(hotkey: str) -> bool:
    """
    Validate a hotkey string format.
    
    Valid formats:
    - ctrl+shift+z
    - alt+s
    - ctrl+alt+q
    
    Args:
        hotkey: The hotkey string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not hotkey or "+" not in hotkey:
        return False
    
    parts = hotkey.lower().replace(" ", "").split("+")
    
    if len(parts) < 2:
        return False
    
    # Check that all parts except the last are modifiers
    modifiers = parts[:-1]
    final_key = parts[-1]
    
    # All modifiers must be valid
    for mod in modifiers:
        if mod not in VALID_MODIFIERS:
            return False
    
    # Final key must be a single character or valid key name
    if len(final_key) == 1 and final_key in VALID_KEYS:
        return True
    
    # Also allow special keys like 'space', 'enter', etc.
    special_keys = {"space", "enter", "tab", "escape", "esc", "backspace", "delete"}
    if final_key in special_keys:
        return True
    
    return False


def print_header() -> None:
    """Print the SnapVision CLI header."""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                    🔍 SnapVision                          ║")
    print("║         Local Vision Assistant for Windows                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()


def prompt_choice(prompt: str, choices: list[str], default: Optional[str] = None) -> str:
    """
    Prompt user for a choice from a list of options.
    
    Args:
        prompt: The prompt message.
        choices: List of valid choices.
        default: Default value if user just presses Enter.
    
    Returns:
        The selected choice.
    """
    choices_str = "/".join(choices)
    default_str = f" [{default}]" if default else ""
    
    while True:
        user_input = input(f"{prompt} ({choices_str}){default_str}: ").strip().lower()
        
        if not user_input and default:
            return default
        
        if user_input in choices:
            return user_input
        
        print(f"  ❌ Invalid choice. Please enter one of: {choices_str}")


def prompt_string(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    """
    Prompt user for a string input.
    
    Args:
        prompt: The prompt message.
        default: Default value if user just presses Enter.
        required: Whether the input is required.
    
    Returns:
        The user's input.
    """
    default_str = f" [{default}]" if default else ""
    required_str = " (required)" if required and not default else ""
    
    while True:
        user_input = input(f"{prompt}{default_str}{required_str}: ").strip()
        
        if not user_input and default:
            return default
        
        if user_input:
            return user_input
        
        if required:
            print("  ❌ This field is required. Please provide a value.")
        else:
            return ""


def prompt_secret(prompt: str, required: bool = True, existing: bool = False) -> str:
    """
    Prompt user for a secret/API key input.
    
    Args:
        prompt: The prompt message.
        required: Whether the input is required.
        existing: Whether there's an existing value.
    
    Returns:
        The user's input.
    """
    existing_str = " [press Enter to keep existing]" if existing else ""
    required_str = " (required)" if required and not existing else ""
    
    while True:
        user_input = input(f"{prompt}{existing_str}{required_str}: ").strip()
        
        if not user_input and existing:
            return ""  # Signal to keep existing
        
        if user_input:
            return user_input
        
        if required and not existing:
            print("  ❌ This field is required. Please provide a value.")
        else:
            return ""


def cmd_configure(args: argparse.Namespace) -> int:
    """
    Handle the 'configure' command.
    
    Interactively prompts the user for configuration values and saves them.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    print_header()
    print("📝 Configuration Setup")
    print("=" * 50)
    print()
    
    # Load existing config if available
    existing_config = load_config()
    if existing_config:
        print(f"ℹ️  Existing configuration found at: {get_config_path()}")
        print("   Press Enter to keep existing values, or type new values to update.")
        print()
    
    # OCR Provider
    print("─── OCR Settings ───")
    default_ocr = existing_config.ocr_provider if existing_config else "google"
    ocr_provider = prompt_choice(
        "OCR provider",
        choices=["google", "local"],
        default=default_ocr
    )
    
    # Google Vision API Key (only if google is selected)
    google_api_key = ""
    if ocr_provider == "google":
        has_existing_key = existing_config and existing_config.google_vision_api_key
        if has_existing_key:
            print("   (existing Google Vision API key found)")
        
        new_key = prompt_secret(
            "Google Vision API key",
            required=True,
            existing=has_existing_key
        )
        
        if new_key:
            google_api_key = new_key
        elif has_existing_key:
            google_api_key = existing_config.google_vision_api_key
    
    print()
    
    # LLM Provider
    print("─── LLM Settings ───")
    default_llm = existing_config.llm_provider if existing_config else "groq"
    llm_provider = prompt_choice(
        "LLM provider",
        choices=["groq", "openai"],
        default=default_llm
    )
    
    # LLM API Key
    has_existing_llm_key = existing_config and existing_config.llm_api_key
    if has_existing_llm_key:
        print("   (existing LLM API key found)")
    
    llm_key_prompt = f"{'Groq' if llm_provider == 'groq' else 'OpenAI'} API key"
    new_llm_key = prompt_secret(
        llm_key_prompt,
        required=True,
        existing=has_existing_llm_key
    )
    
    if new_llm_key:
        llm_api_key = new_llm_key
    elif has_existing_llm_key:
        llm_api_key = existing_config.llm_api_key
    else:
        llm_api_key = ""
    
    print()
    
    # Global Hotkey
    print("─── Hotkey Settings ───")
    print("   Format: modifier+modifier+key (e.g., ctrl+shift+z, alt+s)")
    print("   Valid modifiers: ctrl, shift, alt")
    print("   ⚠️  TYPE the hotkey as text, e.g.: ctrl+shift+z")
    
    # Get existing hotkey, but only use it as default if it's valid
    existing_hotkey = existing_config.global_hotkey if existing_config else None
    if existing_hotkey and validate_hotkey(existing_hotkey):
        default_hotkey = existing_hotkey
    else:
        default_hotkey = "ctrl+shift+z"
        if existing_hotkey:
            print(f"   (existing hotkey '{existing_hotkey}' is invalid, using default)")
    
    while True:
        global_hotkey = prompt_string(
            "Global hotkey",
            default=default_hotkey,
            required=True
        )
        
        # Validate hotkey format
        if validate_hotkey(global_hotkey):
            break
        else:
            print("  ❌ Invalid hotkey format. Use format like: ctrl+shift+z, alt+s, ctrl+alt+q")
    
    print()
    
    # Create and validate configuration
    config = SnapVisionConfig(
        ocr_provider=ocr_provider,
        google_vision_api_key=google_api_key,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        global_hotkey=global_hotkey,
    )
    
    # Validate
    errors = config.validate()
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   • {error}")
        return 1
    
    # Save configuration
    try:
        save_config(config)
        print("═" * 50)
        print("✅ Configuration saved successfully!")
        print(f"   Location: {get_config_path()}")
        print()
        print("📋 Summary:")
        print(f"   • OCR Provider: {config.ocr_provider}")
        print(f"   • LLM Provider: {config.llm_provider}")
        print(f"   • Global Hotkey: {config.global_hotkey}")
        print()
        print("🚀 Run 'snapvision start' to begin using SnapVision.")
        print()
        return 0
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return 1


def on_hotkey_triggered() -> None:
    """
    Callback function when the global hotkey is triggered.
    
    Uses hybrid approach:
    1. Google Vision API for accurate detection (celebrities, text, objects)
    2. Vision LLM to see the image + use hints for a natural response
    """
    from snapvision.ui import select_screen_region
    from snapvision.capture import capture_region
    from snapvision.vision import analyze_image as vision_analyze
    from snapvision.llm import analyze_image_with_hints
    from snapvision.config import load_config
    
    print()
    print("🎯 Hotkey triggered! Opening selection overlay...")
    
    # Show selection overlay
    result = select_screen_region()
    
    if result is None:
        print("   ❌ Selection failed - no result")
        print()
        return
    
    if result.cancelled:
        print("   ⏹️  Selection cancelled")
        print()
        return
    
    if not result.is_valid:
        print("   ❌ Invalid selection (too small)")
        print()
        return
    
    print(f"   📐 Selected region: {result.width} × {result.height} at ({result.x}, {result.y})")
    
    # Use frozen capture if available, otherwise fall back to mss capture
    if hasattr(result, 'captured_path') and result.captured_path:
        print("   ❄️  Using frozen capture...")
        from snapvision.capture import CaptureResult
        capture = CaptureResult(
            image_path=result.captured_path,
            width=result.width,
            height=result.height,
            success=True
        )
    else:
        # Fallback to current screen capture (mss)
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio()
        
        scaled_x = int(result.x * dpr)
        scaled_y = int(result.y * dpr)
        scaled_width = int(result.width * dpr)
        scaled_height = int(result.height * dpr)
        
        capture = capture_region(
            x=scaled_x,
            y=scaled_y,
            width=scaled_width,
            height=scaled_height
        )
    
    if not capture.success:
        print(f"   ❌ Capture failed: {capture.error_message}")
        print()
        return
    
    # Check for Black Screen (DRM Protection)
    from PIL import Image, ImageStat
    img = Image.open(capture.image_path)
    stat = ImageStat.Stat(img)
    # If mean brightness is near 0, it's likely a DRM black screen
    if sum(stat.mean) < 1.0:
        print("\n   🛡️  DRM Protection Detected (Black Screen)")
        print("   It looks like you're capturing a protected window (Netflix, Prime, etc.).")
        print("   FIX: Disable 'Hardware Acceleration' in your browser settings and try again.")
        print()
        return

    print(f"   ✅ Captured: {capture.image_path}")
    
    # === IMMEDIATE FEEDBACK ===
    # Show the "Processing" popup right now so the user knows something is happening.
    from snapvision.ui.popup import show_processing_popup, update_popup_text
    show_processing_popup()
    # ==========================
    
    # Load configuration
    config = load_config()
    if config is None:
        error_msg = "Failed to load configuration"
        print(f"   ❌ {error_msg}")
        update_popup_text(f"❌ {error_msg}", title="Error")
        return
    
    # Step 1: Get hints from Google Vision (for accurate detection)
    print("   🔍 Detecting with Google Vision...")
    
    vision_result = vision_analyze(
        image_path=capture.image_path,
        api_key=config.google_vision_api_key
    )
    
    # Build hints from vision results (even if partial)
    hints = []
    if vision_result.success:
        if vision_result.best_guess:
            hints.append(f"Identified as: {', '.join(vision_result.best_guess)}")
        if vision_result.web_entities:
            hints.append(f"Related entities: {', '.join(vision_result.web_entities[:5])}")
        if vision_result.text:
            hints.append(f"Text found: {vision_result.text[:200]}")
        if vision_result.labels:
            hints.append(f"Labels: {', '.join(vision_result.labels[:5])}")
    
    vision_hints = "\n".join(hints) if hints else "No specific entities detected."
    
    # ========== VERBOSE DEBUG OUTPUT ==========
    print()
    print("   " + "=" * 55)
    print("   📊 COMPLETE VISION API RESPONSE:")
    print("   " + "=" * 55)
    
    if vision_result.success:
        print(f"   ✓ Status: SUCCESS")
        
        if vision_result.best_guess:
            print(f"   🎯 Best Guess: {vision_result.best_guess}")
        else:
            print(f"   🎯 Best Guess: (none)")
            
        if vision_result.web_entities:
            print(f"   🌐 Web Entities: {vision_result.web_entities}")
        else:
            print(f"   🌐 Web Entities: (none)")
            
        if vision_result.labels:
            print(f"   🏷️  Labels: {vision_result.labels}")
        else:
            print(f"   🏷️  Labels: (none)")
            
        if vision_result.objects:
            print(f"   📦 Objects: {vision_result.objects}")
        else:
            print(f"   📦 Objects: (none)")
            
        if vision_result.text:
            print(f"   📝 Text: {repr(vision_result.text[:100])}...")
        else:
            print(f"   📝 Text: (none)")
            
        if vision_result.faces:
            print(f"   👤 Faces: {len(vision_result.faces)} detected")
        else:
            print(f"   👤 Faces: (none)")
            
        if vision_result.matching_pages:
            print(f"   🔗 Matching Pages: {vision_result.matching_pages}")
    else:
        print(f"   ✗ Status: FAILED - {vision_result.error_message}")
        # Update popup with error if vision failed completely
        # But we usually continue even if vision fails (using partial hints)
    
    print()
    print("   " + "-" * 55)
    print("   📋 FULL CONTEXT BEING SENT TO LLM:")
    print("   " + "-" * 55)
    print()
    for line in vision_hints.split('\n'):
        print(f"   {line}")
    print()
    print("   " + "-" * 55)
    print(f"   🖼️  Image: {capture.image_path}")
    print("   " + "=" * 55)
    print()
    
    # Step 2: Send image + hints to vision LLM
    print(f"   🤖 Analyzing with {config.llm_provider.upper()}...")
    
    llm_result = analyze_image_with_hints(
        image_path=capture.image_path,
        vision_hints=vision_hints,
        provider_type=config.llm_provider,
        api_key=config.llm_api_key
    )
    
    if not llm_result.success:
        print(f"   ❌ Analysis failed: {llm_result.error_message}")
        update_popup_text(f"❌ Analysis failed:\n{llm_result.error_message}", title="Error")
        print()
        return
    
    if not llm_result.is_valid:
        print("   ⚠️  No response from AI")
        update_popup_text("⚠️ No response received from AI.", title="Error")
        print()
        return
    
    # Display AI response
    print(f"   ✅ Done!")
    print()
    
    # Prepare final text for popup
    final_popup_text = llm_result.response
    
    # Append extracted text if available
    if vision_result.success and vision_result.text and len(vision_result.text.strip()) > 0:
        # Limit text length to avoid crazy large popups, but give enough context
        display_text = vision_result.text.strip()
        if len(display_text) > 1000:
            display_text = display_text[:1000] + "..."
            
        final_popup_text += f"\n\n---\n**Extracted Text:**\n{display_text}"
    
    # Show the result in a popup
    update_popup_text(final_popup_text, title="SnapVision")
    
    # Still print to console for history/debug
    print("   ┌─ " + "─" * 55)
    
    # Format and display response with word wrapping
    response_lines = llm_result.response.split('\n')
    for line in response_lines:
        # Simple word wrap for long lines
        while len(line) > 70:
            wrap_at = line[:70].rfind(' ')
            if wrap_at == -1:
                wrap_at = 70
            print(f"   │ {line[:wrap_at]}")
            line = line[wrap_at:].lstrip()
        print(f"   │ {line}")
    
    print("   └" + "─" * 57)
    print()



def cmd_stop(args: argparse.Namespace) -> int:
    """
    Handle the 'stop' command.
    
    Stops the currently running SnapVision service using the PID file.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from snapvision.utils import read_pid, remove_pid_file, is_process_running
    import signal
    import os
    
    print_header()
    
    pid = read_pid()
    
    if not pid:
        print("ℹ️  SnapVision is not running (no PID file found).")
        return 0
        
    if not is_process_running(pid):
        print("clean up stale PID file.")
        remove_pid_file()
        print("ℹ️  SnapVision is not running (stale PID file cleaned).")
        return 0
        
    print(f"🛑 Stopping SnapVision (PID: {pid})...")
    
    try:
        os.kill(pid, signal.SIGTERM)
        remove_pid_file()
        print("✅ SnapVision stopped successfully.")
    except Exception as e:
        print(f"❌ Failed to stop SnapVision: {e}")
        # Try harder on Windows? no, kill should work if we have permissions.
        # Fallback to force kill if needed? 
        # For now, let's just report error.
        return 1
        
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """
    Handle the 'start' command.
    
    Loads configuration and starts the SnapVision service with hotkey listening.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from snapvision.hotkeys import create_hotkey_listener
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from snapvision.utils import write_pid, remove_pid_file, read_pid, is_process_running
    import signal
    import atexit
    import subprocess
    import platform
    
    print_header()
    
    # --- Check for existing instance ---
    existing_pid = read_pid()
    if existing_pid and is_process_running(existing_pid):
        print(f"⚠️  SnapVision is already running (PID: {existing_pid}).")
        print()
        print("   Run 'snapvision stop' to stop it first.")
        print()
        return 1
    # -----------------------------------
    
    # --- Daemon / Background Mode Handling ---
    # By default, start in background mode (like claudebot)
    # Use --foreground to run in current terminal (for debugging)
    if not args.foreground:
        print("🚀 Starting SnapVision in background mode...")
        
        # Build the command to run self with --foreground (so it actually runs)
        # We use sys.executable (python.exe) to ensure we use the same environment
        cmd = [sys.executable, "-m", "snapvision.cli", "start", "--foreground"]
        
        if platform.system() == "Windows":
            # Windows specific flags to detach process and hide window
            # DETACHED_PROCESS = 0x00000008
            # CREATE_NO_WINDOW = 0x08000000
            creationflags = 0x00000008 | 0x08000000
            
            subprocess.Popen(
                cmd,
                creationflags=creationflags,
                close_fds=True
            )
        else:
            # POSIX (Linux/Mac)
            subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            
        print("✅ SnapVision is now running in the background!")
        print()
        print("   You can safely close this terminal.")
        print("   Use your hotkey to capture screen regions.")
        print()
        print("   To stop: snapvision stop")
        print()
        return 0
    # -----------------------------------------
    
    # Check if configuration exists
    if not config_exists():
        print("❌ No configuration found!")
        print()
        print("   Please run 'snapvision configure' first to set up SnapVision.")
        print()
        return 1
    
    # Load configuration
    config = load_config()
    if config is None:
        print("❌ Failed to load configuration!")
        print()
        print("   The configuration file may be corrupted.")
        print("   Please run 'snapvision configure' to reconfigure.")
        print()
        return 1
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   • {error}")
        print()
        print("   Please run 'snapvision configure' to fix these issues.")
        print()
        return 1
    
    # Write PID file indicating we are running
    write_pid()
    # Register cleanup to remove PID file on exit
    atexit.register(remove_pid_file)
    
    # Display status
    print("✅ Configuration loaded successfully!")
    print()
    print("📋 Current Settings:")
    print(f"   • OCR Provider: {config.ocr_provider}")
    print(f"   • LLM Provider: {config.llm_provider}")
    print(f"   • Global Hotkey: {config.global_hotkey}")
    print()
    print("═" * 50)
    print()
    print(f"🎯 SnapVision is running!")
    print(f"   Press [{config.global_hotkey.upper()}] to capture a screen region.")
    print()
    print("   Press Ctrl+C to stop.")
    print()
    
    # Create the Qt Application
    # This is required for both the Popup UI and the Screencapture UI
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    # Set up clean exit on Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create and start the hotkey listener
    listener = create_hotkey_listener(hotkey=config.global_hotkey)
    listener.start()
    
    # Create a timer to poll the hotkey listener
    # We do this instead of a while loop so the Qt Event Loop can run
    timer = QTimer()
    timer.setInterval(100)  # Check every 100ms
    
    def check_hotkey():
        # Check if hotkey was pressed (non-blocking)
        if listener.wait_for_hotkey(timeout=0):
            # Handle the hotkey in the main thread
            on_hotkey_triggered()
            
    timer.timeout.connect(check_hotkey)
    timer.start()
    
    try:
        print("⏳ Listening for hotkey...")
        
        # Start the Qt Event Loop
        # This blocks until app.quit() is called
        return app.exec()
        
    except KeyboardInterrupt:
        pass
    finally:
        # Clean shutdown
        listener.stop()
        remove_pid_file() # Ensure PID is removed
        print()
        print()
        print("👋 SnapVision stopped. Goodbye!")
        print()
    
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="snapvision",
        description="SnapVision - A local vision assistant for Windows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  snapvision configure        Set up API keys and preferences
  snapvision start            Start in background (safe to close terminal)
  snapvision start -f         Start in foreground (for debugging)
  snapvision stop             Stop the running assistant
  
For more information, visit: https://github.com/snapvision/snapvision
        """
    )
    
    # Add version argument
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="Available commands",
    )
    
    # Configure command
    configure_parser = subparsers.add_parser(
        "configure",
        help="Set up SnapVision configuration",
        description="Interactively configure SnapVision settings including API keys and hotkeys."
    )
    configure_parser.set_defaults(func=cmd_configure)
    
    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start the SnapVision service (runs in background by default)",
        description="Start SnapVision and begin listening for hotkeys. Runs in background by default."
    )
    start_parser.add_argument(
        "--foreground", "-f",
        action="store_true",
        help="Run in foreground mode (for debugging, will stop when terminal closes)"
    )
    start_parser.set_defaults(func=cmd_start)
    
    # Stop command
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop the SnapVision service",
        description="Stop the currently running SnapVision background service."
    )
    stop_parser.set_defaults(func=cmd_stop)
    
    return parser


def main() -> int:
    """
    Main entry point for the SnapVision CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command is provided, print help
    if args.command is None:
        parser.print_help()
        return 0
    
    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
