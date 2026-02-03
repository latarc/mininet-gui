# syntax=docker/dockerfile:1

FROM node:18-bullseye-slim AS frontend-build
WORKDIR /app/frontend
COPY mininet-gui-frontend/package.json mininet-gui-frontend/package-lock.json ./
RUN npm ci
COPY mininet-gui-frontend/ ./
ARG VITE_BACKEND_URL=http://localhost:8000
ARG VITE_BACKEND_WS_URL=ws://localhost:8000
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}
ENV VITE_BACKEND_WS_URL=${VITE_BACKEND_WS_URL}
RUN npm run build

FROM python:3.11-slim-bookworm AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    ethtool \
    git \
    iperf \
    iperf3 \
    iproute2 \
    iputils-ping \
    lsb-release \
    telnet \
    net-tools \
    openvswitch-switch \
    openvswitch-testcontroller \
    procps \
    socat \
    sudo \
    tcpdump \
    tshark \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/ovs-testcontroller /usr/local/bin/controller \
    && ln -sf /usr/bin/ovs-testcontroller /usr/local/bin/ovs-controller \
    && ln -sf /usr/bin/ovs-testcontroller /usr/local/bin/test-controller \
    && ln -sf /usr/bin/ovs-testcontroller /usr/local/bin/ovs-testcontroller

# build mnexec and install Python package
RUN git clone --depth 1 https://github.com/mininet/mininet /opt/mininet \
    && cd /opt/mininet \
    && make mnexec \
    && install -m 0755 /opt/mininet/mnexec /usr/local/bin/mnexec \
    && pip install --no-cache-dir . \
    && rm -rf /opt/mininet/.git

WORKDIR /app/backend
COPY mininet-gui-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt pyshark
COPY mininet-gui-backend/ ./

COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000 5173
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
