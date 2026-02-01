from xl_docx.word_file import WordFile
from xl_docx.compiler import XMLCompiler
from xl_docx.loader import XMLTemplateLoader
from xl_docx.mixins.component import ComponentMixin
from jinja2 import Environment
from pathlib import Path
import math 
import re


class Sheet(WordFile, ComponentMixin):
    """Word表单对象，用于处理Word模板文件的渲染和XML操作"""
    components_folder = None

    TEMPLATE_FUNCTIONS = {
        'enumerate': enumerate,
        'len': len, 
        'isinstance': isinstance,
        'tuple': tuple,
        'list': list,
        'str': str,
        'float': float,
        'int': int,
        'range': range,
        'ceil': math.ceil,
        'type': type,
        'min': min,
        'max': max
    }

    def __init__(self, tpl_path, xml_folder=None):
        """初始化Sheet对象
        
        Args:
            tpl_path: Word模板文件路径
            xml_folder: 可选的XML模板文件夹路径
        """
        super().__init__(tpl_path)
        self.xml_folder = xml_folder
        # 初始化组件缓存
        self._load_all_components(self.components_folder)


    def render_template(self, template_content, data, is_compile=True):
        """渲染Jinja2模板
        
        Args:
            template_content: 模板内容字符串
            data: 用于渲染的数据字典
            is_compile: 是否编译模板
            
        Returns:
            str: 渲染后的内容
        """
        # 合并数据字典和模板函数
        render_data = {
            **data,
            **self.TEMPLATE_FUNCTIONS
        }
        
        # 如果需要编译，先编译模板
        if is_compile:
            processed_template = XMLCompiler.compile_template(template_content)
        else:
            processed_template = template_content
        
        # 创建Jinja2环境并渲染模板
        env = Environment(
            loader=XMLTemplateLoader(processed_template),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        template = env.get_template('root')
        rendered = template.render(**render_data)
        
        return rendered.replace(' & ', ' &amp; ')


    def get_xml_template(self, xml_filename, use_internal_template=False):
        """获取XML模板内容
        
        Args:
            xml_filename: XML文件名(不含扩展名)
            
        Returns:
            str: XML模板内容
        """
        if use_internal_template:
            return self._read_internal_template(xml_filename)
        if self.xml_folder:
            xml_path = Path(self.xml_folder) / f'{xml_filename}.xml'
            return self._read_external_template(xml_path)
        return self._read_internal_template(xml_filename)

    def _read_external_template(self, xml_path):
        """读取外部XML模板文件
        
        Args:
            xml_path: XML文件完整路径
            
        Returns:
            str: XML文件内容
        """
        with open(xml_path, 'r', encoding='utf-8') as file:
            return file.read()

    def _read_internal_template(self, xml_filename):
        """读取Word文档内部的XML模板
        
        Args:
            xml_filename: XML文件名
            
        Returns:
            str: XML文件内容
        """
        return self[f'word/{xml_filename}.xml'].decode()

    def download_file_as_bytes(self, uri):
        """下载文件为字节数据 - 待实现的方法
        
        Args:
            uri: 文件URI
            
        Returns:
            bytes: 文件字节数据
            
        Raises:
            NotImplementedError: 此方法需要子类实现
        """
        raise NotImplementedError("download_file_as_bytes方法需要在子类中实现")

    def process_image_data(self, xml_string, xml_file):
        """处理XML字符串中的图片数据

        Args:
            xml_string: 渲染后的XML字符串
            xml_filename: XML文件名

        Returns:
            str: 处理后的XML字符串
        """
        # 匹配包含 r:id 属性的 v:imagedata 标签，r:id 可以在任意位置
        # 支持自闭合标签 (<v:imagedata ... />) 和非自闭合标签 (<v:imagedata ...></v:imagedata>)
        pattern = r'(<v:imagedata\s+[^>]*?r:id="([^"]+)"[^>]*?(?:\s*/>|>.*?</v:imagedata>))'
        matches = re.findall(pattern, xml_string)

        for full_match, uri in matches:
            if '/' in uri:
                try:
                    image_bytes = self.download_file_as_bytes(uri)
                    image_rid = self.add_image(image_bytes, xml_file=xml_file)

                    # 检查是否为自闭合标签
                    is_self_closing = full_match.rstrip().endswith('/>')

                    # 提取并保留所有其他属性
                    # 移除 r:id 属性，保留其他所有属性
                    # 匹配属性名（支持命名空间前缀如 o:title）和属性值
                    attrs_pattern = r'([\w:]+)\s*=\s*"([^"]+)"'
                    all_attrs = re.findall(attrs_pattern, full_match)

                    # 构建新的属性字符串，排除旧的 r:id，添加新的 r:id
                    preserved_attrs = []
                    for attr_name, attr_value in all_attrs:
                        if attr_name != 'r:id':
                            preserved_attrs.append(f'{attr_name}="{attr_value}"')

                    # 构建新的标签，保留所有属性并更新 r:id，保持原始格式
                    if preserved_attrs:
                        attrs_str = ' ' + ' '.join(preserved_attrs) + ' '
                        if is_self_closing:
                            new_replacement = f'<v:imagedata{attrs_str}r:id="{image_rid}"/>'
                        else:
                            new_replacement = f'<v:imagedata{attrs_str}r:id="{image_rid}"></v:imagedata>'
                    else:
                        if is_self_closing:
                            new_replacement = f'<v:imagedata r:id="{image_rid}"/>'
                        else:
                            new_replacement = f'<v:imagedata r:id="{image_rid}"></v:imagedata>'

                    xml_string = xml_string.replace(full_match, new_replacement)

                except Exception as e:
                    print(f"处理图片 {uri} 时出错: {e}")
                    # 如果处理失败，找到包含此 imagedata 的完整 pict 标签并移除
                    # 使用非贪婪模式匹配 <w:pict> 标签及其内容
                    pict_pattern = r'(<w:pict\b[^>]*?>.*?</w:pict>|<w:pict\b[^>]*/>)'
                    # 在上下文中查找包含当前 imagedata 的 pict 标签
                    pict_match = re.search(pict_pattern, xml_string)
                    if pict_match:
                        # 检查这个 pict 标签是否包含当前的 imagedata
                        if full_match in pict_match.group(0):
                            # 移除整个 pict 标签
                            xml_string = xml_string.replace(pict_match.group(0), '')

        return xml_string

    def process_header_footer(self, xml_string, data):
        """处理XML字符串中的xl-header和xl-footer标签
        
        Args:
            xml_string: 渲染后的XML字符串
            data: 渲染数据字典
            
        Returns:
            str: 处理后的XML字符串
        """
        # 处理 xl-header 标签（支持自闭合和带结束标签）
        header_pattern = r'<xl-header\s+([^>]*?)(?:\s*/>|>.*?</xl-header>)'
        
        def process_header(match):
            attrs_str = match.group(1)
            # 提取属性
            template_match = re.search(r'template="([^"]+)"', attrs_str)
            key_match = re.search(r'key="([^"]+)"', attrs_str)
            type_match = re.search(r'type="([^"]+)"', attrs_str)
            
            if not template_match:
                # 如果缺少template属性，保持原样
                return match.group(0)
            
            template = template_match.group(1)
            header_type = type_match.group(1) if type_match else 'default'
            
            # 获取数据：如果key不存在，使用整个data
            if key_match:
                key = key_match.group(1)
                header_data = data.get(key, {})
            else:
                header_data = data
            
            try:
                # 渲染并添加header
                rid = self.render_and_add_xml(template, header_data)
                # 替换为 w:headerReference
                return f'<w:headerReference w:type="{header_type}" r:id="{rid}"/>'
            except Exception as e:
                print(f"处理header {template} 时出错: {e}")
                # 如果处理失败，保持原样
                return match.group(0)
        
        xml_string = re.sub(header_pattern, process_header, xml_string)
        
        # 处理 xl-footer 标签（支持自闭合和带结束标签）
        footer_pattern = r'<xl-footer\s+([^>]*?)(?:\s*/>|>.*?</xl-footer>)'
        
        def process_footer(match):
            attrs_str = match.group(1)
            # 提取属性
            template_match = re.search(r'template="([^"]+)"', attrs_str)
            key_match = re.search(r'key="([^"]+)"', attrs_str)
            type_match = re.search(r'type="([^"]+)"', attrs_str)
            
            if not template_match:
                # 如果缺少template属性，保持原样
                return match.group(0)
            
            template = template_match.group(1)
            footer_type = type_match.group(1) if type_match else 'default'
            
            # 获取数据：如果key不存在，使用整个data
            if key_match:
                key = key_match.group(1)
                footer_data = data.get(key, {})
            else:
                footer_data = data
            
            try:
                # 渲染并添加footer
                rid = self.render_and_add_xml(template, footer_data)
                # 替换为 w:footerReference
                return f'<w:footerReference w:type="{footer_type}" r:id="{rid}"/>'
            except Exception as e:
                print(f"处理footer {template} 时出错: {e}")
                # 如果处理失败，保持原样
                return match.group(0)
        
        xml_string = re.sub(footer_pattern, process_footer, xml_string)
        
        return xml_string

    def _wrap_xml_template(self, xml_template, xml_filename):
        """根据XML文件名类型包装XML模板
        
        Args:
            xml_template: XML模板内容
            xml_filename: XML文件名
            
        Returns:
            tuple: (包装后的xml_template, xml_type)
        """
        # 如果xml_filename包含"header"，检查是否需要包装w:hdr标签
        if "header" in xml_filename:
            xml_type = 'header'
            # 检查是否已经包含w:hdr标签
            if "<w:hdr" not in xml_template:
                # 包装在完整的Word header结构中
                word_header_wrapper = '''<w:hdr mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
{content}
</w:hdr>'''
                xml_template = word_header_wrapper.format(content=xml_template)
        
        # 如果xml_filename包含"footer"，检查是否需要包装w:ftr标签
        elif "footer" in xml_filename:
            xml_type = 'footer'
            # 检查是否已经包含w:ftr标签
            if "<w:ftr" not in xml_template:
                # 包装在完整的Word footer结构中
                word_footer_wrapper = '''<w:ftr mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
{content}
</w:ftr>'''
                xml_template = word_footer_wrapper.format(content=xml_template)
        
        # 如果xml_filename包含"document"，检查是否需要包装w:document标签
        else:
            xml_type = 'document'
            # 检查是否已经包含w:document标签
            if "<w:document" not in xml_template:
                # 包装在完整的Word文档结构中
                word_document_wrapper = '''<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14">
<w:body>
{content}
</w:body>
</w:document>'''
                xml_template = word_document_wrapper.format(content=xml_template)
        
        return xml_template, xml_type


    def render_xml(self, xml_filename, data, use_internal_template=False):
        self.register_img()
        try:
            xml_template = self.get_xml_template(xml_filename, use_internal_template=use_internal_template)
            
            xml_template, xml_type = self._wrap_xml_template(xml_template, xml_filename)
            
            xml_template = self.process_components(xml_template)
            xml_content = self.render_template(xml_template, data)
            
            xml_content = self.process_image_data(xml_content, f'{xml_filename}.xml')
            
            if xml_filename == 'document':
                xml_content = self.process_header_footer(xml_content, data)
            
            xml_bytes = xml_content.encode()
            self[f'word/{xml_filename}.xml'] = xml_bytes
            return xml_bytes
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except Exception as e:
            raise e
            print(f"An error occurred: {e}")

    def render_and_add_xml(self, xml_file, data, relation_id=None, use_internal_template=False):
        """渲染并添加新的XML文件到文档
        
        Args:
            xml_file: XML文件名
            data: 渲染数据
            relation_id: 可选的关系ID
            use_internal_template: 是否使用内部模板
            
        Returns:
            str: 生成的关系ID
        """
        xml_template = self.get_xml_template(xml_file, use_internal_template=use_internal_template)
        xml_template, xml_type = self._wrap_xml_template(xml_template, xml_file)
        xml_template = self.process_components(xml_template)
        xml_content = self.render_template(xml_template, data)
        
        xml_id = relation_id or self._generate_random_id()
        xml_filename = f'{xml_type}{xml_id}'
        xml_file = f'{xml_filename}.xml'
        self[f'word/{xml_file}'] = self.process_image_data(xml_content, xml_file)
        self.append_relation('document.xml', xml_type, xml_file, xml_id)
        self.register_xml(xml_type, xml_file)
        return f'rId{xml_id}'
    
