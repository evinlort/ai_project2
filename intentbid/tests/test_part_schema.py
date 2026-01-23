import pytest
from pydantic import ValidationError

from intentbid.app.core.schemas import PartCreate, PartCategory


def test_part_create_accepts_valid_gpu_specs():
    payload = {
        "manufacturer": "NVIDIA",
        "mpn": "H100-SXM5-80GB",
        "category": PartCategory.GPU,
        "key_specs": {
            "chip": "H100",
            "vram_gb": 80,
            "form_factor": "SXM",
            "condition": "new",
            "interface": "SXM5",
        },
        "aliases": ["H100 SXM 80GB"],
    }

    part = PartCreate(**payload)

    assert part.category is PartCategory.GPU
    assert part.key_specs["vram_gb"] == 80
    assert part.aliases == ["H100 SXM 80GB"]


def test_part_create_rejects_missing_gpu_field():
    payload = {
        "manufacturer": "NVIDIA",
        "mpn": "H100-PCIe-80GB",
        "category": PartCategory.GPU,
        "key_specs": {
            "vram_gb": 80,
            "form_factor": "PCIe",
            "condition": "new",
            "interface": "PCIe Gen5",
        },
    }

    with pytest.raises(ValidationError):
        PartCreate(**payload)


def test_part_create_rejects_extra_memory_field():
    payload = {
        "manufacturer": "Samsung",
        "mpn": "M321R8GA0BB0-CQK",
        "category": PartCategory.MEMORY,
        "key_specs": {
            "type": "DDR5",
            "capacity_gb": 64,
            "speed_mt_s": 5600,
            "ecc": True,
            "form_factor": "RDIMM",
            "unexpected": "oops",
        },
    }

    with pytest.raises(ValidationError):
        PartCreate(**payload)
