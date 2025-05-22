import os
import sys
from http.server import HTTPServer

# --- 路径设置 ---
# 获取当前测试脚本所在的目录的绝对路径。
# 假设 local_http_test_server.py 位于项目的根目录下。
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 将项目根目录添加到 Python 的模块搜索路径中。
sys.path.insert(0, PROJECT_ROOT_DIR)

# 导入我们的 MarkdownHandler
# 我们需要确保 markdown_handler.py 中的 PROJECT_ROOT 和 MARKDOWN_BASE_DIRS
# 在这种本地服务器运行时也能正确指向。
# 通常，如果 markdown_handler.py 使用 os.getcwd() 并且这个脚本从项目根目录运行，
# 路径应该是正确的。
from api.markdown_handler import handler as MarkdownHandler  # 导入我们为 Vercel 编写的 handler

# --- 本地 HTTP 服务器配置 ---
HOST_NAME = "127.0.0.1"  # 服务器主机名
SERVER_PORT = 8000  # 服务器端口号


class LocalTestServer(HTTPServer):
    """
    一个简单的 HTTP 服务器，使用我们自定义的 MarkdownHandler。
    """

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        print(f"[INFO] LocalTestServer: 初始化完成。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 确保测试用的 Markdown 目录和文件存在 (与 unittest 版本中的 setUpClass 类似)
    # 这样服务器启动时，handler 就能找到文件。
    markdown_dir_v1 = os.path.join(PROJECT_ROOT_DIR, "markdown_files_v1")
    markdown_dir_v2 = os.path.join(PROJECT_ROOT_DIR, "markdown_files_v2")

    os.makedirs(markdown_dir_v1, exist_ok=True)
    os.makedirs(markdown_dir_v2, exist_ok=True)

    # 创建一些示例文件供测试
    with open(os.path.join(markdown_dir_v1, "local_test_v1.md"), "w", encoding="utf-8") as f:
        f.write("# Local V1 Test File\nThis is for local HTTP server testing (V1).")
    with open(os.path.join(markdown_dir_v2, "local_test_v2.md"), "w", encoding="utf-8") as f:
        f.write("# Local V2 Test File\nThis is for local HTTP server testing (V2).")

    print(f"--- 本地 HTTP 测试服务器 ---")
    print(f"项目根目录: {PROJECT_ROOT_DIR}")
    print(f"V1 Markdown 目录: {markdown_dir_v1}")
    print(f"V2 Markdown 目录: {markdown_dir_v2}")
    print(f"确保 'api/markdown_handler.py' 中的路径是相对于项目根目录的。")

    # 创建 HTTP 服务器实例，指定主机、端口和我们的请求处理程序类
    httpd = LocalTestServer((HOST_NAME, SERVER_PORT), MarkdownHandler)
    print(f"[INFO] 服务器已启动，监听 http://{HOST_NAME}:{SERVER_PORT}")
    print(f"[INFO] 你需要手动构造包含查询参数的 URL 来测试，例如:")
    print(f"       http://{HOST_NAME}:{SERVER_PORT}/?version=v1&type=markdown&filename=local_test_v1")
    print(f"       http://{HOST_NAME}:{SERVER_PORT}/?version=v2&type=markdown&filename=local_test_v2")
    print(f"[INFO] 按下 CTRL+C 停止服务器。")

    try:
        # 永久运行服务器，直到手动停止 (例如 CTRL+C)
        httpd.serve_forever()
    except KeyboardInterrupt:
        # 当用户按下 CTRL+C 时，捕获 KeyboardInterrupt 异常
        print("\n[INFO] 用户请求停止服务器...")
    finally:
        # 关闭服务器
        httpd.server_close()
        print("[INFO] 服务器已成功关闭。")

        # (可选) 清理测试文件
        # files_to_delete = [
        #     os.path.join(markdown_dir_v1, "local_test_v1.md"),
        #     os.path.join(markdown_dir_v2, "local_test_v2.md"),
        # ]
        # for file_path in files_to_delete:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        #         print(f"[INFO] 已删除测试文件: {file_path}")