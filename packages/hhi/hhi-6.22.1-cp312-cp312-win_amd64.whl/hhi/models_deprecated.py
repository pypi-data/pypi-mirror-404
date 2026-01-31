from __future__ import annotations

from functools import partial

import gplugins.sax.models as sm

nm = 1e-3
straight = partial(sm.straight, wl0=1.55, neff=2.4, ng=4.2)
bend_euler_sc = bend_euler = partial(sm.bend, loss_dB_cm=0.03)

################
# MMIs
################


def HHI_MMI1x2E1700():
    return sm.mmi1x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


def HHI_MMI1x2E600():
    return sm.mmi1x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


def HHI_MMI1x2ACT():
    return sm.mmi1x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


def HHI_MMI2x2ACT():
    return sm.mmi2x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


def HHI_MMI2x2E1700():
    return sm.mmi2x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


def HHI_MMI2x2E600():
    return sm.mmi2x2(wl0=1.55, fwhm=0.2, loss_dB=1.0)


coupler = sm.coupler

models = dict(
    straight=straight,
    bend_euler=bend_euler,
    bend_euler_sc=bend_euler_sc,
    HHI_MMI1x2E1700=HHI_MMI1x2E1700,
    HHI_MMI1x2E600=HHI_MMI1x2E600,
    HHI_MMI1x2ACT=HHI_MMI1x2ACT,
    HHI_MMI2x2ACT=HHI_MMI2x2ACT,
    HHI_MMI2x2E1700=HHI_MMI2x2E1700,
    HHI_MMI2x2E600=HHI_MMI2x2E600,
    coupler=coupler,
)
