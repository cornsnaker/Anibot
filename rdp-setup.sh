#!/bin/bash
# Make Instance Ready for Remote Desktop or RDP

echo "Updating package lists..."
sudo apt-get update

echo "Cleaning up previous files..."
# Added sudo in case files are in privileged locations
sudo rm -rf w2012 w2012.img w2012.gz ngrok ngrok.zip ng.sh > /dev/null 2>&1

echo "Download windows files..."
wget -O w2012.gz https://go.aank.me/win/WS2012R2-LinggaHosting.gz
echo "Decompressing Windows image... This may take a while."
gunzip w2012.gz
echo "Wait..."
echo "I m Working Now.."
mv w2012 w2012.img

echo "Downloading ngrok script..."
wget -O ng.sh https://bit.ly/GCngr0k > /dev/null 2>&1
chmod +x ng.sh
./ng.sh
clear

echo "======================="
echo "Choose ngrok region"
echo "======================="
echo "us - United States (Ohio)"
echo "eu - Europe (Frankfurt)"
echo "ap - Asia/Pacific (Singapore)"
echo "au - Australia (Sydney)"
echo "sa - South America (Sao Paulo)"
echo "jp - Japan (Tokyo)"
echo "in - India (Mumbai)"
echo "======================="
read -p "choose ngrok region: " CRP

# Start ngrok in the background
./ngrok tcp --region $CRP 3388 &>/dev/null &
clear

echo "Downloading and installing QEMU..."
# Added sudo for installation
sudo apt-get install qemu-system-x86 -y
echo "Wait..."
echo "Starting Windows VM..."
echo "This step will likely fail or be extremely slow on Gitpod."

# Run QEMU.
# WARNING: Requesting 8G of RAM and 40 cores will likely fail
# on any standard Gitpod instance.
qemu-system-x86_64 -hda w2012.img -m 8G -smp cores=40 -net user,hostfwd=tcp::3388-:3389 -net nic -object rng-random,id=rng0,filename=/dev/urandom -device virtio-rng-pci,rng=rng0 -vga vmware -nographic &>/dev/null &
clear

echo "Attempting to get RDP Address..."
echo "This may take a moment for the ngrok tunnel to initialize."
sleep 10 # Give ngrok time to start

RDP_ADDRESS=$(curl --silent --show-error http://127.0.0.1:4040/api/tunnels | sed -nE 's/.*public_url":"tcp:..([^"]*).*/\1/p')

if [ -z "$RDP_ADDRESS" ]; then
    echo "Could not retrieve RDP address from ngrok."
    echo "Check http://127.0.0.1:4040 in your browser if Gitpod exposes it."
else
    echo "RDP Address:"
    echo $RDP_ADDRESS
fi

echo "===================================="
echo "Username: Administrator"
echo "Password: Lingg@H0sting"
echo "===================================="
echo "===================================="
echo "Don't Close This Tab"
echo "Wait 1 - 2 minutes for finishing bot"
echo "===================================="

# Keep the terminal alive
sleep 43200
