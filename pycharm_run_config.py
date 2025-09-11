import subprocess
import argparse


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start Django server with NVM")
    parser.add_argument(
        "--settings",
        default="project.settings.local",
        help="Django settings module (default: project.settings.local)",
    )
    parser.add_argument("--port", default="8000", help="Port to run server on (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")

    args = parser.parse_args()

    # Start NVM to run in PyCharm IDE Run/Debug Config Shell
    nvm_setup = """
    export NVM_DIR="$HOME/.nvm"
    [ -s $NVM_DIR/nvm.sh ] && \\. $NVM_DIR/nvm.sh
    [ -s $NVM_DIR/bash_completion ] && \\. $NVM_DIR/bash_completion
    nvm install
    nvm use
    """

    # Build Django command with parameters
    django_command = (
        f"python manage.py runserver {args.host}:{args.port} --settings={args.settings}"
    )

    # Combine and run everything in the same shell context
    full_command = nvm_setup + django_command

    subprocess.run(["bash", "-c", full_command])


if __name__ == "__main__":
    main()
