#!/usr/bin/env python3
"""
DaveLoop - Self-Healing Debug Agent
Orchestrates Claude Code CLI in a feedback loop until bugs are resolved.
"""

import subprocess
import sys
import os
import argparse
import threading
import time
import itertools
import json
from datetime import datetime
from pathlib import Path

# Configuration
MAX_ITERATIONS = 20
DEFAULT_TIMEOUT = 600  # 10 minutes in seconds
SCRIPT_DIR = Path(__file__).parent
PROMPT_FILE = SCRIPT_DIR / "daveloop_prompt.md"
MAESTRO_PROMPT_FILE = SCRIPT_DIR / "daveloop_maestro_prompt.md"
WEB_PROMPT_FILE = SCRIPT_DIR / "daveloop_web_prompt.md"
LOG_DIR = SCRIPT_DIR / "logs"

# Exit signals from Claude Code
SIGNAL_RESOLVED = "[DAVELOOP:RESOLVED]"
SIGNAL_BLOCKED = "[DAVELOOP:BLOCKED]"
SIGNAL_CLARIFY = "[DAVELOOP:CLARIFY]"

# ============================================================================
# ANSI Color Codes
# ============================================================================
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"

C = Colors  # Shorthand

# Enable ANSI and UTF-8 on Windows
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")  # Set console to UTF-8
    os.system("")  # Enables ANSI escape sequences in Windows terminal
    # Force UTF-8 encoding for stdout/stderr (only if not already wrapped)
    import io
    if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != 'utf-8':
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# ASCII Art Banner
# ============================================================================
BANNER = f"""{C.BRIGHT_BLUE}  ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄{C.RESET}

{C.BRIGHT_BLUE}{C.BOLD}  ██████╗  █████╗ ██╗   ██╗███████╗██╗      ██████╗  ██████╗ ██████╗
  ██╔══██╗██╔══██╗██║   ██║██╔════╝██║     ██╔═══██╗██╔═══██╗██╔══██╗
  ██║  ██║███████║██║   ██║█████╗  ██║     ██║   ██║██║   ██║██████╔╝
  ██║  ██║██╔══██║╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║   ██║██╔═══╝
  ██████╔╝██║  ██║ ╚████╔╝ ███████╗███████╗╚██████╔╝╚██████╔╝██║
  ╚═════╝ ╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝{C.RESET}

{C.BRIGHT_BLUE}  ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄ · ✦ · ❄{C.RESET}

{C.BRIGHT_WHITE}{C.BOLD}                    Self-Healing Debug Agent{C.RESET}
{C.DIM}                Powered by Claude Code · Autonomous{C.RESET}"""

# ============================================================================
# UI Components
# ============================================================================
def print_header_box(title: str, color: str = C.BRIGHT_BLUE):
    """Print a header."""
    print(f"{color}{C.BOLD}┌─ {title} {'─' * (66 - len(title))}┐{C.RESET}")

def print_section(title: str, color: str = C.BRIGHT_BLUE):
    """Print a section divider."""
    print(f"\n{color}{C.BOLD}◆ {title}{C.RESET}")
    print(f"{color}{'─' * 70}{C.RESET}")

def print_status(label: str, value: str, color: str = C.WHITE):
    """Print a status line."""
    print(f"  {C.BRIGHT_BLUE}│{C.RESET} {C.DIM}{label}:{C.RESET} {color}{value}{C.RESET}")

def print_iteration_header(iteration: int, max_iter: int):
    """Print the iteration header with visual progress."""
    progress = iteration / max_iter
    bar_width = 25
    filled = int(bar_width * progress)
    empty = bar_width - filled
    bar = '█' * filled + '░' * empty

    print(f"""
{C.BRIGHT_BLUE}  ──────────────────────────────────────────────────────────────────────{C.RESET}
{C.BRIGHT_WHITE}{C.BOLD}                         ITERATION {iteration}/{max_iter}{C.RESET}
{C.BRIGHT_BLUE}                      [{bar}] {int(progress*100)}%{C.RESET}
{C.BRIGHT_BLUE}  ──────────────────────────────────────────────────────────────────────{C.RESET}
""")

def print_success_box(message: str = ""):
    """Print an epic success message."""
    print(f"""
{C.BRIGHT_GREEN}{C.BOLD}  ███████╗██╗   ██╗ ██████╗ ██████╗███████╗███████╗███████╗
  ██╔════╝██║   ██║██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝
  ███████╗██║   ██║██║     ██║     █████╗  ███████╗███████╗
  ╚════██║██║   ██║██║     ██║     ██╔══╝  ╚════██║╚════██║
  ███████║╚██████╔╝╚██████╗╚██████╗███████╗███████║███████║
  ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝╚══════╝╚══════╝╚══════╝{C.RESET}

{C.BRIGHT_WHITE}{C.BOLD}                  ✓ BUG SUCCESSFULLY RESOLVED{C.RESET}
""")

def print_error_box(message: str):
    """Print an error message."""
    print(f"""
{C.BRIGHT_RED}╭{'─' * 70}╮
│{C.RESET} {C.BOLD}{C.BRIGHT_RED}✗ ERROR{C.RESET}                                                              {C.BRIGHT_RED}│
│{C.RESET} {C.WHITE}{message[:66]}{C.RESET} {C.BRIGHT_RED}│
╰{'─' * 70}╯{C.RESET}
""")

def print_warning_box(message: str):
    """Print a warning message."""
    print(f"""
{C.BRIGHT_YELLOW}╭{'─' * 70}╮
│{C.RESET} {C.BOLD}{C.BRIGHT_YELLOW}⚠ WARNING{C.RESET}                                                            {C.BRIGHT_YELLOW}│
│{C.RESET} {C.WHITE}{message[:66]}{C.RESET} {C.BRIGHT_YELLOW}│
╰{'─' * 70}╯{C.RESET}
""")

