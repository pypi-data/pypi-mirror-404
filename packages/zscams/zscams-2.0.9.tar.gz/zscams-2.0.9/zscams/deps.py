import subprocess
import sys
import platform
import os
import importlib.util


def is_installed(name):
    return importlib.util.find_spec(name) is not None


def ensure_native_deps():
    # Only run this logic on FreeBSD
    if (
        platform.system().lower() != "freebsd"
        and platform.system().lower() != "zscaleros"
    ):
        # --- Linux/Standard Path ---
        # On Linux, we just use pip to install the missing pieces
        # We use 'PyYAML' instead of 'yaml' for pip
        deps_map = ["cryptography", "pyyaml", "psutil"]
        # Identify which modules are actually missing
        missing_mods = [mod for mod in deps_map if not is_installed(mod)]
        if not missing_mods:
            return  # Everything is already installed
        print(f"--> Installing via pip: {missing_mods}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing_mods, check=True
        )
        return

    # 1. Define what we need and how FreeBSD names them
    py_ver = f"py{sys.version_info.major}{sys.version_info.minor}"
    deps_map = {
        "cryptography": f"{py_ver}-cryptography",
        "yaml": f"{py_ver}-pyyaml",
        "psutil": f"{py_ver}-psutil",
    }

    # Identify which modules are actually missing
    missing_mods = [mod for mod in deps_map if not is_installed(mod)]

    if not missing_mods:
        return  # Everything is already installed

    print(
        f"--> ZscalerOS/FreeBSD detected. Missing requirements: {', '.join(missing_mods)}"
    )

    # 2. Ensure the FreeBSD Mirror is configured
    # We use a custom local file so we don't overwrite Zscaler's system configs
    repo_conf_dir = "/usr/local/etc/pkg/repos"
    repo_conf_file = f"{repo_conf_dir}/FreeBSD.conf"

    if not os.path.exists(repo_conf_file):
        print("--> Mirror not found. Configuring official FreeBSD repository...")
        # Hardcoding the ABI to 13 because ZscalerOS identifies as 42-RELEASE
        mirror_config = (
            "FreeBSD: { "
            'url: "pkg+http://pkg.FreeBSD.org/FreeBSD:13:amd64/latest", '
            'mirror_type: "srv", '
            'signature_type: "fingerprints", '
            'fingerprints: "/usr/share/keys/pkg", '
            "enabled: yes "
            "}"
        )

        try:
            subprocess.run(["sudo", "mkdir", "-p", repo_conf_dir], check=True)
            # Use printf/tee to handle the sudo write to a restricted path
            subprocess.run(
                f"printf '{mirror_config}' | sudo tee {repo_conf_file}",
                shell=True,
                check=True,
                capture_output=True,
            )
            print(
                "--> Mirror configured. Updating package database (this may take a moment)..."
            )
            subprocess.run(["sudo", "pkg", "update", "-f"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"--> Failed to configure mirror. Error: {e}")
            sys.exit(1)

    # 3. Install the missing packages
    targets = [deps_map[m] for m in missing_mods]
    print(f"--> Attempting auto-install of: {', '.join(targets)}")

    try:
        # Install via pkg
        subprocess.run(["sudo", "pkg", "install", "-y"] + targets, check=True)
        print("--> Dependencies installed successfully!")
        print("--> Please restart your command to apply changes.")
        sys.exit(0)
    except subprocess.CalledProcessError:
        print(f"--> Error: Failed to install packages. Check your internet connection.")
        print(f"--> Manual command: sudo pkg install {' '.join(targets)}")
        sys.exit(1)
