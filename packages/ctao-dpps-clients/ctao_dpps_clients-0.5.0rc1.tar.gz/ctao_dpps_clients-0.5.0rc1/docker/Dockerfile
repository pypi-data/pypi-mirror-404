FROM harbor.cta-observatory.org/proxy_cache/python:3.12 AS builder

COPY . /tmp/dpps/

RUN python -m pip install build \
  && python -m build /tmp/dpps --wheel -o /tmp/dist

FROM harbor.cta-observatory.org/proxy_cache/almalinux:9

# TODO: these can be derived from pyproject.toml
ARG USERID=1000
ARG GROUPID=1000
ARG ORAS_VERSION=1.2.2

ARG DATAPIPE_VERSION
ARG CALIBPIPE_VERSION

ENV DIRAC_DIR="/home/dpps"
ENV DIRACOS="${DIRAC_DIR}/diracos"

RUN \
  if getent group ${GROUPID}; then \
    groupmod --new-name dpps $(getent group ${GROUPID} | cut -d: -f1); \
  else \
    groupadd --gid ${GROUPID} dpps; \
  fi\
  && adduser --uid ${USERID} --gid dpps -s /bin/bash -d /home/dpps dpps

RUN mkdir -p ${DIRAC_DIR} \
    && chown -R dpps:dpps ${DIRAC_DIR}

WORKDIR ${DIRAC_DIR}

# Download pipeline cwl
RUN curl -fL "https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz" | tar xz -C /usr/local/bin/ oras && chmod +x /usr/local/bin/oras \
  && oras pull harbor.cta-observatory.org/dpps/datapipe-cwl:$DATAPIPE_VERSION -o /opt/cwl/datapipe-cwl/$DATAPIPE_VERSION \
  && oras pull harbor.cta-observatory.org/dpps/calibpipe-cwl:$CALIBPIPE_VERSION -o /opt/cwl/calibpipe-cwl/$CALIBPIPE_VERSION \
  && find /opt/cwl -name cwl-logo.png -delete \
  && chmod -R go+rwX /opt/cwl

# install nodejs, needed for cwl workflows containing javascript
RUN dnf install -y --setopt install_weak_deps=false  nodejs bzip2 git && dnf clean all -y

# Install DIRAC client
USER dpps

ENV PATH="${DIRAC_DIR}/.local/bin:$PATH"

RUN mkdir -p "${DIRAC_DIR}/.local/bin" \
  && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj -C "${DIRAC_DIR}/.local/bin" --strip-components=1 bin/micromamba  \
  && micromamba create -y -p $DIRACOS python=3.12 dirac-grid rucio-clients

RUN mkdir -p ${DIRAC_DIR}/.globus \
    && mkdir -p ${DIRACOS}/etc/grid-security/certificates

COPY --from=builder /tmp/dist/ /tmp/dist/
RUN ${DIRACOS}/bin/pip install --no-cache-dir /tmp/dist/ctao*

ENV \
  CONDA_PREFIX="${DIRACOS}" \
  MAMBA_ROOT_PREFIX="${DIRACOS}" \
  CONDOR_CONFIG="${DIRACOS}/etc/condor/condor_config" \
  DAVIX_DISABLE_REDIRECT_CACHING=1 \
  DAVIX_USE_LIBCURL=1 \
  GSETTINGS_SCHEMA_DIR="${DIRACOS}/share/glib-2.0/schemas" \
  PATH="${DIRACOS}/bin:${DIRACOS}/condabin:${PATH}" \
  X509_CERT_DIR="${DIRACOS}/etc/grid-security/certificates" \
  X509_VOMSES="${DIRACOS}/etc/grid-security/vomses" \
  X509_VOMS_DIR="${DIRACOS}/etc/grid-security/vomsdir" \
  XML_CATALOG_FILES="file://${DIRACOS}/etc/xml/catalog file:///etc/xml/catalog" \
  RUCIO_POLICY_PACKAGE="bdms_rucio_policy" \
  RUCIO_CLIENT_MODE="1"

COPY ./docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
USER dpps