# ============================================================================
# Spinner Animation
# ============================================================================
class Spinner:
    """Animated spinner for showing work in progress."""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.start_time = None

    def spin(self):
        idx = 0
        while self.running:
            elapsed = time.time() - self.start_time
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r  {C.BRIGHT_CYAN}{frame}{C.RESET} {C.BOLD}{self.message}{C.RESET} {C.DIM}({elapsed:.0f}s){C.RESET}  ")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self, final_message: str = None):
        self.running = False
        if self.thread:
            self.thread.join()
        elapsed = time.time() - self.start_time
        if final_message:
            sys.stdout.write(f"\r  {C.GREEN}✓{C.RESET} {final_message} {C.DIM}({elapsed:.1f}s){C.RESET}                    \n")
        else:
            sys.stdout.write(f"\r  {C.GREEN}✓{C.RESET} {self.message} complete {C.DIM}({elapsed:.1f}s){C.RESET}                    \n")
        sys.stdout.flush()

# ============================================================================
# Task Queue
# ============================================================================
class TaskQueue:
    """Manages multiple bug tasks in sequence."""

    def __init__(self):
        self.tasks = []  # list of {"description": str, "status": "pending"|"active"|"done"|"failed"}

    def add(self, description: str):
        """Add a new task with pending status."""
        self.tasks.append({"description": description, "status": "pending"})

    def next(self):
        """Find first pending task, set it to active, return it. None if no pending tasks."""
        for task in self.tasks:
            if task["status"] == "pending":
                task["status"] = "active"
                return task
        return None

    def current(self):
        """Return the task with status active, or None."""
        for task in self.tasks:
            if task["status"] == "active":
                return task
        return None

    def mark_done(self):
        """Set current active task to done."""
        task = self.current()
        if task:
            task["status"] = "done"

    def mark_failed(self):
        """Set current active task to failed."""
        task = self.current()
        if task:
            task["status"] = "failed"

    def remaining(self) -> int:
        """Count of pending tasks."""
        return sum(1 for t in self.tasks if t["status"] == "pending")

    def all(self):
        """Return all tasks."""
        return self.tasks

    def summary_display(self):
        """Print a nice box showing all tasks with status icons."""
        active_count = sum(1 for t in self.tasks if t["status"] == "active")
        done_count = sum(1 for t in self.tasks if t["status"] == "done")
        total = len(self.tasks)
        active_idx = next((i for i, t in enumerate(self.tasks) if t["status"] == "active"), 0)

        print(f"\n{C.BRIGHT_BLUE}{C.BOLD}◆ TASK QUEUE ({active_idx + 1}/{total} active){C.RESET}")
        print(f"{C.BRIGHT_BLUE}{'─' * 70}{C.RESET}")
        for task in self.tasks:
            desc = task["description"][:50]
            if task["status"] == "done":
                print(f"  {C.BRIGHT_GREEN}✓{C.RESET} {C.WHITE}{desc}{C.RESET}")
            elif task["status"] == "active":
                print(f"  {C.BRIGHT_CYAN}▶{C.RESET} {C.BRIGHT_WHITE}{desc}{C.RESET}  {C.DIM}(active){C.RESET}")
            elif task["status"] == "pending":
                print(f"  {C.DIM}○{C.RESET} {C.DIM}{desc}{C.RESET}    {C.DIM}(pending){C.RESET}")
            elif task["status"] == "failed":
                print(f"  {C.BRIGHT_RED}✗{C.RESET} {C.RED}{desc}{C.RESET}")
        print()


