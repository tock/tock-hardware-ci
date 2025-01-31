#! /usr/bin/env bash

function promptContinue() {
	while true; do
		read -p "$1 (y/n)? " CHOICE
		case "$CHOICE" in
			y|Y ) return 0;;
			n|N ) return 1;;
			* ) continue;;
		esac
	done
}

# If not running in CI, prompt the user before continuing. This script will
# attempt to modify the global system environment.
if [ "$CI" != "true" ]; then
	echo "This script will attempt to install all system dependencies" >&2
	echo "necessary to run the Tock hardware CI Python scripts." >&2
	echo "It will attempt to use sudo, install packages using your" >&2
	echo "system's package manager, and create a Python virtual env." >&2
	echo "You should only run it in an environment that's ephemeral" >&2
	echo "or specifically used for the Tock hardware CI." >&2
	echo "" >&2
	promptContinue "THIS SCRIPT MAY MESS WITH YOUR SYSTEM! Continue"
	if [ $? -ne 0 ]; then
		echo "Aborting on user request." >&2
		exit 1
	fi
fi

# From this point onward, echo all commands and exit on the first error:
set -e -x

# Require rustup to be installed. We don't want to mess with the user's
# installation and GitHub actions will install this for us. Tock will then
# use rustup to ensure the correct target toolchain is installed as part
# of its own build process:
type rustup || (echo "rustup is not installed, aborting."; exit 1)

if ! type elf2tab; then
	# We may not have a rustup default toolchain selected. In this case,
	# select the stable toolchain for elf2tab.
	if ! rustup default; then
		rustup toolchain add stable
		cargo '+stable' install elf2tab
	else
		cargo install elf2tab
	fi
	elf2tab --version
fi

# Install all required system dependencies. For now, we only support Debian
# hosts (such as Raspberry Pi OS).
#
# TODO: currently, the Treadmill Netboot NBD targets have no access to their
# boot parition (e.g., mounted on /boot/firmware) on a Raspberry Pi OS host.
# This causes certain hooks in response to dpkg / apt commands to fail. Thus
# we ignore errors in these steps until we figure this part out.
sudo DEBIAN_FRONTEND=noninteractive apt update || true
sudo DEBIAN_FRONTEND=noninteractive apt install -y \
  git cargo openocd python3 python3-pip python3-serial \
  python3-pexpect gcc-arm-none-eabi libnewlib-arm-none-eabi \
  pkg-config libudev-dev cmake libusb-1.0-0-dev udev make \
  gdb-multiarch gcc-arm-none-eabi build-essential jq || true

# If we don't have any of the tock or libtock-c repos checked out, clone them
# here. We never want to do this for CI, as that'll want to check out specific
# revisions of those repositories (and we don't accidentally want to always
# test the current HEAD).
if [ "$CI" != "true" ]; then
	test ! -d "./repos/tock" \
		&& git clone "https://github.com/tock/tock.git" "./repos/tock"
	test ! -d "./repos/libtock-c" \
		&& git clone "https://github.com/tock/libtock-c.git" "./repos/libtock-c"
fi

# Create a Python virtual environment and install the required dependencies:
python3 -m venv ./.venv
source ./.venv/bin/activate
pip install -r ./requirements.txt -c ./requirements-frozen.txt

set +x

# Fin!
echo "" >&2
echo "All packages installed successfully! To continue, activate the" >&2
echo "Python virtual environment:" >&2
echo "" >&2
echo "    source .venv/bin/activate" >&2
echo "" >&2

