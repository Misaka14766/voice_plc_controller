import re
from typing import Dict, Optional, Tuple, Any
from backend.config import settings

class TemplateMatcher:
    """基于物理名称映射的快速 PLC 操作"""

    def __init__(self, plc_instance):
        self.plc = plc_instance
        self.mappings = settings.mappings  # 从配置加载映射表
        self._build_patterns()

    def _build_patterns(self):
        """为每个物理名称构建正则表达式"""
        self.read_patterns = {}
        self.write_patterns = {}
        for physical_name, info in self.mappings.items():
            var = info['variable']
            vtype = info.get('type', 'REAL')
            # 读取：匹配 "读取 物理名" 或 "物理名 是多少" 等
            read_re = re.compile(
                rf"(?:读取|查看|查一下|告诉我)\s*{physical_name}|{physical_name}\s*(?:是多少|的值|多少了)",
                re.IGNORECASE
            )
            self.read_patterns[physical_name] = (read_re, var, vtype)
            # 写入：匹配 "设置 物理名 为 XXX" 或 "把 物理名 改成 XXX"
            write_re = re.compile(
                rf"(?:设置|把|将)\s*{physical_name}\s*(?:设为|设置为|改成|改为|设成)\s*(\S+)",
                re.IGNORECASE
            )
            self.write_patterns[physical_name] = (write_re, var, vtype)

    def match(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        尝试匹配模板，返回 (操作类型, 参数字典) 或 None
        """
        # 先尝试写入（更严格）
        for physical_name, (pattern, var, vtype) in self.write_patterns.items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                return ('write', {
                    'variable': var,
                    'type': vtype,
                    'value': value,
                    'physical_name': physical_name
                })
        # 再尝试读取
        for physical_name, (pattern, var, vtype) in self.read_patterns.items():
            if pattern.search(text):
                return ('read', {
                    'variable': var,
                    'type': vtype,
                    'physical_name': physical_name
                })
        return None

    def execute(self, op_type: str, params: Dict[str, Any]) -> str:
        """执行操作并返回结果描述文本"""
        var = params['variable']
        vtype = params['type']
        physical_name = params['physical_name']
        if op_type == 'read':
            try:
                val = self.plc.read(var, vtype)
                return f"{physical_name} 当前值为 {val}"
            except Exception as e:
                return f"读取 {physical_name} 失败：{e}"
        elif op_type == 'write':
            value_str = params['value']
            try:
                # 类型转换
                if vtype.upper() == 'BOOL':
                    val = value_str.lower() in ('true', '真', '开', '启动', '1')
                elif vtype.upper() == 'INT':
                    val = int(value_str)
                elif vtype.upper() == 'REAL':
                    val = float(value_str)
                else:
                    val = value_str
                self.plc.write(var, val, vtype)
                return f"已将 {physical_name} 设置为 {value_str}"
            except Exception as e:
                return f"设置 {physical_name} 失败：{e}"
        return ""