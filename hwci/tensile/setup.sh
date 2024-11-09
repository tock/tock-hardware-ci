# Script to create venv, activate, install dependencies. 


# Install nordic tools (this includes Segger JLink and dependencies needed for pynrfjprog).
# Download the .deb file from the nRF website if does not already exist.
if [ ! -f nrf-command-line-tools_10.24.2_arm64.deb ]; then
    wget https://nsscprodmedia.blob.core.windows.net/prod/software-and-other-downloads/desktop-software/nrf-command-line-tools/sw/versions-10-x-x/10-24-2/nrf-command-line-tools_10.24.2_arm64.deb
fi


sudo apt install ./nrf-command-line-tools_10.24.2_arm64.deb -y 
# Fix broken dependencies (JLink doesn't automatically install for some reason).
sudo apt install /opt/nrf-command-line-tools/share/JLink_Linux_V794e_arm64.deb --fix-broken -y

# Install other dependencies that are needed.
sudo DEBIAN_FRONTEND=noninteractive apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y \
           git gcc-arm-none-eabi make gcc-riscv64-unknown-elf \

# Install / setup rust. (@Leon this should be redundant, but I was having issues
# getting cargo working without this).
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Create venv / activate.
python3 -m venv tensile-venv
source tensile-venv/bin/activate

# Install needed python dependencies.
pip install -r requirements.txt

# NOTE: The testing scripts expect these repos to be in the same directory as main.py.
# Clone libtock-c / tock / tockloader (need to clone tockloader from my repo temporarily 
# until the tockloader jlink-selector branch is merged).

if [ ! -f ot-central-controller.hex ]; then
  wget https://book.tockos.org/assets/temperature-sensor/ot-central-controller.hex
fi

git clone https://github.com/tock/tock.git
git clone https://github.com/tock/libtock-c.git


