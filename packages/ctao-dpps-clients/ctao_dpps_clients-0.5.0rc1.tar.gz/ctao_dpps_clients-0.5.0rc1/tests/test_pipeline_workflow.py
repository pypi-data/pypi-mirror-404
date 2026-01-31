import logging
import os
from pathlib import Path

import pytest
import tables
import yaml
from wms.tests.utils import wait_for_status

LOG = logging.getLogger(__name__)

DATAPIPE_TAG = os.environ["DATAPIPE_VERSION"]
DATAPIPE_IMAGE = f"harbor.cta-observatory.org/dpps/datapipe:{DATAPIPE_TAG}"
CWL_BASE = Path(os.getenv("DPPS_CWL_BASE", "/opt/cwl"))
CALIBPIPE_TAG = os.environ["CALIBPIPE_VERSION"]


@pytest.mark.verifies_usecase("DPPS-UC-170-1.3")
@pytest.mark.usefixtures("_init_dirac")
def test_run_datapipe_apptainer(tmp_path):
    """Simple test that we can run a datapipe tool from the image on cvmfs"""
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job

    dirac = Dirac()

    job = Job()
    job.setExecutable(
        "apptainer",
        arguments=f"run /cvmfs/ctao.dpps.test/{DATAPIPE_IMAGE} ctapipe-info --all",
    )
    job.setName("test_apptainer")
    job.setDestination("CTAO.CI.de")

    res = dirac.submitJob(job)
    assert res["OK"]
    job_id = res["Value"]

    wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        job_output_dir=tmp_path,
    )


@pytest.mark.verifies_usecase("DPPS-UC-000-1")
@pytest.mark.usefixtures("_init_dirac")
def test_datapipe_dl0_to_dl1(tmp_path, test_scope, gamma_dl0_lfn):
    from CTADIRAC.Interfaces.API.CWLJob import CWLJob
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.WorkloadManagementSystem.Client.JobMonitoringClient import (
        JobMonitoringClient,
    )

    # pre-conditions 1, 2, 4, 5 and 7 are implicitly checked. If they are not fulfilled,
    # this test will fail during job submission or execution

    # pre-condition 3: an input file is available in BDMS
    # fixture has put the gamma test file from minio into BDMS
    dl0_lfn = gamma_dl0_lfn

    # Precondition 6: CWL is available
    cwl = CWL_BASE / "datapipe-cwl" / DATAPIPE_TAG / "process_dl0_dl1.cwl"

    # UC Step 1, workflow job submission
    inputs_path = tmp_path / "inputs.yaml"
    config_path = tmp_path / "config.yaml"
    config = {
        "DataWriter": {
            "Contact": {
                "name": "Maximilian Linhoff",
            }
        }
    }

    output_lfn = f"/ctao.dpps.test/{test_scope}/test.dl1.h5"
    inputs = {
        "processing_config": {"class": "File", "path": str(config_path)},
        "dl0": {"class": "File", "path": f"lfn://{dl0_lfn}"},
        "dl1_filename": f"lfn://{output_lfn}",
    }

    with config_path.open("w") as f:
        yaml.dump(config, f)

    with inputs_path.open("w") as f:
        yaml.dump(inputs, f)

    job = CWLJob(cwl, inputs_path, Path("/cvmfs/ctao.dpps.test"), output_se="STORAGE-1")
    job.setName("test_datapipe_cwl")
    job.setDestination("CTAO.CI.de")

    # job does conversion to cwl in submit, so we cannot use dirac.submitJob(job)
    res = job.submit()
    assert res["OK"], res["Message"]
    job_id = res["Value"]

    # Step 2 is happening on the WMS server and CE and cannot directly
    # be validated here.

    # Step 3: WMS provides information about the workflow life-cycle
    # the wait_for_status function receives job status updates and returns
    # once the job finishes successfully. It raises an error in case of timeout
    # or job failure.
    output_sandbox = tmp_path / "output_sandbox"
    dirac = Dirac()
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        job_output_dir=output_sandbox,
    )
    # Success condition: the job has terminated successfully
    assert result["Value"][job_id]["Status"] == "Done"

    # Success condition: Job output files haven been ingested into BDMS and are available for download
    destination = tmp_path / "download"
    destination.mkdir()
    dirac = Dirac()
    result = dirac.getFile(output_lfn, destDir=str(destination))
    assert result["OK"], f"Downloading generated DL1 file failed: {result}"

    # check that the output file contains DL1 parameters
    output_path = destination / Path(output_lfn).name
    with tables.open_file(output_path) as f:
        assert "/dl1/event/telescope/parameters" in f.root

    # Success condition: job logs are available
    # job logs are stored in the output sandbox,
    # which is unpacked into ``output_sandbox`` by wait_for_status
    assert (output_sandbox / "ctapipe-process_dl0_dl1.provenance.log").is_file()
    assert (output_sandbox / "std.out").is_file()

    # Success condition: job execution time is recorded
    jmc = JobMonitoringClient()
    result = jmc.getJobSummary(job_id)
    assert result["OK"]
    job_summary = result["Value"]
    assert (
        job_summary["EndExecTime"] - job_summary["StartExecTime"]
    ).total_seconds() > 0


