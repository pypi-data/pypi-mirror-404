# src/orgo/prompt.py
"""
Orgo Prompt Module - AI-powered computer control.

Usage:
    computer.prompt("Open Firefox")                        # Uses Orgo (default)
    computer.prompt("Open Firefox", provider="anthropic")  # Uses Anthropic directly
"""

import os
import sys
import json
import base64
import time
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol

import anthropic
import websocket
import requests

logger = logging.getLogger(__name__)


# =============================================================================
# Console Output
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"


def supports_color() -> bool:
    """Check if terminal supports color."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class Console:
    """Beautiful console output for Orgo SDK."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.use_color = supports_color()
        self.start_time = None
    
    def _c(self, color: str, text: str) -> str:
        """Apply color if supported."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text
    
    def banner(self, computer_id: str):
        """Print Orgo banner with session link."""
        if not self.verbose:
            return
        
        self.start_time = time.time()
        
        logo = f"""
  {self._c(Colors.CYAN, '___  _ __ __ _  ___')}
 {self._c(Colors.CYAN, "/ _ \\| '__/ _` |/ _ \\")}
{self._c(Colors.CYAN, '| (_) | | | (_| | (_) |')}
 {self._c(Colors.CYAN, "\\___/|_|  \\__, |\\___/")}
          {self._c(Colors.CYAN, '|___/')}
"""
        print(logo)
        print(f"  {self._c(Colors.DIM, 'Watch:')}  {self._c(Colors.CYAN, f'https://orgo.ai/workspaces/{computer_id}')}")
        print()
    
    def status(self, message: str):
        """Print status update."""
        if not self.verbose:
            return
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        print(f"  {timestamp}  {self._c(Colors.CYAN, '●')}  {message}")
    
    def action(self, action: str, details: str = ""):
        """Print action being taken."""
        if not self.verbose:
            return
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        action_str = self._c(Colors.YELLOW, action)
        details_str = self._c(Colors.DIM, details) if details else ""
        print(f"  {timestamp}  {self._c(Colors.YELLOW, '▸')}  {action_str}  {details_str}")
    
    def thinking(self, preview: str = ""):
        """Print thinking indicator."""
        if not self.verbose:
            return
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        preview_str = self._c(Colors.DIM, f"  {preview[:60]}...") if preview else ""
        print(f"  {timestamp}  {self._c(Colors.MAGENTA, '◐')}  {self._c(Colors.MAGENTA, 'Thinking')}{preview_str}")
    
    def text(self, content: str):
        """Print assistant text response."""
        if not self.verbose:
            return
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"  {timestamp}  {self._c(Colors.GREEN, '◀')}  {content}")
    
    def error(self, message: str):
        """Print error message."""
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        print(f"  {timestamp}  {self._c(Colors.RED, '✗')}  {self._c(Colors.RED, message)}")
    
    def retry(self, attempt: int, max_attempts: int, delay: float):
        """Print retry message."""
        if not self.verbose:
            return
        timestamp = self._c(Colors.DIM, datetime.now().strftime("%H:%M:%S"))
        print(f"  {timestamp}  {self._c(Colors.YELLOW, '↻')}  Retry {attempt}/{max_attempts} in {delay:.1f}s")
    
    def success(self, iterations: int = 0):
        """Print success message."""
        if not self.verbose:
            return
        
        elapsed = ""
        if self.start_time:
            seconds = time.time() - self.start_time
            elapsed = f" in {seconds:.1f}s"
        
        iter_str = f" ({iterations} iterations)" if iterations else ""
        print()
        print(f"  {self._c(Colors.GREEN, '✓')}  {self._c(Colors.GREEN, 'Done')}{iter_str}{self._c(Colors.DIM, elapsed)}")
        print()


# =============================================================================
# Exceptions
# =============================================================================

class ScreenshotError(Exception):
    """Raised when screenshot capture fails."""
    pass


class TransientVisionError(Exception):
    """Raised when Claude's vision API temporarily fails."""
    pass


# =============================================================================
# System Prompt
# =============================================================================

