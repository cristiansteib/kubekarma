FROM python:3.10-buster as builder
# Always set a working directory
WORKDIR /usr/src/app

# Sets utf-8 encoding for Python et al
ENV LANG=C.UTF-8
# Turns off writing .pyc files; superfluous on an ephemeral container.
ENV PYTHONDONTWRITEBYTECODE=1
# Seems to speed things up
ENV PYTHONUNBUFFERED=1

COPY requirements.controller.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /usr/src/app/wheels \
    -r requirements.controller.txt

FROM python:3.10-slim AS app
LABEL org.opencontainers.image.authors="Cristian Steib"
ENV PYTHONPATH="${PYTHONPATH}:/app"
COPY --from=builder  /usr/src/app/wheels /wheels
RUN pip install  --no-cache  /wheels/* && rm -rf /wheels
WORKDIR /app
COPY kubekarma kubekarma
LABEL org.opencontainers.image.version="0.0.1"

ENV OPERATOR_NAMESPACE="default"

ENTRYPOINT ["kopf"]
# --all-namespaces is required to watch all namespaces in order
# to watch all CRDs of kubekarma.io
CMD ["run", "kubekarma/controlleroperator/kopfmain.py", "--all-namespaces"]
