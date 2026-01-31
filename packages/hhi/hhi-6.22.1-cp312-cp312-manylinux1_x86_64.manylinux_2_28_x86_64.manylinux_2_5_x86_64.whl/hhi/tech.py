import sys
from functools import partial

import gdsfactory as gf
import kfactory as kf
import numpy as np
from gdsfactory.cross_section import get_cross_sections
from gdsfactory.routing.route_bundle_sbend import route_bundle_sbend
from gdsfactory.technology import (
    LayerLevel,
    LayerMap,
    LayerStack,
    LayerViews,
)
from gdsfactory.typings import Layer

from hhi.config import PATH

nm = 1e-3


class LayerMapHHI(LayerMap):
    WG: Layer = (12, 0)  # 2µm passive waveguide
    E200: Layer = (13, 0)  # window; 42um wide 200µm deep etch window
    E600: Layer = (16, 0)  # window 42um wide 600µm deep etch window
    E1700: Layer = (18, 0)  # window 42um wide 1700µm deep etch window
    M1: Layer = (52, 0)  # M2 - 2um, butt-ended
    M2: Layer = (54, 0)  # defines the width
    BB_outline: Layer = (55, 0)  # defines BB placement
    BB_parameter: Layer = (56, 0)  # label with BB parameters
    BB_text: Layer = (59, 0)  # BB annotations
    PIN_LABEL: Layer = (1003, 0)
    FLOORPLAN: Layer = (
        7,
        0,
    )  # for wafer outline, and also for exclusion area cleave edge +/-50µm.
    TEXT: Layer = (24, 0)  # text and logos
    ISO: Layer = (51, 0)  # M2 + 2um, butt-ended

    # convenience layer names for generic PDK
    MTOP: Layer = (54, 0)  # defines the width
    LABEL_INSTANCE: Layer = (1003, 0)
    BB_PIN: Layer = (1002, 0)
    GS: Layer = (1004, 0)  # marker layer for GS pads


class Tech:
    width_e200 = 2.0
    width_e600 = 2.1
    width_e1700 = 2.3
    width_m2 = 12
    width_m1 = 12 + 4
    width_m2 = 148

    gap_m1 = 12
    gap_m2 = 16


TECH = Tech()
LAYER = LayerMapHHI
gf.kcl.layers = LAYER
gf.kcl.infos = kf.LayerInfos(
    **{v.name: kf.kdb.LayerInfo(v.layer, v.datatype) for v in LAYER},  # type: ignore[attr-defined]
)


port_types_electrical = (
    "electrical",
    "electrical",
)
port_names_electrical = ("e1", "e2")
layer_label = LAYER.PIN_LABEL
layer_bbox = LAYER.BB_outline

################################################
# Cross-sections
################################################
xsection = gf.xsection
min_radius_metal = 370


# Optical routing
@xsection
def E200(width: float = TECH.width_e200) -> gf.CrossSection:
    s0 = gf.Section(layer=LAYER.WG, width=width, port_names=("o1", "o2"))
    return gf.CrossSection(
        sections=(s0, gf.Section(layer=LAYER.E200, width=40)),
        radius=10e3,
    )


@xsection
def E600(width: float = TECH.width_e600) -> gf.CrossSection:
    s0 = gf.Section(layer=LAYER.WG, width=width, port_names=("o1", "o2"))
    return gf.CrossSection(
        sections=(s0, gf.Section(layer=LAYER.E600, width=40)),
        radius_min=450,
        radius=500.0,
    )


@xsection
def E1700(width: float = TECH.width_e1700) -> gf.CrossSection:
    s0 = gf.Section(layer=LAYER.WG, width=width, port_names=("o1", "o2"))
    return gf.CrossSection(
        sections=(s0, gf.Section(layer=LAYER.E1700, width=40)),
        radius_min=250,
        radius=300.0,
    )


@xsection
def ACT(width: float = 2.1) -> gf.CrossSection:
    s0 = gf.Section(layer=LAYER.WG, width=width, port_names=("o1", "o2"))
    return gf.CrossSection(sections=(s0,))


@xsection
def FACET(width: float = 2.1) -> gf.CrossSection:
    s0 = gf.Section(layer=LAYER.WG, width=width, port_names=("o1", "o2"))
    return gf.CrossSection(sections=(s0,))


