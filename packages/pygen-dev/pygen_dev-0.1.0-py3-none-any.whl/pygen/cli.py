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
    context = {
    "project_name": args.name,
    "prompt": args.prompt,
    "plugins": args.plugins,
    "cwd": str(Path.cwd()),
    }

    manager = PluginManager(args.plugins)
    manager.run("generate", context)

    if args.command == "health":
        status, results = run_health_check()
        for k, v in results.items():
            print(f"{k}: {v}")
        print("STATUS:", status)
        return
    
    if args.command == "doctor":
        result = Doctor(Path.cwd()).run(strict=args.strict)
        summary = result.summary()

        for f in summary["fixes"]:
            print("FIX:", f)

        for e in summary["errors"]:
            print("ERROR:", e)

        print("STATUS:", summary["status"])
        return


    if not args.prompt:
        parser.print_help()
        return

    gen = PythonProgramGenerator(args.name)
    gen.generate(args.prompt)

    if args.command == "compliance":
        ComplianceExporter().export(
            project="pygen-project",
            findings=context
        )
        print("✔ compliance.json generated")
        return

class Plugin:
    def generate(self, context: dict):
        print("Plugin running for", context["project_name"])

if __name__ == "__main__":
    main()
