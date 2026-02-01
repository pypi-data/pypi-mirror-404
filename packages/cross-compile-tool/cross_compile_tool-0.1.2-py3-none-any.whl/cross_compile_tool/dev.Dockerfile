# Dockerfile.unified
# A single development environment for both Native (x86) and Cross (ARM64) builds.

ARG BASE_IMAGE=ros:humble
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Native Build Tools (for x86) and Docker CLI
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-venv \
    ninja-build \
    ccache \
    mold \ 
    g++-aarch64-linux-gnu \
    gcc-aarch64-linux-gnu

# 2. Setup Virtual Environment (following PEP 668)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install Cross Compile Tool (from PyPI)
RUN pip install cross-compile-tool

# 4. Setup Workspace
WORKDIR /ws
CMD ["/bin/bash"]
