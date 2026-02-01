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


# def animate_contour(
#     data_1,
#     data_2,
#     data_3,
#     date_range,
#     ax,
#     fig,
#     animation_name: str = "power_production_contour.gif",
# ):
#     divider = make_axes_locatable(ax)
#     cax = divider.append_axes("right", size="5%", pad=0.05)

#     def animate(i):
#         ax.clear()
#         ax.set_xlabel("Hour of Day")
#         ax.set_ylabel("Latitude in Deg")
#         ax.set_title(
#             f"Optimal tilt angle {date_range[i].strftime('%Y-%m-%d')} at -60.00 longitude"
#         )
#         im = ax.contourf(
#             data_1,
#             data_2,
#             data_3[i].T,
#             100,
#             cmap="RdGy_r",
#             vmin=-90,
#             vmax=90,
#         )

#         cax.cla()
#         cbar = fig.colorbar(im, cax=cax, orientation="vertical")
#         cbar.set_label("Power in Watts")
#         plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
#         plt.tight_layout()

#     anim = animation.FuncAnimation(
#         fig, animate, frames=len(date_range), interval=100, blit=False
#     )

#     anim.save(animation_name, writer="imagemagick", dpi=150)


# def animate_plot(
#     lat,
#     long,
#     solar_elevation,
#     time_period,
#     date_range,
#     animation_name: str = "solar_elevation_plot_animation.gif",
# ):
#     fig = plt.figure()
#     ax = fig.add_subplot(111)
#     divider = make_axes_locatable(ax)
#     cax = divider.append_axes("right", size="5%", pad=0.05)

#     def animate(i):
#         ax.clear()
#         ax.set_xlabel("Hour of Day")
#         ax.set_ylabel("Solar Elevation")
#         ax.set_title(
#             f"Solar Elevation {date_range[i].strftime('%Y-%m-%d')} at {lat} latitude & {long} longitude"
#         )
#         im = ax.plot(
#             time_period,
#             solar_elevation[i].T,
#         )

#     anim = animation.FuncAnimation(
#         fig, animate, frames=len(date_range), interval=100, blit=False
#     )

#     anim.save(animation_name, writer="imagemagick", dpi=150)


# def animate_contour_solar_elavation(
#     lat, long, date_range, get_refraction, get_solar_elevation
# ):
#     time_period = np.arange(0, 24, 1)

#     solar_elevation = np.zeros((len(date_range), len(time_period), len(lat)))

#     for i in range(len(date_range)):
#         for j in range(len(time_period)):
#             date_time = date_range[i] + timedelta(hours=1) * time_period[j]
#             refraction_correction = get_refraction(lat, long, date_time, elevation=0)

#             solar_elevation[i, j] = get_solar_elevation(
#                 lat, long, date_time, refraction_correction
#             )

#     animate_contour(lat, solar_elevation, time_period, date_range)


# def animate_plot_solar_elevation(date_range, get_refraction, get_solar_elevation):
#     lat = -44.6943
#     long = 169.1417

#     time_period = np.arange(0, 24, 1)
#     solar_elevation = np.zeros((len(date_range), len(time_period)))

#     for i in range(len(date_range)):
#         for j in range(len(time_period)):
#             date_time = date_range[i] + timedelta(hours=1) * time_period[j]
#             refraction_correction = get_refraction(lat, long, date_time, elevation=0)

#             solar_elevation[i, j] = get_solar_elevation(
#                 lat, long, date_time, refraction_correction
#             )

#     animate_plot(lat, long, solar_elevation, time_period, date_range)


# def plot_sol_el_for_day(date, get_refraction, get_solar_elevation):
#     lat = -44.6943
#     long = 169.1417

#     time_period = np.arange(0, 24, 1)
#     solar_elevation = np.zeros((len(date), len(time_period)))

#     for j in range(len(time_period)):
#         date_time = date + timedelta(hours=1) * time_period[j]
#         refraction_correction = get_refraction(lat, long, date_time, elevation=0)

#         solar_elevation[j] = get_solar_elevation(
#             lat, long, date_time, refraction_correction
#         )

