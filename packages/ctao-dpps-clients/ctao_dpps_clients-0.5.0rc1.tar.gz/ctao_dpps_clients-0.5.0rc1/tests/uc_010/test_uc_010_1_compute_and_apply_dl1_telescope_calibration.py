import json
import logging
import os
import subprocess as sp
from pathlib import Path

import pytest
import tables
import yaml
from CTADIRAC.Interfaces.API.CWLJob import CWLJob
from DIRAC.Interfaces.API.Dirac import Dirac
from wms.tests.utils import wait_for_status

LOG = logging.getLogger("test_UC-010-1")
CWL_BASE = Path(os.getenv("DPPS_CWL_BASE", "/opt/cwl"))
DATAPIPE_TAG = os.environ["DATAPIPE_VERSION"]
CALIBPIPE_TAG = os.environ["CALIBPIPE_VERSION"]


def run_cwl(workflow_path, inputs_path=None, cwd=None):
    """Run cwltool on a workflow using subprocess."""
    command = ["cwltool", "--debug", "--no-container", str(workflow_path)]
    if inputs_path is not None:
        command.append(str(inputs_path))
    return sp.run(command, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, cwd=cwd)


calibpipe_configs = {}
calibpipe_configs["process_flatfield"] = """
DataWriter:
  write_dl1_images: true # Required parameter to write flatfield images to DL1
  write_dl1_parameters: false
  write_dl2: false
  transform_image: true
  transform_peak_time: true
EventTypeFilter:
  allowed_types: [FLATFIELD]
CameraCalibrator:
  image_extractor_type:
    - ['type', '*', 'LocalPeakWindowSum']
LocalPeakWindowSum:
  window_shift:
    - ['type', '*', 5]
  window_width:
    - ['type', '*', 12]
  apply_integration_correction:
    - ['type', '*', false]
SimTelEventSource:
  skip_calibration_events: false
"""

calibpipe_configs["process_pedestal"] = """
DataWriter:
  write_dl1_images: true
  write_dl1_parameters: false
  write_dl2: false
  transform_image: true
  transform_peak_time: true
EventTypeFilter:
  allowed_types: [PEDESTAL, SKY_PEDESTAL]
CameraCalibrator:
  image_extractor_type:
    - ['type', '*', 'FixedWindowSum']
FixedWindowSum:
  window_shift:
    - ['type', '*', 6]
  window_width:
    - ['type', '*', 12]
  peak_index:
    - ['type', '*', 18]
  apply_integration_correction:
    - ['type', '*', false]
SimTelEventSource:
  skip_calibration_events: false
"""

calibpipe_configs["pixelstats_pedestal"] = """
PixelStatisticsCalculatorTool:
  input_column_name: image
PixelStatisticsCalculator:
  stats_aggregator_type:
    - ["type", "*", "SigmaClippingAggregator"]
  faulty_pixels_fraction: 0.1
  outlier_detector_list:
    - name: StdOutlierDetector
      apply_to: median
      config:
        std_range_factors: [-10, 10]
    - name: StdOutlierDetector
      apply_to: std
      config:
        std_range_factors: [-10, 10]
SigmaClippingAggregator:
  chunking_type: SizeChunking
  max_sigma: 4
  iterations: 5
SizeChunking:
  chunk_size: 50
  chunk_shift: 25
"""

calibpipe_configs["pixelstats_flatfield_image"] = """
PixelStatisticsCalculatorTool:
  input_column_name: image
PixelStatisticsCalculator:
  stats_aggregator_type:
    - ["type", "*", "SigmaClippingAggregator"]
  faulty_pixels_fraction: 0.1
  outlier_detector_list:
    - name: MedianOutlierDetector
      apply_to: median
      config:
        median_range_factors: [-0.9, 8]
    - name: StdOutlierDetector
      apply_to: std
      config:
        std_range_factors: [-10, 10]
SigmaClippingAggregator:
  chunking_type: SizeChunking
  max_sigma: 4
  iterations: 5
SizeChunking:
  chunk_size: 50
  chunk_shift: 25
"""

