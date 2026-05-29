#!/usr/bin/env python3
# Script name: VerifyPyPkg.py
# Purpose: Creates a Python venv, upgrades pip & installs input packages
# Date Created: February 28, 2025
# Version: 2.0
# Author: Jonathan Serrano
# Copyright (c) NYULH Jonathan Serrano, 2026

from __future__ import annotations

import argparse
import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_VENV_DIR = Path(".venv")
DEFAULT_PYTHON_VERSION = "3.14"


def run_cmd(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process."""
    logging.debug("Running command: %s", " ".join(cmd))

    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def command_exists(command: str) -> bool:
    """Return whether a command exists on PATH."""
    return shutil.which(command) is not None


def is_macos() -> bool:
    """Return whether the current system is macOS."""
    return platform.system() == "Darwin"


def find_brew() -> str | None:
    """Find Homebrew executable."""
    brew_path = shutil.which("brew")

    if brew_path is not None:
        return brew_path

    for path in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if Path(path).exists():
            return path

    return None


def brew_formula_for_python(version: str) -> str:
    """Return the Homebrew formula name for a Python version."""
    major_minor = ".".join(version.split(".")[:2])
    return f"python@{major_minor}"


def brew_python_executable(version: str) -> Path | None:
    """Return the expected Homebrew Python executable path if available."""
    brew = find_brew()

    if brew is None:
        return None

    formula = brew_formula_for_python(version)
    result = run_cmd([brew, "--prefix", formula], check=False)

    if result.returncode != 0:
        return None

    prefix = Path(result.stdout.strip())
    major_minor = ".".join(version.split(".")[:2])
    candidates = (
        prefix / "bin" / f"python{major_minor}",
        prefix / "libexec" / "bin" / "python3",
        prefix / "bin" / "python3",
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def install_brew_python(version: str) -> Path:
    """Install requested Homebrew Python version and return its executable path."""
    if not is_macos():
        raise RuntimeError("--install-brew-python is only supported on macOS.")

    brew = find_brew()

    if brew is None:
        raise RuntimeError("Homebrew was not found. Install Homebrew first, then rerun this script.")

    formula = brew_formula_for_python(version)
    logging.info("Installing or upgrading %s with Homebrew.", formula)

    run_cmd([brew, "update"], check=True)
    run_cmd([brew, "install", formula], check=True)

    python_exe = brew_python_executable(version)

    if python_exe is None:
        raise RuntimeError(f"Could not find Python executable for Homebrew formula: {formula}")

    return python_exe


def find_python(version: str, *, install_brew_python_if_missing: bool) -> Path:
    """Find the requested Python executable."""
    major_minor = ".".join(version.split(".")[:2])
    python_names = [f"python{major_minor}", "python3"]

    for name in python_names:
        path = shutil.which(name)

        if path is not None:
            result = run_cmd([path, "--version"], check=False)

            if result.returncode == 0 and major_minor in result.stdout.strip():
                return Path(path)

    brew_python = brew_python_executable(version)

    if brew_python is not None:
        return brew_python

    if install_brew_python_if_missing:
        return install_brew_python(version)

    raise RuntimeError(
        f"Python {major_minor} was not found. On macOS, rerun with "
        f"--install-brew-python or install it manually with: "
        f"brew install {brew_formula_for_python(version)}"
    )


def venv_python_executable(venv_path: Path) -> Path:
    """Return the Python executable path inside a virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"

    return venv_path / "bin" / "python"


def create_virtual_environment(
    python_exe: Path,
    venv_path: Path,
    *,
    force_recreate: bool,
) -> Path:
    """Create a virtual environment and return its Python executable."""
    if force_recreate and venv_path.exists():
        logging.info("Removing existing virtual environment: %s", venv_path)
        shutil.rmtree(venv_path)

    if not venv_path.exists():
        logging.info("Creating virtual environment at %s using %s", venv_path, python_exe)
        run_cmd([str(python_exe), "-m", "venv", str(venv_path)], check=True)
    else:
        logging.info("Virtual environment already exists at %s", venv_path)

    venv_python = venv_python_executable(venv_path)

    if not venv_python.exists():
        raise RuntimeError(f"Could not find venv Python executable: {venv_python}")

    return venv_python


def upgrade_pip_tools(venv_python: Path) -> None:
    """Upgrade pip, setuptools, and wheel inside the virtual environment."""
    logging.info("Upgrading pip, setuptools, and wheel.")

    run_cmd(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ],
        check=True,
    )


