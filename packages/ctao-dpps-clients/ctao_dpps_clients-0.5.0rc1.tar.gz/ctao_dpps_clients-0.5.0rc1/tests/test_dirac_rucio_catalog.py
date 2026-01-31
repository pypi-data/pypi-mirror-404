from pathlib import Path

import pytest
from rucio.client.didclient import DIDClient
from rucio.client.replicaclient import ReplicaClient
from rucio.client.uploadclient import UploadClient
from wms.tests.utils import wait_for_status


@pytest.fixture(scope="session")
def test_file(test_scope, tmp_path_factory):
    name = "test.dat"
    path = tmp_path_factory.mktemp("data_") / name
    path.write_text("Hello, World!")
    lfn = f"/ctao.dpps.test/{test_scope}/{name}"

    upload_spec = {
        "path": path,
        "rse": "STORAGE-2",
        "did_scope": test_scope,
        "did_name": lfn,
        "lifetime": 2,
    }
    upload_client = UploadClient()
    upload_client.upload([upload_spec])
    did_client = DIDClient()
    did_client.set_metadata(test_scope, lfn, "test-meta", "foo")
    return lfn


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_get_file_metadata(test_file):
    from DIRAC.Resources.Storage.StorageElement import StorageElement

    se = StorageElement("STORAGE-2")
    result = se.getFileMetadata(test_file)
    assert result["OK"], f"Error getting file metadatae: {result['Message']}"


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_get_file_user_metadata(test_file):
    from DIRAC.Resources.Catalog.RucioFileCatalogClient import RucioFileCatalogClient

    dirac = RucioFileCatalogClient()
    result = dirac.getFileUserMetadata(test_file)
    assert result["OK"], f"Error getting file metadatae: {result['Message']}"

    meta = result["Value"]["Successful"][test_file]
    assert meta["test-meta"] == "foo"


@pytest.mark.usefixtures("_init_dirac")
def test_find_file_by_metadata(test_file):
    from DIRAC.Resources.Catalog.RucioFileCatalogClient import RucioFileCatalogClient

    dirac = RucioFileCatalogClient()
    result = dirac.findFilesByMetadata({"test-meta": "foo"})
    assert result["OK"], f"Error finding file by metadatae: {result['Message']}"

    found_lfns = result["Value"]
    assert test_file in found_lfns

    # opposite test, to see that we don't just get all files
    result = dirac.findFilesByMetadata({"test-meta": "non-existent-metadata"})
    assert result["OK"], f"Error finding file by metadatae: {result['Message']}"
    assert result["Value"] == []


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_get_file(test_file, tmp_path):
    from DIRAC.Interfaces.API.Dirac import Dirac

    # Step 1 establishing connection
    dirac = Dirac()

    # Step 2 Downloading a file
    result = dirac.getFile(test_file, destDir=str(tmp_path))

    # Verification
    assert result["OK"], f"Error downloading file: {result['Message']}"
    assert (tmp_path / "test.dat").read_text() == "Hello, World!"


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_add_file(tmp_path, test_scope):
    from DIRAC.DataManagementSystem.Client.DataManager import DataManager
    from DIRAC.Interfaces.API.Dirac import Dirac

    # Creating the local file
    name = "add_test.dat"
    path = tmp_path / name
    path.write_text("Hello from DIRAC")

    # Request upload
    dm = DataManager()
    rse = "STORAGE-1"
    lfn = f"/ctao.dpps.test/{test_scope}/{name}"
    result = dm.putAndRegister(lfn, str(path), rse)

    # Verify the upload succeeded
    assert result["OK"], f"Uploading file failed: {result}"
    failed = result["Value"]["Failed"]
    assert len(failed) == 0, f"Failed to upload file: {failed}, result: {result}"
    successful = result["Value"]["Successful"]
    assert lfn in successful
    assert "put" in successful[lfn]
    assert "register" in successful[lfn]

    # Download the same file again
    destination = tmp_path / "download"
    destination.mkdir()
    dirac = Dirac()
    result = dirac.getFile(lfn, destDir=str(destination))

    assert result["OK"], f"Downloading uploaded file failed: {result}"
    # verify the file content is correct
    assert (destination / "add_test.dat").read_text() == "Hello from DIRAC"


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_rucio_file_as_job_input(test_file, tmp_path):
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job

    dirac = Dirac()

    job = Job()
    name = Path(test_file).name
    job.setExecutable("cat", arguments=name)
    job.setName("test_input_data")
    job.setDestination("CTAO.CI.de")
    job.setInputData([test_file])

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


@pytest.mark.verifies_usecase("DPPS-UC-020-1.1")
@pytest.mark.usefixtures("_init_dirac")
def test_store_output(test_scope, tmp_path):
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job

    rse = "STORAGE-1"

    dirac = Dirac()

    job = Job()
    name = "output.dat"
    job.setExecutable("bash", arguments=f"-c 'echo \"Hello from DIRAC\" > {name}'")
    job.setName("test_output_data")
    job.setDestination("CTAO.CI.de")

    lfn = f"/ctao.dpps.test/{test_scope}/{name}"
    job.setOutputData([f"LFN:{lfn}"], outputSE=rse)

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

    # see that the file is known to rucio
    replica_client = ReplicaClient()
    replicas = list(replica_client.list_replicas([{"scope": test_scope, "name": lfn}]))
    assert len(replicas) == 1
    assert replicas[0]["states"][rse] == "AVAILABLE"

    # get the file with dirac
    result = dirac.getFile(lfn, destDir=str(tmp_path))
    assert result["OK"], f"Error downloading file: {result['Message']}"
    assert (tmp_path / name).read_text() == "Hello from DIRAC\n"
