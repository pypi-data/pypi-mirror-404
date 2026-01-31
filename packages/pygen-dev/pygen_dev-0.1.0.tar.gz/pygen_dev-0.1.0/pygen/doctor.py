from pathlib import Path
import sys

TEXT_EXTENSIONS = {".py", ".toml", ".yaml", ".yml"}

class Doctor:
    def __init__(self, root: Path):
        self.root = root
        self.fixes = []

    def run(self):
        self._fix_bom()
        self._fix_init_files()
        self._fix_env_example()
        self._check_python()
        return self.fixes

    def _fix_bom(self):
        for path in self.root.rglob("*"):
            if path.suffix in TEXT_EXTENSIONS:
                raw = path.read_bytes()
                if raw.startswith(b"\xef\xbb\xbf"):
                    path.write_bytes(raw[3:])
                    self.fixes.append(f"Removed BOM: {path}")

    def _fix_init_files(self):
        for folder in self.root.rglob("*"):
            if folder.is_dir() and any(f.suffix == ".py" for f in folder.iterdir()):
                init = folder / "__init__.py"
                if not init.exists():
                    init.touch()
                    self.fixes.append(f"Created __init__.py: {folder}")

    def _fix_env_example(self):
        env = self.root / ".env.example"
        if not env.exists():
            env.write_text("ENV=dev\n")
            self.fixes.append("Created .env.example")

    def _check_python(self):
        if sys.version_info < (3, 10):
            self.fixes.append("WARNING: Python < 3.10 detected")

class DoctorResult:
    def __init__(self):
        self.fixes = []
        self.errors = []

    def summary(self):
        return {
            "fixes": self.fixes,
            "errors": self.errors,
            "status": "ok" if not self.errors else "failed"
        }
