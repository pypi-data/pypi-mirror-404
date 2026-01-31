import numpy as np
import pandas as pd
import pvlib

from water_column_sonar_annotation.geospatial import GeospatialManager


class AstronomicalManager:
    #######################################################
    def __init__(
        self,
    ):
        self.DECIMAL_PRECISION = 6
        # https://github.com/CI-CMG/water-column-sonar-annotation/issues/6
        self.SUNRISE_DEGREES = 0.0
        self.CIVIL_TWILIGHT_DEGREES = -6.0
        self.NAUTICAL_TWILIGHT_DEGREES = -12.0  # Requested metric to calculate
        self.ASTRONOMICAL_TWILIGHT_DEGREES = -18.0

    @staticmethod
    def get_solar_azimuth(
        iso_time: str = "2026-01-26T00:06:00Z",
        latitude: float = 39.9674884,  # boulder gps coordinates
        longitude: float = -105.2532602,
    ) -> float:
        """
        Good reference for calculating: https://www.suncalc.org/#/39.9812,-105.2495,13/2026.01.26/11:52/1/3
        utc time now: '2026-01-25T18:42:00Z' # 11:43am
            7:14 am↑ (sunrise)
                (Timestamp('2026-01-25 18:42:00+0000', tz='UTC'), Timestamp('2026-01-25 14:15:07.145030400+0000', tz='UTC'))
            5:13 pm↑ (sunset)
                (Timestamp('2026-01-25 18:42:00+0000', tz='UTC'), Timestamp('2026-01-26 00:10:51.244243200+0000', tz='UTC'))
            solar altitude should be: 31.26°, azimuth should be: 174.01°
        """
        solar_position = pvlib.solarposition.get_solarposition(
            time=pd.DatetimeIndex([iso_time]),
            latitude=latitude,
            longitude=longitude,
        )
        # 'elevation' is analogous to 'altitude' in suncalc
        elevation = solar_position.elevation.iloc[0]
        ### The altitude aka elevation is the angle between horizon and the center of the sun including refraction ###
        return np.round(elevation, 2)

    def phase_of_day(
        self,
        iso_time: str,
        latitude: float,
        longitude: float,
    ) -> int:
        """
        Returns whether the time/gps references a Nautical Daylight time
        Going to need to verify the az is correctly computed
        { 'night': 4, 'dawn': 1, 'day': 2, 'dusk': 3 }
        """
        # categories = {"night": 4, "dawn": 1, "day": 2, "dusk": 3}
        solar_azimuth = self.get_solar_azimuth(iso_time, latitude, longitude)
        geospatial_manager = GeospatialManager()
        local_hour = geospatial_manager.get_local_hour_of_day(
            iso_time=iso_time,
            latitude=latitude,
            longitude=longitude,
        )
        if solar_azimuth < self.NAUTICAL_TWILIGHT_DEGREES:
            return 4  # night
        if solar_azimuth >= 0.0:
            return 2  # day
        if local_hour < 12:
            return 1  # dawn
        return 3  # dusk

    # def get_moon_phase(self):
    #     # TODO: add method for getting the moon phase
    #     pass

    # TODO: calculate moonrise and moonset


# if __name__ == "__main__":
#     astronomical_manager = AstronomicalManager()
#     azimuth = astronomical_manager.get_solar_azimuth()
#     print(azimuth)
