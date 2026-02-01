from jinja2 import BaseLoader, TemplateNotFound, Environment


class XMLTemplateLoader(BaseLoader):
    def __init__(self, template_str: str):
        self.template_str = template_str

    def get_source(self, environment: Environment, template: str) -> tuple:
        if template == 'root':
            return self.template_str, None, lambda: True
        raise TemplateNotFound(template)

