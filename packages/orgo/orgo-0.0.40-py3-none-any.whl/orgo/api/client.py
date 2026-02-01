"""API client for Orgo service"""

import requests
from typing import Dict, Any, Optional, List
import logging

from orgo.utils.auth import get_api_key

logger = logging.getLogger(__name__)

class ApiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = get_api_key(api_key)
        self.base_url = base_url or "https://www.orgo.ai/api"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=data)
            else:
                response = self.session.request(method, url, json=data)
            
            # Handle 405 specifically for better debugging
            if response.status_code == 405:
                logger.error(f"Method Not Allowed: {method} {url}")
                logger.error(f"Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log the full error for debugging
            logger.debug(f"API request failed: {method} {url}", exc_info=True)
            
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        raise Exception(error_data['error']) from None
                except (ValueError, KeyError):
                    pass
                raise Exception(f"Request failed with status {e.response.status_code}") from None
            
            # Generic error message without exposing internal details
            raise Exception("Failed to connect to Orgo service. Please check your connection and try again.") from None
    
    # Project methods
    def create_project(self, name: str) -> Dict[str, Any]:
        """Create a new named project"""
        return self._request("POST", "projects", {"name": name})
    
    def get_project_by_name(self, name: str) -> Dict[str, Any]:
        """Get project details by name"""
        projects = self.list_projects()
        for project in projects:
            if project.get("name") == name:
                return project
        raise Exception(f"Project '{name}' not found") from None
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details by ID"""
        return self._request("GET", f"projects/{project_id}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        response = self._request("GET", "projects")
        return response.get("projects", [])
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project and all its computers"""
        return self._request("DELETE", f"projects/{project_id}")
    
    # Computer methods
    def create_computer(self, project_id: str, computer_name: str,
                       os: str = "linux", ram: int = 2, cpu: int = 2,
                       gpu: str = "none", image: Optional[str] = None) -> Dict[str, Any]:
        """Create a new computer within a workspace/project"""
        data = {
            "workspace_id": project_id,  # API accepts both workspace_id and project_id
            "name": computer_name,
            "os": os,
            "ram": ram,
            "cpu": cpu,
            "gpu": gpu
        }
        if image:
            data["image"] = image

        return self._request("POST", "computers", data)
    
    def list_computers(self, project_id: str) -> List[Dict[str, Any]]:
        """List all computers in a project"""
        project = self.get_project(project_id)
        return project.get("desktops", [])
    
    def get_computer(self, computer_id: str) -> Dict[str, Any]:
        """Get computer details"""
        return self._request("GET", f"computers/{computer_id}")
    
    def delete_computer(self, computer_id: str) -> Dict[str, Any]:
        """Delete a computer"""
        return self._request("DELETE", f"computers/{computer_id}")
    
    def restart_computer(self, computer_id: str) -> Dict[str, Any]:
        """Restart a computer"""
        return self._request("POST", f"computers/{computer_id}/restart")
    
    # Computer control methods
    def left_click(self, computer_id: str, x: int, y: int) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/click", {
            "button": "left", "x": x, "y": y
        })
    
    def right_click(self, computer_id: str, x: int, y: int) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/click", {
            "button": "right", "x": x, "y": y
        })
    
    def double_click(self, computer_id: str, x: int, y: int) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/click", {
            "button": "left", "x": x, "y": y, "double": True
        })
    
    def drag(self, computer_id: str, start_x: int, start_y: int, 
             end_x: int, end_y: int, button: str = "left", 
             duration: float = 0.5) -> Dict[str, Any]:
        """Perform a drag operation from start to end coordinates"""
        return self._request("POST", f"computers/{computer_id}/drag", {
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "button": button,
            "duration": duration
        })
    
    def scroll(self, computer_id: str, direction: str, amount: int = 3) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/scroll", {
            "direction": direction, "amount": amount
        })
    
    def type_text(self, computer_id: str, text: str) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/type", {
            "text": text
        })
    
    def key_press(self, computer_id: str, key: str) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/key", {
            "key": key
        })
    
    def get_screenshot(self, computer_id: str) -> Dict[str, Any]:
        return self._request("GET", f"computers/{computer_id}/screenshot")
    
    def execute_bash(self, computer_id: str, command: str) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/bash", {
            "command": command
        })
    
    def execute_python(self, computer_id: str, code: str, timeout: int = 10) -> Dict[str, Any]:
        """Execute Python code on the computer"""
        return self._request("POST", f"computers/{computer_id}/exec", {
            "code": code,
            "timeout": timeout
        })
    
    def wait(self, computer_id: str, duration: float) -> Dict[str, Any]:
        return self._request("POST", f"computers/{computer_id}/wait", {
            "duration": duration
        })
    
    # Streaming methods
    def start_stream(self, computer_id: str, connection_name: str) -> Dict[str, Any]:
        """Start streaming to a configured RTMP connection"""
        return self._request("POST", f"computers/{computer_id}/stream/start", {
            "connection_name": connection_name
        })
    
    def stop_stream(self, computer_id: str) -> Dict[str, Any]:
        """Stop the active stream"""
        return self._request("POST", f"computers/{computer_id}/stream/stop")
    
    def get_stream_status(self, computer_id: str) -> Dict[str, Any]:
        """Get current stream status"""
        return self._request("GET", f"computers/{computer_id}/stream/status")

    # Build methods
    def create_build(self, org_id: str, project_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new build"""
        data = {
            "orgId": org_id,
            "projectId": project_id
        }
        if name:
            data["name"] = name
            
        return self._request("POST", "builds/create", data)

    def get_latest_build(self, org_id: str, project_id: str, name: str) -> Dict[str, Any]:
        """Get latest completed build by name"""
        return self._request("GET", "builds/latest", {
            "orgId": org_id,
            "projectId": project_id,
            "name": name
        })

    def update_build(self, build_id: str, status: str, 
                     error_message: Optional[str] = None, 
                     build_log: Optional[str] = None) -> Dict[str, Any]:
        """Update build status"""
        data = {
            "buildId": build_id,
            "status": status
        }
        if error_message:
            data["errorMessage"] = error_message
        if build_log:
            data["buildLog"] = build_log
            
        return self._request("POST", "builds/update", data)
