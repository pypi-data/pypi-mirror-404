"""Handler for /telegram command."""

import asyncio
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ....design import Colors, header, footer, SEPARATOR_WIDTH

console = Console()


def handle_telegram(args: str) -> None:
    """Handle /telegram command.

    Args:
        args: Command arguments (setup, connect, status, test, disconnect)
    """
    from ....integrations.telegram import TelegramConfig, get_config, save_config
    from ....integrations.telegram.bot import verify_token, TelegramBot

    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else ""
    subargs = subparts[1] if len(subparts) > 1 else ""

    if subcommand == "" or subcommand == "help":
        _show_telegram_help()

    elif subcommand == "setup":
        _handle_setup()

    elif subcommand == "status":
        _handle_status()

    elif subcommand == "test":
        _handle_test()

    elif subcommand == "connect":
        _handle_connect()

    elif subcommand == "disconnect":
        _handle_disconnect()

    elif subcommand == "settings":
        _handle_settings(subargs)

    elif subcommand == "commands":
        _handle_commands()

    else:
        console.print(f"[{Colors.WARNING}]Unknown subcommand: {subcommand}[/{Colors.WARNING}]")
        console.print(f"[{Colors.DIM}]Run /telegram help for usage[/{Colors.DIM}]")


def _show_telegram_help() -> None:
    """Show help for /telegram command."""
    from ....integrations.telegram import get_config

    config = get_config()

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Telegram Integration', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    # Status indicator
    if config.is_configured():
        status = f"[{Colors.SUCCESS}]configured[/{Colors.SUCCESS}]"
        if config.state.enabled:
            status += f" [{Colors.SUCCESS}](enabled)[/{Colors.SUCCESS}]"
    else:
        status = f"[{Colors.WARNING}]not configured[/{Colors.WARNING}]"

    console.print(f"  [{Colors.DIM}]Status:[/{Colors.DIM}] {status}")
    console.print()

    # Commands table
    commands = [
        ("/telegram setup", "Configure bot token and authorize chats"),
        ("/telegram status", "Show current configuration and state"),
        ("/telegram test", "Send a test message to authorized chats"),
        ("/telegram connect", "Start the Telegram bridge (foreground)"),
        ("/telegram disconnect", "Disable Telegram integration"),
        ("/telegram settings", "View/modify settings"),
        ("/telegram commands", "Show BotFather command list to copy"),
    ]

    console.print(f"  [{Colors.DIM}]Commands:[/{Colors.DIM}]")
    console.print()
    for cmd, desc in commands:
        console.print(f"    [{Colors.PRIMARY}]{cmd:24}[/{Colors.PRIMARY}] [{Colors.DIM}]{desc}[/{Colors.DIM}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()


def _handle_setup() -> None:
    """Interactive setup wizard for Telegram bot."""
    from prompt_toolkit import prompt
    from prompt_toolkit.styles import Style

    from ....integrations.telegram import TelegramConfig, get_config, save_config
    from ....integrations.telegram.bot import verify_token, TelegramBot, TelegramAPIError

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Telegram Setup', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]To create a Telegram bot:[/{Colors.DIM}]")
    console.print()
    console.print(f"  [{Colors.SUBTLE}]1. Open Telegram and search for @BotFather[/{Colors.SUBTLE}]")
    console.print(f"  [{Colors.SUBTLE}]2. Send /newbot and follow the prompts[/{Colors.SUBTLE}]")
    console.print(f"  [{Colors.SUBTLE}]3. Copy the bot token and paste below[/{Colors.SUBTLE}]")
    console.print()

    # Get current config
    config = get_config()

    # Prompt for bot token
    style = Style.from_dict({"": Colors.PRIMARY})

    try:
        token = prompt(
            "  Bot Token: ",
            style=style,
            default=config.bot_token or "",
        ).strip()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n  [{Colors.DIM}]Setup cancelled[/{Colors.DIM}]")
        return

    if not token:
        console.print(f"  [{Colors.WARNING}]No token provided, setup cancelled[/{Colors.WARNING}]")
        return

    # Verify token
    console.print()
    console.print(f"  [{Colors.DIM}]Verifying token...[/{Colors.DIM}]")

    bot_info = asyncio.run(verify_token(token))

    if not bot_info:
        console.print(f"  [{Colors.ERROR}]Invalid token. Please check and try again.[/{Colors.ERROR}]")
        return

    console.print(f"  [{Colors.SUCCESS}]Bot verified: @{bot_info.username}[/{Colors.SUCCESS}]")
    console.print()

    # Save config with token
    config.bot_token = token
    save_config(config)

    # Now wait for a user to message the bot to authorize
    console.print(f"  [{Colors.ACCENT}]Now send /start to your bot from Telegram to authorize.[/{Colors.ACCENT}]")
    console.print(f"  [{Colors.DIM}]Waiting for connection... (Ctrl+C to skip)[/{Colors.DIM}]")
    console.print()

    try:
        authorized_chat = asyncio.run(_wait_for_authorization(token))
        if authorized_chat:
            config.add_authorized_chat(authorized_chat["id"])
            config.state.enabled = True
            config.state.last_connected = datetime.now().isoformat()
            save_config(config)

            console.print(f"  [{Colors.SUCCESS}]Authorized: {authorized_chat['name']} (ID: {authorized_chat['id']})[/{Colors.SUCCESS}]")
            console.print()
            console.print(f"  [{Colors.SUCCESS}]Setup complete![/{Colors.SUCCESS}]")
            console.print(f"  [{Colors.DIM}]Run /telegram connect to start the bridge[/{Colors.DIM}]")
    except KeyboardInterrupt:
        # Save config without authorization (user can authorize later)
        save_config(config)
        console.print()
        console.print(f"  [{Colors.DIM}]Token saved. Run /telegram setup again to authorize chats.[/{Colors.DIM}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()


async def _wait_for_authorization(token: str, timeout: int = 60) -> dict | None:
    """Wait for a user to send /start to the bot.

    Args:
        token: Bot token
        timeout: Maximum seconds to wait

    Returns:
        Dict with chat id and name, or None if timeout
    """
    from ....integrations.telegram.bot import TelegramBot

    async with TelegramBot(token) as bot:
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                updates = await bot.get_updates(timeout=5)

                for update in updates:
                    if update.message and update.message.text:
                        text = update.message.text.strip()
                        # Accept /start or any message as authorization
                        if text.startswith("/start") or text:
                            chat = update.message.chat
                            user = update.message.from_user

                            name = chat.display_name
                            if user:
                                name = user.display_name

                            return {
                                "id": chat.id,
                                "name": name,
                            }
            except Exception:
                await asyncio.sleep(1)
                continue

    return None


def _handle_status() -> None:
    """Show current Telegram configuration and status."""
    from ....integrations.telegram import get_config
    from ....integrations.telegram.bot import verify_token

    config = get_config()

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Telegram Status', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    # Configuration
    if config.is_configured():
        console.print(f"  [{Colors.DIM}]Bot Token:[/{Colors.DIM}]    [{Colors.SUCCESS}]configured[/{Colors.SUCCESS}]")

        # Verify token is still valid
        bot_info = asyncio.run(verify_token(config.bot_token))
        if bot_info:
            console.print(f"  [{Colors.DIM}]Bot:[/{Colors.DIM}]          @{bot_info.username}")
        else:
            console.print(f"  [{Colors.DIM}]Bot:[/{Colors.DIM}]          [{Colors.ERROR}]token invalid[/{Colors.ERROR}]")
    else:
        console.print(f"  [{Colors.DIM}]Bot Token:[/{Colors.DIM}]    [{Colors.WARNING}]not configured[/{Colors.WARNING}]")
        console.print()
        console.print(f"  [{Colors.DIM}]Run /telegram setup to configure[/{Colors.DIM}]")
        console.print()
        console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
        console.print()
        return

    # Authorized chats
    if config.authorized_chats:
        console.print(f"  [{Colors.DIM}]Authorized:[/{Colors.DIM}]   {len(config.authorized_chats)} chat(s)")
        for chat_id in config.authorized_chats:
            console.print(f"                 [{Colors.SUBTLE}]{chat_id}[/{Colors.SUBTLE}]")
    else:
        console.print(f"  [{Colors.DIM}]Authorized:[/{Colors.DIM}]   [{Colors.WARNING}]no chats authorized[/{Colors.WARNING}]")

    # State
    console.print()
    enabled_status = f"[{Colors.SUCCESS}]yes[/{Colors.SUCCESS}]" if config.state.enabled else f"[{Colors.DIM}]no[/{Colors.DIM}]"
    console.print(f"  [{Colors.DIM}]Enabled:[/{Colors.DIM}]      {enabled_status}")

    if config.state.last_connected:
        console.print(f"  [{Colors.DIM}]Last Active:[/{Colors.DIM}]  {config.state.last_connected}")

    # Settings
    console.print()
    console.print(f"  [{Colors.DIM}]Settings:[/{Colors.DIM}]")
    console.print(f"    [{Colors.SUBTLE}]Streaming mode:[/{Colors.SUBTLE}]  {config.settings.streaming_mode}")
    console.print(f"    [{Colors.SUBTLE}]Update interval:[/{Colors.SUBTLE}] {config.settings.update_interval_ms}ms")
    console.print(f"    [{Colors.SUBTLE}]Show thinking:[/{Colors.SUBTLE}]   {config.settings.show_thinking}")
    console.print(f"    [{Colors.SUBTLE}]Show tools:[/{Colors.SUBTLE}]      {config.settings.show_tool_calls}")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()


def _handle_test() -> None:
    """Send a test message to authorized chats."""
    from ....integrations.telegram import get_config
    from ....integrations.telegram.bot import TelegramBot

    config = get_config()

    if not config.is_configured():
        console.print(f"[{Colors.WARNING}]Telegram not configured. Run /telegram setup first.[/{Colors.WARNING}]")
        return

    if not config.authorized_chats:
        console.print(f"[{Colors.WARNING}]No authorized chats. Run /telegram setup to authorize.[/{Colors.WARNING}]")
        return

    console.print()
    console.print(f"  [{Colors.DIM}]Sending test message...[/{Colors.DIM}]")

    async def send_test():
        async with TelegramBot(config.bot_token) as bot:
            bot_info = await bot.get_me()
            for chat_id in config.authorized_chats:
                try:
                    await bot.send_message(
                        chat_id,
                        f"*EmDash Test*\n\nBot `@{bot_info.username}` is connected and working.",
                        parse_mode="Markdown",
                    )
                    console.print(f"  [{Colors.SUCCESS}]Sent to chat {chat_id}[/{Colors.SUCCESS}]")
                except Exception as e:
                    console.print(f"  [{Colors.ERROR}]Failed to send to {chat_id}: {e}[/{Colors.ERROR}]")

    asyncio.run(send_test())
    console.print()


def _caffeinate_available() -> bool:
    """Check if caffeinate is available on the system.

    Returns:
        True if caffeinate is available (macOS with command installed)
    """
    import shutil
    return shutil.which("caffeinate") is not None


def _handle_connect() -> None:
    """Start the Telegram bridge in foreground mode."""
    from ....integrations.telegram import get_config, save_config

    config = get_config()

    if not config.is_configured():
        console.print(f"[{Colors.WARNING}]Telegram not configured. Run /telegram setup first.[/{Colors.WARNING}]")
        return

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Telegram Bridge', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.SUCCESS}]Bridge starting...[/{Colors.SUCCESS}]")
    console.print(f"  [{Colors.DIM}]Listening for messages. Press Ctrl+C to stop.[/{Colors.DIM}]")
    console.print()

    # Update state
    config.state.enabled = True
    config.state.last_connected = datetime.now().isoformat()
    save_config(config)

    # Check if caffeinate is available for keeping system awake
    use_caffeinate = _caffeinate_available()
    if use_caffeinate:
        console.print(f"  [{Colors.DIM}]Using caffeinate to prevent sleep[/{Colors.DIM}]")

    try:
        if use_caffeinate:
            # Use caffeinate to prevent system sleep (macOS only)
            import subprocess
            # Start caffeinate in a subprocess to keep system awake
            caffeinate_proc = subprocess.Popen(
                ["caffeinate", "-i", "-s"],  # -i: inhibit sleep, -s: system sleep
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                asyncio.run(_run_bridge(config))
            finally:
                caffeinate_proc.terminate()
                try:
                    caffeinate_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    caffeinate_proc.kill()
        else:
            asyncio.run(_run_bridge(config))
    except KeyboardInterrupt:
        console.print()
        console.print(f"  [{Colors.DIM}]Bridge stopped[/{Colors.DIM}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()


async def _run_bridge(config) -> None:
    """Run the Telegram bridge (receives messages and forwards to agent).

    Connects Telegram messages to the EmDash agent and streams
    SSE responses back as Telegram messages.
    """
    from ....integrations.telegram.bridge import TelegramBridge
    from ....integrations.telegram import save_config
    from ....server_manager import get_server_manager

    # Get server URL from server manager (starts server if needed)
    server = get_server_manager()
    server_url = server.get_server_url()
    console.print(f"  [{Colors.SUBTLE}]Server: {server_url}[/{Colors.SUBTLE}]")

    def on_message(event_type: str, data: dict) -> None:
        """Log bridge events to the console."""
        if event_type == "bridge_started":
            console.print(f"  [{Colors.SUBTLE}]Bot: @{data.get('bot', 'unknown')}[/{Colors.SUBTLE}]")
            console.print()
        elif event_type == "message_received":
            user = data.get("user", "Unknown")
            text = data.get("text", "")[:50]
            if len(data.get("text", "")) > 50:
                text += "..."
            console.print(f"  [{Colors.ACCENT}]{user}:[/{Colors.ACCENT}] {text}")
        elif event_type == "error":
            console.print(f"  [{Colors.ERROR}]Error: {data.get('error', 'unknown')}[/{Colors.ERROR}]")
        elif event_type == "send_error":
            console.print(f"  [{Colors.WARNING}]Send failed: {data.get('error', 'unknown')}[/{Colors.WARNING}]")

    bridge = TelegramBridge(config, server_url=server_url, on_message=on_message)

    try:
        await bridge.start()
    finally:
        # Save config with updated state (last_update_id, etc.)
        save_config(config)


def _handle_disconnect() -> None:
    """Disable Telegram integration."""
    from ....integrations.telegram import get_config, save_config, delete_config
    from prompt_toolkit import prompt

    config = get_config()

    if not config.is_configured():
        console.print(f"[{Colors.DIM}]Telegram is not configured.[/{Colors.DIM}]")
        return

    console.print()
    console.print(f"  [{Colors.WARNING}]This will remove your Telegram configuration.[/{Colors.WARNING}]")

    try:
        confirm = prompt("  Type 'yes' to confirm: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n  [{Colors.DIM}]Cancelled[/{Colors.DIM}]")
        return

    if confirm == "yes":
        delete_config()
        console.print(f"  [{Colors.SUCCESS}]Telegram configuration removed.[/{Colors.SUCCESS}]")
    else:
        console.print(f"  [{Colors.DIM}]Cancelled[/{Colors.DIM}]")

    console.print()


def _handle_settings(args: str) -> None:
    """View or modify Telegram settings."""
    from ....integrations.telegram import get_config, save_config

    config = get_config()

    if not config.is_configured():
        console.print(f"[{Colors.WARNING}]Telegram not configured. Run /telegram setup first.[/{Colors.WARNING}]")
        return

    if not args:
        # Show current settings
        console.print()
        console.print(f"  [{Colors.DIM}]Current Settings:[/{Colors.DIM}]")
        console.print()
        console.print(f"    [{Colors.PRIMARY}]streaming_mode[/{Colors.PRIMARY}]    = {config.settings.streaming_mode}")
        console.print(f"    [{Colors.PRIMARY}]update_interval_ms[/{Colors.PRIMARY}] = {config.settings.update_interval_ms}")
        console.print(f"    [{Colors.PRIMARY}]show_thinking[/{Colors.PRIMARY}]     = {config.settings.show_thinking}")
        console.print(f"    [{Colors.PRIMARY}]show_tool_calls[/{Colors.PRIMARY}]   = {config.settings.show_tool_calls}")
        console.print(f"    [{Colors.PRIMARY}]compact_mode[/{Colors.PRIMARY}]      = {config.settings.compact_mode}")
        console.print()
        console.print(f"  [{Colors.DIM}]Usage: /telegram settings <key> <value>[/{Colors.DIM}]")
        console.print()
        return

    # Parse key=value or key value
    parts = args.replace("=", " ").split()
    if len(parts) < 2:
        console.print(f"[{Colors.WARNING}]Usage: /telegram settings <key> <value>[/{Colors.WARNING}]")
        return

    key = parts[0]
    value = parts[1]

    # Update setting
    if key == "streaming_mode":
        if value not in ("edit", "append"):
            console.print(f"[{Colors.WARNING}]streaming_mode must be 'edit' or 'append'[/{Colors.WARNING}]")
            return
        config.settings.streaming_mode = value
    elif key == "update_interval_ms":
        try:
            config.settings.update_interval_ms = int(value)
        except ValueError:
            console.print(f"[{Colors.WARNING}]update_interval_ms must be a number[/{Colors.WARNING}]")
            return
    elif key == "show_thinking":
        config.settings.show_thinking = value.lower() in ("true", "1", "yes")
    elif key == "show_tool_calls":
        config.settings.show_tool_calls = value.lower() in ("true", "1", "yes")
    elif key == "compact_mode":
        config.settings.compact_mode = value.lower() in ("true", "1", "yes")
    else:
        console.print(f"[{Colors.WARNING}]Unknown setting: {key}[/{Colors.WARNING}]")
        return

    save_config(config)
    console.print(f"  [{Colors.SUCCESS}]Setting updated: {key} = {value}[/{Colors.SUCCESS}]")


def _handle_commands() -> None:
    """Show BotFather command list for easy copy-paste."""
    from ..constants import SLASH_COMMANDS

    console.print()
    console.print(f"[{Colors.MUTED}]{header('BotFather Commands', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Copy the following and paste to @BotFather after /setcommands:[/{Colors.DIM}]")
    console.print()
    console.print(f"  [{Colors.MUTED}]{'─' * 60}[/{Colors.MUTED}]")

    # Generate command list in BotFather format
    # Format: command - description (no leading slash, underscores instead of hyphens)
    for cmd, desc in SLASH_COMMANDS.items():
        # Skip telegram and quit commands (not useful via Telegram)
        if cmd in ("/telegram", "/quit", "/paste"):
            continue

        # Convert /cmd-name to cmd_name (BotFather format)
        botfather_cmd = cmd.lstrip("/").replace("-", "_")

        # Remove any argument placeholders from command
        if " " in botfather_cmd:
            botfather_cmd = botfather_cmd.split()[0]

        # Truncate description if too long (BotFather has limits)
        short_desc = desc.split("(")[0].strip()  # Remove parenthetical notes
        if len(short_desc) > 50:
            short_desc = short_desc[:47] + "..."

        console.print(f"  {botfather_cmd} - {short_desc}")

    console.print(f"  [{Colors.MUTED}]{'─' * 60}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Steps:[/{Colors.DIM}]")
    console.print(f"  [{Colors.SUBTLE}]1. Open @BotFather in Telegram[/{Colors.SUBTLE}]")
    console.print(f"  [{Colors.SUBTLE}]2. Send /setcommands[/{Colors.SUBTLE}]")
    console.print(f"  [{Colors.SUBTLE}]3. Select your bot[/{Colors.SUBTLE}]")
    console.print(f"  [{Colors.SUBTLE}]4. Paste the command list above[/{Colors.SUBTLE}]")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
