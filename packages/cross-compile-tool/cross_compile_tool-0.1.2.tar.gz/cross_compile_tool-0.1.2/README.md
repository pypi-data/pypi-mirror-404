# cross-compile-tool

A blazing fast, generic cross-compilation utility for C++ and ROS 2. It uses Docker to generate an ARM64 sysroot and standard native tools (GCC/Ninja) for compilation.

## Prerequisites
- **Docker**: For building the sysroot & dev environments.
- **Cross Compiler**: `sudo apt install g++-aarch64-linux-gnu` (Only required for Host builds).

## Installation
```bash
# Recommended: Install in a virtual environment
pip install .
```

## Usage

The tool uses subcommands: `build`, `sysroot`, `build-dev`, and `run-dev`.

### 1. Build (The Daily Driver)
Compiles your code. It automatically builds the sysroot if it's missing.

```bash
# Basic usage (compiles current directory)
cross-compile-tool build

# ROS 2 Specific: Build only selected packages
cross-compile-tool build --packages-select my_pkg1 my_pkg2
```

**Common Options:**
- `--packages-select`: Build specific packages only (colcon only).
- `--packages-up-to`: Build specified packages and their dependencies (colcon only).
- `--packages-ignore`: Skip specific packages during the build.
- `--clean`: Wipe build directory before compiling.
- `--build-tool [colcon|cmake]`: Force a specific tool (default: `auto`).

### 2. Dev Environment (Docker)
If you don't want to install cross-compilers on your host, or want a reproducible CI environment:

**Step 1: Build the environment**
```bash
# Uses default tag: cross-compile-dev
cross-compile-tool build-dev
```

**Step 2: Enter the environment**
```bash
# Automatically handles volume mounts
cross-compile-tool run-dev
```
Inside the container, you are at `/ws` and can run `cross-compile-tool build` immediately.

### 3. Sysroot (Environment Management)
Explicitly manage the Docker-based sysroot. **Note: Sysroot generation must be performed on the Host system.**

**Common Commands (Run on Host):**
```bash
# Rebuild the sysroot (forced sync from Docker)
cross-compile-tool sysroot --rebuild

# Build sysroot using a specific packages file
cross-compile-tool sysroot --packages-file my_deps.txt

# Specify a different base image (e.g., for a different ROS distro)
cross-compile-tool sysroot --rebuild --base-image ros:humble-ros-base
```

**Features:**
- **Environment Awareness**: The tool identifies if it's running on **Host** or in **Docker** and prevents invalid operations (like generating sysroots inside the container).
- **Staleness Check**: Tracks dependencies using hashes and warns you if your sysroot needs an update.
- **Optional Python**: Automatically detects and configures Python headers/libraries in the sysroot.

## Configuration
Create an `apt_packages.txt` in your project root to specify dependencies:
```text
libfmt-dev
ros-humble-ros-base
python3-numpy
```
