import os
from pathlib import Path

import astropy.coordinates as coord
import astropy.units as u
import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.time import Time
from tqdm import tqdm

from ..config.load_config import load_config


@click.command()
@click.argument("config_file")
def trajectory_stats(config_file: str) -> None:
    """Generates histograms of the lat, long, and altitude distributions of the trajectory files.

    Args:
        config_file (str): _description_
    """

    print("Loading config file.")
    config = load_config(config_file)
    status = config.status

    plot_path = Path(config.multiple_traj["trajectory_path"])
    names = ["datetime", "lat", "long", "alt", "Ewind", "Nwind"]

    traj_list = os.listdir(plot_path)
    traj_list = np.sort(traj_list)

    total_lat = []
    total_long = []
    total_alt = []
    print("Loading trajectories.")
    for i in tqdm(range(len(traj_list))):
        sim_traj = pd.read_csv(f"{plot_path}/{traj_list[i]}", header=9, names=names)
        locations = coord.EarthLocation(
            lat=sim_traj["lat"] * u.deg,
            lon=sim_traj["long"] * u.deg,
            height=sim_traj["alt"] * u.m,
        )

        total_lat = np.concatenate([total_lat, locations.lat.to_value()])
        total_long = np.concatenate([total_long, locations.lon.to_value()])
        total_alt = np.concatenate([total_alt, locations.height.to_value()])
    print("Generating histograms.")
    fig = plt.figure(figsize=(12, 4))
    ax = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)
    bins = 50

    ax.set_title("Latitudinal Distribution")
    ax2.set_title("Longitudinal Distribution")
    ax3.set_title("Altitude Distribution")

    avg_lat = np.mean(total_lat)
    std_lat = np.std(total_lat)

    avg_long = np.mean(total_long)
    std_long = np.std(total_long)

    avg_alt = np.mean(total_alt)
    std_alt = np.std(total_alt)

    ax.set_xlabel("Degrees")
    ax2.set_xlabel("Degrees")
    ax3.set_xlabel("Meters")
    ax.hist(total_lat, bins=bins, label=f"AVG: {avg_lat:.3f}\nSTD: {std_lat:.3f}")
    ax2.hist(total_long, bins=bins, label=f"AVG: {avg_long:.3f}\nSTD: {std_long:.3f}")
    ax3.hist(total_alt, bins=bins, label=f"AVG: {avg_alt:.3f}\nSTD: {std_alt:.3f}")
    ax.legend()
    ax2.legend()
    ax3.legend()
    plt.tight_layout()

    print("Trajectory stats figure created.")

    plt.savefig("./plots/pass_trajectory_stats.pdf")


if __name__ == "__main__":
    trajectory_stats()
