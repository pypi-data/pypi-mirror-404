"""Hardware Compatibility Matrix - CUDA/GPU compatibility metadata."""

from typing import List, Optional

__version__ = "0.1.1"

from hw_compat_matrix.loader import (
    load_cuda_driver_matrix,
    load_nvidia_sm_map,
    load_gpu_aliases,
)
from hw_compat_matrix.models import (
    CudaDriverMatrix,
    CudaDriverEntry,
    NvidiaSMMap,
    GPUArchitecture,
    GPUAliases,
    CanonicalGPU,
)

# Convenience functions
_cuda_matrix_cache: Optional[CudaDriverMatrix] = None
_sm_map_cache: Optional[NvidiaSMMap] = None
_gpu_aliases_cache: Optional[GPUAliases] = None


def _get_cuda_matrix() -> CudaDriverMatrix:
    """Get cached CUDA driver matrix."""
    global _cuda_matrix_cache
    if _cuda_matrix_cache is None:
        _cuda_matrix_cache = load_cuda_driver_matrix()
    return _cuda_matrix_cache


def _get_sm_map() -> NvidiaSMMap:
    """Get cached SM map."""
    global _sm_map_cache
    if _sm_map_cache is None:
        _sm_map_cache = load_nvidia_sm_map()
    return _sm_map_cache


def _get_gpu_aliases() -> GPUAliases:
    """Get cached GPU aliases."""
    global _gpu_aliases_cache
    if _gpu_aliases_cache is None:
        _gpu_aliases_cache = load_gpu_aliases()
    return _gpu_aliases_cache


def get_min_driver_for_cuda(
    toolkit_version: str,
    variant: str = "ga",
    update: Optional[int] = None,
) -> Optional[str]:
    """Get minimum driver version for a CUDA toolkit version.

    Args:
        toolkit_version: CUDA toolkit version (e.g., "12.8", "11.8")
        variant: "ga" for general availability or "update" for update releases
        update: Update number (required if variant is "update")

    Returns:
        Minimum driver version string (e.g., "570.26") or None if not found
    """
    matrix = _get_cuda_matrix()
    for entry in matrix.entries:
        if entry.toolkit_version == toolkit_version and entry.variant == variant:
            if variant == "ga":
                return entry.min_driver
            elif variant == "update" and entry.update == update:
                return entry.min_driver
    return None


def get_architecture_for_sm(sm_version: str) -> Optional[str]:
    """Get GPU architecture name for an SM version.

    Args:
        sm_version: SM version string (e.g., "89", "90", "80")

    Returns:
        Architecture name (e.g., "Ada Lovelace") or None if not found
    """
    sm_map = _get_sm_map()
    for arch in sm_map.architectures:
        if sm_version in arch.sm_versions:
            return arch.name
    return None


def get_products_for_sm(sm_version: str) -> List[str]:
    """Get list of GPU products for an SM version.

    Args:
        sm_version: SM version string (e.g., "89", "90", "80")

    Returns:
        List of product names or empty list if not found
    """
    sm_map = _get_sm_map()
    for arch in sm_map.architectures:
        if sm_version in arch.sm_versions:
            return arch.products
    return []


def normalize_gpu_name(gpu_name: str, provider: Optional[str] = None) -> Optional[str]:
    """Normalize a GPU name to its canonical form.

    Args:
        gpu_name: GPU name from a provider (e.g., "RTX_4090")
        provider: Provider name (e.g., "vastai", "aws", "lambda", "runpod", "azure", "gcp")
                  If None, searches all providers.

    Returns:
        Canonical GPU name (e.g., "RTX 4090") or None if not found
    """
    aliases = _get_gpu_aliases()
    for gpu in aliases.canonical_gpus:
        if provider:
            provider_aliases = gpu.aliases.get(provider, [])
            if gpu_name in provider_aliases:
                return gpu.canonical_name
        else:
            for provider_aliases in gpu.aliases.values():
                if gpu_name in provider_aliases:
                    return gpu.canonical_name
    return None


def get_gpu_info(canonical_name: str) -> Optional[CanonicalGPU]:
    """Get full GPU information by canonical name.

    Args:
        canonical_name: Canonical GPU name (e.g., "RTX 4090")

    Returns:
        CanonicalGPU object with full information or None if not found
    """
    aliases = _get_gpu_aliases()
    for gpu in aliases.canonical_gpus:
        if gpu.canonical_name == canonical_name:
            return gpu
    return None


def get_sm_for_gpu(canonical_name: str) -> Optional[str]:
    """Get SM version for a GPU by canonical name.

    Args:
        canonical_name: Canonical GPU name (e.g., "RTX 4090")

    Returns:
        SM version string (e.g., "89") or None if not found
    """
    gpu = get_gpu_info(canonical_name)
    if gpu:
        return gpu.sm
    return None


def get_gpu_by_id(canonical_id: str) -> Optional[CanonicalGPU]:
    """Get GPU information by canonical ID.

    Args:
        canonical_id: Machine-stable GPU identifier (e.g., "rtx_4090", "h100")

    Returns:
        CanonicalGPU object with full information or None if not found
    """
    aliases = _get_gpu_aliases()
    return aliases.get_by_canonical_id(canonical_id)


def get_gpus_by_family(family: str) -> List[CanonicalGPU]:
    """Get all GPUs in a family.

    Args:
        family: GPU family identifier (e.g., "h100", "a100", "rtx_4080")

    Returns:
        List of CanonicalGPU objects in the family
    """
    aliases = _get_gpu_aliases()
    return aliases.get_by_family(family)


def normalize_gpu_name_to_id(
    gpu_name: str, provider: Optional[str] = None
) -> Optional[str]:
    """Normalize a GPU name to its canonical ID.

    Args:
        gpu_name: GPU name from a provider (e.g., "RTX_4090")
        provider: Provider name (e.g., "vastai", "aws", "lambda", "runpod", "azure", "gcp")
                  If None, searches all providers.

    Returns:
        Canonical GPU ID (e.g., "rtx_4090") or None if not found
    """
    aliases = _get_gpu_aliases()
    gpu = aliases.find_canonical(gpu_name, provider)
    if gpu:
        return gpu.canonical_id
    return None


__all__ = [
    "__version__",
    # Loader functions
    "load_cuda_driver_matrix",
    "load_nvidia_sm_map",
    "load_gpu_aliases",
    # Models
    "CudaDriverMatrix",
    "CudaDriverEntry",
    "NvidiaSMMap",
    "GPUArchitecture",
    "GPUAliases",
    "CanonicalGPU",
    # Convenience functions
    "get_min_driver_for_cuda",
    "get_architecture_for_sm",
    "get_products_for_sm",
    "normalize_gpu_name",
    "get_gpu_info",
    "get_sm_for_gpu",
    "get_gpu_by_id",
    "get_gpus_by_family",
    "normalize_gpu_name_to_id",
]
