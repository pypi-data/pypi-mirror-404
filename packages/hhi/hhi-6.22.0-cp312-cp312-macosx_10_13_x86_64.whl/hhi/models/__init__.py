"""SAX models for S-parameter circuit simulations using OpenEPDA data."""

from __future__ import annotations

from .hhi_fixed import (
    HHI_GRAT,
    HHI_MIR1E1700,
    HHI_MIR2E1700,
    HHI_SSCLATE200,
    HHI_SSCLATE1700,
    HHI_WGTE200E1700,
    HHI_BJsingle,
    HHI_BJtwin,
    HHI_DirCoupE1700,
    HHI_MMI1x2E600,
    HHI_MMI1x2E1700,
    HHI_MMI2x2E600,
    HHI_MMI2x2E1700,
    HHI_PolSplitter,
)
from .straights import bend_euler, straight

models = {
    "straight": straight,
    "bend_euler": bend_euler,
    "HHI_BJsingle": HHI_BJsingle,
    "HHI_BJtwin": HHI_BJtwin,
    "HHI_DirCoupE1700": HHI_DirCoupE1700,
    "HHI_GRAT": HHI_GRAT,
    "HHI_MIR1E1700": HHI_MIR1E1700,
    "HHI_MIR2E1700": HHI_MIR2E1700,
    "HHI_MMI1x2E1700": HHI_MMI1x2E1700,
    "HHI_MMI1x2E600": HHI_MMI1x2E600,
    "HHI_MMI2x2E1700": HHI_MMI2x2E1700,
    "HHI_MMI2x2E600": HHI_MMI2x2E600,
    "HHI_PolSplitter": HHI_PolSplitter,
    "HHI_SSCLATE1700": HHI_SSCLATE1700,
    "HHI_SSCLATE200": HHI_SSCLATE200,
    "HHI_WGTE200E1700": HHI_WGTE200E1700,
}

__all__ = [
    "models",
    "straight",
    "bend_euler",
    "HHI_BJsingle",
    "HHI_BJtwin",
    "HHI_DirCoupE1700",
    "HHI_GRAT",
    "HHI_MIR1E1700",
    "HHI_MIR2E1700",
    "HHI_MMI1x2E1700",
    "HHI_MMI1x2E600",
    "HHI_MMI2x2E1700",
    "HHI_MMI2x2E600",
    "HHI_PolSplitter",
    "HHI_SSCLATE1700",
    "HHI_SSCLATE200",
    "HHI_WGTE200E1700",
]
