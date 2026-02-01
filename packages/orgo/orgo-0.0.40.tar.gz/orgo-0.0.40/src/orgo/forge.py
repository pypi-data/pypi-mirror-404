import os
import subprocess
import logging
from typing import Optional, List, Union
import uuid

from .api.client import ApiClient

logger = logging.getLogger(__name__)

class Forge:
    def __init__(self, 
                 org_id: str, 
                 project_id: str, 
                 name: Optional[str] = None,
                 api_key: Optional[str] = None, 
                 base_api_url: Optional[str] = None):
        """
        Initialize Orgo Forge for building images.
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            name: Optional friendly name for the image (not used for registry tag currently, but for reference)
            api_key: Orgo API key
            base_api_url: Custom API URL
        """
        self.org_id = org_id
        self.project_id = project_id
        self.name = name
        self.api_key = api_key or os.environ.get("ORGO_API_KEY")
        self.base_api_url = base_api_url
        self.api = ApiClient(self.api_key, self.base_api_url)
        
        # Enforce base image
        self.steps: List[str] = ["FROM registry.fly.io/orgo-image-repo:latest"]
        
    def base(self, image: str) -> 'Forge':
        """
        DEPRECATED: Base image is now enforced to ensure CUA functionality.
        This method will log a warning and ignore the provided image.
        """
        logger.warning("Forge.base() is deprecated. The base image is enforced to 'registry.fly.io/orgo-image-repo:latest'. Ignoring provided image.")
        return self
        
    def run(self, command: str) -> 'Forge':
        """Run a command (RUN instruction)"""
        self.steps.append(f"RUN {command}")
        return self
        
    def copy(self, src: str, dest: str) -> 'Forge':
        """Copy files (COPY instruction)"""
        self.steps.append(f"COPY {src} {dest}")
        return self
        
    def git_clone(self, url: str, dest: str) -> 'Forge':
        """Clone a git repository"""
        # Ensure git is installed or use a base image with git
        self.steps.append(f"RUN git clone {url} {dest}")
        return self
        
    def env(self, key: str, value: str) -> 'Forge':
        """Set environment variable (ENV instruction)"""
        self.steps.append(f"ENV {key}={value}")
        return self
        
    def workdir(self, path: str) -> 'Forge':
        """Set working directory (WORKDIR instruction)"""
        self.steps.append(f"WORKDIR {path}")
        return self

    def build(self, context_path: str = ".", push: bool = True) -> str:
        """
        Execute the build.
        
        1. Registers build with Orgo API to get unique tag.
        2. Generates Dockerfile.
        3. Runs docker build (requires docker CLI installed).
        4. Pushes to registry.
        5. Updates build status.
        
        Returns:
            str: The full image reference (e.g. registry.fly.io/app:tag)
        """
        if not self.steps:
            raise ValueError("No build steps defined. Use .base() to start.")
            
        # 1. Register build
        logger.info("Registering build with Orgo API...")
        try:
            build_info = self.api.create_build(self.org_id, self.project_id, self.name)
            build_data = build_info.get('build', {})
            
            build_id = build_data.get('id')
            tag = build_data.get('tag')
            image_ref = build_data.get('imageRef')
            # buildkit_url = build_data.get('buildkitUrl') # Not used for local docker build yet
            
            if not build_id or not image_ref:
                raise ValueError("Failed to get build ID or image ref from API")
                
            logger.info(f"Build registered. ID: {build_id}, Tag: {tag}")
            logger.info(f"Target Image: {image_ref}")
            
        except Exception as e:
            logger.error(f"Failed to register build: {e}")
            raise e

        # 2. Generate Dockerfile
        dockerfile_path = f"Dockerfile.{tag}"
        try:
            with open(dockerfile_path, "w") as f:
                f.write("\n".join(self.steps))
                
            # 3. Execute Build
            logger.info("Starting build...")
            self.api.update_build(build_id, "building")
            
            # Use remote builder
            builder_name = "orgo-remote"
            remote_url = "tcp://orgoforge.fly.dev:1234"
            
            # Check if builder exists
            try:
                subprocess.run(["docker", "buildx", "inspect", builder_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                logger.info(f"Creating remote builder '{builder_name}' pointing to {remote_url}...")
                subprocess.run(["docker", "buildx", "create", "--name", builder_name, "--driver", "remote", remote_url, "--use"], check=True)
                subprocess.run(["docker", "buildx", "inspect", "--bootstrap"], check=True)

            cmd = ["docker", "buildx", "build", "--builder", builder_name, "-t", image_ref, "-f", dockerfile_path, context_path]
            if push:
                cmd.append("--push")
            
            # Run build
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logs = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line, end="") # Stream to console
                    logs.append(line)
            
            if process.returncode != 0:
                raise Exception(f"Docker build failed with exit code {process.returncode}")
                
            # 5. Report Success
            full_log = "".join(logs)
            self.api.update_build(build_id, "completed", build_log=full_log)
            logger.info("Build completed successfully!")
            
            return image_ref

        except Exception as e:
            logger.error(f"Build failed: {e}")
            full_log = "".join(logs) if 'logs' in locals() else str(e)
            try:
                self.api.update_build(build_id, "failed", error_message=str(e), build_log=full_log)
            except:
                pass # Ignore error reporting failure
            raise e
            
        finally:
            if os.path.exists(dockerfile_path):
                os.remove(dockerfile_path)

