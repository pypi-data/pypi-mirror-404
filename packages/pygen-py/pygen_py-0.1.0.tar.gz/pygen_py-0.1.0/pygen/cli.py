from pygen.engine import PythonProgramGenerator
from pygen.health import run_health_check
from pygen.doctor import Doctor
from pathlib import Path
from pygen.plugins.loader import PluginManager
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Python Programme Generator CLI"
    )

    sub = parser.add_subparsers(dest="command")

    doctor_parser = sub.add_parser("doctor", help="System diagnostics")
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with non-zero exit code if issues are found (CI mode)"
    )

    sub.add_parser("health", help="Run system health check")
    sub.add_parser("compliance", help="Export compliance report")

    parser.add_argument("prompt", nargs="?", help="Project description")
    parser.add_argument("--name", default="generated_project")
    parser.add_argument("--plugins", nargs="*", default=[])

    args = parser.parse_args()

    # --- doctor ---
    if args.command == "doctor":
        Doctor(Path.cwd()).run(strict=args.strict)
        print("✔ Doctor checks passed")
        return

    # --- health ---
    if args.command == "health":
        status, results = run_health_check()
        for k, v in results.items():
            print(f"{k}: {v}")
        print("STATUS:", status)
        return

    # --- shared execution context ---
    context = {
        "project_name": args.name,
        "prompt": args.prompt,
        "plugins": args.plugins,
        "cwd": str(Path.cwd()),
    }

    # --- plugin execution ---
    manager = PluginManager(args.plugins)
    manager.run("generate", context)

    # --- core generation ---
    if not args.prompt:
        parser.print_help()
        return

    generator = PythonProgramGenerator(args.name)
    generator.generate(args.prompt)