def xs_metal(
    section_width: float | tuple[float, ...] = TECH.width_m1,
    width: float | None = None,
    gap: float | None = None,
    radius: float = min_radius_metal,
    **kwargs,
) -> gf.CrossSection:
    """HHI metal tracks (shorthand). Adds isolation correctly.
    Please change if there is a more gdsfactoresque way to do this.
    Will use a signal track for ports. This is important to remember for rS tracks!

    Args:
        section_width: width(s) of the metal tracks
        width: This is just a dummy argument to avoid a BUG in gdsfactory8 with multi-section cross-sections
        gap: gap(s) between the metal tracks
        radius: bend radius
    """

    if not hasattr(section_width, "__iter__"):
        section_width = (section_width,)
    if not hasattr(gap, "__iter__"):
        gap = (gap,) if gap else (0,) * (len(section_width) - 1)

    # Calculate corresponding offsets from gap & section_width
    total_width = sum(section_width) + sum(gap) if gap else sum(section_width)
    offsets = [0]
    if len(section_width) > 1:
        offsets = [
            -(total_width / 2)
            + sum(section_width[:i])
            + sum(gap[:i])
            + section_width[i] / 2
            for i in range(len(section_width))
        ]

    sections = []
    # If GSG or GS or any other multi-track, add the underlying isolation layer first
    # -> needed in gdsfactory 8 to avoid a BUG

    # Create the metal sections
    for i, (w, offset) in enumerate(zip(section_width, offsets)):
        # Only give ports to the central track, or the first track if there are only 1 or 2 tracks
        port_names = (
            ("e1", "e2")
            if (offset == 0 or (len(section_width) == 2 and i == 1))
            else (None, None)
        )
        sections.extend(
            [
                gf.Section(
                    layer=LAYER.M1,
                    width=w,
                    offset=offset,
                    port_names=port_names,
                    port_types=("electrical", "electrical"),
                ),
                gf.Section(layer=LAYER.M2, width=w - 4, offset=offset),
            ]
        )

    sections.append(gf.Section(layer=LAYER.ISO, width=total_width + 4))
    return gf.CrossSection(sections=sections, radius=radius, **kwargs)


# Define the metal routing cross-sections
@xsection
def DC(
    width: float = TECH.width_m1, layer="M1", radius=20, **kwargs
) -> gf.CrossSection:
    """HHI metal tracks for DC routing.

    Args:
        width: width(s) of the metal tracks.
        layer: layer for the metal tracks.
        radius: bend radius.
        kwargs: additional cross-section parameters.

    """
    cladding_layers = ["M2", "ISO"]
    cladding_offsets = [-2, 2]
    return gf.cross_section.metal1(
        width=width,
        layer=layer,
        radius=radius,
        cladding_layers=cladding_layers,
        cladding_offsets=cladding_offsets,
        **kwargs,
    )


@xsection
def GS(
    width_metal: float = 150,
    gap: float = 24,
    radius=min_radius_metal,
    **kwargs,
) -> gf.CrossSection:
    """HHI metal tracks for GS routing. Adds isolation correctly.

    Args:
        section_width: width(s) of the metal tracks.
        width: width(s) of the metal tracks.
        gap: gap between the metal tracks.
        radius: bend radius.
        kwargs: ignored cross-section parameters.
    """
    kwargs.pop("width", None)
    sections = [
        gf.Section(
            layer=LAYER.GS,
            width=gap,
            port_names=port_names_electrical,
            port_types=port_types_electrical,
        )
    ]
    width = width_metal
    total_width = 2 * width + gap
    offsets = [
        -width / 2 - gap / 2,
        width / 2 + gap / 2,
    ]

    for offset in offsets:
        sections.extend(
            [
                gf.Section(
                    layer=LAYER.M1,
                    width=width,
                    offset=offset,
                ),
                gf.Section(layer=LAYER.M2, width=width - 4, offset=offset),
            ]
        )

    sections.append(gf.Section(layer=LAYER.ISO, width=total_width + 4))
    return gf.CrossSection(sections=sections, radius=radius, **kwargs)


@xsection
def GSG(
    section_width: tuple[float, ...] = (100, 60, 100),
    gap: tuple[float, ...] = (50, 50),
    radius: float = min_radius_metal,
    **kwargs,
) -> gf.CrossSection:
    """HHI metal tracks for GSG routing. Adds isolation correctly.

    Args:
        section_width: width(s) of the metal tracks.
        gap: gap(s) between the metal tracks.
        radius: bend radius.
        kwargs: additional cross-section parameters.
    """
    return xs_metal(section_width=section_width, gap=gap, radius=radius, **kwargs)


