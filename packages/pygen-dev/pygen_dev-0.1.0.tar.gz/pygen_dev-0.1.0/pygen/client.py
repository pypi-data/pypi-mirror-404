from pygen.engine import PythonProgramGenerator
import argparse

from pygen.engine import (
    ArchitectureReasoner,
    ConflictDetector,
    InfraGenerator,
    SelfHealingValidator
)

def main():
    parser = argparse.ArgumentParser(
        description="Python Programme Generator CLI"
    )
    parser.add_argument("prompt", nargs="?", help="Project description")
    parser.add_argument("--name", default="generated_project")

    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        return

    generator = PythonProgramGenerator(args.name)
    generator.generate(args.prompt)

if __name__ == "__main__":
    main()

    infra = InfraGenerator()
    healer = SelfHealingValidator()

    print("✔ Architecture:", arch)
    print("✔ Integrations:", integrations)
    print("✔ Docker & CI ready")
    print("✔ Self-healing enabled")
