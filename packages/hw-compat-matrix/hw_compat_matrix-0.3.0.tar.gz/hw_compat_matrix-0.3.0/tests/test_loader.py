"""Tests for data loading functionality."""

from hw_compat_matrix.loader import (
    load_cuda_driver_matrix,
    load_gpu_aliases,
    load_nvidia_sm_map,
    get_data_file_path,
)


class TestCudaDriverMatrixLoader:
    """Tests for CUDA driver matrix loading."""

    def test_load_cuda_driver_matrix(self):
        """Test that CUDA driver matrix loads successfully."""
        matrix = load_cuda_driver_matrix()
        assert matrix.schema_version >= 1
        assert matrix.platform == "linux_x86_64"
        assert len(matrix.entries) > 0

    def test_cuda_matrix_has_expected_versions(self):
        """Test that matrix contains expected CUDA versions."""
        matrix = load_cuda_driver_matrix()
        toolkit_versions = {e.toolkit_version for e in matrix.entries}

        # Check for key CUDA versions
        assert "13.1" in toolkit_versions
        assert "13.0" in toolkit_versions
        assert "12.9" in toolkit_versions
        assert "12.8" in toolkit_versions
        assert "12.4" in toolkit_versions
        assert "11.8" in toolkit_versions
        assert "11.0" in toolkit_versions

    def test_cuda_matrix_driver_format(self):
        """Test that driver versions are in valid format."""
        matrix = load_cuda_driver_matrix()
        for entry in matrix.entries:
            # Driver version should be numeric with dots
            parts = entry.min_driver.split(".")
            assert len(parts) >= 2
            for part in parts:
                assert part.isdigit()

    def test_cuda_matrix_variants(self):
        """Test that entries have valid variants."""
        matrix = load_cuda_driver_matrix()
        for entry in matrix.entries:
            assert entry.variant in ("ga", "update")
            if entry.variant == "update":
                assert entry.update is not None
                assert entry.update >= 1


class TestNvidiaSMMapLoader:
    """Tests for NVIDIA SM map loading."""

    def test_load_nvidia_sm_map(self):
        """Test that SM map loads successfully."""
        sm_map = load_nvidia_sm_map()
        assert sm_map.schema_version >= 1
        assert len(sm_map.architectures) > 0

    def test_sm_map_has_expected_architectures(self):
        """Test that map contains expected architectures."""
        sm_map = load_nvidia_sm_map()
        arch_names = {a.name for a in sm_map.architectures}

        assert "Blackwell" in arch_names
        assert "Hopper" in arch_names
        assert "Ada Lovelace" in arch_names
        assert "Ampere" in arch_names
        assert "Turing" in arch_names
        assert "Volta" in arch_names
        assert "Pascal" in arch_names

    def test_sm_map_has_products(self):
        """Test that each architecture has products."""
        sm_map = load_nvidia_sm_map()
        for arch in sm_map.architectures:
            assert len(arch.products) > 0
            assert len(arch.sm_versions) > 0
            assert len(arch.compute_capabilities) > 0

    def test_sm_versions_are_unique(self):
        """Test that SM versions are not duplicated across architectures."""
        sm_map = load_nvidia_sm_map()
        all_sm_versions = []
        for arch in sm_map.architectures:
            all_sm_versions.extend(arch.sm_versions)

        # Check for duplicates (excluding expected overlaps like 90 and 90a)
        seen = set()
        for sm in all_sm_versions:
            assert sm not in seen, f"SM version {sm} is duplicated"
            seen.add(sm)


class TestGPUAliasesLoader:
    """Tests for GPU aliases loading."""

    def test_load_gpu_aliases(self):
        """Test that GPU aliases load successfully."""
        aliases = load_gpu_aliases()
        assert aliases.schema_version >= 1
        assert len(aliases.canonical_gpus) > 0

    def test_gpu_aliases_have_expected_gpus(self):
        """Test that aliases contain expected GPUs."""
        aliases = load_gpu_aliases()
        canonical_names = {g.canonical_name for g in aliases.canonical_gpus}

        assert "H100" in canonical_names
        assert "A100" in canonical_names
        assert "RTX 4090" in canonical_names
        assert "RTX 3090" in canonical_names
        assert "T4" in canonical_names
        assert "V100" in canonical_names

    def test_gpu_aliases_have_providers(self):
        """Test that GPUs have provider aliases."""
        aliases = load_gpu_aliases()
        for gpu in aliases.canonical_gpus:
            assert len(gpu.aliases) > 0
            # Each GPU should have at least one provider
            assert any(
                len(provider_aliases) > 0 for provider_aliases in gpu.aliases.values()
            )

    def test_gpu_aliases_have_canonical_id(self):
        """Test that all GPUs have canonical_id field."""
        aliases = load_gpu_aliases()
        for gpu in aliases.canonical_gpus:
            assert gpu.canonical_id is not None
            assert len(gpu.canonical_id) > 0
            # canonical_id should be lowercase with underscores
            assert gpu.canonical_id == gpu.canonical_id.lower()
            assert " " not in gpu.canonical_id

    def test_gpu_aliases_have_family(self):
        """Test that all GPUs have family field."""
        aliases = load_gpu_aliases()
        for gpu in aliases.canonical_gpus:
            assert gpu.family is not None
            assert len(gpu.family) > 0
            # family should be lowercase with underscores
            assert gpu.family == gpu.family.lower()
            assert " " not in gpu.family

    def test_gpu_aliases_canonical_id_unique(self):
        """Test that canonical_id is unique across all GPUs."""
        aliases = load_gpu_aliases()
        canonical_ids = [gpu.canonical_id for gpu in aliases.canonical_gpus]
        assert len(canonical_ids) == len(set(canonical_ids)), (
            "canonical_id must be unique"
        )

    def test_gpu_aliases_sm_consistency(self):
        """Test that SM versions in aliases are consistent with SM map."""
        aliases = load_gpu_aliases()
        sm_map = load_nvidia_sm_map()

        all_sm_versions = set()
        for arch in sm_map.architectures:
            all_sm_versions.update(arch.sm_versions)

        for gpu in aliases.canonical_gpus:
            assert gpu.sm in all_sm_versions, (
                f"GPU {gpu.canonical_name} has SM {gpu.sm} not in SM map"
            )


class TestDataFilePath:
    """Tests for data file path utility."""

    def test_get_data_file_path(self):
        """Test that data file paths are valid."""
        cuda_path = get_data_file_path("cuda_driver_matrix.yaml")
        assert cuda_path.exists()

        sm_path = get_data_file_path("nvidia_sm_map.yaml")
        assert sm_path.exists()

        aliases_path = get_data_file_path("gpu_name_aliases.yaml")
        assert aliases_path.exists()
