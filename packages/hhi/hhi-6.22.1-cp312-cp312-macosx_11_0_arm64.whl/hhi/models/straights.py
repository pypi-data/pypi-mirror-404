"""Straight waveguide models."""

from __future__ import annotations

from functools import cache
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import jax.numpy as jnp
import pandas as pd
import sax
import sax.models as sm
import yaml

if TYPE_CHECKING:
    SDict = sax.SDict
else:
    SDict = "sax.SDict"

nm = 0.001

DATA_DIR = Path(__file__).parent / "HHI_PDK_6_22_0_bb_performance_numeric"


@cache
def _load_csvy(filename: str) -> tuple[dict, dict[str, jnp.ndarray]]:
    """Load a csvy file and return metadata and data as jnp arrays."""
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        content = f.read()
    parts = content.split("---", 1)
    yaml_part, csv_part = parts
    metadata = yaml.safe_load(yaml_part)
    df = pd.read_csv(StringIO(csv_part.strip()))
    data = {col: jnp.array(df[col].values) for col in df.columns}
    return metadata, data


@cache
def _get_straight_data(
    cross_section: str,
) -> tuple[jnp.ndarray, jnp.ndarray, float, float]:
    """Get wavelength, loss, neff, ng for a cross section.

    Returns:
        (wavelengths_um, loss_dB_cm, neff, ng)
    """
    if cross_section == "E1700":
        _, loss_data = _load_csvy("HHI_STRAIGHT_WG_E1700_data.csvy")
        _, ng_data = _load_csvy("HHI_E1700_TE_group_index.csvy")
        return (
            loss_data["wavelength"] * nm,  # nm -> um
            loss_data["loss"],  # dB/cm
            2.316,  # neff estimate
            float(jnp.mean(ng_data["group_index"])),  # ng ~3.53
        )
    elif cross_section == "E200":
        _, loss_data = _load_csvy("HHI_STRAIGHT_WG_E200_data.csvy")
        return (
            loss_data["wavelength"] * nm,  # nm -> um
            loss_data["loss"],  # dB/cm
            2.45,  # neff estimate
            3.9,  # ng estimate
        )
    elif cross_section == "E600":
        _, loss_data = _load_csvy("HHI_STRAIGHT_WG_E600_data.csvy")
        return (
            loss_data["wavelength"] * nm,  # nm -> um
            loss_data["loss"],  # dB/cm
            2.4,  # neff estimate
            3.7,  # ng estimate
        )
    else:
        raise ValueError(f"Unknown cross_section: {cross_section}")


def straight(
    *,
    wl: sax.FloatArrayLike = 1.55,
    length: sax.FloatArrayLike = 10.0,
    cross_section: str = "E1700",
) -> SDict:
    """Straight waveguide model with measured loss data.

    Args:
        wl: Wavelength in micrometers.
        length: Waveguide length in micrometers.
        cross_section: Cross section type ("E1700", "E200", "E600").

    Returns:
        S-matrix dictionary.
    """
    wl = jnp.asarray(wl)
    wl_data, loss_data, neff, ng = _get_straight_data(cross_section)

    # Interpolate loss at requested wavelength
    loss_dB_cm = jnp.interp(wl, wl_data, loss_data)

    return sm.straight(
        wl=wl,
        wl0=1.55,
        neff=neff,
        ng=ng,
        length=length,
        loss_dB_cm=loss_dB_cm,
    )


def bend_euler(
    *,
    wl: sax.FloatArrayLike = 1.55,
    radius: float = 10.0,
    angle: float = 90.0,
    cross_section: str = "E1700",
) -> SDict:
    """Euler bend model.

    Uses straight waveguide loss model with arc length.

    Args:
        wl: Wavelength in micrometers.
        radius: Bend radius in micrometers.
        angle: Bend angle in degrees.
        cross_section: Cross section type ("E1700", "E200", "E600").

    Returns:
        S-matrix dictionary.
    """
    angle_radians = jnp.radians(angle)
    length = radius * angle_radians
    return straight(wl=wl, length=length, cross_section=cross_section)
