from xl_docx.compiler.processors.table import TableProcessor


class TestHaha:
    def test_haha(self):
        xml = '''
              
        <xl-table width="9776" align="center" margin-left="0" border="single" grid="1487/2194/992/425/1276/284/992/2126">
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        报告编号
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc span="3" align="center">
                    <xl-p style="align:center">
                        记录编号
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        样品名称
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc span="3" align="center">
                    <xl-p style="align:center">
                        样品编号
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        型号规格
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc span="3" align="center">
                    <xl-p style="align:center">
                        出厂编号
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        生产厂家
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc span="3" align="center">
                    <xl-p style="align:center">
                        检测地点
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        环境条件
                    </xl-p>
                </xl-tc>
                <xl-tc span="7" align="center">
                    <xl-p style="align:center">
                        温度：（    ~    ）℃  湿度：（  ~  ）%RH
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center" merge="start">
                    <xl-p style="align:center">
                        所用设备
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center">
                        EQ019
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ121
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ122
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ127
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ128
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □无线温度记录仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ129
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.05.20
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:left;font-size:24">
                        □无线温压验证仪
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        EQ166
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center;font-size:24">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center;font-size:24">
                        2026.01.15
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:both;font-size:24">
                        □标准测试包
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                        管理编号
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center">
                        EQ203-2
                    </xl-p>
                </xl-tc>
                <xl-tc span="2" align="center">
                    <xl-p style="align:center">
                        有效日期
                    </xl-p>
                </xl-tc>
                <xl-tc align="center">
                    <xl-p style="align:center">
                        2027.06.30
                    </xl-p>
                </xl-tc>
            </xl-tr>
            <xl-tr align="center">
                <xl-tc align="center">
                    <xl-p style="align:center">
                        检测方法
                    </xl-p>
                </xl-tc>
                <xl-tc span="7" align="center">
                    <xl-p style="align:both;font-size:21">
                        ☑
                                                                                                                                                                                                                                                                                                                    GB 8599-2008《大型蒸汽灭菌器技术要求 自动控制型》
                    </xl-p>
                    <xl-p style="align:both;font-size:24">
                        ☑
                                                                                                                                                                                                                                                                                                                                                    WS 310.3-2016 《医院消毒供应中心第3部分：清洗消毒及灭菌效果监测标准》
                    </xl-p>
                </xl-tc>
            </xl-tr>
        </xl-table>
       

'''
        result = TableProcessor.compile(xml)
        print('result~~~~~~~~~~~~~~~~~~~~~~~~~~~~~', result)