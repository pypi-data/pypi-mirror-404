Developer Guide
===============

Running subsystem and system (integration) tests using Kubernetes
-----------------------------------------------------------------

DPPS central services together with standard setup of test CE and SEs
require:

-  6Gb RAM
-  2 CPU
-  30 Gb disk space available to docker

Installation from scratch, including downloading images and
bootstrapping databases, takes up to 10min (it will be improved in the
future). Subsequent updates are much faster.

.. code-block:: shell

   $ git clone git@gitlab.cta-observatory.org:cta-computing/dpps/dpps.git --recurse-submodules
   $ cd dpps
   $ make

You should end up with an interactive prompt, where you can run the integration tests using ``pytest``:

.. code-block:: shell

   [dpps@dpps-pytest dpps]$ python3 -m pytest

See `DPPS AIV
Toolkit <https://gitlab.cta-observatory.org/cta-computing/dpps/aiv/deployment-components/dpps-aiv-toolkit/>`__
for the guide, examples, and templates on running integration tests for
DPPS subsystems and system.



Fetching chart for local usage
------------------------------

.. code-block:: shell

    helm pull https://harbor.cta-observatory.org/dpps/dpps --version <VERSION>
