"""HHI PDK models using measured OpenEPDA data."""

from functools import cache
from io import StringIO
from pathlib import Path

import jax.numpy as jnp
import pandas as pd
import sax
import yaml

CWD = Path(__file__).resolve().parent
DATA_DIR = CWD / "HHI_PDK_6_22_0_bb_performance_numeric"


@cache
def _load_csvy(filename: str) -> tuple[dict, dict[str, jnp.ndarray]]:
    """Load OpenEPDA csvy file.

    Args:
        filename: Name of the csvy file in DATA_DIR

    Returns:
        Tuple of (metadata dict, data dict with jnp arrays)
    """
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        content = f.read()

    parts = content.split("---", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid csvy format: missing '---' separator in {filename}")

    yaml_part, csv_part = parts
    metadata = yaml.safe_load(yaml_part)
    df = pd.read_csv(StringIO(csv_part.strip()))

    # Convert to dict of jnp arrays
    data = {col: jnp.array(df[col].values) for col in df.columns}

    return metadata, data


def HHI_DirCoupE1700(
    *,
    wl: sax.FloatArrayLike = 1.56,
    L_C: sax.FloatArrayLike = 100.0,
) -> sax.SDict:
    """2x2 Directional coupler model using measured data.

    Data measured at fixed wavelength ~1.56um, temperature 25°C.

    Args:
        wl: wavelength [um] (fixed at 1.56um in measured data, but accepts arrays for API compatibility)
        L_C: coupling length [um] (valid range: 825-1150 um in measured data)

    Returns:
        S-parameter dictionary with ports o1, o2, o3, o4
    """
    _, data = _load_csvy("HHI_DirCoupE1700.csvy")

    # Interpolate power coupling coefficients
    kappa_sq = jnp.interp(L_C, data["L_C"], data["cross_coupling"])
    tau_sq = jnp.interp(L_C, data["L_C"], data["bar_coupling"])

    # Amplitude coefficients
    kappa = jnp.sqrt(jnp.clip(kappa_sq, 0, 1))
    tau = jnp.sqrt(jnp.clip(tau_sq, 0, 1))

    # Broadcast to wl shape (for API compatibility, data has no wl dependence)
    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    kappa = jnp.broadcast_to(kappa, wl_arr.shape)
    tau = jnp.broadcast_to(tau, wl_arr.shape)

    return sax.reciprocal(
        {
            ("o1", "o3"): 1j * kappa,  # cross
            ("o1", "o4"): tau,  # bar/through
            ("o2", "o3"): tau,  # bar/through
            ("o2", "o4"): 1j * kappa,  # cross
        }
    )


def HHI_MMI1x2E1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
    Width: sax.FloatArrayLike = 11.8,
) -> sax.SDict:
    """1x2 MMI splitter model using simulated S-matrix data.

    Data simulated with EME method at temperature 27°C.

    Args:
        wl: wavelength [um] (valid range: 1.35-1.75 um)
        Width: MMI width [um] (valid range: 11.63-11.97 um)

    Returns:
        S-parameter dictionary with ports o1 (input), o2, o3 (outputs)
    """
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator

    _, data = _load_csvy("HHI_MMI_SP/HHI_MMI1x2E1700_smatrix.csvy")

    # Get unique grid values (need numpy for scipy interpolator)
    widths = np.sort(np.unique(np.asarray(data["Width"])))
    wavelengths = np.sort(np.unique(np.asarray(data["wavelength"])))
    nw, nl = len(widths), len(wavelengths)

    def make_grid(col):
        return np.asarray(data[col]).reshape(nw, nl)

    # Create interpolators (scipy needs numpy)
    interp_u_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_u_TE:abs2")
    )
    interp_u_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_u_TE:phase")
    )
    interp_d_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_d_TE:abs2")
    )
    interp_d_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_d_TE:phase")
    )

    # Broadcast inputs
    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    width_arr = jnp.atleast_1d(jnp.asarray(Width))
    width_bc, wl_bc = jnp.broadcast_arrays(width_arr, wl_arr)
    output_shape = width_bc.shape

    # Interpolate (convert to numpy for scipy)
    pts = np.column_stack([np.asarray(width_bc).ravel(), np.asarray(wl_bc).ravel()])
    s_u_abs = jnp.sqrt(jnp.clip(interp_u_abs2(pts), 0, 1)).reshape(output_shape)
    s_u_phase = jnp.asarray(interp_u_phase(pts)).reshape(output_shape)
    s_d_abs = jnp.sqrt(jnp.clip(interp_d_abs2(pts), 0, 1)).reshape(output_shape)
    s_d_phase = jnp.asarray(interp_d_phase(pts)).reshape(output_shape)

    # Build complex S-parameters
    s_u = s_u_abs * jnp.exp(1j * s_u_phase)
    s_d = s_d_abs * jnp.exp(1j * s_d_phase)

    # Squeeze if both inputs were scalar
    if jnp.ndim(wl) == 0 and jnp.ndim(Width) == 0:
        s_u = s_u.squeeze()
        s_d = s_d.squeeze()

    return sax.reciprocal(
        {
            ("o1", "o3"): s_u,  # upper output
            ("o1", "o2"): s_d,  # lower output
        }
    )


