import os
from flask import Flask, abort, Response

# --- 配置 ---
# Python 3.11+ 支持这些类型提示
BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
MARKDOWN_DIR_V1: str = os.path.join(BASE_DIR, "markdown_files_v1")
MARKDOWN_DIR_V2: str = os.path.join(BASE_DIR, "markdown_files_v2")

# --- Flask 应用 ---
app = Flask(__name__)

# --- 辅助函数 ---
def _read_markdown_file(directory: str, filename: str) -> str:
    """
    安全地读取指定目录下的 Markdown 文件内容。

    Args:
        directory: Markdown 文件所在的目录的绝对路径。
        filename:  要读取的文件名 (不含路径，但可以包含 .md 后缀)。

    Returns:
        文件的 Markdown 内容字符串。

    Raises:
        FileNotFoundError: 如果文件不存在或路径不安全。
        IOError: 如果读取文件时发生其他 IO 错误。
    """
    # 1. 安全性：确保文件名不包含路径遍历字符
    if ".." in filename or "/" in filename or "\\" in filename:
        app.logger.warning(f"Attempted path traversal: {filename}")
        raise FileNotFoundError("Invalid filename.")

    # 2. 确保是 .md 文件 (可选，但推荐)
    if not filename.lower().endswith(".md"):
        filename += ".md"

    # 3. 构建完整、安全的路径
    # os.path.join 会正确处理路径分隔符
    # os.path.abspath 会解析路径，消除 '..' 等，并给出绝对路径
    safe_filepath = os.path.abspath(os.path.join(directory, filename))

    # 4. 安全性：再次确认解析后的路径仍然在预期的目录下
    # 防止例如 filename 为 "../../../etc/passwd" 之类的情况 (虽然前面已部分处理)
    if not safe_filepath.startswith(directory):
        app.logger.error(f"Security alert: Path {safe_filepath} is outside of {directory}")
        raise FileNotFoundError("Access denied to the requested file.")

    # 5. 检查文件是否存在
    if not os.path.isfile(safe_filepath):
        app.logger.info(f"File not found: {safe_filepath}")
        raise FileNotFoundError(f"Markdown file '{filename}' not found.")

    # 6. 读取文件内容
    try:
        with open(safe_filepath, "r", encoding="utf-8") as f:
            content: str = f.read()
        return content
    except IOError as e:
        app.logger.error(f"Could not read file {safe_filepath}: {e}")
        raise IOError(f"Error reading file '{filename}'.")
    except Exception as e: # 捕获其他潜在错误
        app.logger.error(f"Unexpected error reading file {safe_filepath}: {e}")
        raise # 重新抛出，让上层处理或记录

# --- API 接口 ---

@app.route('/api/v1/doc/<string:filename>', methods=['GET'])
def get_markdown_v1(filename: str) -> Response | tuple[str, int]:
    """
    接口1: 从 markdown_files_v1 目录读取 Markdown 文件。
    访问: /api/v1/doc/example1  (会自动补全 .md)
          /api/v1/doc/another_page.md
    """
    try:
        markdown_content: str = _read_markdown_file(MARKDOWN_DIR_V1, filename)
        # 返回原始 Markdown 字符串，并设置正确的 Content-Type
        return Response(markdown_content, mimetype='text/markdown; charset=utf-8')
    except FileNotFoundError as e:
        abort(404, description=str(e))
    except IOError as e:
        abort(500, description=str(e))
    except Exception as e: # 捕获 _read_markdown_file 中未明确处理的异常
        app.logger.error(f"Unexpected error in get_markdown_v1 for {filename}: {e}")
        abort(500, description="An unexpected server error occurred.")


@app.route('/api/v2/note/intent/prompt', methods=['GET'])
def get_markdown_v2(filename: str) -> Response | tuple[str, int]:
    """
    接口2: 从 markdown_files_v2 目录读取 Markdown 文件。
    访问: /api/v2/note/notes
          /api/v2/note/tutorial.md
    """
    try:
        markdown_content: str = _read_markdown_file(MARKDOWN_DIR_V2, filename)
        return Response(markdown_content, mimetype='text/markdown; charset=utf-8')
    except FileNotFoundError as e:
        abort(404, description=str(e))
    except IOError as e:
        abort(500, description=str(e))
    except Exception as e:
        app.logger.error(f"Unexpected error in get_markdown_v2 for {filename}: {e}")
        abort(500, description="An unexpected server error occurred.")



# --- 应用启动 ---
if __name__ == '__main__':
    # 确保 Markdown 目录存在
    os.makedirs(MARKDOWN_DIR_V1, exist_ok=True)
    os.makedirs(MARKDOWN_DIR_V2, exist_ok=True)

    # 可以在这里添加一些默认文件创建逻辑，如果需要的话
    if not os.path.exists(os.path.join(MARKDOWN_DIR_V1, "example1.md")):
        with open(os.path.join(MARKDOWN_DIR_V1, "example1.md"), "w", encoding="utf-8") as f:
            f.write("# Default V1 Example\n\nThis is a default file for V1.")
    if not os.path.exists(os.path.join(MARKDOWN_DIR_V2, "notes.md")):
        with open(os.path.join(MARKDOWN_DIR_V2, "notes.md"), "w", encoding="utf-8") as f:
            f.write("# Default V2 Notes\n\nThis is a default file for V2.")

    app.run(debug=True, port=5000) # debug=True 方便开发，生产环境应设为 False