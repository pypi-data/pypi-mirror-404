import json
import os
import inspect
import traceback
import logging
from typing import Any, Dict, List, Optional
from sphinx.util.docstrings import prepare_docstring
from sphinx.application import Sphinx

# 设置日志记录器
logger = logging.getLogger(__name__)

# 为复杂类型创建简单别名
autodoc_type_aliases = {
    'Point': 'your_package.types.Point',
    'ImageType': 'typing.Union[np.ndarray, Image.Image]',
    'ResultDict': 'typing.Dict[str, typing.Any]'
}


class DocDataCollector:
    def __init__(self, app: Sphinx):
        self.app = app
        self.function_data = []
        # 确保我们有有效的 app 对象
        if not hasattr(app, 'config'):
            logger.error("Sphinx 应用程序对象无效，缺少 'config' 属性")

        # 注册清理处理程序
        app.connect('build-finished', self.save_data)

    def process_docstring(self, app: Sphinx, what: str, name: str, obj: Any,
                          options: Dict, lines: List[str]):
        """处理文档字符串"""
        try:
            # 只处理函数
            if what != 'function':
                return

            # 调试信息
            logger.info(f"处理函数: {name} (模块: {obj.__module__})")

            # 获取函数签名 - 更健壮的方式
            signature_str = self.get_function_signature(obj, name)

            # 解析文档字符串
            docstring = "\n".join(lines)
            parsed = self.parse_docstring(docstring)

            # 获取源码位置
            file_path, line_number = self.get_source_location(obj)

            # 添加到数据集合
            self.function_data.append({
                "name": name,
                "module": obj.__module__,
                "signature": signature_str,
                "doc": docstring,
                "params": parsed["params"],
                "returns": parsed["returns"],
                "examples": parsed["examples"],
                "notes": parsed["notes"],
                "warnings": parsed["warnings"],
                "file": file_path,
                "line": line_number
            })

        except Exception as e:
            error_msg = f"处理 {name} 时出错: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

    def get_function_signature(self, func: Any, func_name: str) -> str:
        """安全地获取函数签名"""
        try:
            # 尝试获取签名
            signature = inspect.signature(func)
            return str(signature)
        except (ValueError, TypeError, AttributeError):
            # 对于内置函数或其他无法获取签名的对象
            return f"{func_name}(...)"
        except Exception as e:
            logger.error(f"获取函数签名失败: {str(e)}")
            return f"{func_name}(...)"

    def get_source_location(self, obj: Any) -> tuple:
        """安全地获取源码位置"""
        try:
            file_path = inspect.getfile(obj)
            try:
                line_number = inspect.getsourcelines(obj)[1]
            except IndexError:
                line_number = 0
            return file_path, line_number
        except (TypeError, OSError, AttributeError):
            return "unknown", 0
        except Exception as e:
            logger.error(f"获取源码位置失败: {str(e)}")
            return "unknown", 0

    def parse_docstring(self, docstring: str) -> Dict[str, Any]:
        """解析文档字符串结构 - 更健壮的实现"""
        params = {}
        returns = None
        examples = []
        notes = []
        warnings = []

        # 处理空文档字符串
        if not docstring:
            return {
                "params": params,
                "returns": returns,
                "examples": examples,
                "notes": notes,
                "warnings": warnings
            }

        # 准备文档字符串
        try:
            doc_lines = prepare_docstring(docstring)
        except Exception:
            doc_lines = docstring.splitlines()

        # 按行处理
        current_section = None
        for line in doc_lines:
            line = line.rstrip()
            if not line:
                continue

            # 参数部分
            if line.startswith(':param'):
                parts = line.split(':', 2)
                if len(parts) > 2:
                    param_name = parts[1].strip().split()[0]
                    param_desc = parts[2].strip()
                    params[param_name] = param_desc
                current_section = 'param'

            # 返回值部分
            elif line.startswith(':return:'):
                returns = line.split(':', 1)[1].strip()
                current_section = 'return'

            # 警告部分
            elif line.startswith('.. warning::'):
                warning_text = line.split('::', 1)[1].strip() if '::' in line else ""
                warnings.append(warning_text)
                current_section = 'warning'

            # 注意部分
            elif line.startswith('.. note::'):
                note_text = line.split('::', 1)[1].strip() if '::' in line else ""
                notes.append(note_text)
                current_section = 'note'

            # 示例部分
            elif line.lower().startswith('example:') or line.lower().startswith('examples:'):
                current_section = 'example'

            # 示例代码
            elif current_section == 'example' and line.strip():
                examples.append(line.strip())

            # 处理多行内容
            elif current_section and line:
                if current_section == 'warning' and warnings:
                    warnings[-1] += "\n" + line
                elif current_section == 'note' and notes:
                    notes[-1] += "\n" + line
                elif current_section == 'example' and examples:
                    examples[-1] += "\n" + line

        return {
            "params": params,
            "returns": returns,
            "examples": examples,
            "notes": notes,
            "warnings": warnings
        }

    def save_data(self, app: Sphinx, exception: Optional[Exception] = None):
        """保存数据到文件"""
        if exception:
            logger.error(f"构建失败: {str(exception)}")
            return

        try:
            # 确保输出目录存在
            outdir = app.outdir
            if not os.path.exists(outdir):
                os.makedirs(outdir, exist_ok=True)
                logger.info(f"创建输出目录: {outdir}")

            output_path = os.path.join(outdir, 'api_data.json')

            # 写入数据
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.function_data, f, indent=2, ensure_ascii=False)

            logger.info(f"成功保存 API 数据到: {output_path}")
            logger.info(f"共收集 {len(self.function_data)} 个函数文档")

            # 如果数据为空，打印警告
            if not self.function_data:
                logger.warning("收集的函数文档为空！请检查以下可能的原因：")
                logger.warning("1. 确保在 conf.py 中正确配置了 autodoc 扩展")
                logger.warning("2. 确认您的代码中有带文档字符串的函数")
                logger.warning("3. 检查 Sphinx 是否能够导入您的模块")
                logger.warning("4. 确保在 index.rst 中包含了您的模块")

        except Exception as e:
            logger.error(f"保存 API 数据失败: {str(e)}")
            logger.debug(traceback.format_exc())


def setup(app: Sphinx):
    """Sphinx 扩展入口"""
    # 配置日志
    if not hasattr(app, 'logger'):
        # 为旧版本 Sphinx 创建简单日志器
        class SimpleLogger:
            def info(self, msg): print(f"[INFO] {msg}")

            def warning(self, msg): print(f"[WARN] {msg}")

            def error(self, msg): print(f"[ERROR] {msg}")

            def debug(self, msg): pass  # 调试信息不打印

        logger = SimpleLogger()
    else:
        # 使用 Sphinx 的日志系统
        logger = app.logger

    # 创建收集器
    collector = DocDataCollector(app)

    # 连接文档处理事件
    app.connect('autodoc-process-docstring', collector.process_docstring)

    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'env_version': 1
    }