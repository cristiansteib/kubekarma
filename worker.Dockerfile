FROM python:3.10-buster as builder
# Always set a working directory
WORKDIR /usr/src/app

# Sets utf-8 encoding for Python et al
ENV LANG=C.UTF-8
# Turns off writing .pyc files; superfluous on an ephemeral container.
ENV PYTHONDONTWRITEBYTECODE=1
# Seems to speed things up
ENV PYTHONUNBUFFERED=1

COPY requiriments.worker.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /usr/src/app/wheels \
    -r requiriments.worker.txt

FROM python:3.10-slim AS app
LABEL org.opencontainers.image.authors="Cristian Steib"
COPY --from=builder  /usr/src/app/wheels /wheels
RUN pip install  --no-cache  /wheels/* && rm -rf /wheels
WORKDIR /app
COPY kubekarma kubekarma
LABEL org.opencontainers.image.version="0.0.1"
ENV PYTHONPATH="${PYTHONPATH}:/app/"
ENTRYPOINT ["python"]
CMD ["kubekarma/worker/main.py"]