calibpipe_configs["pixelstats_flatfield_time"] = """
PixelStatisticsCalculatorTool:
  input_column_name: peak_time
HDF5Merger:
  append: True
  merge_strategy: "events-single-ob"
PixelStatisticsCalculator:
  stats_aggregator_type:
    - ["type", "*", "PlainAggregator"]
  faulty_pixels_fraction: 0.1
  outlier_detector_list:
    - name: RangeOutlierDetector
      apply_to: median
      config:
        validity_range: [2, 38]
PlainAggregator:
  chunking_type: SizeChunking
SizeChunking:
  chunk_size: 50
  chunk_shift: 25
"""

calibpipe_configs["camera_calibration"] = """
CameraCalibratorTool:
  timestamp_tolerance: 1.0 second
  faulty_pixels_fraction: 0.1
  squared_excess_noise_factor: 1.222
  window_width: 12
"""

datapipe_config = """
SimTelEventSource:
  skip_calibration_events: false
  allowed_tels: [1]
"""

calibpipe_cwl_dir = CWL_BASE / "calibpipe-cwl" / CALIBPIPE_TAG
datapipe_cwl_dir = CWL_BASE / "datapipe-cwl" / DATAPIPE_TAG
calibpipe_workflow = (
    calibpipe_cwl_dir / "telescope/camera/uc-120-2.20-perform-camera-calibration.cwl"
)
datapipe_workflow = datapipe_cwl_dir / "process_dl0_dl1.cwl"

cvmfs_repo = Path("/cvmfs/ctao.dpps.test")