@pytest.mark.verifies_usecase("DPPS-UC-000-1")
@pytest.mark.usefixtures("_init_dirac")
def test_calibpipe_generate_macobac(tmp_path, test_scope):
    import astropy.units as u
    from astropy.table import QTable
    from astropy.units.cds import ppm
    from CTADIRAC.Interfaces.API.CWLJob import CWLJob
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.WorkloadManagementSystem.Client.JobMonitoringClient import (
        JobMonitoringClient,
    )

    # pre-conditions 1, 2, 4, 5 and 7 are implicitly checked. If they are not fulfilled,
    # this test will fail during job submission or execution
    # pre-condition 3: an input file is not needed

    # Precondition 6: CWL is available
    cwl = (
        CWL_BASE
        / "calibpipe-cwl"
        / CALIBPIPE_TAG
        / "atmosphere/uc-120-1.2-calculate-macobac.cwl"
    )

    # UC Step 1, workflow job submission
    calculate_macobac_path = tmp_path / "calculate_macobac.yaml"
    calculate_macobac = {
        "CalculateMACOBAC": {
            "CO2DataHandler": {
                "dataset": "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/monthly/monthly_in_situ_co2_mlo.csv",
                "timeout": 600,
                "data_path": f"{tmp_path}/co2_data/",
            },
        }
    }

    config_path = tmp_path / "config.yaml"
    config = {
        "configuration": {"class": "File", "path": str(calculate_macobac_path)},
    }

    with calculate_macobac_path.open("w") as f:
        yaml.dump(calculate_macobac, f)

    with config_path.open("w") as f:
        yaml.dump(config, f)

    # Submit the job
    dirac = Dirac()
    job = CWLJob(cwl, config_path, Path("/cvmfs/ctao.dpps.test"), output_se="STORAGE-1")
    job.setName("test_calibpipe_cwl")
    job.setDestination("CTAO.CI.de")

    res = job.submit()
    assert res["OK"], res["Message"]
    job_id = res["Value"]

    # Step 2 is happening on the WMS server and CE and cannot directly
    # be validated here.

    # Step 3: WMS provides information about the workflow life-cycle
    # the wait_for_status function receives job status updates and returns
    # once the job finishes successfully. It raises an error in case of timeout
    # or job failure.
    output_sandbox = tmp_path / "output_sandbox"
    result = wait_for_status(
        dirac,
        job_id=job_id,
        status="Done",
        error_on={"Failed"},
        job_output_dir=output_sandbox,
    )
    # Success condition: the job has terminated successfully
    assert result["Value"][job_id]["Status"] == "Done"

    path_macobac = output_sandbox / "macobac.ecsv"
    #  Success condition: Job output does not need to be ingested into BDMS as it will be used as input for other jobs so we download it from the sandbox
    assert (path_macobac).is_file()

    # Validate macobac.ecsv contents
    u.add_enabled_units([ppm])
    table = QTable.read(path_macobac, format="ascii.ecsv")
    assert len(table) == 1, "Table must have exactly one row"
    assert "co2_concentration" in table.colnames, "Missing 'co2_concentration' column"
    assert "estimation_date" in table.colnames, "Missing 'estimation_date' column"
    assert table["co2_concentration"].unit == ppm, (
        "Unit of 'co2_concentration' must be ppm"
    )

    # Success condition: job logs are available
    # job logs are stored in the output sandbox,
    # which is unpacked into ``output_sandbox`` by wait_for_status
    assert (output_sandbox / "std.out").is_file()

    # Success condition: job execution time is recorded
    jmc = JobMonitoringClient()
    result = jmc.getJobSummary(job_id)
    assert result["OK"]
    job_summary = result["Value"]
    assert (
        job_summary["EndExecTime"] - job_summary["StartExecTime"]
    ).total_seconds() > 0
