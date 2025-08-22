#!/usr/bin/env python3
"""
Playwright installer with Ubuntu 24.04 compatibility fixes.
Handles the libasound2 -> libasound2t64 transition and other package naming changes.
"""

import subprocess
import sys
import platform
import os
from typing import List, Tuple


def get_ubuntu_version() -> Tuple[int, int]:
    """Get Ubuntu version as tuple (major, minor)."""
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('VERSION_ID='):
                    version = line.strip().split('=')[1].strip('"')
                    major, minor = version.split('.')
                    return int(major), int(minor)
    except:
        return 0, 0


def get_playwright_dependencies() -> List[str]:
    """Get list of dependencies based on Ubuntu version."""
    ubuntu_version = get_ubuntu_version()
    
    # Base dependencies for all versions
    deps = [
        'libnss3',
        'libnspr4',
        'libatk1.0-0',
        'libatk-bridge2.0-0',
        'libcups2',
        'libdrm2',
        'libdbus-1-3',
        'libatspi2.0-0',
        'libx11-6',
        'libxcomposite1',
        'libxdamage1',
        'libxext6',
        'libxfixes3',
        'libxrandr2',
        'libgbm1',
        'libxcb1',
        'libxkbcommon0',
        'libpango-1.0-0',
        'libcairo2',
        'libgtk-3-0',
        'libgdk-pixbuf-2.0-0',
        'libglib2.0-0',
        'fonts-liberation',
        'libappindicator3-1',
        'libnss3-dev',
        'libgdk-pixbuf2.0-dev',
        'libgtk-3-dev',
        'libxss1',
        'xdg-utils',
    ]
    
    # Ubuntu 24.04+ uses libasound2t64
    if ubuntu_version >= (24, 4):
        deps.append('libasound2t64')
    else:
        deps.append('libasound2')
    
    return deps


def install_system_dependencies():
    """Install system dependencies with error handling."""
    print("Detecting Ubuntu version...")
    version = get_ubuntu_version()
    print(f"Ubuntu version: {version[0]}.{version[1]}")
    
    deps = get_playwright_dependencies()
    
    print(f"Installing {len(deps)} system dependencies...")
    
    # Update package list
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
    except subprocess.CalledProcessError:
        print("Failed to update package list. Running without sudo...")
        subprocess.run(['apt-get', 'update'], check=True)
    
    # Install dependencies
    cmd = ['apt-get', 'install', '-y'] + deps
    
    try:
        subprocess.run(['sudo'] + cmd, check=True)
    except subprocess.CalledProcessError:
        print("Failed to install with sudo. Trying without...")
        subprocess.run(cmd, check=True)
    
    print("System dependencies installed successfully!")


def create_compatibility_links():
    """Create symbolic links for compatibility if needed."""
    # Check if we need to create libasound.so.2 symlink
    lib_paths = [
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib/aarch64-linux-gnu',
        '/usr/lib',
    ]
    
    for lib_path in lib_paths:
        libasound_so = os.path.join(lib_path, 'libasound.so.2')
        libasound_versioned = os.path.join(lib_path, 'libasound.so.2.0.0')
        
        if os.path.exists(libasound_versioned) and not os.path.exists(libasound_so):
            print(f"Creating compatibility symlink: {libasound_so}")
            try:
                subprocess.run(['sudo', 'ln', '-sf', libasound_versioned, libasound_so], check=True)
            except:
                print("Failed to create symlink with sudo, skipping...")


def install_playwright():
    """Install Playwright and browsers."""
    print("\nInstalling Playwright...")
    
    # First ensure playwright is installed via pip
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'playwright'], check=True)
    
    # Install browsers without system deps (we already installed them)
    print("\nInstalling Chromium browser...")
    subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=True)
    
    print("\nPlaywright installation complete!")


def verify_installation():
    """Verify Playwright installation."""
    print("\nVerifying installation...")
    try:
        # Try to import and use playwright
        subprocess.run([
            sys.executable, '-c',
            'from playwright.sync_api import sync_playwright; '
            'with sync_playwright() as p: '
            'print("✓ Playwright is working correctly!")'
        ], check=True)
    except subprocess.CalledProcessError:
        print("⚠ Warning: Playwright verification failed. You may need to troubleshoot.")
        return False
    return True


def main():
    """Main installation process."""
    print("=== Playwright Ubuntu 24.04 Installer ===\n")
    
    # Check if running on Linux
    if platform.system() != 'Linux':
        print("This script is designed for Linux systems only.")
        sys.exit(1)
    
    try:
        # Install system dependencies
        install_system_dependencies()
        
        # Create compatibility links if needed
        create_compatibility_links()
        
        # Install Playwright
        install_playwright()
        
        # Verify installation
        if verify_installation():
            print("\n✅ Installation completed successfully!")
        else:
            print("\n⚠ Installation completed with warnings.")
            
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()