"""Data loading utilities for hardware compatibility files."""

from pathlib import Path
from typing import Optional, Union

import yaml

from hw_compat_matrix.models import CudaDriverMatrix, GPUAliases, NvidiaSMMap

# Path to the data directory
DATA_DIR = Path(__file__).parent / "data"


def load_cuda_driver_matrix(
    path: Optional[Union[Path, str]] = None,
) -> CudaDriverMatrix:
    """Load CUDA driver matrix from YAML file.

    Args:
        path: Optional custom path to YAML file. Uses bundled data if not provided.

    Returns:
        CudaDriverMatrix model with loaded data
    """
    if path is None:
        path = DATA_DIR / "cuda_driver_matrix.yaml"
    else:
        path = Path(path)

    with open(path) as f:
        data = yaml.safe_load(f)

    return CudaDriverMatrix.model_validate(data)


def load_nvidia_sm_map(path: Optional[Union[Path, str]] = None) -> NvidiaSMMap:
    """Load NVIDIA SM map from YAML file.

    Args:
        path: Optional custom path to YAML file. Uses bundled data if not provided.

    Returns:
        NvidiaSMMap model with loaded data
    """
    if path is None:
        path = DATA_DIR / "nvidia_sm_map.yaml"
    else:
        path = Path(path)

    with open(path) as f:
        data = yaml.safe_load(f)

    return NvidiaSMMap.model_validate(data)


def load_gpu_aliases(path: Optional[Union[Path, str]] = None) -> GPUAliases:
    """Load GPU aliases from YAML file.

    Args:
        path: Optional custom path to YAML file. Uses bundled data if not provided.

    Returns:
        GPUAliases model with loaded data
    """
    if path is None:
        path = DATA_DIR / "gpu_name_aliases.yaml"
    else:
        path = Path(path)

    with open(path) as f:
        data = yaml.safe_load(f)

    return GPUAliases.model_validate(data)


def get_data_file_path(filename: str) -> Path:
    """Get the path to a bundled data file.

    Args:
        filename: Name of the data file (e.g., "cuda_driver_matrix.yaml")

    Returns:
        Path to the data file
    """
    return DATA_DIR / filename