# ============================================================================
# Session Memory
# ============================================================================
def load_history(working_dir: str) -> dict:
    """Read .daveloop_history.json from working_dir. Return default if missing or corrupted."""
    history_file = Path(working_dir) / ".daveloop_history.json"
    if not history_file.exists():
        return {"sessions": []}
    try:
        data = json.loads(history_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "sessions" not in data:
            print_warning_box("Corrupted history file - resetting")
            return {"sessions": []}
        return data
    except (json.JSONDecodeError, ValueError):
        print_warning_box("Corrupted history JSON - resetting")
        return {"sessions": []}


def save_history(working_dir: str, history_data: dict):
    """Write to .daveloop_history.json. Keep only last 20 sessions."""
    history_file = Path(working_dir) / ".daveloop_history.json"
    history_data["sessions"] = history_data["sessions"][-20:]
    history_file.write_text(json.dumps(history_data, indent=2), encoding="utf-8")


def summarize_session(bug: str, outcome: str, iterations: int) -> dict:
    """Return a dict summarizing a session."""
    now = datetime.now()
    return {
        "session_id": now.strftime("%Y%m%d_%H%M%S"),
        "bug": bug,
        "outcome": outcome,
        "iterations": iterations,
        "timestamp": now.isoformat()
    }


def format_history_context(sessions: list) -> str:
    """Return markdown string summarizing recent sessions for Claude context."""
    if not sessions:
        return ""
    lines = ["## Previous DaveLoop Sessions"]
    for s in sessions[-10:]:  # Show last 10
        outcome = s.get("outcome", "UNKNOWN")
        bug = s.get("bug", "unknown")[:60]
        iters = s.get("iterations", "?")
        lines.append(f"- [{outcome}] \"{bug}\" ({iters} iterations)")
    return "\n".join(lines)


def print_history_box(sessions: list):
    """Print a nice UI box showing loaded history."""
    if not sessions:
        return
    print(f"\n{C.BRIGHT_BLUE}{C.BOLD}◆ SESSION HISTORY{C.RESET}")
    print(f"{C.BRIGHT_BLUE}{'─' * 70}{C.RESET}")
    for s in sessions[-10:]:
        outcome = s.get("outcome", "UNKNOWN")
        bug = s.get("bug", "unknown")[:55]
        iters = s.get("iterations", "?")
        if outcome == "RESOLVED":
            print(f"  {C.BRIGHT_GREEN}✓{C.RESET} {C.WHITE}{bug}{C.RESET} {C.DIM}({iters} iter){C.RESET}")
        else:
            print(f"  {C.BRIGHT_RED}✗{C.RESET} {C.WHITE}{bug}{C.RESET} {C.DIM}({iters} iter){C.RESET}")
    print()


# ============================================================================
# Output Formatter
# ============================================================================
def format_claude_output(output: str) -> str:
    """Format Claude's output with colors and sections."""
    lines = output.split('\n')
    formatted = []
    in_reasoning = False
    in_code = False

    for line in lines:
        # Reasoning block
        if "=== DAVELOOP REASONING ===" in line:
            in_reasoning = True
            formatted.append(f"\n{C.BRIGHT_YELLOW}┌{'─'*50}┐{C.RESET}")
            formatted.append(f"{C.BRIGHT_YELLOW}│{C.BOLD} 🧠 REASONING{C.RESET}")
            formatted.append(f"{C.BRIGHT_YELLOW}├{'─'*50}┤{C.RESET}")
            continue
        elif "===========================" in line and in_reasoning:
            in_reasoning = False
            formatted.append(f"{C.BRIGHT_YELLOW}└{'─'*50}┘{C.RESET}\n")
            continue

        # Verification block
        if "=== VERIFICATION ===" in line:
            formatted.append(f"\n{C.BRIGHT_GREEN}┌{'─'*50}┐{C.RESET}")
            formatted.append(f"{C.BRIGHT_GREEN}│{C.BOLD} ✓ VERIFICATION{C.RESET}")
            formatted.append(f"{C.BRIGHT_GREEN}├{'─'*50}┤{C.RESET}")
            continue
        elif "====================" in line:
            formatted.append(f"{C.BRIGHT_GREEN}└{'─'*50}┘{C.RESET}\n")
            continue

        # Code blocks
        if line.strip().startswith("```"):
            in_code = not in_code
            if in_code:
                formatted.append(f"{C.DIM}┌─ code ────────────────────────────────{C.RESET}")
            else:
                formatted.append(f"{C.DIM}└───────────────────────────────────────{C.RESET}")
            continue

        # Reasoning labels
        if in_reasoning:
            if line.startswith("KNOWN:"):
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {C.CYAN}KNOWN:{C.RESET}{line[6:]}")
            elif line.startswith("UNKNOWN:"):
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {C.MAGENTA}UNKNOWN:{C.RESET}{line[8:]}")
            elif line.startswith("HYPOTHESIS:"):
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {C.YELLOW}HYPOTHESIS:{C.RESET}{line[11:]}")
            elif line.startswith("NEXT ACTION:"):
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {C.GREEN}NEXT ACTION:{C.RESET}{line[12:]}")
            elif line.startswith("WHY:"):
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {C.BLUE}WHY:{C.RESET}{line[4:]}")
            else:
                formatted.append(f"{C.BRIGHT_YELLOW}│{C.RESET} {line}")
            continue

        # Exit signals - dim them out, don't make prominent
        if "[DAVELOOP:RESOLVED]" in line:
            formatted.append(f"  {C.DIM}→ [Exit signal: RESOLVED]{C.RESET}")
            continue
        elif "[DAVELOOP:BLOCKED]" in line:
            formatted.append(f"  {C.DIM}→ [Exit signal: BLOCKED]{C.RESET}")
            continue
        elif "[DAVELOOP:CLARIFY]" in line:
            formatted.append(f"  {C.DIM}→ [Exit signal: CLARIFY]{C.RESET}")
            continue

        # Code content
        if in_code:
            formatted.append(f"{C.DIM}│{C.RESET} {C.WHITE}{line}{C.RESET}")
            continue

        # Regular content
        formatted.append(f"  {line}")

    return '\n'.join(formatted)

# ============================================================================
# Input Monitor
# ============================================================================
class InputMonitor:
    """Daemon thread that reads stdin for commands while Claude is running.

    After detecting a command, stops reading stdin so that input() calls
    in the main thread can safely read without a race condition.
    Call resume_reading() after the main thread is done with input().
    """

    VALID_COMMANDS = ("wait", "pause", "add", "done")

    def __init__(self):
        self._command = None
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._running = False
        self._read_gate = threading.Event()
        self._read_gate.set()  # Start with reading enabled

    def start(self):
        """Start monitoring stdin."""
        self._running = True
        self._thread.start()

    def stop(self):
        """Stop monitoring stdin."""
        self._running = False
        self._read_gate.set()  # Unblock the thread so it can exit

    def resume_reading(self):
        """Resume reading stdin after an interrupt has been handled."""
        self._read_gate.set()

    def _read_loop(self):
        """Read lines from stdin, looking for valid commands."""
        while self._running:
            # Wait until reading is enabled (blocks after a command is detected)
            self._read_gate.wait()
            if not self._running:
                break
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                cmd = line.strip().lower()
                if cmd in self.VALID_COMMANDS:
                    with self._lock:
                        self._command = cmd
                    # Stop reading so input() in the main thread has no competition
                    self._read_gate.clear()
            except (EOFError, OSError):
                break

    def has_command(self) -> bool:
        """Check if a command has been received."""
        with self._lock:
            return self._command is not None

    def get_command(self) -> str:
        """Get and clear the current command."""
        with self._lock:
            cmd = self._command
            self._command = None
            return cmd


# ============================================================================
# Core Functions
# ============================================================================
def load_prompt() -> str:
    """Load the DaveLoop system prompt."""
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    else:
        print_warning_box(f"Prompt file not found: {PROMPT_FILE}")
        return "You are debugging. Fix the bug. Output [DAVELOOP:RESOLVED] when done."


def load_maestro_prompt() -> str:
    """Load the Maestro mobile testing prompt."""
    if MAESTRO_PROMPT_FILE.exists():
        return MAESTRO_PROMPT_FILE.read_text(encoding="utf-8")
    else:
        print_warning_box(f"Maestro prompt file not found: {MAESTRO_PROMPT_FILE}")
        return None


def load_web_prompt() -> str:
    """Load the Web UI testing prompt."""
    if WEB_PROMPT_FILE.exists():
        return WEB_PROMPT_FILE.read_text(encoding="utf-8")
    else:
        print_warning_box(f"Web prompt file not found: {WEB_PROMPT_FILE}")
        return None


def find_claude_cli():
    """Find Claude CLI executable path."""
    import platform
    import shutil

    # 1. Check environment variable (highest priority)
    env_path = os.environ.get('CLAUDE_CLI_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. Try common installation paths
    is_windows = platform.system() == "Windows"
    if is_windows:
        common_paths = [
            os.path.expanduser("~\\AppData\\Local\\Programs\\claude\\claude.cmd"),
            os.path.expanduser("~\\AppData\\Roaming\\npm\\claude.cmd"),
            "C:\\Program Files\\Claude\\claude.cmd",
            "C:\\Program Files (x86)\\Claude\\claude.cmd",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    else:
        common_paths = [
            "/usr/local/bin/claude",
            "/usr/bin/claude",
            os.path.expanduser("~/.local/bin/claude"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path

    # 3. Check if it's in PATH
    claude_name = "claude.cmd" if is_windows else "claude"
    if shutil.which(claude_name):
        return claude_name

    # 4. Not found
    return None


def run_claude_code(prompt: str, working_dir: str = None, continue_session: bool = False, stream: bool = True, timeout: int = DEFAULT_TIMEOUT, input_monitor=None) -> str:
    """Execute Claude Code CLI with the given prompt.

    If stream=True, output is printed in real-time and also returned.
    timeout is in seconds (default 600 = 10 minutes).
    input_monitor: optional InputMonitor to check for user commands during execution.
    """
    claude_cmd = find_claude_cli()
    if not claude_cmd:
        error_msg = (
            "Claude CLI not found!\n\n"
            "Please install Claude Code CLI or set CLAUDE_CLI_PATH environment variable:\n"
            "  Windows: set CLAUDE_CLI_PATH=C:\\path\\to\\claude.cmd\n"
            "  Linux/Mac: export CLAUDE_CLI_PATH=/path/to/claude\n\n"
            "Install from: https://github.com/anthropics/claude-code"
        )
        print_error_box(error_msg)
        return "[DAVELOOP:ERROR] Claude CLI not found"

    cmd = [claude_cmd]

    if continue_session:
        cmd.append("--continue")

    cmd.extend(["-p", "--verbose", "--output-format", "stream-json", "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Task"])

    try:
        if stream:
            # Stream output in real-time
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=working_dir,
                bufsize=1  # Line buffered
            )

            # Send prompt and close stdin
            process.stdin.write(prompt)
            process.stdin.close()

            # Track start time
            start_time = time.time()

            # Read and display JSON stream output
            output_lines = []
            full_text = []

            for line in process.stdout:

                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    msg_type = data.get("type", "")


                    # Handle different message types
                    if msg_type == "assistant":
                        # Assistant text message
                        content = data.get("message", {}).get("content", [])
                        for block in content:
                            if block.get("type") == "text":
                                text = block.get("text", "")
                                for line_text in text.split('\n'):
                                    formatted = format_output_line(line_text)
                                    print(formatted)
                                full_text.append(text)
                            elif block.get("type") == "tool_use":
                                # Tool being called - show what Claude is doing
                                tool_name = block.get("name", "unknown")
                                tool_input = block.get("input", {})

                                # Format tool call based on type
                                if tool_name == "Bash":
                                    cmd = tool_input.get("command", "")
                                    cmd_display = cmd[:50] + "..." if len(cmd) > 50 else cmd
                                    tool_display = f"{C.BRIGHT_BLUE}Bash{C.RESET}({C.WHITE}{cmd_display}{C.RESET})"
                                elif tool_name == "Read":
                                    file_path = tool_input.get("file_path", "")
                                    filename = file_path.split("\\")[-1].split("/")[-1]
                                    tool_display = f"{C.BRIGHT_BLUE}Read{C.RESET}({C.WHITE}{filename}{C.RESET})"
                                elif tool_name == "Write":
                                    file_path = tool_input.get("file_path", "")
                                    filename = file_path.split("\\")[-1].split("/")[-1]
                                    tool_display = f"{C.BRIGHT_BLUE}Write{C.RESET}({C.WHITE}{filename}{C.RESET})"
                                elif tool_name == "Edit":
                                    file_path = tool_input.get("file_path", "")
                                    filename = file_path.split("\\")[-1].split("/")[-1]
                                    tool_display = f"{C.BRIGHT_BLUE}Edit{C.RESET}({C.WHITE}{filename}{C.RESET})"
                                elif tool_name == "Grep":
                                    pattern = tool_input.get("pattern", "")
                                    pattern_display = pattern[:25] + "..." if len(pattern) > 25 else pattern
                                    tool_display = f"{C.BRIGHT_BLUE}Grep{C.RESET}({C.WHITE}{pattern_display}{C.RESET})"
                                elif tool_name == "Glob":
                                    pattern = tool_input.get("pattern", "")
                                    tool_display = f"{C.BRIGHT_BLUE}Glob{C.RESET}({C.WHITE}{pattern}{C.RESET})"
                                elif tool_name == "Task":
                                    desc = tool_input.get("description", "")
                                    tool_display = f"{C.BRIGHT_BLUE}Task{C.RESET}({C.WHITE}{desc}{C.RESET})"
                                else:
                                    tool_display = f"{C.BRIGHT_BLUE}{tool_name}{C.RESET}"

                                print(f"  {C.BRIGHT_BLUE}▶{C.RESET} {tool_display}")
                                sys.stdout.flush()

                    elif msg_type == "content_block_delta":
                        # Streaming text delta
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            print(text, end='')
                            full_text.append(text)

                    elif msg_type == "tool_use":
                        # Tool being used - show what Claude is doing
                        tool_name = data.get("name", "unknown")
                        tool_input = data.get("input", {})

                        # Format tool call based on type
                        if tool_name == "Bash":
                            cmd = tool_input.get("command", "")
                            cmd_display = cmd[:50] + "..." if len(cmd) > 50 else cmd
                            tool_display = f"{C.BRIGHT_BLUE}Bash{C.RESET}({C.WHITE}{cmd_display}{C.RESET})"
                        elif tool_name == "Read":
                            file_path = tool_input.get("file_path", "")
                            filename = file_path.split("\\")[-1].split("/")[-1]
                            tool_display = f"{C.BRIGHT_BLUE}Read{C.RESET}({C.WHITE}{filename}{C.RESET})"
                        elif tool_name == "Write":
                            file_path = tool_input.get("file_path", "")
                            filename = file_path.split("\\")[-1].split("/")[-1]
                            tool_display = f"{C.BRIGHT_BLUE}Write{C.RESET}({C.WHITE}{filename}{C.RESET})"
                        elif tool_name == "Edit":
                            file_path = tool_input.get("file_path", "")
                            filename = file_path.split("\\")[-1].split("/")[-1]
                            tool_display = f"{C.BRIGHT_BLUE}Edit{C.RESET}({C.WHITE}{filename}{C.RESET})"
                        elif tool_name == "Grep":
                            pattern = tool_input.get("pattern", "")
                            pattern_display = pattern[:25] + "..." if len(pattern) > 25 else pattern
                            tool_display = f"{C.BRIGHT_BLUE}Grep{C.RESET}({C.WHITE}{pattern_display}{C.RESET})"
                        elif tool_name == "Glob":
                            pattern = tool_input.get("pattern", "")
                            tool_display = f"{C.BRIGHT_BLUE}Glob{C.RESET}({C.WHITE}{pattern}{C.RESET})"
                        elif tool_name == "Task":
                            desc = tool_input.get("description", "")
                            tool_display = f"{C.BRIGHT_BLUE}Task{C.RESET}({C.WHITE}{desc}{C.RESET})"
                        else:
                            tool_display = f"{C.BRIGHT_BLUE}{tool_name}{C.RESET}"

                        print(f"  {C.BRIGHT_BLUE}▶{C.RESET} {tool_display}")
                        sys.stdout.flush()

                    elif msg_type == "tool_result":
                        # Tool completed
                        print(f"  {C.BRIGHT_BLUE}└─{C.RESET} {C.GREEN}✓{C.RESET}")

                    elif msg_type == "user":
                        # Tool results come back as user messages
                        content = data.get("message", {}).get("content", [])
                        for block in content:
                            if block.get("type") == "tool_result":
                                print(f"  {C.BRIGHT_BLUE}└─{C.RESET} {C.GREEN}✓{C.RESET}")

                    elif msg_type == "result":
                        # Final result - skip printing as it duplicates streamed content
                        text = data.get("result", "")
                        if text:
                            full_text.append(text)

                    elif msg_type == "error":
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        print(f"  {C.RED}ERROR: {error_msg}{C.RESET}")

                    sys.stdout.flush()

                except json.JSONDecodeError:
                    # Not JSON, just print as-is
                    print(f"  {line}")
                    full_text.append(line)

                output_lines.append(line)

                # Check for user commands from InputMonitor
                if input_monitor and input_monitor.has_command():
                    user_cmd = input_monitor.get_command()
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except Exception:
                        pass
                    return f"[DAVELOOP:INTERRUPTED:{user_cmd}]"

            process.wait(timeout=timeout)
            return '\n'.join(full_text)
        else:
            # Non-streaming mode
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=working_dir,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n{C.RED}[STDERR]{C.RESET}\n{result.stderr}"
            return output

    except subprocess.TimeoutExpired:
        return f"[DAVELOOP:TIMEOUT] Claude Code iteration timed out after {timeout // 60} minutes"
    except FileNotFoundError:
        return "[DAVELOOP:ERROR] Claude Code CLI not found. Is it installed?"
    except Exception as e:
        return f"[DAVELOOP:ERROR] {str(e)}"


def format_output_line(line: str) -> str:
    """Format a single line of Claude's output with colors."""
    # Reasoning markers
    if "=== DAVELOOP REASONING ===" in line:
        return f"""
{C.BRIGHT_BLUE}  ┌─ 🧠 REASONING ─────────────────────────────────────────────────────┐{C.RESET}"""
    if "===========================" in line:
        return f"{C.BRIGHT_BLUE}  └─────────────────────────────────────────────────────────────────────┘{C.RESET}"

    # Reasoning labels
    if line.startswith("KNOWN:"):
        return f"  {C.BRIGHT_BLUE}│{C.RESET} {C.BRIGHT_BLUE}KNOWN:{C.RESET} {C.WHITE}{line[6:]}{C.RESET}"
    if line.startswith("UNKNOWN:"):
        return f"  {C.BRIGHT_BLUE}│{C.RESET} {C.BRIGHT_BLUE}UNKNOWN:{C.RESET} {C.WHITE}{line[8:]}{C.RESET}"
    if line.startswith("HYPOTHESIS:"):
        return f"  {C.BRIGHT_BLUE}│{C.RESET} {C.BRIGHT_BLUE}HYPOTHESIS:{C.RESET} {C.WHITE}{line[11:]}{C.RESET}"
    if line.startswith("NEXT ACTION:"):
        return f"  {C.BRIGHT_BLUE}│{C.RESET} {C.BRIGHT_BLUE}NEXT:{C.RESET} {C.WHITE}{line[12:]}{C.RESET}"
    if line.startswith("WHY:"):
        return f"  {C.BRIGHT_BLUE}│{C.RESET} {C.BRIGHT_BLUE}WHY:{C.RESET} {C.WHITE}{line[4:]}{C.RESET}"

    # Exit signals - hide them, the success/error box will show
    if "[DAVELOOP:RESOLVED]" in line:
        return ""
    if "[DAVELOOP:BLOCKED]" in line:
        return ""
    if "[DAVELOOP:CLARIFY]" in line:
        return ""

    # Code blocks - hide the markers
    if line.strip().startswith("```"):
        return ""

    # Empty lines - minimal spacing
    if not line.strip():
        return ""

    # Default - white text with subtle indent
    return f"  {C.WHITE}{line}{C.RESET}"


def check_exit_condition(output: str) -> tuple[str, bool]:
    """Check if we should exit the loop."""
    if SIGNAL_RESOLVED in output:
        return "RESOLVED", True
    if SIGNAL_BLOCKED in output:
        return "BLOCKED", True
    if SIGNAL_CLARIFY in output:
        return "CLARIFY", True
    if "[DAVELOOP:ERROR]" in output:
        return "ERROR", True
    if "[DAVELOOP:TIMEOUT]" in output:
        return "TIMEOUT", False
    return "CONTINUE", False


def save_log(iteration: int, content: str, session_id: str):
    """Save iteration log to file."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"{session_id}_iteration_{iteration:02d}.log"
    log_file.write_text(content, encoding="utf-8")


# ============================================================================
# Main Entry Point
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="DaveLoop - Self-Healing Debug Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("bug", nargs="*", help="Bug description(s) or error message(s)")
    parser.add_argument("-f", "--file", help="Read bug description from file")
    parser.add_argument("-d", "--dir", help="Working directory for Claude Code")
    parser.add_argument("-m", "--max-iterations", type=int, default=MAX_ITERATIONS)
    parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout per iteration in seconds (default: 600)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--maestro", action="store_true", help="Enable Maestro mobile testing mode")
    parser.add_argument("--web", action="store_true", help="Enable Playwright web UI testing mode")

    args = parser.parse_args()

    # Clear screen and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)

    # Collect bug descriptions
    bug_descriptions = []
    if args.file:
        bug_descriptions.append(Path(args.file).read_text(encoding="utf-8"))
    elif args.bug:
        bug_descriptions.extend(args.bug)
    else:
        print(f"  {C.CYAN}Describe the bug (Ctrl+D or Ctrl+Z to finish):{C.RESET}")
        stdin_input = sys.stdin.read().strip()
        if stdin_input:
            bug_descriptions.append(stdin_input)

    if not bug_descriptions:
        print_error_box("No bug description provided")
        return 1

    # Setup
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_prompt = load_prompt()
    if args.maestro:
        maestro_prompt = load_maestro_prompt()
        if maestro_prompt:
            system_prompt = system_prompt + "\n\n---\n\n" + maestro_prompt
    elif args.web:
        web_prompt = load_web_prompt()
        if web_prompt:
            system_prompt = system_prompt + "\n\n---\n\n" + web_prompt
    working_dir = args.dir or os.getcwd()

    # Load session history
    history_data = load_history(working_dir)
    if history_data["sessions"]:
        print_history_box(history_data["sessions"])

    # Session info
    print_header_box(f"SESSION: {session_id}", C.BRIGHT_BLUE)
    print_status("Directory", working_dir, C.WHITE)
    print_status("Iterations", str(args.max_iterations), C.WHITE)
    print_status("Timeout", f"{args.timeout // 60}m per iteration", C.WHITE)
    print_status("Tasks", str(len(bug_descriptions)), C.WHITE)
    mode_name = "Maestro Mobile Testing" if args.maestro else "Playwright Web Testing" if args.web else "Autonomous"
    print_status("Mode", mode_name, C.WHITE)
    print(f"{C.BRIGHT_BLUE}└{'─' * 70}┘{C.RESET}")

    # Build task queue
    task_queue = TaskQueue()
    for desc in bug_descriptions:
        task_queue.add(desc)

    # Print controls hint
    print(f"\n{C.BRIGHT_BLUE}{C.BOLD}┌─ CONTROLS {'─' * 58}┐{C.RESET}")
    print(f"{C.BRIGHT_BLUE}│{C.RESET} Type while running:  {C.BRIGHT_WHITE}wait{C.RESET} {C.DIM}·{C.RESET} {C.BRIGHT_WHITE}pause{C.RESET} {C.DIM}·{C.RESET} {C.BRIGHT_WHITE}add{C.RESET} {C.DIM}·{C.RESET} {C.BRIGHT_WHITE}done{C.RESET}                     {C.BRIGHT_BLUE}│{C.RESET}")
    print(f"{C.BRIGHT_BLUE}└{'─' * 70}┘{C.RESET}")

    # Start input monitor
    input_monitor = InputMonitor()
    input_monitor.start()

    # Build history context for initial prompt
    history_context = ""
    if history_data["sessions"]:
        history_context = "\n\n" + format_history_context(history_data["sessions"])

    # === OUTER LOOP: iterate over tasks ===
    while True:
        task = task_queue.next()
        if task is None:
            break

        bug_input = task["description"]
        task_queue.summary_display()

        if args.maestro:
            print_section("MAESTRO TASK", C.BRIGHT_CYAN)
            section_color = C.BRIGHT_CYAN
        elif args.web:
            print_section("WEB UI TASK", C.BRIGHT_MAGENTA)
            section_color = C.BRIGHT_MAGENTA
        else:
            print_section("BUG REPORT", C.BRIGHT_RED)
            section_color = C.BRIGHT_RED
        for line in bug_input.split('\n')[:8]:
            print(f"  {section_color}{line[:70]}{C.RESET}")
        if len(bug_input.split('\n')) > 8:
            print(f"  {section_color}... +{len(bug_input.split(chr(10))) - 8} more lines{C.RESET}")
        sys.stdout.flush()

        # Initial context for this task
        if args.maestro:
            context = f"""
## Maestro Mobile Testing Task

{bug_input}
{history_context}

## Instructions

1. First, detect connected devices/emulators (run `adb devices` and/or `xcrun simctl list devices available`)
2. If no device is found, auto-launch an emulator/simulator
3. Ensure the target app is installed on the device
4. Proceed with the Maestro testing task described above
5. Before declaring success, verify by running the flow(s) 3 consecutive times - all must pass

Use the reasoning protocol before each action.
"""
        elif args.web:
            context = f"""
## Web UI Testing Task

{bug_input}
{history_context}

## Instructions

1. First, explore the project to detect the framework and find the dev server command
2. Install Playwright if not already installed (`npm install -D @playwright/test && npx playwright install chromium`)
3. Start the dev server if not already running
4. Read the source code to understand the UI components, especially any gesture/drag/interactive elements
5. Write Playwright tests in an `e2e/` directory that test the app like a real human would - use actual mouse movements, drags, clicks, hovers, keyboard input
6. Test gestures and buttons SEPARATELY - a working button does not prove the gesture works
7. Before declaring success, verify by running the tests 3 consecutive times - all must pass

Use the reasoning protocol before each action.
"""
        else:
            context = f"""
## Bug Report

{bug_input}
{history_context}

## Instructions

Analyze this bug. Gather whatever logs/information you need to understand it.
Then fix it. Use the reasoning protocol before each action.
"""

        iteration_history = []

        # === INNER LOOP: iterations for current task ===
        for iteration in range(1, args.max_iterations + 1):

            if iteration == 1:
                full_prompt = f"{system_prompt}\n\n---\n\n{context}"
                continue_session = False
            else:
                full_prompt = context
                continue_session = True

            if args.verbose:
                print(f"  {C.DIM}[DEBUG] Prompt: {len(full_prompt)} chars, continue={continue_session}{C.RESET}")

            # Show "Claude is working" indicator
            print(f"\n  {C.BRIGHT_BLUE}◆ Agent active...{C.RESET}\n")
            sys.stdout.flush()

            # Run Claude with real-time streaming output
            output = run_claude_code(
                full_prompt, working_dir,
                continue_session=continue_session,
                stream=True, timeout=args.timeout,
                input_monitor=input_monitor
            )

            print(f"\n{C.BRIGHT_BLUE}  {'─' * 70}{C.RESET}")

            # Save log
            save_log(iteration, output, session_id)
            iteration_history.append(output)

            # Check for user interrupt commands
            if "[DAVELOOP:INTERRUPTED:" in output:
                # Extract the command name
                cmd_start = output.index("[DAVELOOP:INTERRUPTED:") + len("[DAVELOOP:INTERRUPTED:")
                cmd_end = output.index("]", cmd_start)
                user_cmd = output[cmd_start:cmd_end]

                if user_cmd in ("wait", "pause"):
                    # Pause and get user correction
                    print(f"\n{C.BRIGHT_YELLOW}{C.BOLD}  \u23f8 PAUSED - DaveLoop is waiting for your input{C.RESET}")
                    print(f"{C.BRIGHT_YELLOW}  {'─' * 70}{C.RESET}")
                    print(f"  {C.WHITE}  Type your correction or additional context:{C.RESET}")
                    try:
                        human_input = input(f"  {C.WHITE}> {C.RESET}")
                    except EOFError:
                        human_input = ""
                    input_monitor.resume_reading()
                    context = f"""
## Human Correction (pause/wait command)

{human_input}

Continue debugging with this corrected context. Use the reasoning protocol before each action.
"""
                    continue

                elif user_cmd == "add":
                    # Prompt for new task, then resume current
                    print(f"\n  {C.BRIGHT_CYAN}Enter new task description:{C.RESET}")
                    try:
                        new_desc = input(f"  {C.WHITE}> {C.RESET}")
                    except EOFError:
                        new_desc = ""
                    input_monitor.resume_reading()
                    if new_desc.strip():
                        task_queue.add(new_desc.strip())
                        print(f"  {C.GREEN}✓{C.RESET} Task added to queue")
                        task_queue.summary_display()
                    # Resume current task with --continue
                    context = f"""
## Continuing after user added a new task to the queue

Continue the current debugging task. Use the reasoning protocol before each action.
"""
                    continue

                elif user_cmd == "done":
                    # Clean exit
                    input_monitor.stop()
                    session_entry = summarize_session(bug_input, "DONE_BY_USER", iteration)
                    history_data["sessions"].append(session_entry)
                    save_history(working_dir, history_data)
                    print(f"\n  {C.GREEN}✓{C.RESET} Session saved. Exiting by user request.")
                    return 0

            # Check exit condition
            signal, should_exit = check_exit_condition(output)

            if should_exit:
                if signal == "RESOLVED":
                    print_success_box("")
                    print(f"  {C.DIM}Session: {session_id}{C.RESET}")
                    print(f"  {C.DIM}Logs: {LOG_DIR}{C.RESET}\n")
                    task_queue.mark_done()
                    session_entry = summarize_session(bug_input, "RESOLVED", iteration)
                    history_data["sessions"].append(session_entry)
                    save_history(working_dir, history_data)
                    break  # Move to next task
                elif signal == "CLARIFY":
                    print_warning_box("Claude needs clarification")
                    print(f"\n  {C.BLUE}Your response:{C.RESET}")
                    try:
                        human_input = input(f"  {C.WHITE}> {C.RESET}")
                    except EOFError:
                        human_input = ""
                    input_monitor.resume_reading()
                    context = f"""
## Human Clarification

{human_input}

Continue debugging with this information. Use the reasoning protocol before each action.
"""
                    continue
                elif signal == "BLOCKED":
                    print_error_box("Claude is blocked - needs human help")
                    print_status("Session", session_id, C.WHITE)
                    print_status("Logs", str(LOG_DIR), C.WHITE)
                    print()
                    task_queue.mark_failed()
                    session_entry = summarize_session(bug_input, "BLOCKED", iteration)
                    history_data["sessions"].append(session_entry)
                    save_history(working_dir, history_data)
                    break  # Move to next task
                else:
                    print_error_box(f"Error occurred: {signal}")
                    task_queue.mark_failed()
                    session_entry = summarize_session(bug_input, "ERROR", iteration)
                    history_data["sessions"].append(session_entry)
                    save_history(working_dir, history_data)
                    break  # Move to next task

            # Prepare context for next iteration
            if args.maestro:
                context = f"""
## Iteration {iteration + 1}

The Maestro flow(s) are NOT yet passing reliably. You have full context from previous iterations.

Continue working on the flows. Check device status, inspect the UI hierarchy, fix selectors or timing issues, and re-run.
Remember: all flows must pass 3 consecutive times before resolving.
Use the reasoning protocol before each action.
"""
            elif args.web:
                context = f"""
## Iteration {iteration + 1}

The Playwright tests are NOT yet passing reliably. You have full context from previous iterations.

Continue working on the tests. Check selectors, timing, server status, and re-run.
Make sure you are testing like a real human - use actual mouse gestures, not just button clicks.
Remember: all tests must pass 3 consecutive times before resolving.
Use the reasoning protocol before each action.
"""
            else:
                context = f"""
## Iteration {iteration + 1}

The bug is NOT yet resolved. You have full context from previous iterations.

Continue debugging. Analyze what happened, determine next steps, and proceed.
Use the reasoning protocol before each action.
"""
        else:
            # Max iterations reached for this task (for-else)
            print_warning_box(f"Max iterations ({args.max_iterations}) reached for current task")
            task_queue.mark_failed()
            session_entry = summarize_session(bug_input, "MAX_ITERATIONS", args.max_iterations)
            history_data["sessions"].append(session_entry)
            save_history(working_dir, history_data)

        # Save iteration summary for this task
        LOG_DIR.mkdir(exist_ok=True)
        summary = f"# DaveLoop Session {session_id}\n\n"
        summary += f"Bug: {bug_input[:200]}...\n\n"
        summary += f"Iterations: {len(iteration_history)}\n\n"
        summary += "## Iteration History\n\n"
        for i, hist in enumerate(iteration_history, 1):
            summary += f"### Iteration {i}\n```\n{hist[:500]}...\n```\n\n"
        (LOG_DIR / f"{session_id}_summary.md").write_text(summary, encoding="utf-8")

    # === All tasks done - print final summary ===
    input_monitor.stop()

    print(f"\n{C.BRIGHT_BLUE}{C.BOLD}◆ ALL TASKS COMPLETE{C.RESET}")
    print(f"{C.BRIGHT_BLUE}{'─' * 70}{C.RESET}")
    for task in task_queue.all():
        desc = task["description"][:55]
        status = task["status"]
        if status == "done":
            print(f"  {C.BRIGHT_GREEN}✓{C.RESET} {C.WHITE}{desc}{C.RESET}")
        elif status == "failed":
            print(f"  {C.BRIGHT_RED}✗{C.RESET} {C.RED}{desc}{C.RESET}")
        else:
            print(f"  {C.DIM}○ {desc}{C.RESET}")
    print()

    print(f"  {C.DIM}Session: {session_id}{C.RESET}")
    print(f"  {C.DIM}Logs: {LOG_DIR}{C.RESET}\n")

    # Return 0 if all tasks done, 1 if any failed
    all_done = all(t["status"] == "done" for t in task_queue.all())
    return 0 if all_done else 1


if __name__ == "__main__":
    sys.exit(main())