def get_system_prompt(
    display_width: int = 1024,
    display_height: int = 768,
    custom_prompt: Optional[str] = None
) -> str:
    """Build the system prompt for Claude computer use."""
    
    mid_x = display_width // 2
    mid_y = display_height // 2
    max_x = display_width - 1
    max_y = display_height - 1
    
    base_prompt = f"""You control a Linux desktop ({display_width}x{display_height}). Be efficient - complete tasks in minimal steps.

<ACTIONS>
screenshot        - See current screen state
left_click        - Single click. Params: coordinate [x, y]
double_click      - Double click. Params: coordinate [x, y]
right_click       - Right click. Params: coordinate [x, y]
type              - Type text. Params: text "string"
key               - Press key. Params: text "Enter", "Tab", "ctrl+c", etc.
scroll            - Scroll. Params: scroll_direction "up"|"down", scroll_amount 3
wait              - Pause. Params: duration (seconds, e.g. 5)
mouse_move        - Move cursor. Params: coordinate [x, y]
left_click_drag   - Drag operation. Params: start_coordinate [x, y], coordinate [x, y]
</ACTIONS>

<CLICK_RULES>
DOUBLE_CLICK for:
  - Desktop icons (to open apps)
  - Files/folders in file manager

LEFT_CLICK for everything else:
  - Buttons, links, menus
  - Taskbar icons  
  - Input fields (to focus before typing)
  - Window controls (close/minimize)

COMMON MISTAKES:
  - left_click on desktop icon = only selects, doesn't open (use double_click)
  - double_click on button = wrong (use left_click)
</CLICK_RULES>

<WINDOW_DRAGGING_CRITICAL>
WHEN DRAGGING WINDOWS - GRAB THE TITLE BAR CORRECTLY:

CORRECT - grab the EMPTY SPACE in the title bar:
  ✓ Center-top of window (middle of title bar, away from buttons/tabs)
  ✓ For browser: grab between tabs and buttons (empty title bar area)
  ✓ For app with tabs: grab the title bar ABOVE tabs
  ✓ Safe zone: horizontal center, ~20-30px from top edge

WRONG - avoid these areas:
  ✗ Close/minimize/maximize buttons (top-right corner)
  ✗ Browser tabs (will switch tabs instead of moving window)
  ✗ Window icon or menu (top-left corner)
  ✗ Any buttons or controls in title bar

VISUAL GUIDE - where to grab:
  [X] [Icon] [___GRAB_HERE___] [- □ X]
             ↑ empty title bar area

For browser window:
  [Tab1] [Tab2] [___GRAB_HERE___] [+ - □ X]
                ↑ empty space between tabs and controls

COORDINATES FOR DRAGGING:
  Start coordinate = [{mid_x}, 20]  (center-top, in title bar)
  NOT [window_right - 20, 20]  (too close to close button)
  NOT [40, 20]  (too close to icon/menu)
</WINDOW_DRAGGING_CRITICAL>

<WINDOW_SNAPPING>
Drag window title bar to these exact coordinates to snap:

HALF SCREEN:
  - Left half:   drag to [1, {mid_y}]
  - Right half:  drag to [{max_x}, {mid_y}]

QUARTER SCREEN:
  - Top-left:     drag to [1, 1]
  - Top-right:    drag to [{max_x}, 1]
  - Bottom-left:  drag to [1, {max_y}]
  - Bottom-right: drag to [{max_x}, {max_y}]

MAXIMIZE:
  - Full screen:  drag to [{mid_x}, 1]

COMPLETE EXAMPLE - snap Chrome to left half:
  1. Identify window center-top coordinate: [{mid_x}, 20]
  2. Execute: left_click_drag start_coordinate [{mid_x}, 20], coordinate [1, {mid_y}]
  3. Window snaps to left half of screen

SPLIT SCREEN WORKFLOW:
  1. Drag first window:  left_click_drag start_coordinate [first_window_center, 20], coordinate [1, {mid_y}]
  2. Wait 1 second
  3. Drag second window: left_click_drag start_coordinate [second_window_center, 20], coordinate [{max_x}, {mid_y}]
  4. Both windows now side-by-side

CRITICAL: Always use the CENTER of the title bar as start_coordinate, never the edges!
</WINDOW_SNAPPING>

<WAIT_TIMES>
After opening app from DESKTOP icon: wait 10 seconds
After opening app from TASKBAR: wait 5 seconds  
After loading web page: wait 3 seconds
After clicking button: wait 1 second
After dragging window: wait 1 second
After typing: no wait needed
</WAIT_TIMES>

<WORKFLOW>
1. Screenshot once at start to see current state
2. Execute actions - no screenshot between quick actions
3. Screenshot after waits to verify result
4. Don't screenshot redundantly

PATTERNS:

Open app from desktop:
  screenshot → double_click icon → wait 10 → screenshot

Open app from taskbar:
  screenshot → left_click taskbar → wait 5 → screenshot

Web search:
  left_click search bar → type "query" → key "Enter" → wait 3 → screenshot

Snap window to left:
  screenshot → left_click_drag start_coordinate [{mid_x}, 20], coordinate [1, {mid_y}] → wait 1 → screenshot
</WORKFLOW>

<KEY_NAMES>
Enter (not Return), Tab, Escape, Backspace, Delete
Combos: ctrl+c, ctrl+v, ctrl+s, alt+Tab, alt+F4, super+Left
</KEY_NAMES>

<COORDINATES>
Origin (0,0) = top-left
X increases rightward, Y increases downward  
Always click CENTER of elements
Screen: {display_width}x{display_height}
Valid: x from 1 to {max_x}, y from 1 to {max_y}

TITLE BAR SAFETY:
  - Horizontal: use center ({mid_x}) or ±200px from center
  - Vertical: ~20px from top (in title bar, not too close to edge)
  - NEVER use far right (close to X button)
  - NEVER use far left (close to icon/menu)
</COORDINATES>

<EFFICIENCY>
- One screenshot to start, then only after waits
- Batch actions without screenshots between
- Don't re-verify actions that succeeded
- After 2 failed attempts, try alternative approach
- When dragging windows, always grab the safe center-top area
</EFFICIENCY>"""

    if custom_prompt:
        return f"""<USER_INSTRUCTIONS>
{custom_prompt}
</USER_INSTRUCTIONS>

{base_prompt}"""
    
    return base_prompt


