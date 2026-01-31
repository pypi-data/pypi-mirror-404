CWL Pipeline Jobs
=================

DPPS uses `Common Workflow Language <https://www.commonwl.org/>`_ to describe
command line tools and workflows to process data.
This is the interface between the pipeline subsystems and the
`Workflow Management System <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/workload/wms/latest/>`_.

Obtaining Pipeline CWL descriptions
-----------------------------------

The CWL definitions of the pipelines are published to the `DPPS group in the CTAO Harbor <https://harbor.cta-observatory.org/harbor/projects/4/repositories>`_
as OCI artifacts in repositories called ``<pipeline name>-cwl``.

To download these artifacts, you can use the `oras tool <https://oras.land/docs/installation>`_:

.. code:: shell

   $ oras pull harbor.cta-observatory.org/dpps/datapipe-cwl:v0.2.0 -o datapipe-cwl-v0.2.0
   $ ls datapipe-cwl-v0.2.0


The pipeline CWL descriptions are also available under ``/opt/cwl`` in the
`dpps-clients <https://harbor.cta-observatory.org/harbor/projects/4/repositories/dpps-clients/artifacts-tab>`_ docker container.



Submitting WMS Jobs using CWL
-----------------------------

You can then submit a Job to the WMS using a CWL file and a yaml file specifying the configuration for that
job:

.. code:: python

   from DIRAC.Interfaces.API.Dirac import Dirac
   from CTADIRAC.Interfaces.API.CWLJob import CWLJob

   dirac = Dirac()

   job = CWLJob(
       cwl_path,
       inputs_path,
       cvmfs_base_path="/cvmfs/sw.cta-observatory.org",
       output_se="STORAGE-1"
   )
   job.setName(name)
   job.setDestination(data_center)
   job.submit()

Where ``cwl_path`` points to the CWL file, ``inputs_path`` to the configuration yaml file,
``cvmfs_base_path`` is the CVMFS repository where apptainer images of the pipelines are installed
and ``output_se`` is the BDMS storage element where output files will be stored. See below.

To access files stored in the BDMS for inputs, prepend the LFN with ``lfn://``
and use a CWL class ``File``:

.. code:: yaml

   input_file:
     class: File
     path: lfn://<LFN of the input file>

To store output files in BDMS, the CWL should define an input value for the name
of the output file, which can then also be set to an ``lfn://`` string:

.. code:: yaml

   output_file: lfn://<LFN of the input file>

If input or output files are not prefixed with ``lfn://`` they are assumed to be local files
on the submitting host (for inputs) or in the job directory (for outputs) and will be stored
the DIRAC input sandbox or output sandbox respectively.
