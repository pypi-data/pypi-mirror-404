"""Docker client wrapper for Docker Dashboard."""

import docker
from docker.models.containers import Container
from docker.models.images import Image
from typing import Optional
from dataclasses import dataclass
import time


@dataclass
class ContainerInfo:
    """Container information."""
    id: str
    short_id: str
    name: str
    image: str
    status: str
    state: str
    ports: dict
    created: str
    cpu_percent: float = 0.0
    memory_usage: str = "0B"
    memory_percent: float = 0.0


@dataclass
class ImageInfo:
    """Image information."""
    id: str
    short_id: str
    tags: list[str]
    size: str
    created: str


class DockerClient:
    """Docker client wrapper."""

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.connected = True
        except docker.errors.DockerException:
            self.client = None
            self.connected = False

    def is_connected(self) -> bool:
        """Check if Docker is connected."""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def list_containers(self, all: bool = True) -> list[ContainerInfo]:
        """List all containers."""
        if not self.client:
            return []

        try:
            containers = self.client.containers.list(all=all)
            return [self._container_to_info(c) for c in containers]
        except Exception:
            return []

    def _container_to_info(self, container: Container) -> ContainerInfo:
        """Convert container to ContainerInfo."""
        # Get port mappings
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}

        # Get image name
        image_tags = container.image.tags if container.image.tags else [container.image.short_id]
        image_name = image_tags[0] if image_tags else "unknown"

        return ContainerInfo(
            id=container.id,
            short_id=container.short_id,
            name=container.name,
            image=image_name,
            status=container.status,
            state=container.attrs.get("State", {}).get("Status", "unknown"),
            ports=ports,
            created=container.attrs.get("Created", "")[:19],
        )

    def get_container_stats(self, container_id: str) -> Optional[dict]:
        """Get container stats (CPU, memory)."""
        if not self.client:
            return None

        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                        stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                           stats["precpu_stats"]["system_cpu_usage"]
            cpu_count = stats["cpu_stats"].get("online_cpus", 1)

            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100

            # Calculate memory
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 1)
            memory_percent = (memory_usage / memory_limit) * 100

            return {
                "cpu_percent": round(cpu_percent, 1),
                "memory_usage": self._format_bytes(memory_usage),
                "memory_percent": round(memory_percent, 1),
            }
        except Exception:
            return None

    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}TB"

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs."""
        if not self.client:
            return "Docker not connected"

        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
            return logs
        except Exception as e:
            return f"Error: {e}"

    def start_container(self, container_id: str) -> bool:
        """Start a container and verify it's running."""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_id)
            container.start()

            # Wait briefly and check if container is actually running
            time.sleep(0.5)
            container.reload()

            # Return True only if container is actually running
            return container.status == "running"
        except Exception:
            return False

    def stop_container(self, container_id: str) -> bool:
        """Stop a container."""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_id)
            container.stop()
            return True
        except Exception:
            return False

    def restart_container(self, container_id: str) -> bool:
        """Restart a container and verify it's running."""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_id)
            container.restart()

            # Wait briefly and check if container is actually running
            time.sleep(0.5)
            container.reload()

            # Return True only if container is actually running
            return container.status == "running"
        except Exception:
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a container."""
        if not self.client:
            return False

        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            return True
        except Exception:
            return False

    def list_images(self) -> list[ImageInfo]:
        """List all images."""
        if not self.client:
            return []

        try:
            images = self.client.images.list()
            return [self._image_to_info(img) for img in images]
        except Exception:
            return []

    def _image_to_info(self, image: Image) -> ImageInfo:
        """Convert image to ImageInfo."""
        size = image.attrs.get("Size", 0)

        return ImageInfo(
            id=image.id,
            short_id=image.short_id,
            tags=image.tags or ["<none>"],
            size=self._format_bytes(size),
            created=image.attrs.get("Created", "")[:19],
        )

    def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove an image."""
        if not self.client:
            return False

        try:
            self.client.images.remove(image_id, force=force)
            return True
        except Exception:
            return False

    def pull_image(self, name: str) -> bool:
        """Pull an image."""
        if not self.client:
            return False

        try:
            self.client.images.pull(name)
            return True
        except Exception:
            return False
