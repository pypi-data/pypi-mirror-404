"""
Orgo Computer - Control virtual computers with AI.

Usage:
    from orgo import Computer
    
    computer = Computer(project="your-project")
    computer.prompt("Open Firefox and search for AI news")
"""

import os as operating_system
import base64
import logging
import uuid
import io
import random
from typing import Dict, List, Any, Optional, Callable, Literal, Union
from PIL import Image
import requests
from requests.exceptions import RequestException

from .api.client import ApiClient
from .prompt import get_provider

logger = logging.getLogger(__name__)


def _generate_computer_name() -> str:
    """Generate a random computer name like 'computer-1568'"""
    return f"computer-{random.randint(1000, 9999)}"


def _print_success(message: str):
    """Print a success message with nice formatting"""
    print(f"✓ {message}")


def _print_error(message: str):
    """Print an error message with nice formatting"""
    print(f"✗ {message}")


def _print_info(message: str):
    """Print an info message with nice formatting"""
    print(f"→ {message}")


class Computer:
    """
    Control an Orgo virtual computer.
    
    Examples:
        # Create computer in new/existing project
        computer = Computer(project="my-project")
        
        # Create with specific name
        computer = Computer(project="my-project", name="dev-machine")
        
        # Connect to existing computer by ID
        computer = Computer(computer_id="abc123")
        
        # AI control (uses Orgo by default)
        computer.prompt("Open Firefox")
        
        # AI control with Anthropic directly
        computer.prompt("Open Firefox", provider="anthropic")
    """
    
    def __init__(self,
                 project: Optional[Union[str, 'Project']] = None,
                 workspace: Optional[Union[str, 'Project']] = None,  # Alias for project
                 name: Optional[str] = None,
                 computer_id: Optional[str] = None,
                 api_key: Optional[str] = None,
                 base_api_url: Optional[str] = None,
                 ram: Optional[Literal[1, 2, 4, 8, 16, 32, 64]] = None,
                 memory: Optional[Literal[1, 2, 4, 8, 16, 32, 64]] = None,
                 cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
                 os: Optional[Literal["linux", "windows"]] = None,
                 gpu: Optional[Literal["none", "a10", "l40s", "a100-40gb", "a100-80gb"]] = None,
                 image: Optional[Union[str, Any]] = None,
                 verbose: bool = True):
        """
        Initialize an Orgo virtual computer.

        Args:
            project: Project/workspace name or instance (creates if doesn't exist)
            workspace: Alias for project (preferred name going forward)
            name: Computer name (auto-generated if not provided)
            computer_id: Connect to existing computer by ID
            api_key: Orgo API key (defaults to ORGO_API_KEY env var)
            base_api_url: Custom API URL
            ram/memory: RAM in GB (1, 2, 4, 8, 16, 32, 64)
            cpu: CPU cores (1, 2, 4, 8, 16)
            os: "linux" or "windows"
            gpu: "none", "a10", "l40s", "a100-40gb", "a100-80gb"
            image: Custom image reference or Forge object
            verbose: Show console output (default: True)
        """
        # workspace is an alias for project
        if workspace is not None and project is None:
            project = workspace
        self.api_key = api_key or operating_system.environ.get("ORGO_API_KEY")
        self.base_api_url = base_api_url
        self.api = ApiClient(self.api_key, self.base_api_url)
        self.verbose = verbose
        
        if ram is None and memory is not None:
            ram = memory
        
        self.os = os or "linux"
        self.ram = ram or 2
        self.cpu = cpu or 2
        self.gpu = gpu or "none"
        self.image = image
        
        if hasattr(self.image, 'build') and callable(self.image.build):
            if self.verbose:
                _print_info("Building image from Forge object...")
            self.image = self.image.build()
        
        if computer_id:
            self.computer_id = computer_id
            self.name = name
            self.project_id = None
            self.project_name = None
            if self.verbose:
                _print_success(f"Connected to computer: {self.computer_id}")
        elif project:
            if isinstance(project, str):
                self.project_name = project
                self._initialize_with_project_name(project, name)
            else:
                from .project import Project as ProjectClass
                if isinstance(project, ProjectClass):
                    self.project_name = project.name
                    self.project_id = project.id
                    self._initialize_with_project_instance(project, name)
                else:
                    raise ValueError("project must be a string or Project instance")
        else:
            self._create_new_project_and_computer(name)
    
    # =========================================================================
    # Initialization Helpers
    # =========================================================================
    
    def _initialize_with_project_name(self, project_name: str, computer_name: Optional[str]):
        """Initialize computer with project name (create project if needed)"""
        try:
            # Try to get existing project
            project = self.api.get_project_by_name(project_name)
            self.project_id = project.get("id")
            
            # If no computer name specified, generate one
            if not computer_name:
                computer_name = _generate_computer_name()
            
            # Create the computer in this project
            self._create_computer(self.project_id, computer_name, project_name)
            
        except Exception:
            # Project doesn't exist, create it
            if self.verbose:
                _print_info(f"Creating project: {project_name}")
            project = self.api.create_project(project_name)
            self.project_id = project.get("id")
            
            # Generate name if not specified
            if not computer_name:
                computer_name = _generate_computer_name()
            
            self._create_computer(self.project_id, computer_name, project_name)
    
    def _initialize_with_project_instance(self, project: 'Project', computer_name: Optional[str]):
        """Initialize computer with Project instance"""
        # Generate name if not specified
        if not computer_name:
            computer_name = _generate_computer_name()
        
        self._create_computer(project.id, computer_name, project.name)
    
    def _create_new_project_and_computer(self, computer_name: Optional[str]):
        """Create a new project and computer when no project specified"""
        project_name = f"project-{uuid.uuid4().hex[:8]}"
        
        if self.verbose:
            _print_info(f"Creating project: {project_name}")
        
        project = self.api.create_project(project_name)
        self.project_id = project.get("id")
        self.project_name = project_name
        
        # Generate name if not specified
        if not computer_name:
            computer_name = _generate_computer_name()
        
        self._create_computer(self.project_id, computer_name, project_name)
    
    def _connect_to_existing_computer(self, computer_info: Dict[str, Any]):
        """Connect to an existing computer"""
        self.computer_id = computer_info.get("id")
        self.name = computer_info.get("name")
        if self.verbose:
            _print_success(f"Connected to: {self.name} ({self.computer_id})")
    
    def _create_computer(self, project_id: str, computer_name: str, project_name: str):
        """Create a new computer with beautiful console output"""
        self.name = computer_name
        
        # Validate parameters
        if self.ram not in [1, 2, 4, 8, 16, 32, 64]:
            raise ValueError("ram must be: 1, 2, 4, 8, 16, 32, or 64 GB")
        if self.cpu not in [1, 2, 4, 8, 16]:
            raise ValueError("cpu must be: 1, 2, 4, 8, or 16 cores")
        if self.os not in ["linux", "windows"]:
            raise ValueError("os must be: 'linux' or 'windows'")
        if self.gpu not in ["none", "a10", "l40s", "a100-40gb", "a100-80gb"]:
            raise ValueError("gpu must be: 'none', 'a10', 'l40s', 'a100-40gb', or 'a100-80gb'")
        
        # Resolve image if needed
        image_ref = self.image
        if image_ref and isinstance(image_ref, str) and not image_ref.startswith("registry.fly.io"):
            try:
                project_info = self.api.get_project(project_id)
                org_id = project_info.get("org_id", "orgo")
                response = self.api.get_latest_build(org_id, project_id, image_ref)
                if response and response.get("build"):
                    resolved = response.get("build", {}).get("imageRef")
                    if resolved:
                        image_ref = resolved
            except Exception as e:
                if self.verbose:
                    logger.warning(f"Failed to resolve image: {e}")
        
        # Create the computer
        try:
            computer = self.api.create_computer(
                project_id=project_id,
                computer_name=computer_name,
                os=self.os,
                ram=self.ram,
                cpu=self.cpu,
                gpu=self.gpu,
                image=image_ref
            )
            self.computer_id = computer.get("id")
            
            # Beautiful success message
            if self.verbose:
                _print_success(
                    f"Computer [{self.name}] successfully created under workspace [{project_name}]"
                )
                _print_info(f"ID: {self.computer_id}")
                _print_info(f"View at: https://orgo.ai/workspaces/{self.computer_id}")
        
        except Exception as e:
            if self.verbose:
                _print_error(f"Failed to create computer: {str(e)}")
            raise
    
    # =========================================================================
    # Computer Management
    # =========================================================================
    
    def status(self) -> Dict[str, Any]:
        """Get current computer status."""
        return self.api.get_computer(self.computer_id)
    
    def restart(self) -> Dict[str, Any]:
        """Restart the computer."""
        if self.verbose:
            _print_info(f"Restarting computer: {self.name}")
        result = self.api.restart_computer(self.computer_id)
        if self.verbose:
            _print_success("Computer restarted")
        return result
    
    def destroy(self) -> Dict[str, Any]:
        """Delete the computer."""
        if self.verbose:
            _print_info(f"Deleting computer: {self.name}")
        result = self.api.delete_computer(self.computer_id)
        if self.verbose:
            _print_success("Computer deleted")
        return result
    
    # =========================================================================
    # Mouse Actions
    # =========================================================================
    
    def left_click(self, x: int, y: int) -> Dict[str, Any]:
        """Left click at coordinates."""
        return self.api.left_click(self.computer_id, x, y)
    
    def right_click(self, x: int, y: int) -> Dict[str, Any]:
        """Right click at coordinates."""
        return self.api.right_click(self.computer_id, x, y)
    
    def double_click(self, x: int, y: int) -> Dict[str, Any]:
        """Double click at coordinates."""
        return self.api.double_click(self.computer_id, x, y)
    
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
             button: str = "left", duration: float = 0.5) -> Dict[str, Any]:
        """Drag from start to end coordinates."""
        return self.api.drag(self.computer_id, start_x, start_y, end_x, end_y, button, duration)
    
    def scroll(self, direction: str = "down", amount: int = 3) -> Dict[str, Any]:
        """Scroll in direction."""
        return self.api.scroll(self.computer_id, direction, amount)
    
    # =========================================================================
    # Keyboard Actions
    # =========================================================================
    
    def type(self, text: str) -> Dict[str, Any]:
        """Type text."""
        return self.api.type_text(self.computer_id, text)
    
    def key(self, key: str) -> Dict[str, Any]:
        """Press key (e.g., "Enter", "ctrl+c")."""
        return self.api.key_press(self.computer_id, key)
    
    # =========================================================================
    # Screen Capture
    # =========================================================================
    
    def screenshot(self) -> Image.Image:
        """Capture screenshot as PIL Image."""
        response = self.api.get_screenshot(self.computer_id)
        image_data = response.get("image", "")
        
        if image_data.startswith(('http://', 'https://')):
            img_response = requests.get(image_data)
            img_response.raise_for_status()
            return Image.open(io.BytesIO(img_response.content))
        else:
            return Image.open(io.BytesIO(base64.b64decode(image_data)))
    
    def screenshot_base64(self) -> str:
        """Capture screenshot as base64 string."""
        response = self.api.get_screenshot(self.computer_id)
        image_data = response.get("image", "")
        
        if image_data.startswith(('http://', 'https://')):
            img_response = requests.get(image_data)
            img_response.raise_for_status()
            return base64.b64encode(img_response.content).decode('utf-8')
        return image_data
    
    # =========================================================================
    # Code Execution
    # =========================================================================
    
    def bash(self, command: str) -> str:
        """Execute bash command."""
        response = self.api.execute_bash(self.computer_id, command)
        return response.get("output", "")
    
    def exec(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """Execute Python code."""
        return self.api.execute_python(self.computer_id, code, timeout)
    
    def wait(self, seconds: float) -> Dict[str, Any]:
        """Wait for seconds."""
        return self.api.wait(self.computer_id, seconds)
    
    # =========================================================================
    # Streaming
    # =========================================================================
    
    def start_stream(self, connection: str) -> Dict[str, Any]:
        """Start RTMP stream."""
        return self.api.start_stream(self.computer_id, connection)
    
    def stop_stream(self) -> Dict[str, Any]:
        """Stop stream."""
        return self.api.stop_stream(self.computer_id)
    
    def stream_status(self) -> Dict[str, Any]:
        """Get stream status."""
        return self.api.get_stream_status(self.computer_id)
    
    # =========================================================================
    # AI Control
    # =========================================================================
    
    def prompt(self, 
               instruction: str,
               provider: Optional[str] = None,
               verbose: bool = True,
               callback: Optional[Callable[[str, Any], None]] = None,
               model: str = "claude-sonnet-4-5-20250929",
               display_width: int = 1024,
               display_height: int = 768,
               thinking_enabled: bool = True,
               thinking_budget: int = 1024,
               max_tokens: int = 4096,
               max_iterations: int = 100,
               max_saved_screenshots: int = 3,
               system_prompt: Optional[str] = None,
               api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Control the computer with natural language.
        
        Args:
            instruction: What you want the computer to do
            provider: "orgo" (default) or "anthropic"
            verbose: Show progress logs (default: True)
            callback: Optional callback for events
            model: AI model to use
            display_width: Screen width
            display_height: Screen height
            thinking_enabled: Enable extended thinking
            thinking_budget: Token budget for thinking
            max_tokens: Max response tokens
            max_iterations: Max agent iterations
            max_saved_screenshots: Screenshots to keep in context
            system_prompt: Custom instructions
            api_key: Anthropic key (only for provider="anthropic")
        
        Returns:
            List of conversation messages
        
        Examples:
            # Default: Uses Orgo hosted agent
            computer.prompt("Open Firefox and search for AI news")
            
            # Quiet mode (no logs)
            computer.prompt("Open Firefox", verbose=False)
            
            # Use Anthropic directly
            computer.prompt("Open Firefox", provider="anthropic")
            
            # With callback
            computer.prompt("Search Google", callback=lambda t, d: print(f"{t}: {d}"))
        """
        provider_instance = get_provider(provider)
        
        return provider_instance.execute(
            computer_id=self.computer_id,
            instruction=instruction,
            callback=callback,
            verbose=verbose,
            api_key=api_key,
            model=model,
            display_width=display_width,
            display_height=display_height,
            thinking_enabled=thinking_enabled,
            thinking_budget=thinking_budget,
            max_tokens=max_tokens,
            max_iterations=max_iterations,
            max_saved_screenshots=max_saved_screenshots,
            system_prompt=system_prompt,
            orgo_api_key=self.api_key,
            orgo_base_url=self.base_api_url
        )
    
    # =========================================================================
    # URL Helper
    # =========================================================================
    
    @property
    def url(self) -> str:
        """Get the URL to view this computer."""
        return f"https://orgo.ai/workspaces/{self.computer_id}"
    
    def __repr__(self):
        if hasattr(self, 'name') and self.name:
            return f"Computer(name='{self.name}', id='{self.computer_id}')"
        return f"Computer(id='{self.computer_id}')"