cross_sections = get_cross_sections(sys.modules[__name__])

################################################
# Routing functions
################################################

route_single_e200 = partial(gf.routing.route_single, cross_section="E200")
route_single_e600 = partial(gf.routing.route_single, cross_section="E600")
route_single_e1700 = partial(gf.routing.route_single, cross_section="E1700")
route_single_dc = partial(
    gf.routing.route_single, cross_section="DC", allow_width_mismatch=True
)
route_single_gs = partial(gf.routing.route_single, cross_section="GS")
route_single_gsg = partial(gf.routing.route_single, cross_section="GSG")

route_single_sbend_e200 = partial(gf.routing.route_single_sbend, cross_section="E200")
route_single_sbend_e600 = partial(gf.routing.route_single_sbend, cross_section="E600")
route_single_sbend_e1700 = partial(gf.routing.route_single_sbend, cross_section="E1700")
route_single_sbend_dc = partial(gf.routing.route_single_sbend, cross_section="DC")
route_single_sbend_gs = partial(gf.routing.route_single_sbend, cross_section="GS")
route_single_sbend_gsg = partial(gf.routing.route_single_sbend, cross_section="GSG")

route_bundle_e200 = partial(gf.routing.route_bundle, cross_section="E200")
route_bundle_e600 = partial(gf.routing.route_bundle, cross_section="E600")
route_bundle_e1700 = partial(gf.routing.route_bundle, cross_section="E1700")
route_bundle_dc = partial(
    gf.routing.route_bundle,
    cross_section="DC",
    auto_taper=False,
    router="optical",
    separation=30,
    bend="bend_circular_metal",
    allow_width_mismatch=True,
)
route_bundle_dc_corner = partial(
    gf.routing.route_bundle,
    cross_section="DC",
    router="optical",
    bend="wire_corner45",
    auto_taper=False,
    separation=30,
    allow_width_mismatch=True,
)
route_bundle_gsg = partial(
    gf.routing.route_bundle, cross_section="GSG", auto_taper=False, router="optical"
)

route_bundle_all_angle = partial(
    gf.routing.route_bundle_all_angle,
    cross_section="E200",
    separation=5,
    bend="bend_euler_all_angle",
    straight="straight_all_angle",
)


route_bundle_gs = partial(
    gf.routing.route_bundle,
    cross_section="GS",
    bend="bend_circular_metal",
    router="optical",
)

route_bundle_sbend_e200 = partial(
    route_bundle_sbend, cross_section="E200", bend_s="bend_s"
)
route_bundle_sbend_e600 = partial(
    route_bundle_sbend, cross_section="E600", bend_s="bend_s"
)
route_bundle_sbend_e1700 = partial(
    route_bundle_sbend, cross_section="E1700", bend_s="bend_s"
)
route_bundle_sbend_dc = partial(
    route_bundle_sbend,
    cross_section="DC",
    bend_s="bend_s",
    allow_width_mismatch=True,
    port_name="e1",
)
route_bundle_sbend_gs = partial(
    route_bundle_sbend,
    cross_section="GS",
    bend_s="bend_s",
    allow_width_mismatch=True,
    port_name="e1",
)
route_bundle_sbend_gsg = partial(
    route_bundle_sbend,
    cross_section="GSG",
    bend_s="bend_s",
    allow_width_mismatch=True,
    allow_layer_mismatch=True,
    port_name="e1",
)

routing_strategies = dict(
    route_bundle_e200=route_bundle_e200,
    route_bundle_e600=route_bundle_e600,
    route_bundle_e1700=route_bundle_e1700,
    route_bundle_dc=route_bundle_dc,
    route_bundle_gs=route_bundle_gs,
    route_bundle_gsg=route_bundle_gsg,
    route_bundle_sbend_e200=route_bundle_sbend_e200,
    route_bundle_sbend_e600=route_bundle_sbend_e600,
    route_bundle_sbend_e1700=route_bundle_sbend_e1700,
    route_bundle_sbend_dc=route_bundle_sbend_dc,
    route_bundle_sbend_gs=route_bundle_sbend_gs,
    route_bundle_sbend_gsg=route_bundle_sbend_gsg,
)


