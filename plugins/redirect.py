import logging
from pathlib import Path

from jinja2 import BaseLoader, Environment
from pelican import signals
from pelican.generators import Generator

logger = logging.getLogger(__name__)

template = Environment(loader=BaseLoader()).from_string(
    """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8" />
            <meta http-equiv="refresh" content="0;url={{ destination }}" />
        </head>
    </html>
    """
)


class RedirectGenerator(Generator):

    def generate_output(self, writer):
        redirects_file = (
            Path(self.settings["PATH"]) / self.settings["DATA_DIR"] / "redirects.txt"
        )
        # If a redirects file doesn't exist, exit so that the site can be built without it
        if not redirects_file.exists():
            return

        with open(redirects_file) as f:
            redirects = f.readlines()

        for line in redirects:
            line = line.strip()
            # Skip blank lines, treat lines beginning with `#` as comments
            if not line or line.startswith("#"):
                continue

            # TODO: Currently, destination is intended to be used as a standard
            # path. Future releases of Pelican support a semi-public API that
            # helps with the URL lookup of tags by name, pages by file path, etc.
            # This may be worth supporting in a future version of this plugin.
            source, destination = line.split()

            # Only support redirecting to on-site, root-level paths (for now)
            if not destination.startswith("/"):
                logger.warn(f"Not generating unsupported redirect to {destination}")
                continue

            source_path = Path(source)
            if source_path.suffix:
                source_file = source_path.name
                source_path = source_path.parent
            else:
                source_file = "index.html"

            output_directory = Path(self.output_path) / str(source_path).lstrip("/")
            output_directory.mkdir(parents=True, exist_ok=True)
            with open(output_directory / source_file, "w") as f:
                f.write(template.render({"destination": destination}))


def get_generators(generators):
    return RedirectGenerator


def register():
    signals.get_generators.connect(get_generators)

