import importlib.metadata
import tomllib  # Python 3.11+, use tomli for older versions


def get_version():
    try:
        return importlib.metadata.metadata('mywatering-client')['Version']
    except (importlib.metadata.PackageNotFoundError, KeyError):
        try:
            with open("pyproject.toml", "rb") as f:
                pyproject_data = tomllib.load(f)
            return pyproject_data["project"]["version"]
        except Exception:
            return "unknown"


__version__ = get_version()