################################################
# LayerStack
################################################
LAYER_VIEWS = LayerViews(PATH.lyp_yaml)
constants = {
    "fiber_array_spacing": 127.0,
    "fiber_spacing": 50.0,
    "fiber_input_to_output_spacing": 200.0,
    "metal_spacing": 30.0,
    "pad_pitch": 150.0,
    "pad_size": (66, 66),
}


# Define the layer stack
bias_E1700 = -150 * nm + 70 * nm  # second value to compensate
sidewall_angle = 5  # [°]

# TODO:Integrate these values into the layer stack
etch_depth_E1700 = 1850 * nm
etch_depth_E200 = 300 * nm
etch_depth_E600 = 650 * nm

layer_thicknesses = {
    "Substrate": 10000 * nm,
    "E1700_1": 100 * nm,
    "E1700_2": 700 * nm,
    "E1700_3": 820 * nm,
    "E1700_4": 20 * nm,
    "E1700_5": 205 * nm,
    "E1700_6": 5 * nm,
    "E1700_7": 50 * nm,
}


def get_layer_stack(
    layer_thicknesses: dict = layer_thicknesses,
    etch_depth_E1700: float = etch_depth_E1700,
    sidewall_angle: float = sidewall_angle,
) -> LayerStack:
    """Returns LayerStack."""

    layers = dict(
        Substrate=LayerLevel(
            layer=LAYER.E1700,
            thickness=layer_thicknesses["Substrate"],
            zmin=0,
            material="InP",
            mesh_order=1,
            sidewall_angle=0,
        ),
        E1700_1=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_1"],
            zmin=layer_thicknesses["Substrate"],
            material="Q(1.06)",
            mesh_order=2,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700,
        ),
        E1700_2=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_2"],
            zmin=layer_thicknesses["Substrate"] + layer_thicknesses["E1700_1"],
            material="InP",
            mesh_order=3,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
        E1700_3=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_3"],
            zmin=layer_thicknesses["Substrate"]
            + layer_thicknesses["E1700_1"]
            + layer_thicknesses["E1700_2"],
            material="Q(1.06)",
            mesh_order=4,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_2"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
        E1700_4=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_4"],
            zmin=layer_thicknesses["Substrate"]
            + layer_thicknesses["E1700_1"]
            + layer_thicknesses["E1700_2"]
            + layer_thicknesses["E1700_3"],
            material="InP",
            mesh_order=5,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_2"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_3"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
        E1700_5=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_5"],
            zmin=layer_thicknesses["Substrate"]
            + layer_thicknesses["E1700_1"]
            + layer_thicknesses["E1700_2"]
            + layer_thicknesses["E1700_3"]
            + layer_thicknesses["E1700_4"],
            material="Q(1.06)",
            mesh_order=6,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_2"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_3"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_4"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
        E1700_6=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_6"],
            zmin=layer_thicknesses["Substrate"]
            + layer_thicknesses["E1700_1"]
            + layer_thicknesses["E1700_2"]
            + layer_thicknesses["E1700_3"]
            + layer_thicknesses["E1700_4"]
            + layer_thicknesses["E1700_5"],
            material="InP",
            mesh_order=7,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_2"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_3"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_4"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_5"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
        E1700_7=LayerLevel(
            layer=LAYER.WG,
            thickness=layer_thicknesses["E1700_7"],
            zmin=layer_thicknesses["Substrate"]
            + layer_thicknesses["E1700_1"]
            + layer_thicknesses["E1700_2"]
            + layer_thicknesses["E1700_3"]
            + layer_thicknesses["E1700_4"]
            + layer_thicknesses["E1700_5"]
            + layer_thicknesses["E1700_6"],
            material="sin",
            mesh_order=8,
            sidewall_angle=sidewall_angle,
            bias=bias_E1700
            - layer_thicknesses["E1700_1"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_2"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_3"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_4"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_5"] / np.tan(np.deg2rad(90 - sidewall_angle))
            - layer_thicknesses["E1700_6"] / np.tan(np.deg2rad(90 - sidewall_angle)),
        ),
    )

    return LayerStack(layers=layers)


LAYER_STACK = get_layer_stack()


MATERIALS_INDEX = {  # this is a placeholder.
    # We have very accurate material models, but still unclear how to implement them here
    "InP": 3.167,
    "Q(1.06)": 3.258,
    "sin": 2.0,
}
