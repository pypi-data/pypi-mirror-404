"""Tests for Pydantic models."""

from hw_compat_matrix.models import (
    CudaDriverEntry,
    CudaDriverMatrix,
    GPUAliases,
    GPUArchitecture,
    CanonicalGPU,
    NvidiaSMMap,
)


class TestCudaDriverEntry:
    """Tests for CudaDriverEntry model."""

    def test_create_ga_entry(self):
        """Test creating a GA entry."""
        entry = CudaDriverEntry(
            toolkit_version="12.8",
            variant="ga",
            min_driver="570.26",
        )
        assert entry.toolkit_version == "12.8"
        assert entry.variant == "ga"
        assert entry.update is None
        assert entry.min_driver == "570.26"

    def test_create_update_entry(self):
        """Test creating an update entry."""
        entry = CudaDriverEntry(
            toolkit_version="12.8",
            variant="update",
            update=1,
            min_driver="570.124.06",
        )
        assert entry.toolkit_version == "12.8"
        assert entry.variant == "update"
        assert entry.update == 1
        assert entry.min_driver == "570.124.06"


class TestCudaDriverMatrix:
    """Tests for CudaDriverMatrix model."""

    def test_get_entry_ga(self):
        """Test finding a GA entry."""
        matrix = CudaDriverMatrix(
            schema_version=1,
            platform="linux_x86_64",
            entries=[
                CudaDriverEntry(
                    toolkit_version="12.8",
                    variant="ga",
                    min_driver="570.26",
                ),
                CudaDriverEntry(
                    toolkit_version="12.8",
                    variant="update",
                    update=1,
                    min_driver="570.124.06",
                ),
            ],
        )

        entry = matrix.get_entry("12.8", variant="ga")
        assert entry is not None
        assert entry.min_driver == "570.26"

    def test_get_entry_update(self):
        """Test finding an update entry."""
        matrix = CudaDriverMatrix(
            schema_version=1,
            platform="linux_x86_64",
            entries=[
                CudaDriverEntry(
                    toolkit_version="12.8",
                    variant="ga",
                    min_driver="570.26",
                ),
                CudaDriverEntry(
                    toolkit_version="12.8",
                    variant="update",
                    update=1,
                    min_driver="570.124.06",
                ),
            ],
        )

        entry = matrix.get_entry("12.8", variant="update", update=1)
        assert entry is not None
        assert entry.min_driver == "570.124.06"

    def test_get_entry_not_found(self):
        """Test that missing entry returns None."""
        matrix = CudaDriverMatrix(
            schema_version=1,
            platform="linux_x86_64",
            entries=[],
        )

        entry = matrix.get_entry("99.9")
        assert entry is None


class TestGPUArchitecture:
    """Tests for GPUArchitecture model."""

    def test_create_architecture(self):
        """Test creating an architecture."""
        arch = GPUArchitecture(
            name="Ada Lovelace",
            sm_versions=["89"],
            compute_capabilities=["8.9"],
            products=["RTX 4090", "L40"],
        )
        assert arch.name == "Ada Lovelace"
        assert "89" in arch.sm_versions
        assert "RTX 4090" in arch.products


class TestNvidiaSMMap:
    """Tests for NvidiaSMMap model."""

    def test_get_architecture_by_sm(self):
        """Test finding architecture by SM version."""
        sm_map = NvidiaSMMap(
            schema_version=1,
            architectures=[
                GPUArchitecture(
                    name="Ada Lovelace",
                    sm_versions=["89"],
                    compute_capabilities=["8.9"],
                    products=["RTX 4090"],
                ),
                GPUArchitecture(
                    name="Ampere",
                    sm_versions=["80", "86"],
                    compute_capabilities=["8.0", "8.6"],
                    products=["A100", "RTX 3090"],
                ),
            ],
        )

        arch = sm_map.get_architecture("89")
        assert arch is not None
        assert arch.name == "Ada Lovelace"

        arch = sm_map.get_architecture("80")
        assert arch is not None
        assert arch.name == "Ampere"

    def test_get_architecture_by_name(self):
        """Test finding architecture by name."""
        sm_map = NvidiaSMMap(
            schema_version=1,
            architectures=[
                GPUArchitecture(
                    name="Ada Lovelace",
                    sm_versions=["89"],
                    compute_capabilities=["8.9"],
                    products=["RTX 4090"],
                ),
            ],
        )

        arch = sm_map.get_architecture_by_name("Ada Lovelace")
        assert arch is not None
        assert "89" in arch.sm_versions


