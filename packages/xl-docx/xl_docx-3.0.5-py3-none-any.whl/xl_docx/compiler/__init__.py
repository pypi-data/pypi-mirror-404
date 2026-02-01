from xl_docx.compiler.processors import StyleProcessor, DirectiveProcessor, \
TableProcessor, ParagraphProcessor, PagerProcessor
from xl_docx.mixins.component import ComponentMixin


class XMLCompiler:
    """XML编译器主类"""
    
    # 自定义语法映射到Jinja2语法
    SYNTAX_MAP = {
        r'($': '{%',
        r'$)': '%}', 
        r'((': '{{',
        r'))': '}}',
    }

    processors = [
        StyleProcessor(),
        DirectiveProcessor(), 
        TableProcessor(),
        ParagraphProcessor(),
        PagerProcessor(),
        ComponentMixin
    ]

    @classmethod
    def convert_syntax(cls, content: str) -> str:
        for custom, jinja in cls.SYNTAX_MAP.items():
            content = content.replace(custom, jinja)
        return content

    @classmethod
    def compile_template(cls, template: str) -> str:
        for processor in cls.processors:
            if hasattr(processor, 'compile'):
                template = processor.compile(template)
        
        template = cls.convert_syntax(template)
        
        return template
    
    @classmethod
    def decompile_template(cls, template: str) -> str:
        for processor in cls.processors:
            if hasattr(processor, 'decompile'):
                template = processor.decompile(template)
            
        return template
