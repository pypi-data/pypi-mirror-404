###
export CHART_NAME=dpps
export CHART_LOCATION=chart
include aiv-toolkit/Makefile


export TEST_ARTIFACTS_PATH ?= $(PWD)
export TEST_REPORT_CONFIG ?= $(PWD)/config.yml


DATAPIPE_VERSION=$(call aiv_config,DATAPIPE_VERSION,)
CALIBPIPE_VERSION=$(call aiv_config,CALIBPIPE_VERSION,)

export DEV_IMAGE_SUFFIX=-clients
export DEV_DOCKER_EXTRA_ARGS=\
	--build-arg DATAPIPE_VERSION=${DATAPIPE_VERSION} \
	--build-arg=CALIBPIPE_VERSION=${CALIBPIPE_VERSION}
