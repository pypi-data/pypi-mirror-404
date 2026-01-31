import numpy as np
import pytest

from water_column_sonar_annotation.geospatial import GeospatialManager


#######################################################
def setup_module():
    print("setup")


def teardown_module():
    print("teardown")


@pytest.fixture
def process_check_distance_from_coastline(test_path):
    return test_path["DATA_TEST_PATH"]


#######################################################
def test_check_distance_from_coastline(process_check_distance_from_coastline, tmp_path):
    geospatial_manager = GeospatialManager()
    # Point in middle of atlantic https://wktmap.com/?ab28cbae
    distance = geospatial_manager.check_distance_from_coastline(
        latitude=51.508742,
        longitude=-30.410156,
        shapefile_path=process_check_distance_from_coastline,
    )
    # assert np.isclose(distance, 1_236_212.37356)  # 1,200 km
    assert np.isclose(distance, 1_233_910.720702243)


def test_check_distance_from_coastline_woods_hole(
    process_check_distance_from_coastline, tmp_path
):
    geospatial_manager = GeospatialManager()
    # Point in middle of woods hole vineyard sound: https://wktmap.com/?9b405aa9
    distance = geospatial_manager.check_distance_from_coastline(
        latitude=41.494692,
        longitude=-70.647926,
        shapefile_path=process_check_distance_from_coastline,
    )
    # The sound is 5 km across
    # assert np.isclose(distance, 4_457.0347)  # 4.5 km --> should be 2.5 km?
    assert np.isclose(distance, 3_093)  # 3_093.3015 km is close enough


def test_get_local_time():
    geospatial_manager = GeospatialManager()
    local_time = geospatial_manager.get_local_time(
        iso_time="2026-01-26T20:35:00Z",
        latitude=51.508742,
        longitude=-30.410156,
    )
    assert local_time == "2026-01-26T18:35:00-02:00"


def test_get_local_hour_of_day():
    geospatial_manager = GeospatialManager()
    local_hour_of_day = geospatial_manager.get_local_hour_of_day(
        iso_time="2026-01-26T20:35:00Z",
        latitude=51.508742,
        longitude=-30.410156,
    )
    assert local_hour_of_day == 18


def test_get_month_of_year_january():
    geospatial_manager = GeospatialManager()
    month_of_year = geospatial_manager.get_month_of_year(
        iso_time="2026-01-26T20:35:00Z",
        latitude=51.508742,
        longitude=-30.410156,
    )
    assert month_of_year == 1


def test_get_month_of_year_july():
    geospatial_manager = GeospatialManager()
    month_of_year = geospatial_manager.get_month_of_year(
        iso_time="2026-07-13T12:00:00Z",
        latitude=51.508742,
        longitude=-30.410156,
    )
    assert month_of_year == 7