#     fig = plt.figure()
#     ax = fig.add_subplot(111)
#     ax.set_title(f"Solar Elevation for {date} at {lat} lat & {long} long")
#     ax.set_xlabel("Time in Hours")
#     ax.set_ylabel("Solar Elevation")
#     ax.plot(time_period, solar_elevation)
#     plt.show()


# def plot_soc_over_time(date_range: DateRange, state_of_charge, ax):
#     ax.set_title("State of Charge")
#     ax.set_xlabel("Date in UTC")
#     ax.set_ylabel("State of Charge %")
#     ax.plot(date_range.date_range, state_of_charge)
#     plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")


# def plot_net_power_production_over_time(
#     date_range: DateRange, net_power_production, ax
# ):
#     ax.set_title("Net Power Production")
#     ax.set_xlabel("Date in UTC")
#     ax.set_ylabel("Net Power Production in Watts")
#     ax.plot(date_range.date_range, net_power_production)
#     plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")


# def plot_energy_vs_latitude(
#     config: PassConfig,
#     date_range: Times,
#     ax,
#     *args,
#     **kwargs,
# ):

#     lat_range = config.latitude_range
#     increment = date_range.frequency

#     total_energy_production = np.zeros(len(lat_range), dtype=u.Quantity)
#     total_energy_consumption = np.zeros(len(lat_range), dtype=u.Quantity)
#     net_power_production = np.zeros(len(date_range), dtype=u.Quantity)
#     net_power_consumption = np.zeros(len(date_range), dtype=u.Quantity)

#     for i, coordinates in enumerate(lat_range.latitude_range):

#         for count, time in enumerate(date_range.times):
#             (
#                 power_in_Wh,
#                 energy_production,
#                 energy_consumption,
#             ) = generate_battery_bank_capacitance(config, time, coordinates, increment)

#             net_power_production[count] = energy_production
#             net_power_consumption[count] = energy_consumption

#         total_energy_production[i] = (
#             (np.sum(net_power_production) / increment).to(u.W).value
#         )
#         total_energy_consumption[i] = (
#             (np.sum(net_power_consumption) / increment).to(u.W).value
#         )

#     print(lat_range.latitudes, total_energy_production, total_energy_consumption)

#     ax.plot(
#         lat_range.latitudes,
#         total_energy_production,
#         **kwargs,
#     )

#     # ax.plot(
#     #     lat_range.latitudes,
#     #     total_energy_consumption.to(u.W).value,
#     #     color="red",
#     #     label="Power Consumption",
#     # )
#     ax.set_xlabel("Latitude in Degrees")
#     ax.set_ylabel("Energy in Watt-hours")

# def plot_many_lats_one_day_plot(
#     coords: LatitudeRange,
#     dates: DateRange,
#     solar_array: SolarArray,
#     ax,
#     ax2,
#     fig,
# ):
#     solar_elevation_angles = np.zeros((len(coords), len(dates)))
#     astropy_solar_elevation_angles = np.zeros((len(coords), len(dates)))
#     power_production = np.zeros((len(coords), len(dates)))

#     # Calculate the solar elevation angle over the whole input range
#     for lat_count, lat_coords in enumerate(coords.latitude_range):
#         for time_count, date in enumerate(dates.date_range):
#             solar_elevation_angles[lat_count, time_count] = get_solar_elevation(
#                 date, lat_coords
#             )

#         ax.plot(
#             dates.date_range,
#             solar_elevation_angles[lat_count],
#             label=f"Lat = {lat_coords.latitude}",
#         )
#         ax2.plot(
#             dates.date_range,
#             astropy_solar_elevation_angles[lat_count],
#             label=f"Lat = {lat_coords.latitude}",
#         )

#         print(
#             f"Solar Els: {solar_elevation_angles[lat_count]} for Lat: {lat_coords.latitude}"
#         )

#         # Calculate the power production
#         power_production[lat_count] = solar_array.get_power_production(
#             solar_elevation_angles[lat_count]
#         )
