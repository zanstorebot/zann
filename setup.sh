#!/bin/bash

set -e

# Detect if running as root (Docker) or user (VPS)
if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

# Update and install packages
$SUDO apt-get update -y && $SUDO apt-get upgrade -y
$SUDO apt-get install -y --no-install-recommends \
    ffmpeg git neofetch apt-utils libmediainfo0v5 \
    libgl1 libglib2.0-0 fonts-noto-color-emoji \
    tmux python3-venv python3-pip sqlite3 net-tools lsof curl

$SUDO apt-get clean
$SUDO rm -rf /var/lib/apt/lists/*

# Setup swap (only if not already existing)
if ! swapon --show | grep -q '/swapfile'; then
    echo "Setting up swap..."
    $SUDO fallocate -l 8G /swapfile
    $SUDO chmod 600 /swapfile
    $SUDO mkswap /swapfile
    $SUDO swapon /swapfile
    echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab
else
    echo "Swapfile already exists. Skipping swap setup."
fi

# Configure swappiness and cache pressure
echo "Configuring memory management parameters..."
echo 'vm.swappiness=90' | $SUDO tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=200' | $SUDO tee -a /etc/sysctl.conf
$SUDO sysctl -p

# Show swap and memory status
echo "Swap status:"
swapon --show
echo "Memory usage:"
free -h
echo "Current memory parameters:"
echo "Swappiness: $(cat /proc/sys/vm/swappiness)"
echo "VFS Cache Pressure: $(cat /proc/sys/vm/vfs_cache_pressure)"

# Set ulimit
if ! grep -q "* soft nofile" /etc/security/limits.conf; then
    echo "* soft nofile 4096" | $SUDO tee -a /etc/security/limits.conf
    echo "* hard nofile 8192" | $SUDO tee -a /etc/security/limits.conf
else
    echo "ulimit already configured."
fi

# Install Docker
echo "Installing Docker..."
curl -sSL https://get.docker.com | $SUDO sh

ulimit -n 100000

echo "Menetapkan ulimit -n menjadi 100000"

# Menambahkan batasan ke /etc/security/limits.conf
LIMITS_CONF="/etc/security/limits.conf"
echo "root soft nofile 100000" | sudo tee -a $LIMITS_CONF
echo "root hard nofile 100000" | sudo tee -a $LIMITS_CONF
echo "Batasan telah ditambahkan ke $LIMITS_CONF"

# Menambahkan batasan ke /etc/systemd/system.conf dan /etc/systemd/user.conf
SYSTEMD_CONF="/etc/systemd/system.conf"
USER_CONF="/etc/systemd/user.conf"

echo "DefaultLimitNOFILE=100000" | sudo tee -a $SYSTEMD_CONF
echo "DefaultLimitNPROC=100000" | sudo tee -a $SYSTEMD_CONF

echo "DefaultLimitNOFILE=100000" | sudo tee -a $USER_CONF
echo "DefaultLimitNPROC=100000" | sudo tee -a $USER_CONF

echo "Batasan telah ditambahkan ke konfigurasi systemd."

echo "Restarting systemd to apply changes..."
sudo systemctl daemon-reexec

echo "Konfigurasi selesai. Silakan reboot agar perubahan diterapkan sepenuhnya."

echo "✅ Setup completed successfully!"
