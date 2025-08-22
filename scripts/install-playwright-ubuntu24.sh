#!/bin/bash
# Install Playwright dependencies for Ubuntu 24.04 (Noble)
# Fixes the libasound2 -> libasound2t64 transition issue

set -e

echo "Installing Playwright dependencies for Ubuntu 24.04..."

# Update package list
sudo apt-get update

# Install dependencies with correct package names for Ubuntu 24.04
sudo apt-get install -y \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxshmfence1 \
    xvfb \
    fonts-liberation \
    libu2f-udev \
    libvulkan1

# Create compatibility symlink if needed
if [ ! -f /usr/lib/x86_64-linux-gnu/libasound.so.2 ] && [ -f /usr/lib/x86_64-linux-gnu/libasound.so.2.0.0 ]; then
    sudo ln -sf /usr/lib/x86_64-linux-gnu/libasound.so.2.0.0 /usr/lib/x86_64-linux-gnu/libasound.so.2
fi

echo "Dependencies installed successfully!"

# Install Playwright browsers without --with-deps flag
echo "Installing Playwright browsers..."
playwright install chromium

echo "Playwright installation complete!"