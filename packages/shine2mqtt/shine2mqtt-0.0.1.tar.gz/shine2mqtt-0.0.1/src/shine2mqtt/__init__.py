from importlib.metadata import metadata, version
from pathlib import Path

__version__ = version(__name__)

PROJECT_URLS = dict(
    tuple(line.split(", ", 1)) for line in metadata(__name__).get_all("Project-URL", [])
)
HOME_PAGE = PROJECT_URLS.get("Homepage")

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
