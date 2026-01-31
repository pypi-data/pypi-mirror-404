from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pooch
from dateutil import tz
from shapely import Point
from timezonefinder import TimezoneFinder

"""
Gets the distance between a point and a coastline
https://www.kaggle.com/code/notcostheta/shortest-distance-to-a-coastline
https://www.naturalearthdata.com/downloads/50m-physical-vectors/50m-coastline/

Well known text map: https://wktmap.com/
Calculate distance map: https://www.calcmaps.com/map-distance/
"""

HB1906_DATA = pooch.create(
    path=pooch.os_cache("water-column-sonar-annotation"),
    base_url="https://github.com/CI-CMG/water-column-sonar-annotation/releases/download/v26.1.0/",
    retry_if_failed=1,
    registry={
        # "HB201906_BOTTOMS.zip": "sha256:20609581493ea3326c1084b6868e02aafbb6c0eae871d946f30b8b5f0e7ba059",
        # "HB201906_EVR.zip": "sha256:ceed912a25301be8f1b8f91e134d0ca4cff717f52b6623a58677832fd60c2990",
        #
        # "ne_50m_coastline.shp": "sha256:797d675af9613f80b51ab6049fa32e589974d7a97c6497ca56772965f179ed26",
        # "ne_50m_coastline.shx": "sha256:0ff1792f2d16b58246d074215edd9d12fa280880ecaad61a91b9382fee854065",
        #
        "ne_10m_coastline.shp": "sha256:459a4a97c09db19aadf5244026612de9d43748be27f83a360242b99f7fabb3c1",
        "ne_10m_coastline.shx": "sha256:f873afee7f56779ce52253f740ec251c2f12244aea911dc40f0a85d75de8d5f2",
    },
)


def fetch_raw_files():
    HB1906_DATA.fetch(fname="ne_10m_coastline.shp", progressbar=True)
    file_name = HB1906_DATA.fetch(fname="ne_10m_coastline.shx", progressbar=True)
    return Path(file_name).parent


def data_path():
    return {
        "DATA_PATH": fetch_raw_files(),
    }


class GeospatialManager:
    #######################################################
    def __init__(
        self,
    ):
        self.DECIMAL_PRECISION = 6
        self.crs = "EPSG:4326"  # "EPSG:3857"  # "EPSG:4326"

    def check_distance_from_coastline(
        self,  # -30.410156 51.508742)
        latitude: float = 51.508742,  # 42.682435,
        longitude: float = -30.410156,  # -68.741455,
        shapefile_path: str = data_path()["DATA_PATH"],
    ) -> np.float32 | None:
        """
        # Note this takes about 14 seconds each, very slow!!!
        """
        try:
            # requires the shape file too
            geometry_one = gpd.read_file(f"{shapefile_path}/ne_10m_coastline.shp")
            geometry_one = geometry_one.set_crs(self.crs)
            geometry_two = Point([longitude, latitude])
            gdf_p = gpd.GeoDataFrame(geometry=[geometry_two], crs=self.crs)
            gdf_l = geometry_one
            gdf_p = gdf_p.to_crs(gdf_p.estimate_utm_crs())
            # print(gdf_p.to_string())
            gdf_l = gdf_l.to_crs(gdf_p.crs)
            # TODO: index 1399 has inf values, investigate
            # RuntimeWarning: invalid value encountered in distance
            #   return lib.distance(a, b, **kwargs)
            all_distances = [
                gdf_p.geometry.distance(gdf_l.get_geometry(0)[i])[0]
                for i in range(len(gdf_l.get_geometry(0)))
                if gdf_l.get_geometry(0)[i].is_valid
            ]
            return np.round(np.min(all_distances), 0)
        except Exception as e:
            print(f"Could not process the distance: {e}")

    @staticmethod
    def get_local_time(
        # self,
        iso_time: str = "2026-01-26T20:35:00Z",
        latitude: float = 51.508742,
        longitude: float = -30.410156,
    ) -> str:
        # https://www.geeksforgeeks.org/python/get-time-zone-of-a-given-location-using-python/
        obj = TimezoneFinder()
        calculated_timezone = obj.timezone_at(lng=longitude, lat=latitude)
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz(calculated_timezone)
        utc = datetime.fromisoformat(iso_time)
        utc = utc.replace(tzinfo=from_zone)
        local_time = utc.astimezone(to_zone)
        return local_time.isoformat()  # [:19]

    def get_local_hour_of_day(
        self,
        iso_time: str = "2026-01-26T20:35:00Z",
        latitude: float = 51.508742,
        longitude: float = -30.410156,
    ) -> int:
        obj = TimezoneFinder()
        calculated_timezone = obj.timezone_at(lng=longitude, lat=latitude)
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz(calculated_timezone)
        utc = datetime.fromisoformat(iso_time)
        utc = utc.replace(tzinfo=from_zone)
        local_time = utc.astimezone(to_zone)
        return local_time.hour

    def get_month_of_year(
        self,
        iso_time: str = "2026-01-26T20:35:00Z",
        latitude: float = 51.508742,
        longitude: float = -30.410156,
    ):
        local_time = self.get_local_time(
            iso_time=iso_time,
            latitude=latitude,
            longitude=longitude,
        )
        return int(local_time[5:7])


#
# if __name__ == "__main__":
#     geospatial_manager = GeospatialManager()
#     # x = geospatial_manager.check_distance_from_coastline()
#     x = geospatial_manager.get_local_time(
#         iso_time="2026-01-26T20:35:00Z",
#         latitude=51.508742,
#         longitude=-30.410156,
#     )
#     print(x)
