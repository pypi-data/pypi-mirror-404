from pathlib import Path

import pooch
import pytest

HERE = Path(__file__).parent.absolute()
TEST_DATA_FOLDER = HERE / "test_resources"

HB1906_DATA = pooch.create(
    path=pooch.os_cache("water-column-sonar-annotation"),
    base_url="https://github.com/CI-CMG/water-column-sonar-annotation/releases/download/v26.1.0/",
    retry_if_failed=1,
    registry={
        "HB201906_BOTTOMS.zip": "sha256:20609581493ea3326c1084b6868e02aafbb6c0eae871d946f30b8b5f0e7ba059",
        "HB201906_EVR.zip": "sha256:ceed912a25301be8f1b8f91e134d0ca4cff717f52b6623a58677832fd60c2990",
        #
        # "ne_50m_coastline.shp": "sha256:797d675af9613f80b51ab6049fa32e589974d7a97c6497ca56772965f179ed26",
        # "ne_50m_coastline.shx": "sha256:0ff1792f2d16b58246d074215edd9d12fa280880ecaad61a91b9382fee854065",
        #
        "ne_10m_coastline.shp": "sha256:459a4a97c09db19aadf5244026612de9d43748be27f83a360242b99f7fabb3c1",
        "ne_10m_coastline.shx": "sha256:f873afee7f56779ce52253f740ec251c2f12244aea911dc40f0a85d75de8d5f2",
    },
)


def fetch_raw_files():
    HB1906_DATA.fetch(fname="HB201906_BOTTOMS.zip", progressbar=True)
    HB1906_DATA.fetch(fname="HB201906_EVR.zip", progressbar=True)

    # HB1906_DATA.fetch(fname="ne_50m_coastline.shp", progressbar=True)
    # HB1906_DATA.fetch(fname="ne_50m_coastline.shx", progressbar=True)

    HB1906_DATA.fetch(fname="ne_10m_coastline.shp", progressbar=True)
    HB1906_DATA.fetch(fname="ne_10m_coastline.shx", progressbar=True)

    file_name = HB1906_DATA.fetch(fname="HB201906_EVR.zip", progressbar=True)

    """
    water-column-sonar-annotation user$ ls /Users/user/Library/Caches/water-column-sonar-annotation
    HB201906_BOTTOMS.zip	HB201906_EVR.zip	ne_10m_coastline.shp	ne_10m_coastline.shx
    """
    return Path(file_name).parent


@pytest.fixture(scope="session")
def test_path():
    return {
        "DATA_TEST_PATH": fetch_raw_files(),
    }


# """
# Folder locations in mac and windows:
#
# Windows
# C:\Users\<user>\AppData\Local\echopype\Cache\2024.12.23.10.10
#
# MacOS
# /Users//Library/Caches/echopype/2024.12.23.10.10
# """
