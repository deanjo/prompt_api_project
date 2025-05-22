import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper())

PROJECT_ROOT: str = os.getcwd()
# 修改 MARKDOWN_BASE_DIRS 的键以匹配新的逻辑
# key 将是 "v1_markdown" 和 "v2_markdown"
MARKDOWN_BASE_DIRS = {
    "v1_markdown": os.path.join(PROJECT_ROOT, "markdown_files_v1"),  # 假设 v1 对应 markdown_files_v1
    "v2_markdown": os.path.join(PROJECT_ROOT, "markdown_files_v2"),  # 假设 v2 对应 markdown_files_v2
}


# _read_markdown_file 函数保持不变，因为它只关心目录和文件名
def _read_markdown_file(directory: str, filename_from_param: str) -> str:
    if not filename_from_param or ".." in filename_from_param or "/" in filename_from_param or "\\" in filename_from_param:
        logger.warning(f"文件名参数中包含无效字符: {filename_from_param}")
        raise FileNotFoundError("无效的文件名。")

    actual_filename = filename_from_param
    if not actual_filename.lower().endswith(".md"):
        actual_filename += ".md"

    safe_filepath = os.path.abspath(os.path.join(directory, actual_filename))

    if not safe_filepath.startswith(os.path.abspath(directory)):
        logger.error(f"安全警报：路径 {safe_filepath} 超出了允许的目录 {directory}")
        raise FileNotFoundError("对请求文件的访问被拒绝。")

    if not os.path.isfile(safe_filepath):
        logger.info(f"文件未找到: {safe_filepath}")
        raise FileNotFoundError(f"在 {directory} 中未找到 Markdown 文件 '{actual_filename}'。")

    try:
        with open(safe_filepath, "r", encoding="utf-8") as f:
            content: str = f.read()
        return content
    except IOError as e:
        logger.error(f"无法读取文件 {safe_filepath}: {e}")
        raise IOError(f"读取文件 '{actual_filename}' 时出错。")
    except Exception as e:
        logger.error(f"读取文件 {safe_filepath} 时发生意外错误: {e}")
        raise


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        version = query_params.get('version', [None])[0]
        doc_type = query_params.get('type', [None])[0]  # 这个会从 vercel.json 中得到 "markdown"
        filename = query_params.get('filename', [None])[0]

        if not all([version, doc_type, filename]):
            self.send_error(400, "请求参数不完整 (需要 version, type, filename)。")
            return

        # 根据 version 和固定的 type="markdown" 确定正确的 Markdown 目录
        dir_key = f"{version}_{doc_type}"  # 例如 "v1_markdown" 或 "v2_markdown"
        markdown_dir = MARKDOWN_BASE_DIRS.get(dir_key)

        if not markdown_dir:
            logger.error(f"未知的版本/类型组合: {dir_key}")
            self.send_error(400, f"不支持的版本/类型组合: {version}/{doc_type}")
            return

        if not os.path.isdir(markdown_dir):  # 确保目标目录实际存在
            logger.error(f"Markdown 目录不存在: {markdown_dir}")
            self.send_error(500, "服务器配置错误：Markdown 目录丢失。")
            return

        try:
            logger.info(f"尝试从 {markdown_dir} 读取: {filename} (请求版本: {version}, 类型: {doc_type})")
            markdown_content: str = _read_markdown_file(markdown_dir, filename)

            self.send_response(200)
            self.send_header('Content-type', 'text/markdown; charset=utf-8')
            self.end_headers()
            self.wfile.write(markdown_content.encode('utf-8'))
        except FileNotFoundError as e:
            logger.warning(f"文件未找到: {filename} 在 {markdown_dir} - {e}")
            self.send_error(404, str(e))
        except IOError as e:
            logger.error(f"IOError: {filename} 在 {markdown_dir} - {e}")
            self.send_error(500, str(e))
        except Exception as e:
            logger.error(f"处理 {filename} (位于 {markdown_dir}) 时发生意外错误: {e}")
            self.send_error(500, "服务器发生意外错误。")
        return