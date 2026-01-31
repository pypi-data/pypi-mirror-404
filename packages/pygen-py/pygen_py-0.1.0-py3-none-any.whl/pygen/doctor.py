from pathlib import Path
import sys

TEXT_EXTENSIONS = {".py", ".toml", ".yaml", ".yml"}

class DoctorResult:
    def __init__(self):
        self.fixes = []
        self.errors = []

    def ok(self):
        return len(self.errors) == 0

    def summary(self):
        return {
            "fixes": self.fixes,
            "errors": self.errors,
            "status": "ok" if self.ok() else "failed",
        }

class Doctor:
     def __init__(self, root: Path):
        self.root = root
        self.result = DoctorResult()

     def run(self,strict: bool = False):
        self._check_bom()
        self._check_structure()
        self._check_python()
        self._fix_bom()
        self._fix_init_files()
        self._fix_env_example()

        if strict and not self.result.ok():
            raise SystemExit(1)

        return self.result

     def _check_bom(self):
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".toml", ".yaml", ".yml"}:
                try:
                    raw = path.read_bytes()
                except Exception:
                    continue

                if raw.startswith(b"\xef\xbb\xbf"):
                    self.result.errors.append(f"BOM detected: {path}")

     def _check_structure(self):
        required = [
            self.root / "pygen" / "engine.py",
            self.root / "pygen" / "cli.py",
        ]

        for file in required:
            if not file.exists():
                self.result.errors.append(f"Missing required file: {file}")

        # ensure __init__.py exists where needed
        for folder in (self.root / "pygen").rglob("*"):
            if folder.is_dir():
                py_files = list(folder.glob("*.py"))
                if py_files:
                    init = folder / "__init__.py"
                    if not init.exists():
                        self.result.fixes.append(f"Missing __init__.py: {folder}")

     def _check_python(self):
        if sys.version_info < (3, 10):
            self.result.errors.append(
                f"Python {sys.version_info.major}.{sys.version_info.minor} detected; >=3.10 required"
            )

     def _fix_bom(self):
        for path in self.root.rglob("*"):
            if path.suffix in TEXT_EXTENSIONS:
                raw = path.read_bytes()
                if raw.startswith(b"\xef\xbb\xbf"):
                    path.write_bytes(raw[3:])
                    self.result.fixes.append(f"Removed BOM: {path}")

     def _fix_init_files(self):
        for folder in self.root.rglob("*"):
            if folder.is_dir() and any(f.suffix == ".py" for f in folder.iterdir ()):
                init = folder / "__init__.py"
                if not init.exists():
                    init.touch()
                    self.result.fixes.append(f"Created __init__.py: {folder}")

     def _fix_env_example(self):
        env = self.root / ".env.example"
        if not env.exists():
            env.write_text("ENV=dev\n")
            self.result.fixes.append("Created .env.example")