def install_packages(
    venv_python: Path,
    packages: list[str],
    *,
    upgrade: bool,
) -> None:
    """Install packages inside the virtual environment."""
    if not packages:
        return

    cmd = [str(venv_python), "-m", "pip", "install"]

    if upgrade:
        cmd.append("--upgrade")

    cmd.extend(packages)

    logging.info("Installing packages: %s", ", ".join(packages))
    run_cmd(cmd, check=True)


def install_requirements(
    venv_python: Path,
    requirements: Path | None,
    *,
    upgrade: bool,
) -> None:
    """Install packages from a requirements file."""
    if requirements is None:
        return

    if not requirements.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements}")

    cmd = [str(venv_python), "-m", "pip", "install"]

    if upgrade:
        cmd.append("--upgrade")

    cmd.extend(["-r", str(requirements)])

    logging.info("Installing requirements from %s", requirements)
    run_cmd(cmd, check=True)


def print_summary(venv_path: Path, venv_python: Path) -> None:
    """Print final usage summary."""
    version = run_cmd([str(venv_python), "--version"], check=True).stdout.strip()

    print()
    print("Virtual environment is ready.")
    print(f"Python: {version}")
    print(f"Venv:   {venv_path.resolve()}")
    print()
    print("Activate with:")
    print(f"source {venv_path}/bin/activate")
    print()
    print("Run scripts with:")
    print(f"{venv_python} your_script.py")
    print()
    print("Portable shebang for scripts run inside an activated venv:")
    print("#!/usr/bin/env python3")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Create a Python virtual environment, optionally install newer "
            "Homebrew Python on macOS, and install Python packages."
        )
    )

    parser.add_argument(
        "packages",
        nargs="*",
        help="Python packages to install, for example: numpy pandas requests",
    )

    parser.add_argument(
        "--requirements",
        "-r",
        type=Path,
        default=None,
        help="Optional requirements.txt file to install.",
    )

    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV_DIR,
        help=f"Path to the virtual environment directory. Default: {DEFAULT_VENV_DIR}",
    )

    parser.add_argument(
        "--python-version",
        default=DEFAULT_PYTHON_VERSION,
        help=f"Python major.minor version to prefer. Default: {DEFAULT_PYTHON_VERSION}",
    )

    parser.add_argument(
        "--install-brew-python",
        action="store_true",
        help="On macOS, install the requested Python version with Homebrew if missing.",
    )

    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Delete and recreate the virtual environment.",
    )

    parser.add_argument(
        "--no-upgrade",
        action="store_true",
        help="Do not pass --upgrade when installing packages.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the script."""
    args = parse_arguments()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        python_exe = find_python(
            args.python_version,
            install_brew_python_if_missing=args.install_brew_python,
        )

        venv_python = create_virtual_environment(
            python_exe,
            args.venv,
            force_recreate=args.force_recreate,
        )

        upgrade_pip_tools(venv_python)

        install_requirements(
            venv_python,
            args.requirements,
            upgrade=not args.no_upgrade,
        )

        install_packages(
            venv_python,
            args.packages,
            upgrade=not args.no_upgrade,
        )

        print_summary(args.venv, venv_python)

    except (subprocess.CalledProcessError, OSError, RuntimeError) as error:
        logging.critical("%s", error)

        if isinstance(error, subprocess.CalledProcessError):
            if error.stdout:
                logging.critical("STDOUT:\n%s", error.stdout.strip())
            if error.stderr:
                logging.critical("STDERR:\n%s", error.stderr.strip())

        sys.exit(1)


if __name__ == "__main__":
    main()
