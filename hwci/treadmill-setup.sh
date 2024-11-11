#!/usr/bin/env bash

set -x
set -e

if [ ! -d tock ]; then
  echo "Cloning Tock kernel repository"
  git clone https://github.com/tock/tock
fi

if [ ! -d libtock-c ]; then
  echo "Cloning libtock-c repository"
  git clone https://github.com/tock/libtock-c
fi

# TODO: currently, the Netboot NBD targets have no access to their
# boot parition (e.g., mounted on /boot/firmware) on a Raspberry Pi OS
# host. This causes certain hooks in response to dpkg / apt commands
# to fail. Thus we ignore errors in these steps until we figure this
# part out.
sudo DEBIAN_FRONTEND=noninteractive apt update || true
sudo DEBIAN_FRONTEND=noninteractive apt install -y \
  git cargo openocd python3 python3-pip python3-serial \
  python3-pexpect gcc-arm-none-eabi libnewlib-arm-none-eabi \
  pkg-config libudev-dev cmake libusb-1.0-0-dev udev make \
  gdb-multiarch gcc-arm-none-eabi build-essential || true

# Install probe-rs:
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/probe-rs/probe-rs/releases/latest/download/probe-rs-tools-installer.sh \
  | sh

if [ ! -d ./hwcienv ]; then
  python3 -m venv ./hwcienv
fi
source ./hwcienv/bin/activate
pip install -r requirements.txt -c requirements-frozen.txt

echo "Prepared hwci environment!"
echo "1. Activate the venv: 'source ./hwcienv/bin/activate'"
echo "2. Set the PYTHONPATH: 'export PYTHONPATH=\"$PWD:$PYTHONPATH\"'"
echo "3. Run a test: 'python3 core/main.py --board boards/nrf52dk.py --test tests/c_hello.py'"
