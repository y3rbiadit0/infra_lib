from pathlib import Path
from typing import Callable, Dict, Optional
from jinja2 import Environment as JinjaEnvironment

from .header import DefaultHeaderGenerator, HeaderGenerator

class TemplateFile:
    def __init__(
        self,
        source: Path,
        target: Path,
        context_provider: Optional[Callable[[], Dict]] = None,
        header_generator: Optional[HeaderGenerator] = DefaultHeaderGenerator(),
    ):
        """
        Args:
            source: Path to template (may be .j2 or plain file)
            target: Path where the file should be written
            context_provider: Function returning context dict for rendering (if None → copy raw)
        """
        self.source = source
        self.target = target
        self.context_provider = context_provider
        self.header_generator = header_generator

    def generate(self, jinja_env: JinjaEnvironment):
        if self.source.suffix == ".j2":
            relative_path = self.source.relative_to(jinja_env.loader.searchpath[0])
            template = jinja_env.get_template(str(relative_path).replace("\\", "/"))
            context = self.context_provider() if self.context_provider else {}
            content = template.render(context)
        else:
            content = self.source.read_text()

        if self.header_generator:
            content = self.header_generator.generate_header(self.target) + content


        self.target.write_text(content)
