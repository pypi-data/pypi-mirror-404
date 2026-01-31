from json import dumps

"""
Format for export to parquet and bulk ingest into neo4j:
"""
# TODO:
#  [1] write the records to a pandas dataframe
#  [2] write df to parquet and tag as github resource


class ParquetRecordManager:
    def __init__(
        self,
        classification,
        point_count,
        geometry,
        time_start,
        time_end,
        depth_min,
        depth_max,
        month,
        # altitude,
        # latitude: float,
        # longitude: float,
        # local_time,
        # distance_from_coastline,
        # solar_altitude,
        # is_daytime,
        filename,
        region_id,
        geometry_hash,  # sha256 hash
        ship: str = "Henry_B._Bigelow",
        cruise: str = "HB1906",
        instrument: str = "EK60",
    ):
        print("__init__ called")
        self.classification: str = classification
        self.point_count: int = point_count
        # self.geometry: str = geometry
        ### geospatial ###
        self.time_start: str = time_start
        self.time_end: str = time_end
        self.depth_min: float = depth_min
        self.depth_max: float = depth_max
        self.month: int = month
        # self.altitude: float = altitude
        # self.latitude: float = latitude
        # self.longitude: float = longitude
        # self.local_time: str = local_time
        # self.distance_from_coastline: float = distance_from_coastline
        # ### astronomical ###
        # self.solar_altitude: float = solar_altitude
        # self.is_daytime: bool = is_daytime
        ### provenance ###
        self.filename: str = filename
        self.region_id: str = region_id
        self.geometry_hash: str = geometry_hash
        self.ship: str = ship
        self.cruise: str = cruise
        self.instrument: str = instrument

    # def __enter__(self):
    #     print("__enter__ called")
    #     return self

    # def __exit__(self, *a):
    #     print("__exit__ called")

    def to_dict(
        self,
    ):
        try:
            return self.__dict__
        except Exception as parquet_record_exception:
            print(f"Problem with parquet record: {parquet_record_exception}")

    def to_json(
        self,
    ):
        try:
            return dumps(self.__dict__)
        except Exception as parquet_record_exception:
            print(f"Problem with parquet record: {parquet_record_exception}")