class TestCanonicalGPU:
    """Tests for CanonicalGPU model."""

    def test_create_gpu(self):
        """Test creating a canonical GPU."""
        gpu = CanonicalGPU(
            canonical_id="rtx_4090",
            canonical_name="RTX 4090",
            sm="89",
            architecture="Ada Lovelace",
            aliases={
                "vastai": ["RTX_4090", "RTX4090"],
                "aws": ["NVIDIA GeForce RTX 4090"],
            },
        )
        assert gpu.canonical_id == "rtx_4090"
        assert gpu.canonical_name == "RTX 4090"
        assert gpu.sm == "89"
        assert "RTX_4090" in gpu.aliases["vastai"]

    def test_create_gpu_with_family(self):
        """Test creating a canonical GPU with family."""
        gpu = CanonicalGPU(
            canonical_id="rtx_4080_super",
            canonical_name="RTX 4080 Super",
            family="rtx_4080",
            sm="89",
            architecture="Ada Lovelace",
            aliases={"vastai": ["RTX_4080_Super"]},
        )
        assert gpu.canonical_id == "rtx_4080_super"
        assert gpu.family == "rtx_4080"

    def test_get_aliases_for_provider(self):
        """Test getting aliases for a provider."""
        gpu = CanonicalGPU(
            canonical_id="rtx_4090",
            canonical_name="RTX 4090",
            sm="89",
            architecture="Ada Lovelace",
            aliases={
                "vastai": ["RTX_4090", "RTX4090"],
                "aws": ["NVIDIA GeForce RTX 4090"],
            },
        )

        vastai_aliases = gpu.get_aliases_for_provider("vastai")
        assert "RTX_4090" in vastai_aliases
        assert "RTX4090" in vastai_aliases

        unknown_aliases = gpu.get_aliases_for_provider("unknown")
        assert unknown_aliases == []


class TestGPUAliases:
    """Tests for GPUAliases model."""

    def test_find_canonical_by_provider(self):
        """Test finding canonical GPU by provider alias."""
        aliases = GPUAliases(
            schema_version=2,
            canonical_gpus=[
                CanonicalGPU(
                    canonical_id="rtx_4090",
                    canonical_name="RTX 4090",
                    family="rtx_4090",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={
                        "vastai": ["RTX_4090", "RTX4090"],
                        "aws": ["NVIDIA GeForce RTX 4090"],
                    },
                ),
            ],
        )

        gpu = aliases.find_canonical("RTX_4090", provider="vastai")
        assert gpu is not None
        assert gpu.canonical_name == "RTX 4090"

    def test_find_canonical_any_provider(self):
        """Test finding canonical GPU across all providers."""
        aliases = GPUAliases(
            schema_version=2,
            canonical_gpus=[
                CanonicalGPU(
                    canonical_id="rtx_4090",
                    canonical_name="RTX 4090",
                    family="rtx_4090",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={
                        "vastai": ["RTX_4090", "RTX4090"],
                        "aws": ["NVIDIA GeForce RTX 4090"],
                    },
                ),
            ],
        )

        gpu = aliases.find_canonical("NVIDIA GeForce RTX 4090")
        assert gpu is not None
        assert gpu.canonical_name == "RTX 4090"

    def test_get_by_canonical_name(self):
        """Test finding GPU by canonical name."""
        aliases = GPUAliases(
            schema_version=2,
            canonical_gpus=[
                CanonicalGPU(
                    canonical_id="rtx_4090",
                    canonical_name="RTX 4090",
                    family="rtx_4090",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={"vastai": ["RTX_4090"]},
                ),
            ],
        )

        gpu = aliases.get_by_canonical_name("RTX 4090")
        assert gpu is not None
        assert gpu.sm == "89"

    def test_get_by_canonical_id(self):
        """Test finding GPU by canonical ID."""
        aliases = GPUAliases(
            schema_version=2,
            canonical_gpus=[
                CanonicalGPU(
                    canonical_id="rtx_4090",
                    canonical_name="RTX 4090",
                    family="rtx_4090",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={"vastai": ["RTX_4090"]},
                ),
            ],
        )

        gpu = aliases.get_by_canonical_id("rtx_4090")
        assert gpu is not None
        assert gpu.canonical_name == "RTX 4090"

        gpu = aliases.get_by_canonical_id("nonexistent")
        assert gpu is None

    def test_get_by_family(self):
        """Test finding GPUs by family."""
        aliases = GPUAliases(
            schema_version=2,
            canonical_gpus=[
                CanonicalGPU(
                    canonical_id="rtx_4080",
                    canonical_name="RTX 4080",
                    family="rtx_4080",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={"vastai": ["RTX_4080"]},
                ),
                CanonicalGPU(
                    canonical_id="rtx_4080_super",
                    canonical_name="RTX 4080 Super",
                    family="rtx_4080",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={"vastai": ["RTX_4080_Super"]},
                ),
                CanonicalGPU(
                    canonical_id="rtx_4090",
                    canonical_name="RTX 4090",
                    family="rtx_4090",
                    sm="89",
                    architecture="Ada Lovelace",
                    aliases={"vastai": ["RTX_4090"]},
                ),
            ],
        )

        family_gpus = aliases.get_by_family("rtx_4080")
        assert len(family_gpus) == 2
        names = {gpu.canonical_name for gpu in family_gpus}
        assert "RTX 4080" in names
        assert "RTX 4080 Super" in names

        family_gpus = aliases.get_by_family("nonexistent")
        assert len(family_gpus) == 0
