"""Waveguide components."""

import gdsfactory as gf
from gdsfactory.typings import CrossSectionSpec


@gf.cell
def straight(
    length: float = 10,
    cross_section: CrossSectionSpec = "E1700",
    width: float | None = None,
) -> gf.Component:
    """Returns a Straight waveguide.

    Args:
        length: straight length (um).
        cross_section: specification (CrossSection, string or dict).
        width: width to use. Defaults to cross_section.width.
    """
    return gf.c.straight(
        length=length, cross_section=cross_section, npoints=2, width=width
    )


@gf.cell
def bend_euler(
    radius: float | None = None,
    angle: float = 90,
    width: float | None = None,
    p: float = 1,
    with_arc_floorplan: bool = True,
    cross_section: CrossSectionSpec = "E1700",
) -> gf.Component:
    """Euler bend.

    Args:
        radius: in um.
        angle: total angle of the curve.
        width: width of the waveguide.
        p: proportion of the curve that is an Euler curve.
        with_arc_floorplan: if True the size of the bend will be adjusted to match an arc bend with the specified radius. If False: `radius` is the minimum radius of curvature.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
    """
    return gf.c.bend_euler(
        radius=radius,
        angle=angle,
        p=p,
        cross_section=cross_section,
        width=width,
        with_arc_floorplan=with_arc_floorplan,
    )


@gf.cell
def bend_circular(
    radius: float | None = None,
    angle: float = 90,
    width: float | None = None,
    cross_section: CrossSectionSpec = "E1700",
) -> gf.Component:
    """Euler bend.

    Args:
        radius: in um.
        angle: total angle of the curve.
        width: width of the waveguide.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
    """
    return bend_euler(
        radius=radius, angle=angle, p=0, cross_section=cross_section, width=width
    )


@gf.cell
def bend_circular_metal(
    radius: float | None = None,
    angle: float = 90,
    width: float | None = None,
    cross_section: CrossSectionSpec = "GS",
) -> gf.Component:
    """Euler bend.

    Args:
        radius: in um.
        angle: total angle of the curve.
        width: width of the waveguide.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
    """
    return bend_euler(
        radius=radius, angle=angle, p=0, cross_section=cross_section, width=width
    )


@gf.cell
def taper(
    width1: float = 1.0,
    width2: float | None = 2.0,
    length: float | None = None,
    cross_section: CrossSectionSpec = "E1700",
) -> gf.Component:
    """Linear taper, which tapers only the main cross section section.

    Args:
        width1: width of the west/left port.
        width2: width of the east/right port. Defaults to width1.
        length: taper length. If None it will be calculated based on the widths.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
    """
    width2 = width2 or width1
    if length is None:
        length = abs(width2 - width1) * 100

    return gf.c.taper(
        width1=width1,
        width2=width2,
        cross_section=cross_section,
        length=length,
        layer=None,
        port=None,
        with_two_ports=True,
        port_names=("o1", "o2"),
        port_types=("optical", "optical"),
        with_bbox=True,
    )


port_types = ("electrical", "electrical")
port_names = ("e1", "e2")


@gf.cell
def taper_metal(
    width1: float = 3.0,
    width2: float | None = 3.0,
    length: float | None = None,
) -> gf.Component:
    """Linear taper, which tapers only the main cross section section.

    Args:
        width1: width of the west/left port.
        width2: width of the east/right port. Defaults to width1.
        length: taper length. If None it will be calculated based on the widths.
    """
    width2 = width2 or width1
    length = length or abs(width2 - width1) / 2 or 10

    return gf.c.taper(
        width1=width1,
        width2=width2,
        cross_section="DC",
        port_names=port_names,
        port_types=port_types,
        layer=None,
        length=length,
        port=None,
        with_two_ports=True,
        with_bbox=True,
    )


@gf.cell
def sbend(
    offset: float = 40.0,
    radius: float | None = None,
    cross_section: CrossSectionSpec = "E1700",
    width: float | None = None,
    with_euler: bool = False,
) -> gf.Component:
    """An s-bend with a specific vertical offset and radius.

    Args:
        offset: in um.
        radius: in um.
        cross_section: spec.
        width: width to use. Defaults to cross_section.width.
        with_euler: if True uses an Euler bend, if False uses a circular bend.
    """
    return gf.c.bend_s_offset(
        offset=offset,
        radius=radius,
        cross_section=cross_section,
        width=width,
        with_euler=with_euler,
    )


