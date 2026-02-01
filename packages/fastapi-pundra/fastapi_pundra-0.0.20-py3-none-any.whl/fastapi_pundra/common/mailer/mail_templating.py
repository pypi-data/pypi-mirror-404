import jinja2
import warnings
from os import PathLike
from .inline_css import inline_css

try:
    import jinja2
except ModuleNotFoundError:
    jinja2 = None


class EmailTemplates:
    def __init__(
        self,
        directory,
        *,
        context_processors=None,
        env=None,
        **env_options
    ):
        assert jinja2 is not None, "jinja2 must be installed to use EmailTemplates"
        assert directory or env, "either 'directory' or 'env' arguments must be passed"
        self.context_processors = context_processors or []
        if directory is not None:
            self.env = self._create_env(directory, **env_options)
        elif env is not None:
            self.env = env

        self._setup_env_defaults(self.env)

    def _create_env(
        self,
        directory,
        **env_options
    ):
        loader = jinja2.FileSystemLoader(directory)
        env_options.setdefault("loader", loader)
        env_options.setdefault("autoescape", True)

        return jinja2.Environment(**env_options)

    def _setup_env_defaults(self, env):
        pass

    def get_template(self, name):
        return self.env.get_template(name)

    def render_template(
        self,
        name,
        context=None,
    ):
        context = context or {}
        for context_processor in self.context_processors:
            context.update(context_processor())

        template = self.get_template(name)
        a =  template.render(**context)
        return inline_css(a)