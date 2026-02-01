"""Project class for managing Orgo projects"""
import os as operating_system  # Renamed to avoid any potential conflicts
import uuid
from typing import Dict, List, Any, Optional

from .api.client import ApiClient

class Project:
    def __init__(self, 
                 name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 base_api_url: Optional[str] = None):
        """
        Initialize an Orgo project.
        
        Args:
            name: Project name. If exists, connects to it. If not, creates it.
            api_key: Orgo API key (defaults to ORGO_API_KEY env var)
            base_api_url: Custom API URL (optional)
        """
        self.api_key = api_key or operating_system.environ.get("ORGO_API_KEY")
        self.base_api_url = base_api_url
        self.api = ApiClient(self.api_key, self.base_api_url)
        
        if name:
            self.name = name
        else:
            # Generate a unique name if not provided
            self.name = f"project-{uuid.uuid4().hex[:8]}"
        
        # Try to get existing project or create new one
        self._initialize_project()
    
    def _initialize_project(self):
        """Get existing project or create new one"""
        try:
            # Try to get existing project
            project = self.api.get_project_by_name(self.name)
            self.id = project.get("id")
            self._info = project
        except Exception:
            # Project doesn't exist, create it
            project = self.api.create_project(self.name)
            self.id = project.get("id")
            self._info = project
    
    def status(self) -> Dict[str, Any]:
        """Get project status"""
        return self.api.get_project(self.id)
    
    def start(self) -> Dict[str, Any]:
        """Start all computers in the project"""
        return self.api.start_project(self.id)
    
    def stop(self) -> Dict[str, Any]:
        """Stop all computers in the project"""
        return self.api.stop_project(self.id)
    
    def restart(self) -> Dict[str, Any]:
        """Restart all computers in the project"""
        return self.api.restart_project(self.id)
    
    def destroy(self) -> Dict[str, Any]:
        """Delete the project and all its computers"""
        return self.api.delete_project(self.id)
    
    def list_computers(self) -> List[Dict[str, Any]]:
        """List all computers in this project"""
        return self.api.list_computers(self.id)
    
    def get_computer(self, computer_name: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific computer in this project by name, or the first one if no name specified"""
        computers = self.list_computers()
        if not computers:
            return None
        
        if computer_name:
            for computer in computers:
                if computer.get("name") == computer_name:
                    return computer
            return None
        else:
            # Return first computer if no name specified
            return computers[0]
    
    def __repr__(self):
        return f"Project(name='{self.name}', id='{self.id}')"