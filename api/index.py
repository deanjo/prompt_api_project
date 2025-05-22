import os
import logging
from flask import Flask, Response, abort  # 导入 Flask, Response (用于自定义响应), abort (用于错误处理)

# --- 日志配置 ---
# Flask 有自己的 logger，可以通过 app.logger 访问
# logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO").upper()) # 也可以用标准 logging

# --- 配置 ---
PROJECT_ROOT: str = os.getcwd()  # 在 Vercel Serverless Function 中，这通常是项目根目录
MARKDOWN_BASE_DIRS = {
    "v1": os.path.join(PROJECT_ROOT, "markdown_files_v1"),
    "v2": os.path.join(PROJECT_ROOT, "markdown_files_v2"),
}

# --- Flask 应用实例 ---
# Vercel 会寻找一个名为 'app' 的 Flask (或 Sanic/FastAPI) 应用实例
app = Flask(__name__)


# --- 辅助函数 (_read_markdown_file) ---
# (这个函数的代码与你之前提供的版本完全相同，这里为了简洁省略，请直接复制过来)
# 你也可以将它放在一个单独的 utils.py 文件中然后导入，如果它变得复杂的话。
def _read_markdown_file(directory: str, filename_from_param: str) -> str:
    # ... (省略 _read_markdown_file 的完整代码，确保它在这里定义) ...
    # 确保这里的 logger 使用 app.logger 或者你配置的全局 logger
    # 例如: app.logger.warning(...) 或 logger.warning(...)
    if not filename_from_param or ".." in filename_from_param or "/" in filename_from_param or "\\" in filename_from_param:
        app.logger.warning(f"文件名参数中包含无效字符: {filename_from_param}")
        raise FileNotFoundError("无效的文件名.")  # Flask 会捕获这个

    actual_filename = filename_from_param
    if not actual_filename.lower().endswith(".md"):
        actual_filename += ".md"

    safe_filepath = os.path.abspath(os.path.join(directory, actual_filename))

    if not safe_filepath.startswith(os.path.abspath(directory)):
        app.logger.error(f"安全警报：路径 {safe_filepath} 超出了允许的目录 {directory}")
        raise FileNotFoundError("对请求文件的访问被拒绝。")

    if not os.path.isfile(safe_filepath):
        app.logger.info(f"文件未找到: {safe_filepath}")
        raise FileNotFoundError(f"在 {directory} 中未找到 Markdown 文件 '{actual_filename}'。")
    try:
        with open(safe_filepath, "r", encoding="utf-8") as f:
            content: str = f.read()
        return content
    except IOError as e:
        app.logger.error(f"无法读取文件 {safe_filepath}: {e}")
        raise IOError(f"读取文件 '{actual_filename}' 时出错。")  # 可以被 abort(500) 捕获
    except Exception as e:
        app.logger.error(f"读取文件 {safe_filepath} 时发生意外错误: {e}")
        raise  # 可以被 abort(500) 捕获


# --- API 接口定义 ---

@app.route("/prompt/v1/api/markdown/<string:filename>", methods=['GET'])  # Flask 的路由装饰器和路径参数语法
def get_markdown_v1(filename: str):  # Flask 处理函数是同步的
    """
    接口1: 从 markdown_files_v1 目录读取 Markdown 文件。
    """
    app.logger.info(f"V1 请求: filename='{filename}'")
    markdown_dir = MARKDOWN_BASE_DIRS.get("v1")

    if not markdown_dir or not os.path.isdir(markdown_dir):
        app.logger.error(f"V1 Markdown 目录配置错误或不存在: {markdown_dir}")
        abort(500, description="服务器配置错误 (V1 目录丢失)。")  # 使用 abort 发送 HTTP 错误

    try:
        markdown_content: str = _read_markdown_file(markdown_dir, filename)
        # 使用 Flask Response 对象返回文本内容，并设置 mimetype (Content-Type)
        return Response(markdown_content, mimetype='text/markdown; charset=utf-8')
    except FileNotFoundError as e:
        app.logger.warning(f"V1 文件未找到: {filename} - {e}")
        abort(404, description=str(e))  # Flask 的 404 错误
    except IOError as e:  # _read_markdown_file 中可能抛出
        app.logger.error(f"V1 读取文件时发生IO错误: {filename} - {e}")
        abort(500, description=f"读取文件时发生服务器内部错误。")
    except Exception as e:  # 捕获其他意外错误
        app.logger.error(f"V1 处理请求时发生未知错误: {filename} - {e}")
        abort(500, description="处理请求时发生意外的服务器错误。")


@app.route("/prompt/v2/api/markdown/<string:filename>", methods=['GET'])
def get_markdown_v2(filename: str):
    """
    接口2: 从 markdown_files_v2 目录读取 Markdown 文件。
    """
    app.logger.info(f"V2 请求: filename='{filename}'")
    markdown_dir = MARKDOWN_BASE_DIRS.get("v2")

    if not markdown_dir or not os.path.isdir(markdown_dir):
        app.logger.error(f"V2 Markdown 目录配置错误或不存在: {markdown_dir}")
        abort(500, description="服务器配置错误 (V2 目录丢失)。")

    try:
        markdown_content: str = _read_markdown_file(markdown_dir, filename)
        return Response(markdown_content, mimetype='text/markdown; charset=utf-8')
    except FileNotFoundError as e:
        app.logger.warning(f"V2 文件未找到: {filename} - {e}")
        abort(404, description=str(e))
    except IOError as e:
        app.logger.error(f"V2 读取文件时发生IO错误: {filename} - {e}")
        abort(500, description=f"读取文件时发生服务器内部错误。")
    except Exception as e:
        app.logger.error(f"V2 处理请求时发生未知错误: {filename} - {e}")
        abort(500, description="处理请求时发生意外的服务器错误。")

# 注意：当部署到 Vercel 时，你不需要 app.run()。
# Vercel 会使用 WSGI 接口 (例如通过 Gunicorn 或类似工具) 来运行你的 Flask 应用。
# 如果你想在本地直接运行这个文件进行测试 (不通过 Vercel CLI)：
# if __name__ == "__main__":
#     # 确保测试用的 Markdown 目录和文件存在
#     os.makedirs(MARKDOWN_BASE_DIRS["v1"], exist_ok=True)
#     os.makedirs(MARKDOWN_BASE_DIRS["v2"], exist_ok=True)
#     with open(os.path.join(MARKDOWN_BASE_DIRS["v1"], "localdev.md"), "w", encoding="utf-8") as f:
#         f.write("# Local Dev V1 Flask")
#     # Flask 开发服务器
#     app.run(host="0.0.0.0", port=8000, debug=True)