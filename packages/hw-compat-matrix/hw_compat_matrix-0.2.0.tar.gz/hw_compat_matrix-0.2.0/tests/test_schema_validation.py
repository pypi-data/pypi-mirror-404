"""Tests for JSON schema validation of YAML data files."""

import json
from pathlib import Path

import pytest
import yaml

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
DATA_DIR = PROJECT_ROOT / "src" / "hw_compat_matrix" / "data"


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestSchemaValidation:
    """Tests that validate YAML data files against JSON schemas."""

    def load_schema(self, schema_name: str) -> dict:
        """Load a JSON schema file."""
        schema_path = SCHEMAS_DIR / schema_name
        with open(schema_path) as f:
            return json.load(f)

    def load_yaml_data(self, data_name: str) -> dict:
        """Load a YAML data file."""
        data_path = DATA_DIR / data_name
        with open(data_path) as f:
            return yaml.safe_load(f)

    def test_cuda_driver_matrix_schema(self):
        """Validate cuda_driver_matrix.yaml against its schema."""
        schema = self.load_schema("cuda_driver_matrix.schema.json")
        data = self.load_yaml_data("cuda_driver_matrix.yaml")

        jsonschema.validate(data, schema)

    def test_nvidia_sm_map_schema(self):
        """Validate nvidia_sm_map.yaml against its schema."""
        schema = self.load_schema("nvidia_sm_map.schema.json")
        data = self.load_yaml_data("nvidia_sm_map.yaml")

        jsonschema.validate(data, schema)

    def test_gpu_name_aliases_schema(self):
        """Validate gpu_name_aliases.yaml against its schema."""
        schema = self.load_schema("gpu_name_aliases.schema.json")
        data = self.load_yaml_data("gpu_name_aliases.yaml")

        jsonschema.validate(data, schema)


class TestDriverVersionSanity:
    """Sanity checks for driver version ordering."""

    def test_driver_versions_are_increasing(self):
        """Test that newer CUDA versions require newer drivers (for GA releases)."""
        from hw_compat_matrix.loader import load_cuda_driver_matrix

        matrix = load_cuda_driver_matrix()

        # Group GA entries by major.minor version
        ga_entries = [e for e in matrix.entries if e.variant == "ga"]

        # Sort by toolkit version
        def version_key(v: str) -> tuple:
            parts = v.split(".")
            return tuple(int(p) for p in parts)

        ga_entries.sort(key=lambda e: version_key(e.toolkit_version))

        # Check that driver versions generally increase
        # (Note: This is a soft check since updates may have lower drivers)
        for i in range(len(ga_entries) - 1):
            current = ga_entries[i]
            next_entry = ga_entries[i + 1]

            current_driver = version_key(current.min_driver)
            next_driver = version_key(next_entry.min_driver)

            # Newer CUDA should require same or newer driver
            assert next_driver >= current_driver, (
                f"CUDA {next_entry.toolkit_version} requires older driver "
                f"({next_entry.min_driver}) than CUDA {current.toolkit_version} "
                f"({current.min_driver})"
            )


class TestSMVersionConsistency:
    """Tests for SM version consistency across data files."""

    def test_gpu_aliases_reference_valid_architectures(self):
        """Test that GPU aliases reference valid architectures from SM map."""
        from hw_compat_matrix.loader import load_gpu_aliases, load_nvidia_sm_map

        aliases = load_gpu_aliases()
        sm_map = load_nvidia_sm_map()

        valid_architectures = {a.name for a in sm_map.architectures}

        for gpu in aliases.canonical_gpus:
            assert gpu.architecture in valid_architectures, (
                f"GPU {gpu.canonical_name} references unknown architecture "
                f"'{gpu.architecture}'"
            )

    def test_sm_versions_match_architectures(self):
        """Test that SM versions in aliases match their claimed architectures."""
        from hw_compat_matrix.loader import load_gpu_aliases, load_nvidia_sm_map

        aliases = load_gpu_aliases()
        sm_map = load_nvidia_sm_map()

        for gpu in aliases.canonical_gpus:
            arch = sm_map.get_architecture_by_name(gpu.architecture)
            assert arch is not None, f"Architecture {gpu.architecture} not found"

            assert gpu.sm in arch.sm_versions, (
                f"GPU {gpu.canonical_name} has SM {gpu.sm} but architecture "
                f"{gpu.architecture} has SM versions {arch.sm_versions}"
            )