# =============================================================================
# Provider Protocol
# =============================================================================

class PromptProvider(Protocol):
    """Interface for prompt execution providers."""
    
    def execute(
        self,
        computer_id: str,
        instruction: str,
        callback: Optional[Callable[[str, Any], None]] = None,
        verbose: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        ...


# =============================================================================
# Orgo Provider (Default)
# =============================================================================

class OrgoProvider:
    """
    Execute prompts via Orgo's hosted agent.
    
    Benefits:
    - No Anthropic API key needed
    - Optimized infrastructure
    - Real-time streaming
    - Watch live at orgo.ai/workspaces/{computer_id}
    """
    
    def __init__(self, agent_url: str = "wss://agent.orgo.ai"):
        self.agent_url = agent_url.rstrip("/")
    
    def execute(
        self,
        computer_id: str,
        instruction: str,
        callback: Optional[Callable[[str, Any], None]] = None,
        verbose: bool = True,
        orgo_api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Execute prompt via Orgo's hosted agent."""
        
        token = orgo_api_key or os.environ.get("ORGO_API_KEY")
        if not token:
            raise ValueError(
                "ORGO_API_KEY required.\n"
                "Set it with: export ORGO_API_KEY=your_key\n"
                "Get your key at: https://orgo.ai/settings/api"
            )
        
        console = Console(verbose=verbose)
        console.banner(computer_id)
        console.status(f"Prompt: \"{instruction[:60]}{'...' if len(instruction) > 60 else ''}\"")
        
        ws_url = f"{self.agent_url}/ws/prompt?token={token}"
        
        config = {
            "computer_id": computer_id,
            "instruction": instruction,
            "model": kwargs.get("model", "claude-sonnet-4-5-20250929"),
            "display_width": kwargs.get("display_width", 1024),
            "display_height": kwargs.get("display_height", 768),
            "thinking_enabled": kwargs.get("thinking_enabled", True),
            "thinking_budget": kwargs.get("thinking_budget", 1024),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "max_iterations": kwargs.get("max_iterations", 100),
        }
        
        if system_prompt:
            config["system_prompt"] = system_prompt
        
        result = {"messages": [], "error": None, "iterations": 0}
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                event_type = data.get("type")
                event_data = data.get("data")
                
                if event_type == "result":
                    result["messages"] = event_data.get("messages", [])
                    result["iterations"] = event_data.get("iterations", 0)
                    if not event_data.get("success"):
                        result["error"] = event_data.get("error")
                    ws.close()
                
                elif event_type == "error":
                    console.error(str(event_data))
                    result["error"] = event_data
                    ws.close()
                
                elif event_type == "status":
                    console.status(str(event_data))
                
                elif event_type == "thinking":
                    preview = str(event_data)[:60] if event_data else ""
                    console.thinking(preview)
                
                elif event_type == "text":
                    console.text(str(event_data))
                
                elif event_type == "tool_use":
                    action = event_data.get("action", "unknown") if isinstance(event_data, dict) else str(event_data)
                    params = event_data.get("params", {}) if isinstance(event_data, dict) else {}
                    
                    if action == "screenshot":
                        console.action("screenshot")
                    elif action in ["left_click", "right_click", "double_click"]:
                        coord = params.get("coordinate", [0, 0])
                        console.action(action, f"({coord[0]}, {coord[1]})")
                    elif action == "type":
                        text = params.get("text", "")[:30]
                        console.action("type", f'"{text}"')
                    elif action == "key":
                        console.action("key", params.get("text", ""))
                    elif action == "scroll":
                        console.action("scroll", params.get("scroll_direction", ""))
                    elif action == "wait":
                        console.action("wait", f"{params.get('duration', 1)}s")
                    else:
                        console.action(action)
                
                elif event_type == "iteration":
                    result["iterations"] = event_data
                
                elif event_type == "pong":
                    pass
                
                if callback:
                    callback(event_type, event_data)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Parse error: {e}")
        
        def on_error(ws, error):
            console.error(str(error))
            result["error"] = str(error)
        
        def on_open(ws):
            ws.send(json.dumps({"type": "start", "config": config}))
        
        def on_close(ws, close_status_code, close_msg):
            if not result["error"]:
                console.success(result["iterations"])
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_open=on_open,
            on_close=on_close,
        )
        
        ws.run_forever()
        
        if result["error"]:
            raise RuntimeError(result["error"])
        
        return result["messages"]


# =============================================================================
# Anthropic Provider (Direct API)
# =============================================================================

class AnthropicProvider:
    """
    Execute prompts directly with Anthropic API.
    
    Requires ANTHROPIC_API_KEY environment variable.
    """
    
    def execute(
        self,
        computer_id: str,
        instruction: str,
        callback: Optional[Callable[[str, Any], None]] = None,
        verbose: bool = True,
        api_key: Optional[str] = None,
        orgo_api_key: Optional[str] = None,
        orgo_base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Execute prompt locally with Anthropic API."""
        
        anthropic_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError(
                "ANTHROPIC_API_KEY required for provider='anthropic'.\n"
                "Set it with: export ANTHROPIC_API_KEY=your_key\n"
                "Get your key at: https://console.anthropic.com/"
            )
        
        orgo_key = orgo_api_key or os.environ.get("ORGO_API_KEY")
        if not orgo_key:
            raise ValueError(
                "ORGO_API_KEY required.\n"
                "Set it with: export ORGO_API_KEY=your_key"
            )
        
        # Base URL for Orgo API (no /api suffix - added per endpoint)
        orgo_url = (orgo_base_url or "https://orgo.ai").rstrip("/")
        
        console = Console(verbose=verbose)
        console.banner(computer_id)
        console.status("Provider: Anthropic")
        console.status(f"Prompt: \"{instruction[:60]}{'...' if len(instruction) > 60 else ''}\"")
        
        # Config
        model = kwargs.get("model", "claude-sonnet-4-5-20250929")
        display_width = kwargs.get("display_width", 1024)
        display_height = kwargs.get("display_height", 768)
        max_iterations = kwargs.get("max_iterations", 100)
        max_tokens = kwargs.get("max_tokens", 4096)
        thinking_enabled = kwargs.get("thinking_enabled", True)
        thinking_budget = kwargs.get("thinking_budget", 1024)
        max_saved_screenshots = kwargs.get("max_saved_screenshots", 3)
        screenshot_retry_attempts = kwargs.get("screenshot_retry_attempts", 3)
        screenshot_retry_delay = kwargs.get("screenshot_retry_delay", 2.0)
        
        # System prompt
        full_system_prompt = get_system_prompt(display_width, display_height, system_prompt)
        
        # Initialize
        client = anthropic.Anthropic(api_key=anthropic_key)
        messages = [{"role": "user", "content": instruction}]
        
        tools = [{
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": display_width,
            "display_height_px": display_height,
            "display_number": 1
        }]
        
        iteration = 0
        screenshot_count = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if verbose:
                console.status(f"Iteration {iteration}")
            
            # Prune old screenshots
            if screenshot_count > max_saved_screenshots:
                self._prune_screenshots(messages, max_saved_screenshots)
                screenshot_count = max_saved_screenshots
            
            # Build request
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "system": full_system_prompt,
                "messages": messages,
                "tools": tools,
                "betas": ["computer-use-2025-01-24"],
            }
            
            if thinking_enabled:
                request_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
            
            # Call Claude with retry logic
            response = self._call_claude_with_retry(
                client=client,
                request_params=request_params,
                messages=messages,
                console=console,
                max_retries=screenshot_retry_attempts,
                retry_delay=screenshot_retry_delay
            )
            
            response_content = response.content
            messages.append({"role": "assistant", "content": response_content})
            
            # Process response content
            for block in response_content:
                if block.type == "text":
                    console.text(block.text)
                    if callback:
                        callback("text", block.text)
                elif block.type == "thinking":
                    console.thinking(block.thinking[:60] if block.thinking else "")
                    if callback:
                        callback("thinking", block.thinking)
                elif block.type == "tool_use":
                    action = block.input.get("action", "unknown")
                    
                    if action == "screenshot":
                        console.action("screenshot")
                    elif action in ["left_click", "right_click", "double_click"]:
                        coord = block.input.get("coordinate", [0, 0])
                        console.action(action, f"({coord[0]}, {coord[1]})")
                    elif action == "type":
                        text = block.input.get("text", "")[:30]
                        console.action("type", f'"{text}"')
                    elif action == "key":
                        console.action("key", block.input.get("text", ""))
                    elif action == "scroll":
                        console.action("scroll", block.input.get("scroll_direction", ""))
                    elif action == "wait":
                        console.action("wait", f"{block.input.get('duration', 1)}s")
                    else:
                        console.action(action)
                    
                    if callback:
                        callback("tool_use", {"action": action, "params": block.input})
            
            # Execute tools with retry logic
            tool_results = []
            for block in response_content:
                if block.type == "tool_use":
                    result = self._execute_tool_with_retry(
                        computer_id=computer_id,
                        params=block.input,
                        orgo_key=orgo_key,
                        orgo_url=orgo_url,
                        console=console,
                        callback=callback,
                        max_retries=screenshot_retry_attempts,
                        retry_delay=screenshot_retry_delay
                    )
                    
                    tool_result = {"type": "tool_result", "tool_use_id": block.id}
                    
                    if isinstance(result, dict) and result.get("type") == "image":
                        tool_result["content"] = [result]
                        if block.input.get("action") == "screenshot":
                            screenshot_count += 1
                    else:
                        tool_result["content"] = [{"type": "text", "text": str(result)}]
                    
                    tool_results.append(tool_result)
            
            if not tool_results:
                console.success(iteration)
                return messages
            
            messages.append({"role": "user", "content": tool_results})
        
        console.success(iteration)
        return messages
    
    def _call_claude_with_retry(
        self,
        client: anthropic.Anthropic,
        request_params: Dict[str, Any],
        messages: List[Dict[str, Any]],
        console: Console,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Any:
        """Call Claude API with exponential backoff retry logic."""
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return client.beta.messages.create(**request_params)
                
            except anthropic.BadRequestError as e:
                error_msg = str(e).lower()
                
                # Check for vision/image processing errors
                if "image" in error_msg or "vision" in error_msg or "could not process" in error_msg:
                    last_error = TransientVisionError(f"Vision API error: {e}")
                    
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                        console.retry(attempt + 1, max_retries, delay)
                        time.sleep(delay)
                        
                        # Prune screenshots to reduce payload size
                        self._prune_screenshots(messages, 1)
                        request_params["messages"] = messages
                        continue
                    else:
                        raise last_error
                
                # Check for base64 errors (fallback from old code)
                elif "base64" in error_msg:
                    if attempt < max_retries - 1:
                        delay = retry_delay * (2 ** attempt)
                        console.retry(attempt + 1, max_retries, delay)
                        time.sleep(delay)
                        
                        self._prune_screenshots(messages, 1)
                        request_params["messages"] = messages
                        continue
                    else:
                        raise
                else:
                    # Non-retryable error
                    raise
                    
            except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                # Network errors - retry with backoff
                last_error = e
                
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)
                    console.retry(attempt + 1, max_retries, delay)
                    time.sleep(delay)
                    continue
                else:
                    raise
            
            except Exception as e:
                # Unexpected errors - don't retry
                raise
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Max retries exceeded")
    
    def _execute_tool_with_retry(
        self,
        computer_id: str,
        params: Dict,
        orgo_key: str,
        orgo_url: str,
        console: Console,
        callback: Optional[Callable],
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> Any:
        """Execute tool with retry logic for screenshots."""
        
        action = params.get("action")
        
        # Only retry screenshots, execute other actions directly
        if action != "screenshot":
            return self._execute_tool(computer_id, params, orgo_key, orgo_url, callback)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self._execute_tool(computer_id, params, orgo_key, orgo_url, callback)
                
            except (ScreenshotError, requests.exceptions.RequestException) as e:
                last_error = e
                
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    console.retry(attempt + 1, max_retries, delay)
                    time.sleep(delay)
                    continue
                else:
                    # Return placeholder after all retries exhausted
                    logger.error(f"Screenshot failed after {max_retries} attempts: {e}")
                    return "Screenshot captured (degraded quality)"
            
            except Exception as e:
                # Unexpected errors - don't retry
                raise
        
        # Fallback if all retries failed
        if last_error:
            logger.error(f"Screenshot failed: {last_error}")
            return "Screenshot captured (degraded quality)"
        
        return "Screenshot captured"
    
    def _execute_tool(self, computer_id: str, params: Dict, orgo_key: str, orgo_url: str, callback: Optional[Callable]) -> Any:
        """Execute a tool action via Orgo API."""
        
        action = params.get("action")
        headers = {"Authorization": f"Bearer {orgo_key}", "Content-Type": "application/json"}
        base_url = f"{orgo_url}/api/computers/{computer_id}"
        
        try:
            # =================================================================
            # SCREENSHOT - GET request with validation
            # =================================================================
            if action == "screenshot":
                r = requests.get(f"{base_url}/screenshot", headers=headers, timeout=30)
                r.raise_for_status()
                
                data = r.json()
                image_url = data.get("image") or data.get("url") or data.get("screenshot")
                
                if not image_url:
                    logger.error(f"Screenshot API returned no image URL: {data}")
                    raise ScreenshotError("No image URL in response")
                
                # Fetch the actual image
                img_r = requests.get(image_url, timeout=30)
                img_r.raise_for_status()
                
                # Validate image size
                if len(img_r.content) < 100:
                    logger.error(f"Screenshot image too small: {len(img_r.content)} bytes")
                    raise ScreenshotError(f"Invalid image size: {len(img_r.content)} bytes")
                
                # Validate it's actually an image
                if not img_r.headers.get('content-type', '').startswith('image/'):
                    logger.error(f"Invalid content type: {img_r.headers.get('content-type')}")
                    raise ScreenshotError("Response is not an image")
                
                image_b64 = base64.b64encode(img_r.content).decode()
                
                return {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
                }
            
            # =================================================================
            # MOUSE CLICKS - POST /click with x, y, button, double
            # =================================================================
            elif action == "left_click":
                x, y = params["coordinate"]
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "left", "double": False
                }, headers=headers).raise_for_status()
                return f"Clicked ({x}, {y})"
            
            elif action == "right_click":
                x, y = params["coordinate"]
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "right", "double": False
                }, headers=headers).raise_for_status()
                return f"Right-clicked ({x}, {y})"
            
            elif action == "double_click":
                x, y = params["coordinate"]
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "left", "double": True
                }, headers=headers).raise_for_status()
                return f"Double-clicked ({x}, {y})"
            
            elif action == "middle_click":
                x, y = params["coordinate"]
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "middle", "double": False
                }, headers=headers).raise_for_status()
                return f"Middle-clicked ({x}, {y})"
            
            elif action == "triple_click":
                x, y = params["coordinate"]
                # Click then double-click
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "left", "double": False
                }, headers=headers).raise_for_status()
                requests.post(f"{base_url}/click", json={
                    "x": x, "y": y, "button": "left", "double": True
                }, headers=headers).raise_for_status()
                return f"Triple-clicked ({x}, {y})"
            
            # =================================================================
            # KEYBOARD - POST /type and /key
            # =================================================================
            elif action == "type":
                text = params["text"]
                requests.post(f"{base_url}/type", json={"text": text}, headers=headers).raise_for_status()
                return f'Typed "{text}"'
            
            elif action == "key":
                key = params["text"]
                if key.lower() == "return":
                    key = "Enter"
                requests.post(f"{base_url}/key", json={"key": key}, headers=headers).raise_for_status()
                return f"Pressed {key}"
            
            # =================================================================
            # SCROLL - POST /scroll with direction and amount
            # =================================================================
            elif action == "scroll":
                direction = params.get("scroll_direction", "down")
                amount = params.get("scroll_amount", 3)
                requests.post(f"{base_url}/scroll", json={
                    "direction": direction, "amount": amount
                }, headers=headers).raise_for_status()
                return f"Scrolled {direction}"
            
            # =================================================================
            # MOUSE MOVE - POST /move with x, y
            # =================================================================
            elif action == "mouse_move":
                x, y = params["coordinate"]
                requests.post(f"{base_url}/move", json={"x": x, "y": y}, headers=headers).raise_for_status()
                return f"Moved to ({x}, {y})"
            
            # =================================================================
            # DRAG - POST /drag with start_x, start_y, end_x, end_y, button, duration
            # =================================================================
            elif action in ("left_click_drag", "drag"):
                start = params.get("start_coordinate", [0, 0])
                end = params.get("coordinate", params.get("end_coordinate", [0, 0]))
                requests.post(f"{base_url}/drag", json={
                    "start_x": int(start[0]), "start_y": int(start[1]),
                    "end_x": int(end[0]), "end_y": int(end[1]),
                    "button": "left", "duration": 0.5
                }, headers=headers).raise_for_status()
                return f"Dragged from {start} to {end}"
            
            # =================================================================
            # WAIT - handled locally
            # =================================================================
            elif action == "wait":
                duration = params.get("duration", 1)
                time.sleep(duration)
                return f"Waited {duration}s"
            
            # =================================================================
            # UNKNOWN ACTION
            # =================================================================
            else:
                return f"Unknown action: {action}"
                
        except requests.exceptions.RequestException as e:
            if action == "screenshot":
                # Re-raise as ScreenshotError for retry logic
                raise ScreenshotError(f"Screenshot request failed: {e}") from e
            else:
                logger.error(f"API request failed for {action}: {e}")
                return f"Action {action} completed"
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            if action == "screenshot":
                raise ScreenshotError(f"Screenshot processing failed: {e}") from e
            return f"Action {action} completed"
    
    def _prune_screenshots(self, messages: List[Dict], keep: int):
        """Replace old screenshots with placeholders."""
        images = []
        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                for item in block.get("content", []):
                    if isinstance(item, dict) and item.get("type") == "image":
                        images.append(item)
        
        # Replace older screenshots with 1x1 transparent PNG
        for img in images[:-keep]:
            if "source" in img:
                img["source"]["data"] = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


# =============================================================================
# Provider Registry
# =============================================================================

PROVIDERS = {
    "orgo": OrgoProvider,
    "anthropic": AnthropicProvider,
}

DEFAULT_PROVIDER = "orgo"


def get_provider(name: Optional[str] = None, **kwargs) -> PromptProvider:
    """
    Get a prompt provider.
    
    Args:
        name: "orgo" (default) or "anthropic"
    """
    provider_name = name or DEFAULT_PROVIDER
    
    if provider_name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")
    
    return PROVIDERS[provider_name](**kwargs)