@pytest.mark.parametrize(
    "use_wms",
    [
        pytest.param(False, id="cwltool"),
        pytest.param(True, id="wms"),
    ],
)
@pytest.mark.usefixtures("_init_dirac")
@pytest.mark.verifies_usecase("DPPS-UC-010-1")
def test_compute_and_apply_dl1_telescope_calibration(
    use_wms,
    tmp_path,
    simulated_dl0_pedestal_events,
    simulated_dl0_flatfield_events,
    gamma_prod6_path,
):
    calibpipe_dir = tmp_path / "calibpipe_job"
    calibpipe_dir.mkdir()

    # Prepare configuration files for execution of CalibPipe UC-120-2.20
    config_paths = {}
    for name, content in calibpipe_configs.items():
        config_path = calibpipe_dir / (name + ".yaml")
        config_path.write_text(content)
        config_paths[name] = str(config_path)

    def cwl_file(path):
        if isinstance(path, dict):
            if use_wms:
                path = "lfn://" + str(path["lfn"])
            else:
                path = path["path"]

        return {"class": "File", "path": str(path)}

    calibpipe_output_name = "camera_calibration_lst1.mon.dl1.h5"

    cwl_inputs_calibpipe = {
        "dl0_pedestal_data": [cwl_file(simulated_dl0_pedestal_events)],
        "dl0_flatfield_data": [cwl_file(simulated_dl0_flatfield_events)],
        "ped_process_config": [cwl_file(config_paths["process_pedestal"])],
        "ped_img_pix_stats_config": cwl_file(config_paths["pixelstats_pedestal"]),
        "ff_process_config": [cwl_file(config_paths["process_flatfield"])],
        "ff_img_pix_stats_config": cwl_file(config_paths["pixelstats_flatfield_image"]),
        "ff_time_pix_stats_config": cwl_file(config_paths["pixelstats_flatfield_time"]),
        "coeffs_camcalib_config": cwl_file(config_paths["camera_calibration"]),
        "output_filename": calibpipe_output_name,
    }
    cwl_inputs_path_calibpipe = calibpipe_dir / "inputs.yaml"
    with cwl_inputs_path_calibpipe.open("w") as f:
        yaml.dump(cwl_inputs_calibpipe, f)

    # Step 1 of UC-010-1, execute CalibPipe UC-120-2.20
    if use_wms:
        dirac = Dirac()

        calibpipe_job = CWLJob(
            calibpipe_workflow,
            cwl_inputs_path_calibpipe,
            cvmfs_repo,
            output_se="STORAGE-1",
        )

        translated_cwl_path = calibpipe_dir / "translated_calibpipe.cwl"
        translated_cwl_path.write_text(yaml.dump(calibpipe_job.transformed_cwl.save()))

        calibpipe_job.setName("test_UC-010-1_compute_coefficients")
        calibpipe_job.setDestination("CTAO.CI.de")

        res = calibpipe_job.submit()
        assert res["OK"], res["Message"]
        calibpipe_job_id = res["Value"]
        output_sandbox = calibpipe_dir / "output_sandbox"
        result = wait_for_status(
            dirac,
            job_id=calibpipe_job_id,
            status="Done",
            error_on={"Failed"},
            job_output_dir=output_sandbox,
            timeout=600,
        )
        calibpipe_output = output_sandbox / calibpipe_output_name
        # Success condition: the job has terminated successfully
        assert result["Value"][calibpipe_job_id]["Status"] == "Done"
    else:
        res = run_cwl(calibpipe_workflow, cwl_inputs_path_calibpipe, cwd=calibpipe_dir)
        calibpipe_output = calibpipe_dir / calibpipe_output_name
        assert res.returncode == 0, f"Running calibpipe job failed:\n{res.stdout}"

    # part 2, run DataPipe UC-130-1.2.1

    # prepare configuration and cwl inputs
    datapipe_dir = tmp_path / "datapipe_job"
    datapipe_dir.mkdir()
    datapipe_config_path = datapipe_dir / "config.yaml"
    datapipe_config_path.write_text(datapipe_config)

    datapipe_output_name = "gamma.dl1.h5"

    cwl_inputs_datapipe = {
        "dl0": cwl_file(gamma_prod6_path),
        "processing_config": cwl_file(datapipe_config_path),
        "dl1_filename": datapipe_output_name,
        "camera_calibration_file": cwl_file(calibpipe_output),
        "images": True,
        "parameters": True,
    }
    cwl_inputs_path_datapipe = datapipe_dir / "inputs.yaml"
    with cwl_inputs_path_datapipe.open("w") as f:
        yaml.dump(cwl_inputs_datapipe, f)

    # execute
    if use_wms:
        datapipe_job = CWLJob(
            datapipe_workflow,
            cwl_inputs_path_datapipe,
            cvmfs_repo,
            output_se="STORAGE-1",
        )

        translated_cwl_path = datapipe_dir / "translated_datapipe.cwl"
        translated_cwl_path.write_text(yaml.dump(datapipe_job.transformed_cwl.save()))

        datapipe_job.setName("test_UC-010-1_apply_coefficients")
        datapipe_job.setDestination("CTAO.CI.de")

        res = datapipe_job.submit()
        assert res["OK"], res["Message"]
        datapipe_job_id = res["Value"]
        output_sandbox = datapipe_dir / "output_sandbox"
        result = wait_for_status(
            dirac,
            job_id=datapipe_job_id,
            status="Done",
            error_on={"Failed"},
            job_output_dir=output_sandbox,
            timeout=600,
        )
        # Success condition: the job has terminated successfully
        assert result["Value"][datapipe_job_id]["Status"] == "Done"
        output_dir = output_sandbox
    else:
        res = run_cwl(datapipe_workflow, cwl_inputs_path_datapipe, cwd=datapipe_dir)
        LOG.info("cwl output:\n%s", res.stdout)
        assert res.returncode == 0, f"Running datapipe job failed:\n{res.stdout}"
        output_dir = datapipe_dir

    # verify output
    prov_log = output_dir / "ctapipe-process_dl0_dl1.provenance.log"
    provenance = json.loads(prov_log.read_text())
    inputs = provenance[0]["input"]
    input_names = {Path(i["url"]).name for i in inputs}
    # make sure calibration file was actually used
    assert calibpipe_output.name in input_names

    datapipe_output = output_dir / datapipe_output_name
    with tables.open_file(datapipe_output, "r") as f:
        images = f.root["dl1/event/telescope/images/tel_001"][:]
        assert len(images) == 3
        mean = images["image"].mean()
        LOG.info("Mean of images: %f, First image: %s", mean, images["image"][0])
        # rough check for calibration, images should have values around 0.0 in most pixels
        assert -1.0 <= mean <= 1.0
