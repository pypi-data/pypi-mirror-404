# hw-compat-matrix

Canonical CUDA/GPU compatibility metadata for hardware compatibility checking.

## Overview

This package provides structured data and utilities for:
- CUDA toolkit version to minimum driver version mapping
- NVIDIA SM (Streaming Multiprocessor) version to GPU architecture mapping
- GPU name normalization across cloud providers (Vast.ai, AWS, Lambda, RunPod, Azure)

## Installation

```bash
pip install hw-compat-matrix
```

## Usage

```python
from hw_compat_matrix import (
    get_min_driver_for_cuda,
    get_architecture_for_sm,
    normalize_gpu_name,
)

# Get minimum driver version for a CUDA toolkit version
min_driver = get_min_driver_for_cuda("12.8")  # Returns "570.26"

# Get GPU architecture for an SM version
arch = get_architecture_for_sm("89")  # Returns "Ada Lovelace"

# Normalize GPU names from different providers
canonical = normalize_gpu_name("RTX_4090", provider="vastai")  # Returns "RTX 4090"
```

### Loading Raw Data

```python
from hw_compat_matrix import (
    load_cuda_driver_matrix,
    load_nvidia_sm_map,
    load_gpu_aliases,
)

# Load raw data as Pydantic models
cuda_matrix = load_cuda_driver_matrix()
sm_map = load_nvidia_sm_map()
gpu_aliases = load_gpu_aliases()
```

## Data Sources

- **cuda_driver_matrix.yaml**: From [CUDA Toolkit Release Notes](https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/)
- **nvidia_sm_map.yaml**: From [CUDA GPUs](https://developer.nvidia.com/cuda-gpus)
- **gpu_name_aliases.yaml**: Collected from provider APIs

## Contributing

### Adding New CUDA Versions

1. Update `src/hw_compat_matrix/data/cuda_driver_matrix.yaml`
2. Run validation: `pytest tests/`
3. Submit a PR

### Adding New GPU Aliases

1. Update `src/hw_compat_matrix/data/gpu_name_aliases.yaml`
2. Run validation: `pytest tests/`
3. Submit a PR

## License

MIT License - see [LICENSE](LICENSE) for details.
