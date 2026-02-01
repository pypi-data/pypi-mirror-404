"""Pydantic models for hardware compatibility data."""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CudaDriverEntry(BaseModel):
    """A single CUDA toolkit to driver version mapping."""

    toolkit_version: str = Field(..., description="CUDA toolkit version (e.g., '12.8')")
    variant: Literal["ga", "update"] = Field(
        ..., description="Release variant: 'ga' for general availability or 'update'"
    )
    update: Optional[int] = Field(
        None, description="Update number (only for variant='update')"
    )
    min_driver: str = Field(
        ..., description="Minimum required driver version (e.g., '570.26')"
    )


class CudaDriverMatrix(BaseModel):
    """CUDA toolkit to minimum driver version mapping."""

    schema_version: int = Field(..., description="Schema version number")
    platform: str = Field(..., description="Platform identifier (e.g., 'linux_x86_64')")
    entries: List[CudaDriverEntry] = Field(
        ..., description="List of CUDA-driver version mappings"
    )

    def get_entry(
        self,
        toolkit_version: str,
        variant: str = "ga",
        update: Optional[int] = None,
    ) -> Optional["CudaDriverEntry"]:
        """Find a specific CUDA-driver mapping.

        Args:
            toolkit_version: CUDA toolkit version
            variant: "ga" or "update"
            update: Update number (required if variant is "update")

        Returns:
            Matching CudaDriverEntry or None
        """
        for entry in self.entries:
            if entry.toolkit_version == toolkit_version and entry.variant == variant:
                if variant == "ga":
                    return entry
                elif variant == "update" and entry.update == update:
                    return entry
        return None


class GPUArchitecture(BaseModel):
    """NVIDIA GPU architecture with SM versions and products."""

    name: str = Field(..., description="Architecture name (e.g., 'Ada Lovelace')")
    sm_versions: List[str] = Field(..., description="SM version strings (e.g., ['89'])")
    compute_capabilities: List[str] = Field(
        ..., description="Compute capability versions (e.g., ['8.9'])"
    )
    products: List[str] = Field(
        ..., description="List of GPU products in this architecture"
    )


class NvidiaSMMap(BaseModel):
    """NVIDIA SM version to architecture mapping."""

    schema_version: int = Field(..., description="Schema version number")
    architectures: List[GPUArchitecture] = Field(
        ..., description="List of GPU architectures"
    )

    def get_architecture(self, sm_version: str) -> Optional["GPUArchitecture"]:
        """Find architecture by SM version.

        Args:
            sm_version: SM version string (e.g., "89")

        Returns:
            Matching GPUArchitecture or None
        """
        for arch in self.architectures:
            if sm_version in arch.sm_versions:
                return arch
        return None

    def get_architecture_by_name(self, name: str) -> Optional["GPUArchitecture"]:
        """Find architecture by name.

        Args:
            name: Architecture name (e.g., "Ada Lovelace")

        Returns:
            Matching GPUArchitecture or None
        """
        for arch in self.architectures:
            if arch.name == name:
                return arch
        return None


class CanonicalGPU(BaseModel):
    """A canonical GPU with provider-specific aliases."""

    canonical_id: str = Field(
        ...,
        description="Machine-stable identifier (lowercase, underscore-separated, e.g., 'rtx_4090')",
    )
    canonical_name: str = Field(
        ..., description="Human-readable canonical GPU name (e.g., 'RTX 4090')"
    )
    family: Optional[str] = Field(
        None,
        description="GPU family identifier for grouping variants (e.g., 'h100', 'a100')",
    )
    sm: str = Field(..., description="SM version (e.g., '89')")
    architecture: str = Field(
        ..., description="Architecture name (e.g., 'Ada Lovelace')"
    )
    aliases: Dict[str, List[str]] = Field(
        ...,
        description="Provider-specific aliases (provider -> list of names)",
    )

    def get_aliases_for_provider(self, provider: str) -> List[str]:
        """Get aliases for a specific provider.

        Args:
            provider: Provider name (e.g., "vastai", "aws")

        Returns:
            List of aliases or empty list
        """
        return self.aliases.get(provider, [])


class GPUAliases(BaseModel):
    """GPU name aliases across cloud providers."""

    schema_version: int = Field(..., description="Schema version number")
    canonical_gpus: List[CanonicalGPU] = Field(
        ..., description="List of canonical GPUs with their aliases"
    )

    def find_canonical(
        self, gpu_name: str, provider: Optional[str] = None
    ) -> Optional["CanonicalGPU"]:
        """Find canonical GPU by provider alias.

        Args:
            gpu_name: GPU name from a provider
            provider: Provider name (optional, searches all if not specified)

        Returns:
            Matching CanonicalGPU or None
        """
        for gpu in self.canonical_gpus:
            if provider:
                if gpu_name in gpu.aliases.get(provider, []):
                    return gpu
            else:
                for aliases in gpu.aliases.values():
                    if gpu_name in aliases:
                        return gpu
        return None

    def get_by_canonical_name(self, canonical_name: str) -> Optional["CanonicalGPU"]:
        """Find GPU by canonical name.

        Args:
            canonical_name: Canonical GPU name (e.g., "RTX 4090")

        Returns:
            Matching CanonicalGPU or None
        """
        for gpu in self.canonical_gpus:
            if gpu.canonical_name == canonical_name:
                return gpu
        return None

    def get_by_canonical_id(self, canonical_id: str) -> Optional["CanonicalGPU"]:
        """Find GPU by canonical ID.

        Args:
            canonical_id: Machine-stable GPU identifier (e.g., "rtx_4090")

        Returns:
            Matching CanonicalGPU or None
        """
        for gpu in self.canonical_gpus:
            if gpu.canonical_id == canonical_id:
                return gpu
        return None

    def get_by_family(self, family: str) -> List["CanonicalGPU"]:
        """Find all GPUs in a family.

        Args:
            family: GPU family identifier (e.g., "h100", "a100")

        Returns:
            List of matching CanonicalGPU objects
        """
        return [gpu for gpu in self.canonical_gpus if gpu.family == family]
