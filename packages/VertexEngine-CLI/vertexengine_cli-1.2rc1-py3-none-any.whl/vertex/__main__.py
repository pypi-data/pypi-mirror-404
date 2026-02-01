# __main__.py
from pathlib import Path
import os
import subprocess
from PyInstaller.__main__ import run as pyinstaller_run

from .minicli import CLI
from .templates import TEMPLATES
import sys
import glob

def main():
    cli = CLI()

    # -----------------
    # Upload
    # -----------------
    @cli.command("upload")
    def upload_package(dist_path="dist/*", username=None, password=None):
        """
        Upload a Python package to PyPI using Twine.

        dist_path: glob path to distribution files (default: dist/*)
        username: PyPI username (optional if stored in .pypirc)
        password: PyPI password or token (optional if stored in .pypirc)
        """
        # Expand wildcards in a cross-platform way
        files = glob.glob(dist_path)
        if not files:
            print(f"❌ No files found at {dist_path}")
            return

        # Use Python to call Twine (works on Windows, Linux, macOS)
        command = [sys.executable, "-m", "twine", "upload"] + files

        if username:
            command += ["-u", username]
        if password:
            command += ["-p", password]

        print(f"🚀 Running: {' '.join(command)}")
        try:
            subprocess.run(command, check=True)
            print("✅ Upload complete!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload failed: {e}")


        print(f"🚀 Running: {' '.join(command)}")
        try:
            subprocess.run(command, check=True)
            print("✅ Upload complete!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload failed: {e}")
    # -----------------
    # Remove
    # -----------------
    @cli.command("remove")
    def remove_file(
        script_path: str
    ):
        """Remove a script from your project."""
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        os.remove(script_path)
    # ------------------
    # build command
    # ------------------
    @cli.command("build")
    def build_executable(
        script_path: str,
        onefile: bool = False,
        windowed: bool = False,
    ):
        """
        Build an executable from a Python script using PyInstaller.
        """
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        args = ["--clean"]

        if onefile:
            args.append("--onefile")
        if windowed:
            args.append("--windowed")

        args.append(script_path)

        print(f"Running PyInstaller with args: {args}")
        pyinstaller_run(args)

    # ------------------
    # init command
    # ------------------
    @cli.command("init")
    def init(kind: str = "game"):
        """Initialize a project template"""
        if kind not in TEMPLATES:
            print("Available templates:", ", ".join(TEMPLATES))
            return

        for rel_path, content in TEMPLATES[kind].items():
            path = Path.cwd() / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)

            if path.exists():
                print(f"Skipped existing file: {rel_path}")
                continue

            path.write_text(content, encoding="utf-8")
            print(f"Created {rel_path}")

        print(f"Template '{kind}' initialized ✔")

    cli.run()


if __name__ == "__main__":
    main()
