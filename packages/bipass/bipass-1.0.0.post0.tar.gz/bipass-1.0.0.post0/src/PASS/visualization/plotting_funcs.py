# The Clear BSD License
#
# Copyright (c) 2024 Julia Burton
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted (subject to the limitations in the disclaimer
# below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import datetime
from datetime import timedelta

import astropy.units as u
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.time import Time
from matplotlib import animation
from matplotlib.pyplot import gca
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm

from ..config.config import PassConfig
from ..general_framework.general_classes import LatitudeRange, SimpleLocation, Times
from ..solar_production.solar_elevation_angle import get_solar_elevation
from ..solar_production.solar_production_classes import SolarArray
from .style import document_nw as doc


def plot_contour_phase_space(
    fig: mpl.figure.Figure,
    ax: mpl.axes.Axes,
    x: np.ndarray,
    y: np.ndarray,
    c: np.ndarray,
    color_bar_label,
    ticks,
    levels=500,
    fontsize=12,
    cmap="RdGy_r",
) -> None:
    """Function to make a contour plot with colorbar

    Args:
        fig (mpl.figure.Figure): Figure to plot into
        ax (mpl.axes.Axes): axes to plot the contour into
        x (np.ndarray): X-axis
        y (np.ndarray): Y-axis
        c (np.ndarray): color value size = (len(x), len(y))
        cmap (str, optional): Choice of the colormap. Defaults to "RdGy_r".
    """

    ticks = np.arange(0, 25, 4)

    # Make contour plot
    im = ax.contourf(x, y, c, cmap=cmap, levels=levels)

    # Make colorbar
    a = gca()
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="10%", pad=0.05)
    cax.cla()
    cbar = fig.colorbar(
        im,
        cax=cax,
        orientation="vertical",
        ticks=ticks,
    )
    cbar.set_label(color_bar_label, fontsize=fontsize)


def plot_contour(
    fig: mpl.figure.Figure,
    ax: mpl.axes.Axes,
    x: np.ndarray,
    y: np.ndarray,
    c: np.ndarray,
    color_bar_label,
    levels=500,
    fontsize=12,
    cmap="RdGy_r",
) -> None:
    """Function to make a contour plot with colorbar

    Args:
        fig (mpl.figure.Figure): Figure to plot into
        ax (mpl.axes.Axes): axes to plot the contour into
        x (np.ndarray): X-axis
        y (np.ndarray): Y-axis
        c (np.ndarray): color value size = (len(x), len(y))
        cmap (str, optional): Choice of the colormap. Defaults to "RdGy_r".
    """
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="10%", pad=0.05)

    im = ax.contourf(x, y, c, cmap=cmap, levels=levels)
    cax.cla()
    cbar = fig.colorbar(
        im,
        cax=cax,
        orientation="vertical",
        # ticks=ticks,
    )
    cbar.set_label(color_bar_label, fontsize=fontsize)
    cbar.set_ticks(np.linspace(np.min(c), np.max(c), 7, endpoint=True))
    ax.set_yticks(np.linspace(np.min(y), np.max(y), 10, endpoint=True))


def plot_min_cap(fig, ax, cap_day, cap_lat, colors, color_bar_label, fontsize):
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="10%", pad=0.05)
    cax.cla()
    im = ax.scatter(
        cap_day,
        cap_lat,
        c=colors,
    )
    ax.set_title("Minimum Battery Capacitance")
    ax.set_xlabel("Date Range in UTC")
    ax.set_ylabel("Latitudes in Deg")
    cbar = fig.colorbar(
        im,
        cax=cax,
        orientation="vertical",
        # ticks=ticks,
    )
    cbar.set_label(color_bar_label, fontsize=fontsize)


def plot_power_produciton_many_lat_one_day(
    config: PassConfig,
    dates: Times,
    solar_array: SolarArray,
    ax: mpl.axes.Axes,
    fig: mpl.figure.Figure,
    increment,
    label,
) -> None:
    """Function to make a contour plot of the power production

    Args:
        coords (LatitudeRange): Coordinates of the detector
        dates (DateRange): Dates to do the calculation for
        solar_array (SolarArray): Solar Array or solar skirt
        ax (mpl.axes.Axes): axes to plot into
        fig (mpl.figure.Figure): figure to plot into
    """

    coords = config.latitude_range

    # Define arrays for the solar elevation angles
    solar_elevation_angles = np.zeros((len(coords), len(dates)), dtype=u.Quantity)
    power_production = np.zeros((len(coords), len(dates)), dtype=float)

    # Calculate the solar elevation angle over the whole input range
    for lat_count in tqdm((range(len(coords.latitude_range)))):
        lat_coords = coords.latitude_range[lat_count]
        limb = lat_coords.get_limb()
        solar_elevation_angles = get_solar_elevation(dates.times, lat_coords)

        # Calculate the power production
        power_production[lat_count] = solar_array.get_power_production(solar_elevation_angles, limb) * increment / 1000

    # Create plot
    ax.set_xlabel("Date in UTC")
    ax.set_ylabel("Latitude in Degrees")
    plot_contour(
        fig,
        ax,
        dates.date_range,
        coords.latitudes.to("deg").value,
        power_production,
        label,
    )
    y_ticks = np.arange(
        config.latitude_range.latitude_start.to_value(),
        config.latitude_range.latitude_end.to_value() + 1,
        10,
    )

    ax.set_yticks(y_ticks, minor=False)

    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")


def stored_power_overview(
    day_range,
    lat,
    stored_power,
    power_consumption,
    power_production,
    solar_elevation_angle,
    lunar_elevation_angle,
):
    fig, ax = doc.figure(1, 1)
    ax.plot(
        day_range.date_range,
        stored_power.to(u.W * u.h).value,
        "b",
        label="Stored Power",
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Stored Power in Wh")
    ax.set_title(f"Stored Power for {day_range.start_time} to {day_range.end_time}")
    ax2 = ax.twinx()
    ax2.plot(
        day_range.date_range,
        (power_consumption / day_range.frequency).to(u.W).value,
        "r",
        label="Power Consumption",
    )
    ax2.plot(
        day_range.date_range,
        (power_production / day_range.frequency).to(u.W).value,
        "g",
        label="Power Production",
    )
    ax2.set_ylabel("Power in Watts")
    ax3 = ax.twinx()
    ax3.spines.right.set_position(("axes", 1.1))
    ax3.plot(
        day_range.date_range,
        solar_elevation_angle.to(u.deg).value,
        "r",
        linestyle="--",
        label="Solar Elevation Angle",
    )
    ax3.plot(
        day_range.date_range,
        lunar_elevation_angle.to(u.deg).value,
        "g",
        linestyle="--",
        label="Lunar Elevation Angle",
    )
    ax3.axhline(lat.get_limb().to(u.deg).value, color="k", linestyle="--", label="Limb")
    ax3.set_ylabel("Elevation Angle in deg")
    fig.legend(loc="upper left")