def HHI_MMI1x2E600(
    *,
    wl: sax.FloatArrayLike = 1.55,
    Width: sax.FloatArrayLike = 12.3,
) -> sax.SDict:
    """1x2 MMI splitter model (E600 waveguide) using simulated S-matrix data.

    Data simulated with EME method at temperature 27°C.

    Args:
        wl: wavelength [um] (valid range: 1.35-1.75 um)
        Width: MMI width [um] (valid range: 12.13-12.47 um)

    Returns:
        S-parameter dictionary with ports o1 (input), o2, o3 (outputs)
    """
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator

    _, data = _load_csvy("HHI_MMI_SP/HHI_MMI1x2E600_smatrix.csvy")

    widths = np.sort(np.unique(np.asarray(data["Width"])))
    wavelengths = np.sort(np.unique(np.asarray(data["wavelength"])))
    nw, nl = len(widths), len(wavelengths)

    def make_grid(col):
        return np.asarray(data[col]).reshape(nw, nl)

    interp_u_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_u_TE:abs2")
    )
    interp_u_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_u_TE:phase")
    )
    interp_d_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_d_TE:abs2")
    )
    interp_d_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_d_TE:phase")
    )

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    width_arr = jnp.atleast_1d(jnp.asarray(Width))
    width_bc, wl_bc = jnp.broadcast_arrays(width_arr, wl_arr)
    output_shape = width_bc.shape

    pts = np.column_stack([np.asarray(width_bc).ravel(), np.asarray(wl_bc).ravel()])
    s_u_abs = jnp.sqrt(jnp.clip(interp_u_abs2(pts), 0, 1)).reshape(output_shape)
    s_u_phase = jnp.asarray(interp_u_phase(pts)).reshape(output_shape)
    s_d_abs = jnp.sqrt(jnp.clip(interp_d_abs2(pts), 0, 1)).reshape(output_shape)
    s_d_phase = jnp.asarray(interp_d_phase(pts)).reshape(output_shape)

    s_u = s_u_abs * jnp.exp(1j * s_u_phase)
    s_d = s_d_abs * jnp.exp(1j * s_d_phase)

    if jnp.ndim(wl) == 0 and jnp.ndim(Width) == 0:
        s_u = s_u.squeeze()
        s_d = s_d.squeeze()

    return sax.reciprocal(
        {
            ("o1", "o3"): s_u,
            ("o1", "o2"): s_d,
        }
    )


