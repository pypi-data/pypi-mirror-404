from typing import Literal, Optional

from pydantic import BaseModel, field_validator

# Machine size in format 'cpu:memory' (e.g., '1:2' = 1 CPU, 2GB memory)
MachineSize = Literal[
    '0.1:0.1',
    '0.5:0.5',
    '1:1',
    '2:2',
    '4:4',
    '0.1:0.2',
    '0.5:1',
    '1:2',
    '2:4',
    '4:8',
    '0.1:0.4',
    '0.5:2',
    '1:4',
    '2:8',
    '4:16',
]

class SandboxBucketConfig(BaseModel):
    mount_path: str
    """Path inside the container where the bucket will be mounted."""

    read_only: bool = True
    """Whether the bucket should be mounted in read-only mode."""

    only_dir: Optional[str] = None
    """If set, only mount the specified directory from the bucket."""

    implicit_dirs: bool = True
    """If True, mount all subdirectories of the bucket."""

class SandboxSidecarContainer(BaseModel):
    name: str
    """Unique name for this sidecar container."""

    image: str
    """Container image to run."""

    command: Optional[list[str]] = None
    """Optional command override for the container entrypoint."""

    args: Optional[list[str]] = None
    """Optional arguments to pass to the command."""

    env: Optional[dict[str, str]] = None
    """Environment variables for this container."""

    machine_size: MachineSize
    """Machine size to run the container in."""

    ports: Optional[list[int]] = None
    """Ports this container exposes (informational, used for probes)."""

    @field_validator("name")
    def validate_name_not_reserved(cls, value: str) -> str:
        if value.lower() in {"main", "sidecar"}:
            raise ValueError("Sidecar container names 'main' and 'sidecar' are reserved.")
        return value


class SandboxHostAlias(BaseModel):
    """Configuration for adding hostname aliases to /etc/hosts."""

    ip: str
    """IP address to map hostnames to, e.g. '127.0.0.1'."""

    hostnames: list[str]
    """List of hostnames to map to the IP"""

class SandboxSettings(BaseModel):
    """Compute resource settings for a container."""

    environment: str
    """OpenReward environment to run the container in."""

    image: str
    """Container image to run, e.g. "python:3.10-slim"."""

    machine_size: MachineSize
    """
    Machine size to run the container in.
    Example: "0.1:0.2" = 0.1 CPU and 0.2 GB memory.
    """

    # TODO: do we want these?
    # disk_request: Optional[str] = None
    # """Minimum ephemeral storage requested (if using emptyDir volumes). Example: "1Gi" = 1 GB."""

    # disk_limit: Optional[str] = None
    # """Maximum ephemeral storage allowed; exceeding this causes eviction."""

    env: Optional[dict[str, str]] = None
    """Environment variables for the container, e.g. {"ENV": "prod"}."""

    block_network: bool = False
    """If True, disables outbound network access (Kubernetes egress policies required)."""

    bucket_config: Optional[SandboxBucketConfig] = None
    """List of buckets to mount; mounts them into the container at runtime."""

    # labels: Optional[dict[str, str]] = None
    # """Labels to add to running computer for attribution."""

    sidecars: Optional[list[SandboxSidecarContainer]] = None
    """Additional containers to run in the same pod."""

    host_aliases: Optional[list[SandboxHostAlias]] = None
    """Hostname aliases to add to /etc/hosts in all containers."""

class PodTerminatedError(RuntimeError):
    def __init__(self, reason: str, *, client_id: str | None):
        super().__init__(f"Pod terminated (client_id={client_id!r}): {reason}")
        self.reason = reason
        self.client_id = client_id
