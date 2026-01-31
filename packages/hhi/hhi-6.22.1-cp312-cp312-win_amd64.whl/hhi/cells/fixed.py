from functools import partial

import gdsfactory as gf
from gdsfactory.add_pins import add_pins_inside2um
from gdsfactory.config import CONF

CONF.max_cellname_length = 32

cell = partial(gf.cell, set_name=False)
layer_bbox = (55, 0)
layer_bbmetal = None
layer_pin_label = (1003, 0)
layer_pin = None  # (1002, 0)
layer_pin_optical = (1003, 0)
layer_pin_electrical = (1004, 0)
layer_label = (56, 0)
layer_text = (59, 0)
add_abstract_pins = False


@gf.cell
def text_function(
    text: str = "abcd",
    size: float = 5.0,
    justify: str = "left",
    layer=layer_text,
) -> gf.Component:
    return gf.c.text(
        text=text,
        size=size,
        justify=justify,
        layer=layer,
        position=(0.0, 0.0),
    )


add_pins = partial(
    add_pins_inside2um,
    layer_label=layer_pin_optical,
    layer=layer_pin_optical,
    skip_cross_sections=("GS",),
)

layer_label = (56, 0)


@gf.cell
def HHI_BJsingle() -> gf.Component:
    """Single butt-joint from an E1700 to an active waveguide."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [200.0, 60.0], [200.0, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_BJsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(200.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_BJtwin() -> gf.Component:
    """Twin butt-joint from an E1700 to an active waveguide."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [200.0, 60.0], [200.0, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_BJtwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(200.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(200.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_BPD() -> gf.Component:
    """Balanced Photo Diode"""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 185.0], [1155.0, 185.0], [1155.0, -185.0], [0.0, -185.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = "HHI_BPD"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1154.0, 130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1154.0, -130.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(260.0, -185.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 25.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(0.0, -25.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(260.0, 185.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((1155.0 + 1155.0) / 2, (130.0 + -130.0) / 2),
        orientation=0,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 60.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1154.0, 0.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DBR(
    L_FR: float = 200.0,
    L_IF: float = 40.0,
    L_IM: float = 40.0,
    L_IR: float = 40.0,
    L_PS: float = 50.0,
    L_RR: float = 50.0,
    L_SOA: float = 400.0,
    WL_FR: float = 1550.0,
    WL_RR: float = 1550.0,
) -> gf.Component:
    """Distributed Bragg reflector (DBR) grating laser based on MQWs, connecting to E1700 waveguides.

    Args:
      L_FR: length of front reflector (min: 20.0, max: 800.0, um).
      L_IF: length of front isolation section (min: 10.0, max: 800.0, um).
      L_IM: length of middle isolation section (min: 10.0, max: 800.0, um).
      L_IR: length of rear isolation section (min: 10.0, max: 800.0, um).
      L_PS: length of phase section (min: 20.0, max: 2000.0, um).
      L_RR: length of rear reflector (min: 20.0, max: 800.0, um).
      L_SOA: length of SOA section (min: 20.0, max: 2000.0, um).
      WL_FR: wavelength of front reflector (min: 1500.0, max: 1580.0, nm).
      WL_RR: wavelength of rear reflector (min: 1500.0, max: 1580.0, nm).
    """

    if L_FR < 20.0 or L_FR > 800.0:
        raise ValueError("L_FR must be between 20.0 and 800.0 um")

    if L_IF < 10.0 or L_IF > 800.0:
        raise ValueError("L_IF must be between 10.0 and 800.0 um")

    if L_IM < 10.0 or L_IM > 800.0:
        raise ValueError("L_IM must be between 10.0 and 800.0 um")

    if L_IR < 10.0 or L_IR > 800.0:
        raise ValueError("L_IR must be between 10.0 and 800.0 um")

    if L_PS < 20.0 or L_PS > 2000.0:
        raise ValueError("L_PS must be between 20.0 and 2000.0 um")

    if L_RR < 20.0 or L_RR > 800.0:
        raise ValueError("L_RR must be between 20.0 and 800.0 um")

    if L_SOA < 20.0 or L_SOA > 2000.0:
        raise ValueError("L_SOA must be between 20.0 and 2000.0 um")

    if WL_FR < 1500.0 or WL_FR > 1580.0:
        raise ValueError("WL_FR must be between 1500.0 and 1580.0 nm")

    if WL_RR < 1500.0 or WL_RR > 1580.0:
        raise ValueError("WL_RR must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR + 400.0, 60.0],
            [L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR + 400.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DBR:L_FR={L_FR},L_IF={L_IF},L_IM={L_IM},L_IR={L_IR},L_PS={L_PS},L_RR={L_RR},L_SOA={L_SOA},WL_FR={WL_FR},WL_RR={WL_RR}"

    ysize = c.ysize
    c.add_label(
        text=f"L_FR:{L_FR}", position=(xc, yc - 0 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IF:{L_IF}", position=(xc, yc - 1 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IM:{L_IM}", position=(xc, yc - 2 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IR:{L_IR}", position=(xc, yc - 3 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_PS:{L_PS}", position=(xc, yc - 4 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_RR:{L_RR}", position=(xc, yc - 5 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_SOA:{L_SOA}", position=(xc, yc - 6 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_FR:{WL_FR}", position=(xc, yc - 7 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_RR:{WL_RR}", position=(xc, yc - 8 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 9 / 10 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_RR / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR + 400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_RR / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p2",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p3",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p4",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DBRsection(
    L_FR: float = 200.0,
    L_IF: float = 40.0,
    L_IM: float = 40.0,
    L_IR: float = 40.0,
    L_PS: float = 50.0,
    L_RR: float = 50.0,
    L_SOA: float = 400.0,
    WL_FR: float = 1550.0,
    WL_RR: float = 1550.0,
) -> gf.Component:
    """Distributed Bragg reflector (DBR) grating laser section based on MQWs, connecting to active waveguides.

    Args:
      L_FR: length of front reflector (min: 20.0, max: 800.0, um).
      L_IF: length of front isolation section (min: 10.0, max: 800.0, um).
      L_IM: length of middle isolation section (min: 10.0, max: 800.0, um).
      L_IR: length of rear isolation section (min: 10.0, max: 800.0, um).
      L_PS: length of phase section (min: 20.0, max: 2000.0, um).
      L_RR: length of rear reflector (min: 20.0, max: 800.0, um).
      L_SOA: length of SOA section (min: 20.0, max: 2000.0, um).
      WL_FR: wavelength of front reflector (min: 1500.0, max: 1580.0, nm).
      WL_RR: wavelength of rear reflector (min: 1500.0, max: 1580.0, nm).
    """

    if L_FR < 20.0 or L_FR > 800.0:
        raise ValueError("L_FR must be between 20.0 and 800.0 um")

    if L_IF < 10.0 or L_IF > 800.0:
        raise ValueError("L_IF must be between 10.0 and 800.0 um")

    if L_IM < 10.0 or L_IM > 800.0:
        raise ValueError("L_IM must be between 10.0 and 800.0 um")

    if L_IR < 10.0 or L_IR > 800.0:
        raise ValueError("L_IR must be between 10.0 and 800.0 um")

    if L_PS < 20.0 or L_PS > 2000.0:
        raise ValueError("L_PS must be between 20.0 and 2000.0 um")

    if L_RR < 20.0 or L_RR > 800.0:
        raise ValueError("L_RR must be between 20.0 and 800.0 um")

    if L_SOA < 20.0 or L_SOA > 2000.0:
        raise ValueError("L_SOA must be between 20.0 and 2000.0 um")

    if WL_FR < 1500.0 or WL_FR > 1580.0:
        raise ValueError("WL_FR must be between 1500.0 and 1580.0 nm")

    if WL_RR < 1500.0 or WL_RR > 1580.0:
        raise ValueError("WL_RR must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR, 60.0],
            [L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DBRsection:L_FR={L_FR},L_IF={L_IF},L_IM={L_IM},L_IR={L_IR},L_PS={L_PS},L_RR={L_RR},L_SOA={L_SOA},WL_FR={WL_FR},WL_RR={WL_RR}"

    ysize = c.ysize
    c.add_label(
        text=f"L_FR:{L_FR}", position=(xc, yc - 0 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IF:{L_IF}", position=(xc, yc - 1 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IM:{L_IM}", position=(xc, yc - 2 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_IR:{L_IR}", position=(xc, yc - 3 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_PS:{L_PS}", position=(xc, yc - 4 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_RR:{L_RR}", position=(xc, yc - 5 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"L_SOA:{L_SOA}", position=(xc, yc - 6 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_FR:{WL_FR}", position=(xc, yc - 7 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_RR:{WL_RR}", position=(xc, yc - 8 / 10 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 9 / 10 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_RR / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_RR / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p2",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p3",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p4",
        width=16.0,
        cross_section="DC",
        center=(L_RR + L_IR + L_SOA + L_IM + L_PS + L_IF + L_FR / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DFB(WL_L: float = 1550.0) -> gf.Component:
    """Distributed feedback (DFB) grating laser with RF modulation and thermal tuning, connecting to E1700 waveguides.

    Args:
      WL_L: wavelength of laser (min: 1500.0, max: 1580.0, nm).
    """

    if WL_L < 1500.0 or WL_L > 1580.0:
        raise ValueError("WL_L must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 110.0], [600.0, 110.0], [600.0, -110.0], [0.0, -110.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DFB:WL_L={WL_L}"

    ysize = c.ysize
    c.add_label(
        text=f"WL_L:{WL_L}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(209.0, -110.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(391.0, -110.0),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (170.0, 109.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (430.0, 109.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(600.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((170.0 + 430.0) / 2, (110.0 + 110.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (300.0, 109.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DFBsection(WL_L: float = 1550.0) -> gf.Component:
    """Distributed feedback (DFB) grating laser with RF modulation and thermal tuning, connecting to active waveguides.

    Args:
      WL_L: wavelength of laser (min: 1500.0, max: 1580.0, nm).
    """

    if WL_L < 1500.0 or WL_L > 1580.0:
        raise ValueError("WL_L must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 110.0], [400.0, 110.0], [400.0, -110.0], [0.0, -110.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DFBsection:WL_L={WL_L}"

    ysize = c.ysize
    c.add_label(
        text=f"WL_L:{WL_L}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(109.0, -110.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(291.0, -110.0),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (70.0, 109.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (330.0, 109.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((70.0 + 330.0) / 2, (110.0 + 110.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (200.0, 109.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DirCoupE1700(L_C: float = 100.0) -> gf.Component:
    """2x2 Directional coupler connection to E1700 waveguides.

    Args:
      L_C: length of coupling (min: 1.0, max: 1000.0, um).
    """

    if L_C < 1.0 or L_C > 1000.0:
        raise ValueError("L_C must be between 1.0 and 1000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[L_C + 610.0, 30.0], [L_C + 610.0, -30.0], [0, -30.0], [0.0, 30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DirCoupE1700:L_C={L_C}"

    ysize = c.ysize
    c.add_label(
        text=f"L_C:{L_C}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_C + 610.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(L_C + 610.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_DirCoupE600(L_C: float = 100.0) -> gf.Component:
    """2x2 Directional coupler connection to E600 waveguides.

    Args:
      L_C: length of coupling (min: 1.0, max: 1000.0, um).
    """

    if L_C < 1.0 or L_C > 1000.0:
        raise ValueError("L_C must be between 1.0 and 1000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[L_C + 200.0, 30.0], [L_C + 200.0, -30.0], [0, -30.0], [0.0, 30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_DirCoupE600:L_C={L_C}"

    ysize = c.ysize
    c.add_label(
        text=f"L_C:{L_C}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(L_C + 200.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.1,
        cross_section="E600",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.1,
        cross_section="E600",
        center=(L_C + 200.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EAM(L_E: float = 100.0) -> gf.Component:
    """Electro-absorbtion modulator (EAM) connecting to E1700 waveguides.

    Args:
      L_E: length of EAM (min: 60.0, max: 1000.0, um).
    """

    if L_E < 60.0 or L_E > 1000.0:
        raise ValueError("L_E must be between 60.0 and 1000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0, 110.0], [L_E + 400.0, 110.0], [L_E + 400.0, -110.0], [0.0, -110.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EAM:L_E={L_E}"

    ysize = c.ysize
    c.add_label(
        text=f"L_E:{L_E}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 70.0, 109.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 330.0, 109.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_E + 400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((L_E / 2 + 70.0 + L_E / 2 + 330.0) / 2, (110.0 + 110.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 200.0, 109.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EAMsection(L_E: float = 100.0) -> gf.Component:
    """Electro-absorbtion modulator (EAM) section connecting to active waveguides.

    Args:
      L_E: length of EAM (min: 60.0, max: 1000.0, um).
    """

    if L_E < 60.0 or L_E > 1000.0:
        raise ValueError("L_E must be between 60.0 and 1000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, -110.0], [L_E + 300.0, -110.0], [L_E + 300.0, 110.0], [0.0, 110.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EAMsection:L_E={L_E}"

    ysize = c.ysize
    c.add_label(
        text=f"L_E:{L_E}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 20.0, 109.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 280.0, 109.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_E + 300.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((L_E / 2 + 20.0 + L_E / 2 + 280.0) / 2, (110.0 + 110.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (L_E / 2 + 150.0, 109.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOBiasSectionSingle(L_B: float = 500.0) -> gf.Component:
    """P-Contact Bias Pads for the upper- and lower- waveguide.

    Args:
      L_B: length of PMEO (min: 50.0, max: 2000.0, um).
    """

    if L_B < 50.0 or L_B > 2000.0:
        raise ValueError("L_B must be between 50.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[L_B, -60.0], [L_B, 60.0], [0.0, 60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOBiasSectionSingle:L_B={L_B}"

    ysize = c.ysize
    c.add_label(
        text=f"L_B:{L_B}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_B / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_B, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_B / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOBiasSectionTwin(L_B: float = 500.0) -> gf.Component:
    """ActiveRF waveguide and containing the P-Contact Bias Pads.

    Args:
      L_B: length of the Bias Pads section (min: 50.0, max: 2000.0, um).
    """

    if L_B < 50.0 or L_B > 2000.0:
        raise ValueError("L_B must be between 50.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_B, 60.0], [L_B, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOBiasSectionTwin:L_B={L_B}"

    ysize = c.ysize
    c.add_label(
        text=f"L_B:{L_B}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_B, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(L_B, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_B / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p2",
        width=16.0,
        cross_section="DC",
        center=(L_B / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOElectricalGND() -> gf.Component:
    """ActiveRF waveguide and containing the N Contact Pad of the subsequent- or previous MZM and PMEO modulator."""

    c = gf.Component()
    c.add_polygon(
        [[130.0, -60.0], [130.0, 60.0], [0.0, 60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_EOElectricalGND"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(65.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(65.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(130.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(130.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOPMTWSingleDD(N: int = 4.0) -> gf.Component:
    """Electro Optic phase modulator connecting to only one active waveguide.

    Args:
      N: Number of 250um sections (min: 1.0, max: 50.0, null).
    """

    if N < 1.0 or N > 50.0:
        raise ValueError("N must be between 1.0 and 50.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [180.0, 60.0],
            [180.0, 130.0],
            [N * 250.0 + 580.0, 130.0],
            [N * 250.0 + 580.0, 60.0],
            [N * 250.0 + 760.0, 60.0],
            [N * 250.0 + 760.0, -60.0],
            [N * 250.0 + 580.0, -60.0],
            [N * 250.0 + 580.0, -130.0],
            [180.0, -130.0],
            [180.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOPMTWSingleDD:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (262.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (498.0 + N * 250.0, -129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(65.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(65.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((262.0 + 436.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (436.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((498.0 + N * 250.0 + 324.0 + N * 250.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (324.0 + N * 250.0, -129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOPMTWSingleDU(N: int = 4.0) -> gf.Component:
    """Electro Optic phase modulator connecting to only one active waveguide where the RF-input and RF-output are directed towards opposite direction.

    Args:
      N: Number of 250um sections (min: 1.0, max: 50.0, null).
    """

    if N < 1.0 or N > 50.0:
        raise ValueError("N must be between 1.0 and 50.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [180.0, 60.0],
            [180.0, 130.0],
            [N * 250.0 + 580.0, 130.0],
            [N * 250.0 + 580.0, 60.0],
            [N * 250.0 + 760.0, 60.0],
            [N * 250.0 + 760.0, -60.0],
            [N * 250.0 + 580.0, -60.0],
            [N * 250.0 + 580.0, -130.0],
            [180.0, -130.0],
            [180.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOPMTWSingleDU:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (262.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (498.0 + N * 250.0, 129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(65.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(65.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((262.0 + 436.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (436.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((498.0 + N * 250.0 + 324.0 + N * 250.0) / 2, (130.0 + 130.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (324.0 + N * 250.0, 129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOPMTWTwinDD(N: int = 4.0) -> gf.Component:
    """Electro Optic phase modulator connecting to only one active waveguide.

    Args:
      N: Number of 250um sections (min: 1.0, max: 50.0, null).
    """

    if N < 1.0 or N > 50.0:
        raise ValueError("N must be between 1.0 and 50.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [180.0, 60.0],
            [180.0, 130.0],
            [N * 250.0 + 580.0, 130.0],
            [N * 250.0 + 580.0, 60.0],
            [N * 250.0 + 760.0, 60.0],
            [N * 250.0 + 760.0, -60.0],
            [N * 250.0 + 580.0, -60.0],
            [N * 250.0 + 580.0, -130.0],
            [180.0, -130.0],
            [180.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOPMTWTwinDD:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (262.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (498.0 + N * 250.0, -129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(65.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(65.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((262.0 + 436.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (436.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((498.0 + N * 250.0 + 324.0 + N * 250.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (324.0 + N * 250.0, -129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOPMTWTwinDU(N: int = 4.0) -> gf.Component:
    """Electro Optic phase modulator connecting to only one active waveguide where the RF-input and RF-output are directed towards opposite direction.

    Args:
      N: Number of 250um sections (min: 1.0, max: 50.0, null).
    """

    if N < 1.0 or N > 50.0:
        raise ValueError("N must be between 1.0 and 50.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [180.0, 60.0],
            [180.0, 130.0],
            [N * 250.0 + 580.0, 130.0],
            [N * 250.0 + 580.0, 60.0],
            [N * 250.0 + 760.0, 60.0],
            [N * 250.0 + 760.0, -60.0],
            [N * 250.0 + 580.0, -60.0],
            [N * 250.0 + 580.0, -130.0],
            [180.0, -130.0],
            [180.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_EOPMTWTwinDU:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (262.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (498.0 + N * 250.0, 129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(65.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(65.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(N * 250.0 + 695.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(N * 250.0 + 760.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((262.0 + 436.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (436.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((498.0 + N * 250.0 + 324.0 + N * 250.0) / 2, (130.0 + 130.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (324.0 + N * 250.0, 129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_EOPMTermination() -> gf.Component:
    """GS RF 50 Ohm Termination."""

    c = gf.Component()
    c.add_polygon(
        [[210.0, 170.0], [0.0, 170.0], [0.0, -170.0], [210.0, -170.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_EOPMTermination"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 150.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, -87.0)
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((0.0 + 0.0) / 2, (-87.0 + 87.0) / 2),
        orientation=180,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 150.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, 87.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_FacetWGE1700(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Facet end and WG protection to E1700 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflectance (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 20.0], [100.0, 20.0], [100.0, -20.0], [0.0, -20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_FacetWGE1700:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(100.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_FacetWGE1700twin(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Facet end and WG protection to twin E1700 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflectance (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[100.0, 25.0], [100.0, -25.0], [0.0, -25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_FacetWGE1700twin:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(100.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=10.0,
        cross_section="FACET",
        center=(100.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_FacetWGE200(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Facet end and WG protection to E200 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflectance (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 20.0], [100.0, 20.0], [100.0, -20.0], [0.0, -20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_FacetWGE200:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(100.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_FacetWGE600(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Facet end and WG protection to E600 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflectance (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 20.0], [100.0, 20.0], [100.0, -20.0], [0.0, -20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_FacetWGE600:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(100.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_GRAT(L_G: float = 100.0, WL_G: float = 1550.0) -> gf.Component:
    """Tunable distributed Bragg reflector (DBR) grating connecting to E1700 waveguides.

    Args:
      L_G: length of grating (min: 20.0, max: 800.0, um).
      WL_G: wavelength for grating (min: 1500.0, max: 1580.0, nm).
    """

    if L_G < 20.0 or L_G > 800.0:
        raise ValueError("L_G must be between 20.0 and 800.0 um")

    if WL_G < 1500.0 or WL_G > 1580.0:
        raise ValueError("WL_G must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_G + 400.0, 60.0], [L_G + 400.0, -60.0], [0.0, -60.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_GRAT:L_G={L_G},WL_G={WL_G}"

    ysize = c.ysize
    c.add_label(
        text=f"L_G:{L_G}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_G:{WL_G}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_G / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_G + 400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_G / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_GRATsection(L_G: float = 100.0, WL_G: float = 1550.0) -> gf.Component:
    """Tunable distributed Bragg reflector (DBR) grating connecting to active waveguides.

    Args:
      L_G: length of grating (min: 24.0, max: 800.0, um).
      WL_G: wavelength for grating (min: 1500.0, max: 1580.0, nm).
    """

    if L_G < 24.0 or L_G > 800.0:
        raise ValueError("L_G must be between 24.0 and 800.0 um")

    if WL_G < 1500.0 or WL_G > 1580.0:
        raise ValueError("WL_G must be between 1500.0 and 1580.0 nm")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_G, 60.0], [L_G, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_GRATsection:L_G={L_G},WL_G={WL_G}"

    ysize = c.ysize
    c.add_label(
        text=f"L_G:{L_G}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"WL_G:{WL_G}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_G / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_G, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_G / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_GSGtoGS() -> gf.Component:
    """GSG to GS transition"""

    c = gf.Component()
    c.add_polygon(
        [[250.0, 190.0], [250.0, -190.0], [0.0, -190.0], [0.0, 190.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_GSGtoGS"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, 130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 150.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (249.0, -105.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, -130.0)
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((0.0 + 0.0) / 2, (130.0 + -130.0) / 2),
        orientation=180,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 60.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, 0.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((250.0 + 250.0) / 2, (-105.0 + 69.0) / 2),
        orientation=0,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 150.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (249.0, 69.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_ISOsectionSingle(L_I: float = 100.0) -> gf.Component:
    """Single P-side isolation section (resistance) for in between two optical-active waveguide sections.

    Args:
      L_I: length of isolation (min: 10.0, max: 12000.0, um).
    """

    if L_I < 10.0 or L_I > 12000.0:
        raise ValueError("L_I must be between 10.0 and 12000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_I, 60.0], [L_I, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_ISOsectionSingle:L_I={L_I}"

    ysize = c.ysize
    c.add_label(
        text=f"L_I:{L_I}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_I, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_ISOsectionTwin(L_I: float = 100.0) -> gf.Component:
    """Twin P-side isolation section (resistance) for in between two optical-active waveguide sections.

    Args:
      L_I: length of isolation (min: 10.0, max: 12000.0, um).
    """

    if L_I < 10.0 or L_I > 12000.0:
        raise ValueError("L_I must be between 10.0 and 12000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_I, 60.0], [L_I, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_ISOsectionTwin:L_I={L_I}"

    ysize = c.ysize
    c.add_label(
        text=f"L_I:{L_I}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_I, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(L_I, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_METMETx() -> gf.Component:
    """Crossing between DC-line and another DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 23.0], [76.0, 23.0], [76.0, -23.0], [0.0, -23.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_METMETx"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(0.0, 0.0),
        orientation=180,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(76.0, 0.0),
        orientation=0,
        port_type="electrical",
    )
    c.add_port(
        name="e3",
        width=16.0,
        cross_section="DC",
        center=(38.0, -23.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="e4",
        width=16.0,
        cross_section="DC",
        center=(38.0, 23.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MIR1E1700() -> gf.Component:
    """Single port Multi-mode interference reflector (MIR) in E1700. Component for broadband power reflection."""

    c = gf.Component()
    c.add_polygon(
        [[130.0, 20.0], [130.0, -20.0], [0.0, -20.0], [0.0, 20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MIR1E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MIR2E1700() -> gf.Component:
    """Dual port Multi-mode interference reflector (MIR) in E1700. Component for broadband power reflection and splitting."""

    c = gf.Component()
    c.add_polygon(
        [[190.0, 25.0], [190.0, -25.0], [0.0, -25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MIR2E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -2.0),
        orientation=180,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI1x2ACT() -> gf.Component:
    """1x2 Multi-mode interference (MMI) coupler in optical-active waveguide. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [445.0, 60.0], [445.0, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI1x2ACT"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(445.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(445.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI1x2E1700() -> gf.Component:
    """1x2 Multi-mode interference (MMI) coupler in E1700. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [220.0, 25.0], [220.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI1x2E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(220.0, 2.6),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(220.0, -2.6),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI1x2E600() -> gf.Component:
    """1x2 Multi-mode interference (MMI) coupler in E600. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [280.0, 25.0], [280.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI1x2E600"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(280.0, 3.1),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.1,
        cross_section="E600",
        center=(280.0, -3.1),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI2x2ACT() -> gf.Component:
    """2x2 Multi-mode interference (MMI) coupler in optical-active waveguide. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [900.0, 60.0], [900.0, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI2x2ACT"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(900.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(900.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI2x2E1700() -> gf.Component:
    """2x2 Multi-mode interference (MMI) coupler in E1700. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 26.0], [310.0, 26.0], [310.0, -26.0], [0.0, -26.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI2x2E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(310.0, 2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(310.0, -2.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MMI2x2E600() -> gf.Component:
    """2x2 Multi-mode interference (MMI) coupler in E600. Component for power splitting and combining."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 28.0], [490.0, 28.0], [490.0, -28.0], [0.0, -28.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MMI2x2E600"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 2.8),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(490.0, 2.8),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.1,
        cross_section="E600",
        center=(0.0, -2.8),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.1,
        cross_section="E600",
        center=(490.0, -2.8),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MZIswitch() -> gf.Component:
    """Thermal-optical Mach-Zehnder modulator."""

    c = gf.Component()
    c.add_polygon(
        [[1490.0, 50.0], [1490.0, -50.0], [0.0, -50.0], [0.0, 50.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_MZIswitch"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(557.0, 50.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(933.0, 50.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e3",
        width=16.0,
        cross_section="DC",
        center=(557.0, -50.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="e4",
        width=16.0,
        cross_section="DC",
        center=(933.0, -50.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(1490.0, 2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(1490.0, -2.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MZMDD(N: int = 16.0) -> gf.Component:
    """Push-Pull Mach-Zehnder Modulator with GS track connecting to E1700 waveguides and where the RF-input and RF-output are both directed downward.

    Args:
      N: Number of 250um sections (min: 2.0, max: 32.0, null).
    """

    if N < 2.0 or N > 32.0:
        raise ValueError("N must be between 2.0 and 32.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [1300.0, 60.0],
            [1300.0, 130.0],
            [1700.0 + N * 250.0, 130.0],
            [1700.0 + N * 250.0, 60.0],
            [2670.0 + N * 250.0, 60.0],
            [2670.0 + N * 250.0, -60.0],
            [1700.0 + N * 250.0, -60.0],
            [1700.0 + N * 250.0, -130.0],
            [1300.0, -130.0],
            [1300.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_MZMDD:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1382.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1618.0 + N * 250.0, -129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(1185.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(1185.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(1815.0 + N * 250.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(1815.0 + N * 250.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(2670.0 + N * 250.0, 2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(2670.0 + N * 250.0, -2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(870.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p2",
        width=16.0,
        cross_section="DC",
        center=(870.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((1382.0 + 1556.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1556.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((1618.0 + N * 250.0 + 1444.0 + N * 250.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1444.0 + N * 250.0, -129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_MZMDU(N: int = 16.0) -> gf.Component:
    """Push-Pull Mach-Zehnder Modulator with GS track connecting to E1700 waveguides and where the RF-input and RF-output are directed towards opposite direction.

    Args:
      N: Number of 250um sections (min: 2.0, max: 32.0, null).
    """

    if N < 2.0 or N > 32.0:
        raise ValueError("N must be between 2.0 and 32.0 null")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 60.0],
            [1300.0, 60.0],
            [1300.0, 130.0],
            [1700.0 + N * 250.0, 130.0],
            [1700.0 + N * 250.0, 60.0],
            [2670.0 + N * 250.0, 60.0],
            [2670.0 + N * 250.0, -60.0],
            [1700.0 + N * 250.0, -60.0],
            [1700.0 + N * 250.0, -130.0],
            [1300.0, -130.0],
            [1300.0, -60.0],
            [0.0, -60.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_MZMDU:N={N}"

    ysize = c.ysize
    c.add_label(text=f"N:{N}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1382.0, -129.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1444.0 + N * 250.0, 129.0)
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(1185.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n2",
        width=16.0,
        cross_section="DC",
        center=(1185.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="n3",
        width=16.0,
        cross_section="DC",
        center=(1815.0 + N * 250.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="n4",
        width=16.0,
        cross_section="DC",
        center=(1815.0 + N * 250.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(2670.0 + N * 250.0, 2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(2670.0 + N * 250.0, -2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(870.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="p2",
        width=16.0,
        cross_section="DC",
        center=(870.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((1382.0 + 1556.0) / 2, (-130.0 + -130.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1556.0, -129.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((1444.0 + N * 250.0 + 1618.0 + N * 250.0) / 2, (130.0 + 130.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1618.0 + N * 250.0, 129.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PDDC() -> gf.Component:
    """DC photo-diode."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -30.0], [100.0, -30.0], [100.0, 30.0], [0.0, 30.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PDDC"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(50.0, -30.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(100.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(50.0, 30.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PDRFsingle() -> gf.Component:
    """RF photo-diode."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -200.0], [200.0, -200.0], [200.0, 200.0], [0.0, 200.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PDRFsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (199.0, 130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (199.0, -130.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((200.0 + 200.0) / 2, (130.0 + -130.0) / 2),
        orientation=0,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 60.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (199.0, 0.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PDRFtwin() -> gf.Component:
    """Twin RF photo-diode."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -50.0], [400.0, -50.0], [400.0, 50.0], [0.0, 50.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PDRFtwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (70.0, -49.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (330.0, -49.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((70.0 + 330.0) / 2, (-50.0 + -50.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (200.0, -49.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PMTOE1700(L_P: float = 200.0) -> gf.Component:
    """Thermal-optical phase modulator in E1700.

    Args:
      L_P: length of phase shifter (min: 162.0, max: 2000.0, um).
    """

    if L_P < 162.0 or L_P > 2000.0:
        raise ValueError("L_P must be between 162.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 40.0], [L_P + 248.0, 40.0], [L_P + 248.0, -30.0], [0.0, -30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_PMTOE1700:L_P={L_P}"

    ysize = c.ysize
    c.add_label(
        text=f"L_P:{L_P}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(117.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(L_P + 131.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_P + 248.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PMTOE200(L_P: float = 100.0) -> gf.Component:
    """Thermal-optical phase modulator in E200.

    Args:
      L_P: length of phase shifter (min: 10.0, max: 2000.0, um).
    """

    if L_P < 10.0 or L_P > 2000.0:
        raise ValueError("L_P must be between 10.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 40.0], [L_P + 44.0, 40.0], [L_P + 44.0, -30.0], [0.0, -30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_PMTOE200:L_P={L_P}"

    ysize = c.ysize
    c.add_label(
        text=f"L_P:{L_P}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(L_P + 29.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(L_P + 44.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PMTOE600(L_P: float = 200.0) -> gf.Component:
    """Thermal-optical phase modulator in E600.

    Args:
      L_P: length of phase shifter (min: 162.0, max: 2000.0, um).
    """

    if L_P < 162.0 or L_P > 2000.0:
        raise ValueError("L_P must be between 162.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 40.0], [L_P + 248.0, 40.0], [L_P + 248.0, -30.0], [0.0, -30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_PMTOE600:L_P={L_P}"

    ysize = c.ysize
    c.add_label(
        text=f"L_P:{L_P}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(117.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(L_P + 131.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(L_P + 248.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PolConverter45() -> gf.Component:
    """Polarization converter for 45 degrees."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 40.0], [718.0, 40.0], [718.0, -40.0], [0.0, -40.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PolConverter45"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(718.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PolConverter90() -> gf.Component:
    """Polarization converter for 90 degrees."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -40.0], [994.0, -40.0], [994.0, 40.0], [0.0, 40.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PolConverter90"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(994.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_PolSplitter() -> gf.Component:
    """Polarization splitter."""

    c = gf.Component()
    c.add_polygon(
        [[1930.0, 50.0], [1930.0, -50.0], [0.0, -50.0], [0.0, 50.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_PolSplitter"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(997.0, 50.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(1373.0, 50.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e3",
        width=16.0,
        cross_section="DC",
        center=(997.0, -50.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="e4",
        width=16.0,
        cross_section="DC",
        center=(1373.0, -50.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(1930.0, 2.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -2.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(1930.0, -2.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_R50GSG() -> gf.Component:
    """50 ohm resistor between GSG tracks."""

    c = gf.Component()
    c.add_polygon(
        [[100.0, 190.0], [100.0, -190.0], [0.0, -190.0], [0.0, 190.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_R50GSG"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, 130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (99.0, 130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, -130.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 100.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (99.0, -130.0)
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((0.0 + 100.0) / 2, (130.0 + 130.0) / 2),
        orientation=180,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 60.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (1.0, 0.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((0.0 + 100.0) / 2, (130.0 + 130.0) / 2),
        orientation=0,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(2, 60.0), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (99.0, 0.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_SGDBRTO(
    N_B: int = 10.0, W_S: float = 1550.0, Z_0: float = 50.0, Z_1: float = 25.0
) -> gf.Component:
    """Thermal-optical sampled grating (max. grating length Z0*(NB-1)+Z1 = 800um)

    Args:
      N_B: Number of Bursts (min: 2.0, max: 32.0, int).
      W_S: Wavelength (min: 1500.0, max: 1580.0, nm).
      Z_0: Burst length (min: 25.0, max: 400.0, um).
      Z_1: Gratings length (min: 1.52, max: 400.0, um).
    """

    if N_B < 2.0 or N_B > 32.0:
        raise ValueError("N_B must be between 2.0 and 32.0 int")

    if W_S < 1500.0 or W_S > 1580.0:
        raise ValueError("W_S must be between 1500.0 and 1580.0 nm")

    if Z_0 < 25.0 or Z_0 > 400.0:
        raise ValueError("Z_0 must be between 25.0 and 400.0 um")

    if Z_1 < 1.52 or Z_1 > 400.0:
        raise ValueError("Z_1 must be between 1.52 and 400.0 um")

    c = gf.Component()
    c.add_polygon(
        [
            [0.0, 40.0],
            [N_B * Z_0 + 100.0, 40.0],
            [N_B * Z_0 + 100.0, -30.0],
            [0.0, -30.0],
        ],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_SGDBRTO:N_B={N_B},W_S={W_S},Z_0={Z_0},Z_1={Z_1}"

    ysize = c.ysize
    c.add_label(
        text=f"N_B:{N_B}", position=(xc, yc - 0 / 5 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"W_S:{W_S}", position=(xc, yc - 1 / 5 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"Z_0:{Z_0}", position=(xc, yc - 2 / 5 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text=f"Z_1:{Z_1}", position=(xc, yc - 3 / 5 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 4 / 5 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(N_B * Z_0 + 85.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(N_B * Z_0 + 100.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_SOA(L_S: float = 100.0) -> gf.Component:
    """Optical gain section with butt joints connecting to E1700 waveguides.

    Args:
      L_S: length of SOA (min: 20.0, max: 2000.0, um).
    """

    if L_S < 20.0 or L_S > 2000.0:
        raise ValueError("L_S must be between 20.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_S + 400.0, 60.0], [L_S + 400.0, -60.0], [0.0, -60.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_SOA:L_S={L_S}"

    ysize = c.ysize
    c.add_label(
        text=f"L_S:{L_S}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_S / 2 + 200.0, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(L_S + 400.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_S / 2 + 200.0, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_SOAsection(L_S: float = 100.0) -> gf.Component:
    """Optical gain section connecting to active waveguides.

    Args:
      L_S: length of SOA (min: 24.0, max: 2000.0, um).
    """

    if L_S < 24.0 or L_S > 2000.0:
        raise ValueError("L_S must be between 24.0 and 2000.0 um")

    c = gf.Component()
    c.add_polygon(
        [[0.0, 60.0], [L_S, 60.0], [L_S, -60.0], [0.0, -60.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_SOAsection:L_S={L_S}"

    ysize = c.ysize
    c.add_label(
        text=f"L_S:{L_S}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label
    )

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="n1",
        width=16.0,
        cross_section="DC",
        center=(L_S / 2, -60.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L_S, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="p1",
        width=16.0,
        cross_section="DC",
        center=(L_S / 2, 60.0),
        orientation=90,
        port_type="electrical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_SSCLATE1700(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Spot-size converter (SSC) to 10 um connecting to E1700 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflection (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[0.0, -57.0], [1200.0, -57.0], [1200.0, 57.0], [0.0, 57.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_SSCLATE1700:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(1200.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_SSCLATE200(R: float = 0.0001, n: float = 1.0) -> gf.Component:
    """Spot-size converter (SSC) to 10 um connecting to E200 waveguides. Placement can be under an angle for lowering reflections.

    Args:
      R: Reflection (min: 0.0001, max: 1.0, ).
      n: Refraction (min: 1.0, max: 10.0, ).
    """

    if R < 0.0001 or R > 1.0:
        raise ValueError("R must be between 0.0001 and 1.0 ")

    if n < 1.0 or n > 10.0:
        raise ValueError("n must be between 1.0 and 10.0 ")

    c = gf.Component()
    c.add_polygon(
        [[0.0, -57.0], [1200.0, -57.0], [1200.0, 57.0], [0.0, 57.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = f"HHI_SSCLATE200:R={R},n={n}"

    ysize = c.ysize
    c.add_label(text=f"R:{R}", position=(xc, yc - 0 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(text=f"n:{n}", position=(xc, yc - 1 / 3 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 2 / 3 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=10.0,
        cross_section="FACET",
        center=(1200.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_TOBiasSection(L: float = 100.0) -> gf.Component:
    """Thermal-optical phase modulator on active waveguide.

    Args:
      L: Heater length (min: 20.0, max: 800.0, um).
    """

    if L < 20.0 or L > 800.0:
        raise ValueError("L must be between 20.0 and 800.0 um")

    c = gf.Component()
    c.add_polygon(
        [[L + 44.0, -30.0], [L + 44.0, 40.0], [0.0, 40.0], [0.0, -30.0]],
        layer=layer_bbox,
    )
    xc = c.x
    yc = c.y
    name = f"HHI_TOBiasSection:L={L}"

    ysize = c.ysize
    c.add_label(text=f"L:{L}", position=(xc, yc - 0 / 2 / 2 * ysize), layer=layer_label)

    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 1 / 2 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(L + 29.0, 40.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(L + 44.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTGSGsingle() -> gf.Component:
    """Crossing between an active waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [374.0, 25.0], [374.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTGSGsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(374.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTGSGtwin() -> gf.Component:
    """Crossing between an twin active waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [374.0, 25.0], [374.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTGSGtwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(374.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(374.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTGSsingle() -> gf.Component:
    """Crossing between an active waveguide and a GSG RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [340.0, 25.0], [340.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTGSsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(340.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTGStwin() -> gf.Component:
    """Crossing between an twin active waveguide and a GSG RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, 25.0], [340.0, 25.0], [340.0, -25.0], [0.0, -25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTGStwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(340.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(340.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTsingle() -> gf.Component:
    """Crossing between an active waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(30.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxACTtwin() -> gf.Component:
    """Crossing between an twin active waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxACTtwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="ACT",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="ACT",
        center=(30.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.0,
        cross_section="ACT",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.0,
        cross_section="ACT",
        center=(30.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700GSGsingle() -> gf.Component:
    """Crossing between an E1700 waveguide and a GSG RF-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [374.0, -25.0], [374.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700GSGsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(374.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700GSGtwin() -> gf.Component:
    """Crossing between twin E1700 waveguide and a GSG RF-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [374.0, -25.0], [374.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700GSGtwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(374.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(374.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700GSsingle() -> gf.Component:
    """Crossing between an E1700 waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [340.0, -25.0], [340.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700GSsingle"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(340.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700GStwin() -> gf.Component:
    """Crossing between twin E1700 waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [340.0, -25.0], [340.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700GStwin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(340.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(340.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700single() -> gf.Component:
    """Crossing between an E1700 waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700single"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(30.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE1700twin() -> gf.Component:
    """Crossing between twin E1700 waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE1700twin"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.3,
        cross_section="E1700",
        center=(0.0, 6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(0.0, -6.5),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o3",
        width=2.3,
        cross_section="E1700",
        center=(30.0, 6.5),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="o4",
        width=2.3,
        cross_section="E1700",
        center=(30.0, -6.5),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE200() -> gf.Component:
    """Crossing between an E200 waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE200"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(30.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE200GS() -> gf.Component:
    """Crossing between an E200 waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [340.0, -25.0], [340.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE200GS"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(340.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE200GSG() -> gf.Component:
    """Crossing between an E200 waveguide and a GSG RF-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [374.0, -25.0], [374.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE200GSG"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.0,
        cross_section="E200",
        center=(374.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE600() -> gf.Component:
    """Crossing between an E600 waveguide and a DC-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [30.0, -25.0], [30.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE600"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="e1",
        width=16.0,
        cross_section="DC",
        center=(15.0, 25.0),
        orientation=90,
        port_type="electrical",
    )
    c.add_port(
        name="e2",
        width=16.0,
        cross_section="DC",
        center=(15.0, -25.0),
        orientation=-90,
        port_type="electrical",
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(30.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE600GS() -> gf.Component:
    """Crossing between an E600 waveguide and a Ground Signal RF track."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [340.0, -25.0], [340.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE600GS"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (83.0, -24.0)
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(340.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gs" + "s1"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (25.0 + 25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, 24.0)
    c.add_port(
        name="gs" + "s2"[1:],
        width=24,
        cross_section="GS",
        center=((83.0 + 257.0) / 2, (-25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(150.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (257.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGMETxE600GSG() -> gf.Component:
    """Crossing between an E600 waveguide and a GSG RF-line."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -25.0], [374.0, -25.0], [374.0, 25.0], [0.0, 25.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGMETxE600GSG"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (57.0, -24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, 24.0)
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(100.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (317.0, -24.0)
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(374.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    c.add_port(
        name="gsg" + "s1"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, 24.0)
    c.add_port(
        name="gsg" + "s2"[1:],
        width=60.0,
        cross_section="GSG",
        center=((57.0 + 57.0) / 2, (25.0 + -25.0) / 2),
        orientation=-90,
        port_type="electrical",
    )
    if add_abstract_pins:
        pin = c << gf.c.rectangle(
            size=(60.0, 2), centered=True, layer="BB_PIN", port_type=None
        )
        pin.center = (187.0, -24.0)
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGTE200E1700() -> gf.Component:
    """Transition element from an E200 to an E1700 waveguide."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -20.0], [205.0, -20.0], [205.0, 20.0], [0.0, 20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGTE200E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(205.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGTE200E600() -> gf.Component:
    """Transition element from an E200 to an E600 waveguide."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -20.0], [205.0, -20.0], [205.0, 20.0], [0.0, 20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGTE200E600"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.0,
        cross_section="E200",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.1,
        cross_section="E600",
        center=(205.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


@gf.cell
def HHI_WGTE600E1700() -> gf.Component:
    """Transition element from an E600 to an E1700 waveguide."""

    c = gf.Component()
    c.add_polygon(
        [[0.0, -20.0], [205.0, -20.0], [205.0, 20.0], [0.0, 20.0]], layer=layer_bbox
    )
    xc = c.x
    yc = c.y
    name = "HHI_WGTE600E1700"

    ysize = c.ysize
    c.add_label(
        text="pdk_version: 6.21.0",
        position=(xc, yc - 0 / 1 / 2 * ysize),
        layer=layer_label,
    )
    c.add_port(
        name="o1",
        width=2.1,
        cross_section="E600",
        center=(0.0, 0.0),
        orientation=180,
        port_type="optical",
    )
    c.add_port(
        name="o2",
        width=2.3,
        cross_section="E1700",
        center=(205.0, 0.0),
        orientation=0,
        port_type="optical",
    )
    text = c << text_function(text=name)
    text.x = xc
    text.y = yc

    c.name = name
    if layer_pin:
        add_pins(c, layer=layer_pin)
    return c


if __name__ == "__main__":
    from hhi import PDK

    PDK.activate()

    c = HHI_EOPMTWSingleDD()
    c.show()
