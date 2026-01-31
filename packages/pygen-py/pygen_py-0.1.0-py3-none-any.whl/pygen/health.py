import importlib

REQUIRED_MODULES = [
    "pygen.cli",
    "pygen.engine",
]

def run_health_check():
    results = {}
    status = "ok"

    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            results[mod] = "ok"
        except Exception as e:
            results[mod] = str(e)
            status = "failed"

    return status, results