@gf.cell
def bend_s(
    size: tuple[float, float] = (40, 1),
    cross_section: CrossSectionSpec = "E1700",
    width: float | None = None,
    npoints: int = 99,
    allow_min_radius_violation: bool = False,
) -> gf.Component:
    """A bezier s-bend with a specific vertical offset and radius.

    Args:
        size: in um.
        cross_section: spec.
        width: width to use. Defaults to cross_section.width.
        npoints: number of points to use.
        allow_min_radius_violation: if True allows radius to be smaller than cross_section radius.

    """
    return gf.c.bend_s(
        size=size,
        cross_section=cross_section,
        width=width,
        npoints=npoints,
        allow_min_radius_violation=allow_min_radius_violation,
    )


@gf.cell
def wire_corner45(
    radius: float = 10,
    width: float | None = 5.0,
    cross_section: CrossSectionSpec = "DC",
) -> gf.Component:
    """Returns 45 degrees electrical corner wire.

    Args:
        radius: of the corner.
        width: of the wire.
        cross_section: metal_routing.
    """
    c = gf.Component()

    p = gf.Path(
        [
            (0.0, 0.0),
            (radius / 2.0, 0.0),
            (radius, radius / 2.0),
            (radius, radius),
        ]
    )

    xs = gf.get_cross_section(cross_section, width=width)
    c = p.extrude(cross_section=xs)
    return c


@gf.cell
def wire_corner45_straight(
    width: float | None = None,
    radius: float | None = None,
    cross_section: CrossSectionSpec = "DC",
) -> gf.Component:
    """Returns 90 degrees electrical corner wire.

    Args:
        width: of the wire.
        radius: of the corner. Defaults to width.
        cross_section: metal_routing.
    """
    return gf.c.wire_corner45_straight(
        width=width,
        radius=radius,
        cross_section=cross_section,
    )


@gf.cell
def wire_corner(cross_section: CrossSectionSpec = "DC", **kwargs) -> gf.Component:
    """Returns a wire corner with 90 degrees."""
    return gf.c.wire_corner_sections(
        cross_section=cross_section,
    )


@gf.vcell
def straight_all_angle(
    length: float = 10.0,
    npoints: int = 2,
    cross_section: CrossSectionSpec = "E1700",
    width: float | None = None,
) -> gf.ComponentAllAngle:
    """Returns a Straight waveguide with offgrid ports.

    Args:
        length: straight length (um).
        npoints: number of points.
        cross_section: specification (CrossSection, string or dict).
        width: width of the waveguide. If None, it will use the width of the cross_section.

    .. code::

        o1  ──────────────── o2
                length
    """
    return gf.c.straight_all_angle(
        length=length,
        npoints=npoints,
        cross_section=cross_section,
        width=width,
    )


@gf.vcell
def bend_euler_all_angle(
    radius: float | None = None,
    angle: float = 90.0,
    p: float = 0.5,
    with_arc_floorplan: bool = True,
    npoints: int | None = None,
    layer: gf.typings.LayerSpec | None = None,
    width: float | None = None,
    cross_section: CrossSectionSpec = "E1700",
    allow_min_radius_violation: bool = False,
) -> gf.ComponentAllAngle:
    """Regular degree euler bend with arbitrary angle.

    Args:
        radius: in um. Defaults to cross_section_radius.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        with_arc_floorplan: if True the size of the bend will be adjusted to match an arc bend with the specified radius. If False: `radius` is the minimum radius of curvature.
        npoints: Number of points used per 360 degrees.
        layer: layer to use. Defaults to cross_section.layer.
        width: width to use. Defaults to cross_section.width.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
        allow_min_radius_violation: if True allows radius to be smaller than cross_section radius.

    """
    return gf.c.bend_euler_all_angle(
        radius=radius,
        angle=angle,
        p=p,
        with_arc_floorplan=with_arc_floorplan,
        npoints=npoints,
        layer=layer,
        width=width,
        cross_section=cross_section,
        allow_min_radius_violation=allow_min_radius_violation,
    )
