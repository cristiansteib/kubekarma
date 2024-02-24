FROM python:3.11-buster as builder
RUN apt-get update && apt-get install --no-install-recommends -y git && apt-get clean
WORKDIR /usr/src/app
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m pip install hatch
COPY readme.md .
COPY pyproject.toml .

RUN hatch dep show requirements --all > requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /wheels \
    -r requirements.txt

COPY . .
RUN  --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.11-slim AS application
LABEL org.opencontainers.image.authors="Cristian Steib"
ENV PYTHONPATH="${PYTHONPATH}:/app"
COPY --from=builder  /wheels /wheels
RUN pip install  --no-cache  /wheels/* && rm -rf /wheels
WORKDIR /app/kubekarma
COPY kubekarma/controlleroperator   controlleroperator
COPY kubekarma/shared               shared
COPY kubekarma/grpcgen            grpcgen

LABEL org.opencontainers.image.version="0.0.1"

ENV OPERATOR_NAMESPACE="default"

ENTRYPOINT ["kopf"]
# --all-namespaces is required to watch all namespaces in order
# to watch all CRDs of kubekarma.io
CMD ["run", "/app/kubekarma/controlleroperator/kopfmain.py", "--all-namespaces"]