def HHI_MMI2x2E1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
    Width: sax.FloatArrayLike = 12.0,
) -> sax.SDict:
    """2x2 MMI coupler model (E1700 waveguide) using simulated S-matrix data.

    Data simulated with EME method at temperature 27°C.

    Args:
        wl: wavelength [um] (valid range: 1.35-1.75 um)
        Width: MMI width [um] (valid range: 11.83-12.17 um)

    Returns:
        S-parameter dictionary with ports o1, o2 (inputs), o3, o4 (outputs)
    """
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator

    _, data = _load_csvy("HHI_MMI_SP/HHI_MMI2x2E1700_smatrix.csvy")

    widths = np.sort(np.unique(np.asarray(data["Width"])))
    wavelengths = np.sort(np.unique(np.asarray(data["wavelength"])))
    nw, nl = len(widths), len(wavelengths)

    def make_grid(col):
        return np.asarray(data[col]).reshape(nw, nl)

    interp_bar_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_bar_TE:abs2")
    )
    interp_bar_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_bar_TE:phase")
    )
    interp_cross_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_cross_TE:abs2")
    )
    interp_cross_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_cross_TE:phase")
    )

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    width_arr = jnp.atleast_1d(jnp.asarray(Width))
    width_bc, wl_bc = jnp.broadcast_arrays(width_arr, wl_arr)
    output_shape = width_bc.shape

    pts = np.column_stack([np.asarray(width_bc).ravel(), np.asarray(wl_bc).ravel()])
    s_bar_abs = jnp.sqrt(jnp.clip(interp_bar_abs2(pts), 0, 1)).reshape(output_shape)
    s_bar_phase = jnp.asarray(interp_bar_phase(pts)).reshape(output_shape)
    s_cross_abs = jnp.sqrt(jnp.clip(interp_cross_abs2(pts), 0, 1)).reshape(output_shape)
    s_cross_phase = jnp.asarray(interp_cross_phase(pts)).reshape(output_shape)

    s_bar = s_bar_abs * jnp.exp(1j * s_bar_phase)
    s_cross = s_cross_abs * jnp.exp(1j * s_cross_phase)

    if jnp.ndim(wl) == 0 and jnp.ndim(Width) == 0:
        s_bar = s_bar.squeeze()
        s_cross = s_cross.squeeze()

    return sax.reciprocal(
        {
            ("o1", "o3"): s_bar,  # bar
            ("o1", "o4"): s_cross,  # cross
            ("o2", "o3"): s_cross,  # cross
            ("o2", "o4"): s_bar,  # bar
        }
    )


def HHI_MMI2x2E600(
    *,
    wl: sax.FloatArrayLike = 1.55,
    Width: sax.FloatArrayLike = 16.0,
) -> sax.SDict:
    """2x2 MMI coupler model (E600 waveguide) using simulated S-matrix data.

    Data simulated with EME method at temperature 27°C.

    Args:
        wl: wavelength [um] (valid range: 1.35-1.75 um)
        Width: MMI width [um] (valid range: 15.83-16.17 um)

    Returns:
        S-parameter dictionary with ports o1, o2 (inputs), o3, o4 (outputs)
    """
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator

    _, data = _load_csvy("HHI_MMI_SP/HHI_MMI2x2E600_smatrix.csvy")

    widths = np.sort(np.unique(np.asarray(data["Width"])))
    wavelengths = np.sort(np.unique(np.asarray(data["wavelength"])))
    nw, nl = len(widths), len(wavelengths)

    def make_grid(col):
        return np.asarray(data[col]).reshape(nw, nl)

    interp_bar_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_bar_TE:abs2")
    )
    interp_bar_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_bar_TE:phase")
    )
    interp_cross_abs2 = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_cross_TE:abs2")
    )
    interp_cross_phase = RegularGridInterpolator(
        (widths, wavelengths), make_grid("S_cross_TE:phase")
    )

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    width_arr = jnp.atleast_1d(jnp.asarray(Width))
    width_bc, wl_bc = jnp.broadcast_arrays(width_arr, wl_arr)
    output_shape = width_bc.shape

    pts = np.column_stack([np.asarray(width_bc).ravel(), np.asarray(wl_bc).ravel()])
    s_bar_abs = jnp.sqrt(jnp.clip(interp_bar_abs2(pts), 0, 1)).reshape(output_shape)
    s_bar_phase = jnp.asarray(interp_bar_phase(pts)).reshape(output_shape)
    s_cross_abs = jnp.sqrt(jnp.clip(interp_cross_abs2(pts), 0, 1)).reshape(output_shape)
    s_cross_phase = jnp.asarray(interp_cross_phase(pts)).reshape(output_shape)

    s_bar = s_bar_abs * jnp.exp(1j * s_bar_phase)
    s_cross = s_cross_abs * jnp.exp(1j * s_cross_phase)

    if jnp.ndim(wl) == 0 and jnp.ndim(Width) == 0:
        s_bar = s_bar.squeeze()
        s_cross = s_cross.squeeze()

    return sax.reciprocal(
        {
            ("o1", "o3"): s_bar,
            ("o1", "o4"): s_cross,
            ("o2", "o3"): s_cross,
            ("o2", "o4"): s_bar,
        }
    )


