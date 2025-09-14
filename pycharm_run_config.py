import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Start Django server with NVM")
    parser.add_argument(
        "--settings",
        default="project.settings.local",
        help="Django settings module (default: project.settings.local)",
    )
    parser.add_argument("--port", default="8000", help="Port to run server on (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")

    args = parser.parse_args()

    # Validate inputs to prevent injection
    if not args.port.isdigit() or not (1 <= int(args.port) <= 65535):
        sys.exit(1)

    # Basic validation for settings module (should be alphanumeric + dots)
    if not all(c.isalnum() or c in "._" for c in args.settings):
        sys.exit(1)

    bash_path = "/bin/bash"
    if not Path(bash_path).exists():
        bash_path = "/usr/bin/bash"
        if not Path(bash_path).exists():
            sys.exit(1)

    # Start NVM to run in PyCharm IDE Run/Debug Config Shell
    nvm_setup = """
    export NVM_DIR="$HOME/.nvm"
    [ -s $NVM_DIR/nvm.sh ] && \\. $NVM_DIR/nvm.sh
    [ -s $NVM_DIR/bash_completion ] && \\. $NVM_DIR/bash_completion
    nvm install
    nvm use
    """

    # Build Django command with properly escaped parameters
    django_command = (
        f"python manage.py runserver {shlex.quote(args.host)}:{shlex.quote(args.port)} "
        f"--settings={shlex.quote(args.settings)}"
    )

    # Combine and run everything in the same shell context
    full_command = nvm_setup + django_command

    try:
        subprocess.run([bash_path, "-c", full_command], check=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError:
        sys.exit(1)


if __name__ == "__main__":
    main()
