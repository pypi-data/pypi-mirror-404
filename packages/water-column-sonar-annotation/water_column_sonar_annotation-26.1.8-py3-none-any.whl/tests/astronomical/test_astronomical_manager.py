import numpy as np

from water_column_sonar_annotation.astronomical import AstronomicalManager


#######################################################
def setup_module():
    print("setup")


def teardown_module():
    print("teardown")


def test_get_solar_azimuth():
    astronomical_manager = AstronomicalManager()
    # https://www.suncalc.org/#/39.9812,-105.2495,13/2026.01.26/11:52/1/3
    azimuth_noon = astronomical_manager.get_solar_azimuth(
        iso_time="2026-01-26T19:00:00Z",  # noon
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert np.isclose(azimuth_noon, 31.38)  # 15)

    azimuth_sunset = astronomical_manager.get_solar_azimuth(
        iso_time="2026-01-26T00:00:00Z",  # sunset
        latitude=39.9674884,
        longitude=-105.2532602,
    )
    assert np.isclose(azimuth_sunset, 1.25)  # 27)


def test_get_solar_azimuth_boulder_2pm():
    # 2026-01-29 @2pm is UTC: "2026-01-29T21:02:23Z"
    astronomical_manager = AstronomicalManager()
    # https://www.suncalc.org/#/39.9812,-105.2495,13/2026.01.26/11:52/1/3
    azimuth_noon = astronomical_manager.get_solar_azimuth(
        iso_time="2026-01-29T21:02:23Z",  # 2pm
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert np.isclose(azimuth_noon, 27.01)


### PHASE OF DAY ###
# { 'dawn': 1, 'day': 2, 'dusk': 3, 'night': 4 }
def test_phase_of_day_at_noon():
    astronomical_manager = AstronomicalManager()
    phase = astronomical_manager.phase_of_day(
        iso_time="2026-01-27T19:00:00Z",  # noon
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase == 2


def test_phase_of_day_at_midnight():
    astronomical_manager = AstronomicalManager()
    phase = astronomical_manager.phase_of_day(
        iso_time="2026-01-28T07:00:00Z",
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase == 4


def test_phase_of_day_before_sunset():
    astronomical_manager = AstronomicalManager()
    phase = astronomical_manager.phase_of_day(
        # sunset is at 5:13pm on jan 27th, per https://psl.noaa.gov/boulder/boulder.sunset.html
        iso_time="2026-01-28T00:09:00Z",  # sunset @ 5:13pm, nautical sunset @6:16pm
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase == 2  # day


def test_phase_of_day_after_sunset():
    astronomical_manager = AstronomicalManager()
    phase = astronomical_manager.phase_of_day(
        # sunset is at 5:13pm on jan 27th, per https://psl.noaa.gov/boulder/boulder.sunset.html
        iso_time="2026-01-28T00:10:00Z",  # sunset @ 5:13pm, nautical sunset @6:16pm
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase == 3  # dusk


def test_phase_of_day_before_nautical_sunset():
    astronomical_manager = AstronomicalManager()
    # an hour'ish later is nautical sunset
    phase_before_nautical_sunset = astronomical_manager.phase_of_day(
        iso_time="2026-01-28T01:15:00Z",  # sunset @5:13pm, nautical sunset @6:16pm
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase_before_nautical_sunset == 3  # dusk


def test_phase_of_day_after_nautical_sunset():
    astronomical_manager = AstronomicalManager()
    phase_after_nautical_sunset = astronomical_manager.phase_of_day(
        iso_time="2026-01-28T01:17:00Z",  # sunset @5:13pm, nautical sunset @6:16pm
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase_after_nautical_sunset == 4  # night


def test_phase_of_day_before_sunrise():
    astronomical_manager = AstronomicalManager()
    phase_at_sunrise = astronomical_manager.phase_of_day(
        iso_time="2026-01-27T14:13:00Z",  # sunrise @7:13am, nautical sunrise @6:12am
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase_at_sunrise == 1  # dusk


def test_phase_of_day_after_sunrise():
    astronomical_manager = AstronomicalManager()
    phase_at_sunrise = astronomical_manager.phase_of_day(
        iso_time="2026-01-27T14:20:00Z",  # sunrise @7:13am, nautical sunrise @6:12am
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase_at_sunrise == 2  # day


def test_phase_of_day_before_nautical_sunrise():
    astronomical_manager = AstronomicalManager()
    # about an hour before is nautical sunrise
    phase_before_nautical_sunrise = astronomical_manager.phase_of_day(
        iso_time="2026-01-27T13:12:00Z",  # sunrise @7:13am, nautical sunrise @6:12am
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase_before_nautical_sunrise == 4  # night


def test_phase_of_day_after_nautical_sunrise():
    astronomical_manager = AstronomicalManager()
    phase = astronomical_manager.phase_of_day(
        iso_time="2026-01-27T14:13:00Z",  # sunrise @7:13am, nautical sunrise @6:12am
        latitude=39.9674884,  # Boulder
        longitude=-105.2532602,
    )
    assert phase == 1