def HHI_BJsingle(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Single butt-joint (E1700 to active waveguide) model.

    Data measured at fixed wavelength, temperature 20°C. Loss: 1.5 dB.

    Args:
        wl: wavelength [um] (for API compatibility, data has no wl dependence)

    Returns:
        S-parameter dictionary with ports o1, o2
    """
    _, data = _load_csvy("HHI_BJsingle.csvy")
    loss_dB = float(data["loss"][0])
    transmission = jnp.asarray(10 ** (-loss_dB / 20))

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    transmission = jnp.broadcast_to(transmission, wl_arr.shape)

    return sax.reciprocal({("o1", "o2"): transmission})


def HHI_BJtwin(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Twin butt-joint (E1700 to active waveguide) model.

    Data measured at fixed wavelength, temperature 20°C. Loss: 1.5 dB.

    Args:
        wl: wavelength [um] (for API compatibility, data has no wl dependence)

    Returns:
        S-parameter dictionary with ports o1, o2, o3, o4
    """
    _, data = _load_csvy("HHI_BJtwin.csvy")
    loss_dB = float(data["loss"][0])
    transmission = jnp.asarray(10 ** (-loss_dB / 20))

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    transmission = jnp.broadcast_to(transmission, wl_arr.shape)

    # Twin has two parallel paths
    return sax.reciprocal({("o1", "o2"): transmission, ("o3", "o4"): transmission})


def HHI_SSCLATE200(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Spot size converter lateral taper (E200) model.

    Data measured at fixed wavelength. Loss: 1.1 dB.

    Args:
        wl: wavelength [um] (for API compatibility, data has no wl dependence)

    Returns:
        S-parameter dictionary with ports o1, o2
    """
    _, data = _load_csvy("HHI_SSCLATE200.csvy")
    loss_dB = float(data["loss"][0])
    transmission = jnp.asarray(10 ** (-loss_dB / 20))

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    transmission = jnp.broadcast_to(transmission, wl_arr.shape)

    return sax.reciprocal({("o1", "o2"): transmission})


def HHI_SSCLATE1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Spot size converter lateral taper (E1700) model.

    Data measured at fixed wavelength. Loss: 1.1 dB.

    Args:
        wl: wavelength [um] (for API compatibility, data has no wl dependence)

    Returns:
        S-parameter dictionary with ports o1, o2
    """
    _, data = _load_csvy("HHI_SSCLATE1700.csvy")
    loss_dB = float(data["loss"][0])
    transmission = jnp.asarray(10 ** (-loss_dB / 20))

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    transmission = jnp.broadcast_to(transmission, wl_arr.shape)

    return sax.reciprocal({("o1", "o2"): transmission})


def HHI_PolSplitter(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Polarization splitter model.

    Data measured at fixed wavelength. Insertion loss: 2.5 dB.
    TE output on o2, TM output on o3.

    Args:
        wl: wavelength [um] (for API compatibility, data has no wl dependence)

    Returns:
        S-parameter dictionary with ports o1 (input), o2 (TE), o3 (TM)
    """
    _, data = _load_csvy("HHI_PolSplitter.csvy")
    loss_dB = float(data["insertion loss"][0])
    transmission = jnp.asarray(10 ** (-loss_dB / 20))

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    transmission = jnp.broadcast_to(transmission, wl_arr.shape)

    # Ideal polarization splitting with loss
    return sax.reciprocal({("o1", "o2"): transmission, ("o1", "o3"): transmission})


def HHI_WGTE200E1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Waveguide transition E200 to E1700 model.

    Data measured at temperature 25°C.

    Args:
        wl: wavelength [um] (valid range: 1.47-1.57 um)

    Returns:
        S-parameter dictionary with ports o1, o2
    """
    _, data = _load_csvy("HHI_WGTE200E1700.csvy")

    # Wavelength in data is in pm, convert to um
    wl_data = data["wavelength"] / 1e6
    loss_te_dB = data["loss_TE"]

    # Interpolate loss at requested wavelength
    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    loss_dB = jnp.interp(wl_arr, wl_data, loss_te_dB)
    transmission = 10 ** (-loss_dB / 20)

    return sax.reciprocal({("o1", "o2"): transmission})


def HHI_MIR1E1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Mirror type 1 (E1700 waveguide) - full reflector.

    Data measured at temperature 27°C.

    Args:
        wl: wavelength [um] (valid range: 1.5-1.6 um)

    Returns:
        S-parameter dictionary with port o1 (reflection)
    """
    _, data = _load_csvy("HHI_MIR1.csvy")

    # Wavelength in um, reflectivity in %
    wl_data = data["wavelength"]
    reflectivity_pct = data["reflectivity_TE"]

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    r_pct = jnp.interp(wl_arr, wl_data, reflectivity_pct)
    r = jnp.sqrt(jnp.clip(r_pct / 100, 0, 1))

    return {("o1", "o1"): r}


def HHI_MIR2E1700(
    *,
    wl: sax.FloatArrayLike = 1.55,
) -> sax.SDict:
    """Mirror type 2 (E1700 waveguide) - partial reflector/splitter.

    Data measured at temperature 25°C.

    Args:
        wl: wavelength [um] (valid range: 1.5-1.6 um)

    Returns:
        S-parameter dictionary with ports o1, o2 (reflection + transmission)
    """
    _, data = _load_csvy("HHI_MIR2.csvy")

    # Wavelength in um, reflectivity in %
    wl_data = data["wavelength"]
    reflectivity_pct = data["reflectivity_TE"]

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    r_pct = jnp.interp(wl_arr, wl_data, reflectivity_pct)
    r_sq = jnp.clip(r_pct / 100, 0, 1)
    r = jnp.sqrt(r_sq)
    t = jnp.sqrt(1 - r_sq)

    return sax.reciprocal({("o1", "o1"): r, ("o1", "o2"): t})


def HHI_GRAT(
    *,
    wl: sax.FloatArrayLike = 1.54,
    L_G: float = 100.0,
    WL_G: float = 1540.0,
) -> sax.SDict:
    """Tunable DBR grating model.

    Data measured at temperature 25°C, voltage 0V, length 100um, input_power 1000uW.
    Note: Current data is for fixed L_G=100, WL_G=1540. Other values not interpolated.

    Args:
        wl: wavelength [um] (valid range: 1.525-1.545 um)
        L_G: grating length [um] (data only for L_G=100)
        WL_G: grating design wavelength [nm] (data only for WL_G=1540)

    Returns:
        S-parameter dictionary with ports o1, o2 (reflection on o1)
    """
    _, data = _load_csvy("HHI_GRAT.csvy")

    # Wavelength in nm, convert to um for interpolation
    wl_data = data["wavelength"] / 1000  # nm to um
    output_power = data["output_power"]
    input_power = 1000.0  # uW from metadata

    # Reflection coefficient from power ratio
    reflectivity = output_power / input_power

    wl_arr = jnp.atleast_1d(jnp.asarray(wl))
    r_sq = jnp.interp(wl_arr, wl_data, reflectivity)
    r = jnp.sqrt(jnp.clip(r_sq, 0, 1))
    t = jnp.sqrt(jnp.clip(1 - r_sq, 0, 1))

    # Grating: reflection back to o1, transmission to o2
    return sax.reciprocal({("o1", "o1"): r, ("o1", "o2"): t})


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # HHI_DirCoupE1700 - flat response vs wavelength (no wl data)
    wl = jnp.linspace(1.5, 1.6, 100)
    s = HHI_DirCoupE1700(wl=wl, L_C=1000.0)
    axes[0].plot(wl, jnp.abs(s[("o1", "o3")]) ** 2, ".-", label="Cross")
    axes[0].plot(wl, jnp.abs(s[("o1", "o4")]) ** 2, ".-", label="Bar")
    axes[0].set_xlabel("Wavelength [um]")
    axes[0].set_ylabel("Power coupling")
    axes[0].set_title("HHI_DirCoupE1700 (L_C=1000)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # HHI_MMI1x2E1700
    wl = jnp.linspace(1.5, 1.6, 100)
    s = HHI_MMI1x2E1700(wl=wl, Width=11.8)
    axes[1].plot(wl, jnp.abs(s[("o1", "o3")]) ** 2, ".-", label="o1→o3")
    axes[1].plot(wl, jnp.abs(s[("o1", "o2")]) ** 2, ".-", label="o1→o2")
    axes[1].set_xlabel("Wavelength [um]")
    axes[1].set_ylabel("Power coupling")
    axes[1].set_title("HHI_MMI1x2E1700 (Width=11.8)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
