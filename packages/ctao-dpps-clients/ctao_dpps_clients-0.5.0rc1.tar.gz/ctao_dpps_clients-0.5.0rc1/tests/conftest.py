import logging
import os
import re
import subprocess as sp
from datetime import datetime
from pathlib import Path
from secrets import token_hex

import pytest
import requests
from rucio.client.scopeclient import ScopeClient

LOG = logging.getLogger(__name__)


def pytest_configure():
    # gfal is overly verbose on info (global default), reduce a bit
    logging.getLogger("gfal2").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def test_user():
    return "root"


@pytest.fixture(scope="session")
def user_cert():
    return os.getenv("RUCIO_CFG_CLIENT_CERT", "/opt/rucio/etc/usercert.pem")


@pytest.fixture(scope="session")
def user_key():
    return os.getenv("RUCIO_CFG_CLIENT_KEY", "/opt/rucio/etc/userkey.pem")


@pytest.fixture(scope="session")
def auth_proxy(user_key, user_cert):
    """Auth proxy needed for accessing RSEs"""
    ret = sp.run(
        [
            "voms-proxy-init",
            "-valid",
            "9999:00",
            "-cert",
            user_cert,
            "-key",
            user_key,
        ],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    m = re.match(r"Created proxy in (.*)\.", ret.stdout.strip())
    if m is None:
        raise ValueError(f"Failed to parse output of voms-proxy-init: {ret.stdout!r}")
    return Path(m.group(1))


@pytest.fixture(scope="session")
def test_scope(test_user):
    """To avoid name conflicts and old state, use a unique scope for the tests"""
    # length of scope is limited to 25 characters
    random_hash = token_hex(2)
    date_str = f"{datetime.now():%Y%m%d_%H%M%S}"
    scope = f"t_{date_str}_{random_hash}"

    sc = ScopeClient()
    sc.add_scope(test_user, scope)
    return scope


USER_CERT = os.getenv("RUCIO_CFG_CLIENT_CERT", "/tmp/usercert.pem")
USER_KEY = os.getenv("RUCIO_CFG_CLIENT_KEY", "/tmp/userkey.pem")


@pytest.fixture(scope="session")
def _dirac_proxy():
    sp.run(["dirac-proxy-init", "-g", "dpps_group"], check=True)


@pytest.fixture(scope="session")
def _init_dirac(_dirac_proxy):
    """Import and init DIRAC, needs to be run first for anything using DIRAC"""
    import DIRAC

    DIRAC.initialize()


def _download_file(url, destination):
    """Download a file from a URL and save it to the specified destination."""
    if destination.exists():
        LOG.info("Skipping download, output exists %s", destination)
        return

    LOG.info("Downloading %s to %s", url, destination)
    response = requests.get(url, stream=True)
    response.raise_for_status()

    Path(destination).parent.mkdir(exist_ok=True, parents=True)
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    LOG.info("Successfully downloaded %s", url)


@pytest.fixture(scope="session")
def test_data_dir():
    p = Path("test_data")
    p.mkdir(exist_ok=True)
    return p.absolute()


@pytest.fixture(scope="session")
def gamma_dl0_path(test_data_dir):
    url = "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/ctapipe-test-data/v1.1.0/gamma_prod5.simtel.zst"
    dl0_path = test_data_dir / "gamma_prod5.simtel.zst"
    _download_file(url, dl0_path)
    return dl0_path


@pytest.fixture(scope="session")
def gamma_prod6_path(test_data_dir):
    name = "gamma_prod6_preliminary.simtel.zst"
    url = f"https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/ctapipe-test-data/v1.1.0/{name}"
    dl0_path = test_data_dir / name
    _download_file(url, dl0_path)
    return dl0_path


@pytest.fixture(scope="session")
def simulated_dl0_pedestal_events(test_data_dir, test_scope):
    url = "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/calibpipe-test-data/camera-calibration-test-data/pedestals_LST_dark.simtel.gz"
    dl0_path = test_data_dir / "pedestals_LST_dark.simtel.gz"
    _download_file(url, dl0_path)
    dl0_lfn = f"/ctao.dpps.test/{test_scope}/{dl0_path.name}"
    _dirac_upload(dl0_path, dl0_lfn)
    return {"lfn": dl0_lfn, "path": dl0_path}


@pytest.fixture(scope="session")
def simulated_dl0_flatfield_events(test_data_dir, test_scope):
    url = "https://minio-cta.zeuthen.desy.de/dpps-testdata-public/data/calibpipe-test-data/camera-calibration-test-data/flasher_LST_dark.simtel.gz"
    dl0_path = test_data_dir / "flasher_LST_dark.simtel.gz"
    _download_file(url, dl0_path)
    dl0_lfn = f"/ctao.dpps.test/{test_scope}/{dl0_path.name}"
    _dirac_upload(dl0_path, dl0_lfn)
    return {"lfn": dl0_lfn, "path": dl0_path}


def _dirac_upload(path, lfn, rse="STORAGE-1"):
    from DIRAC.DataManagementSystem.Client.DataManager import DataManager

    LOG.info("Uploading %s using dirac using lfn: %s", path, lfn)
    dm = DataManager()
    result = dm.putAndRegister(lfn, str(path), rse)
    LOG.debug("putFileAndRegister result for %s: %s", gamma_dl0_path, result)
    msg = f"Uploading file {lfn} failed: {result}"
    assert result["OK"], msg
    assert result["Value"]["Failed"] == {}, msg
    LOG.info("Successfully uploaded %s", lfn)


@pytest.fixture(scope="session")
def gamma_dl0_lfn(gamma_dl0_path, _init_dirac, test_scope):
    dl0_lfn = f"/ctao.dpps.test/{test_scope}/gamma_prod5.simtel.zst"
    _dirac_upload(gamma_dl0_path, dl0_lfn)
    return dl0_lfn
