#!/bin/bash -l

eval "$(micromamba shell hook --shell bash)"
exec micromamba run "$@"
