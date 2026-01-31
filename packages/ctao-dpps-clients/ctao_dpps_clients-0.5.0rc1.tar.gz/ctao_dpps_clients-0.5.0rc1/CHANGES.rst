DPPS v0.5.0 (2026-01-30)
------------------------

- New versions of DPPS subsystems

  - `Bulk Data Management System v0.6.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/v0.6.0/>`_
  - `Workload Management System v0.5.2 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/workload/wms/v0.5.2/>`_
  - `CalibPipe v0.4.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/v0.4.0/>`_
  - `DataPipe v0.3.1 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/datapipe/datapipe/v0.3.1/>`_
  - `QualPipe v0.2.3 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/qualpipe/qualpipe/v0.2.3/>`_
  - `QualPipe WebApp v0.2.0 <http://gui-861dca.gitlab-pages.cta-observatory.org/v0.2.0/>`_


Maintenance
~~~~~~~~~~~

- Update the python version in the dpps-clients container from 3.11 to 3.12 to be
  compliant with the CTAO reference version. [`!154 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/154>`__]


DPPS v0.4.0 (2025-11-28)
------------------------

- New versions of DPPS subsystems [`!106 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/146>`__]:

  - `Bulk Data Management System v0.5.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/v0.5.0/>`_
  - `CalibPipe v0.3.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/v0.3.0/>`_
  - `DataPipe v0.3.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/datapipe/datapipe/v0.3.0/>`_
  - `SimPipe v0.3.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/simpipe/simpipe/v0.3.0/>`_
  - `QualPipe v0.2.2 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/qualpipe/qualpipe/v0.2.2/>`_
  - `QualPipe WebApp v0.1.2 <http://gui-861dca.gitlab-pages.cta-observatory.org/v0.1.2/>`_


DPPS v0.3.0 (2025-10-01)
------------------------

This update is mainly concerned with updating BDMS and WMS.

The updates include major updates of our main dependencies, Rucio from 35 LTS to 38 LTS
and Dirac from v8 to Dirac v9 including DiracX.


- Update BDMS to v0.4.1. [`!131 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/131>`__]

- Update WMS to v0.4.0. [`!124 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/124>`__]


DPPS v0.2.2 (2025-07-29)
------------------------

This is a maintenance release, updating BDMS to v0.3.1.


New Features
~~~~~~~~~~~~

- Add configuration of default data sources and dashboards
  for the Grafana subchart in the default values. [`!115 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/115>`__]


Maintenance
~~~~~~~~~~~

- Update BDMS to v0.3.1 [`!118 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/118>`__]


DPPS v0.2.1 (2025-07-11)
------------------------

This is a maintenance release updating version of WMS and making fluentbit dependency configurable.

Bug Fixes
~~~~~~~~~

- Add missing condition for inclusion of fluent-bit subchart. [`!111 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/111>`__]


New Features
~~~~~~~~~~~~

- Upgrade WMS to v0.3.1. [`!112 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/112>`__]


DPPS v0.2.0 (2025-06-27)
------------------------



- New versions of DPPS subsystems [`!106 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/106>`__]:

  - `Workload Management System v0.3.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/workload/wms/v0.3.0/>`_
  - `Bulk Data Management System v0.3.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/v0.3.0/>`_
  - `CalibPipe v0.2.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/v0.2.0/>`_
  - `DataPipe v0.2.1 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/datapipe/datapipe/v0.2.1/>`_
  - `SimPipe v0.2.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/simpipe/simpipe/v0.2.0/>`_
  - `QualPipe v0.2.1 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/qualpipe/qualpipe/v0.2.1/>`_


- Add tests to verify collection of observability information. [`!97 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/97>`__]

DPPS v0.1.1 (2025-06-11)
------------------------

This is a maintenance release updating the helm chart of DPPS and
BDMS

Maintenance
~~~~~~~~~~~

- Update dependencies of python package to pin CTADIRAC==2.2.74,
  WMS clients to 0.2.0 and BDMS clients to 0.2.1.
  [`!101 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/101>`__]

- Update `BDMS to 0.2.1 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/latest/changelog.html#bdms-v0-2-1-2025-06-03>`_
  [`!98 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/98>`__]

- Use dpps own chart templates, allows to skip WMS. [`!98 <https://gitlab.cta-observatory.org/cta-computing/dpps/dpps/-/merge_requests/98>`__]


DPPS v0.1.0 (2025-05-08)
------------------------

First DPPS release to integrate pipelines and add functionality to ingest ACADA DL0 data
into BDMS.

This release integrates:

- `Workload Management System v0.2.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/workload/wms/v0.2.0/>`_
- `Bulk Data Management System v0.2.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/v0.2.0/>`_
- `CalibPipe v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/v0.1.0/>`_
- `DataPipe v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/datapipe/datapipe/v0.1.0/>`_
- `SimPipe v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/simpipe/simpipe/v0.1.0/>`_
- `QualPipe v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/qualpipe/qualpipe/v0.1.0/>`_


Deployment is facilitated by docker images and helm charts.


DPPS v0.0.0 (2025-02-26)
------------------------

Initial Release of the Data Processing and Preservation System.

This release integrates

- `Workload Management System v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/workload/wms/v0.1.0/>`_
- `Bulk Data Management System v0.1.0 <http://cta-computing.gitlab-pages.cta-observatory.org/dpps/bdms/bdms/v0.1.0/>`_

Deployment is facilitated by docker images and helm charts.
