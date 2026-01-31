Data Processing and Preservation System
=======================================


| **Version**: |version|
| **Date**: |today|


.. toctree::
    :maxdepth: 1
    :caption: Contents:
    :hidden:

    developer-guide
    user-guide/index
    chart
    changelog


Introduction
------------

The Data Processing and Preservation Systems is one of the major
components of CTAO Computing. It is responsible for transferring and
preserving the DL0 data produced by
`ACADA <https://gitlab.cta-observatory.org/cta-computing/acada/array-control-and-data-acquisition>`_
and then processing it to data level DL3.

DPPS is composed of seven subsystems, split into three management
subsystems:

-  `Bulk Data Management System (BDMS) <https://gitlab.cta-observatory.org/cta-computing/dpps/bdms/bdms>`_
-  `Workload Management System (WMS) <https://gitlab.cta-observatory.org/cta-computing/dpps/workload>`_
-  `Operations Management System(OPS) <https://gitlab.cta-observatory.org/cta-computing/dpps/ops>`_

and four pipeline subsystems:

- `Calibration Production Pipeline (CalibPipe) <https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe>`_
- `Data Processing Pipeline (DataPipe) <https://gitlab.cta-observatory.org/cta-computing/dpps/datapipe/datapipe>`_
- `Data Quality Pipeline (QualPipe) <https://gitlab.cta-observatory.org/cta-computing/dpps/qualpipe>`_
- `Simulation Production Pipeline (SimPipe) <https://gitlab.cta-observatory.org/cta-computing/dpps/simulationpipeline>`_

This repository contains helm chart definitions, documentation, configuration and integration
tests.

The central components of DPPS are deployed using a Kubernetes Helm Chart.

The DPPS system is assembled from the Helm Charts of the subsystems in a
single Helm Chart, which is published to the `CTAO Harbor instance <https://harbor.cta-observatory.org/harbor/projects/4/repositories/dpps/artifacts-tab>`_.
