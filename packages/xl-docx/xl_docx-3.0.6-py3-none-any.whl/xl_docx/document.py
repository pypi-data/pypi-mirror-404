from xl_docx.sheet import Sheet
from xl_docx.compiler import XMLCompiler
from pathlib import Path


class Document(Sheet):
    """Word表单对象，用于处理组件化的Word文档渲染"""

    def __init__(self, tpl_path, xml_folder=None, elements_folder=None):
        super().__init__(tpl_path, xml_folder)
        if elements_folder:
            self.elements_folder = elements_folder
    
    def _get_element_files(self):
        """获取所有组件XML文件"""
        if not self.elements_folder:
            return []
        return [f for f in Path(self.elements_folder).rglob('*.xml')]    

    def _read_element_file(self, filepath):
        """读取组件文件内容
        
        Args:
            filepath: 组件文件路径
            
        Returns:
            str: 组件文件内容
        """
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()


    def render_elements(self, data):
        elements = data.get('data', [])
        element_files = self._get_element_files() 
        template_xml = ''
        for item in elements:
            for filepath in element_files:
                element_type = filepath.stem
                element_content = self._read_element_file(filepath)
                if item.get('element') == element_type:
                    element_data = item.get('data')
                    element_content = self.process_components(element_content)
                    element_content = XMLCompiler.convert_syntax(element_content)
                    element_content = self.render_template(element_content, element_data, is_compile=False)
                    template_xml += element_content
        document_xml = self.get_xml_template('document')
        document_xml, xml_type = self._wrap_xml_template(document_xml, 'document')
        document_xml = self.render_template(document_xml, dict(document=template_xml))
        document_xml = XMLCompiler.compile_template(document_xml)
        document_xml = self.process_image_data(document_xml, 'document.xml')
        document_xml = self.process_header_footer(document_xml, data)
        self['word/document.xml'] = document_xml.encode('utf-8')

