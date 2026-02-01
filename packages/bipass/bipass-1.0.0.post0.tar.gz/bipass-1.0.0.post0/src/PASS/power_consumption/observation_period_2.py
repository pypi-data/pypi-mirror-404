# import numpy as np
# from astropy import units as u
# from astropy.coordinates import AltAz
# from astropy.time import Time

# from .sun_moon_cuts import SunMoonAltitudeFoVCuts


# def get_observation_times(
#     source: ToOEvent,
#     detector: BalloonInterpolation,
#     schedule_period: Time,
# ) -> list[ObservationPeriod]:
#     """Calculate time and location when a source would be in the detectable range

#     Args:
#         source_location (ToOEvent): Source to be tracked
#         detector (BalloonInterpolation): Detector to be used
#         schedule_period (Time): time period to calculate observations for

#     Returns:
#         list[ObservationPeriod]: list of possible observations
#     """

#     # Make list of times to check location of the source for
#     start_time = schedule_period[0]
#     obs_duration = schedule_period[1] - start_time
#     times = start_time + np.arange(0, obs_duration.to("hour").value, (0.1 / 6)) * u.hour

#     # Track the source through the sky during observation period
#     det_frames = AltAz(obstime=times, location=detector.traj_prediction(times))
#     tracked_source_loc = source.coordinates.transform_to(det_frames)

#     # Calculate times when source would be visible
#     sun_moon_fov_cuts = SunMoonAltitudeFoVCuts()
#     visibility_cuts = sun_moon_fov_cuts(det_frames, tracked_source_loc.alt.deg, times)
#     visibility_cuts = visibility_cuts
#     visibility_cuts = np.append(np.array([0]), visibility_cuts)
#     visibility_cuts = np.append(visibility_cuts, np.array([0, 0]))

#     # Extract times when source moves in and out of detectable region
#     start = np.flatnonzero(np.diff(visibility_cuts) == 1)
#     end = np.flatnonzero(np.diff(visibility_cuts) == -1)

#     if len(start) == 0:
#         return []
#     if end[-1] == len(times):
#         end[-1] -= 1

#     # Write result into observation period object
#     observation_periods = [
#         ObservationPeriod(
#             start_time=times[start[i]],
#             start_loc=tracked_source_loc[start[i]],
#             end_time=times[end[i]],
#             end_loc=tracked_source_loc[end[i]],
#             move_time=start_time,
#             pointing_dir=get_detector_pointing(tracked_source_loc, start[i], end[i]),
#         )
#         for i in range(len(start))
#     ]

#     return observation_periods


# def get_detector_pointing(tracked_source_loc, start, end):
#     """Determine where to point the detector.

#     Center source trajectory in fov and maximize observation time
#     """
#     halffov_az = 6.4 * np.pi / 180.0
#     point_alt = -9.0 * np.pi / 180.0
#     az_st = tracked_source_loc[start].az.rad
#     if end > 0:
#         az_en = tracked_source_loc[end - 1].az.rad
#     else:
#         az_en = tracked_source_loc[end].az.rad
#     az_diff = az_en - az_st
#     if (halffov_az * 2.0 - np.abs(az_diff)) > 0:
#         point_az = tracked_source_loc[start].az.rad + az_diff / 2.0
#     else:
#         # point_az = tracked_source_loc[st].az.rad+np.sign(az_diff)*halffov_az
#         point_az = tracked_source_loc[start].az.rad - halffov_az
#     return AltAz(az=point_az * u.rad, alt=point_alt * u.rad)


# def get_source_trajectories(
#     source_location: ToOEvent,
#     detector: BalloonInterpolation,
#     schedule_period: Time,
# ) -> tuple[Time, AltAz, list[bool]]:
#     start_time = schedule_period[0]
#     observation_duration = schedule_period[1] - start_time
#     time_steps = (
#         start_time
#         + np.arange(0, observation_duration.to("hour").value, (1 / 6)) * u.hour
#     )

#     sun_moon_fov_cuts = SunMoonAltitudeFoVCuts()

#     det_frames = AltAz(
#         obstime=time_steps, location=detector.traj_prediction(time_steps)
#     )
#     tracked_source_loc = source_location.coordinates.transform_to(det_frames)
#     visibility_cuts = sun_moon_fov_cuts(
#         det_frames, tracked_source_loc.alt.deg, time_steps
#     )
#     visibility_cuts = visibility_cuts

#     return time_steps, tracked_source_loc, visibility_cuts
