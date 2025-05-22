import os
import sys

# --- 路径设置 ---
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT_DIR)

# --- 导入 Flask 应用 ---
try:
    from api.index import app
except ImportError as e:
    print(f"[错误] 无法导入 Flask 应用。请确保 'api/index.py' 文件存在，")
    print(f"       并且其中有一个名为 'app' 的 Flask 应用实例。")
    print(f"       错误详情: {e}")
    sys.exit(1)

# --- 本地服务器配置 ---
HOST = "127.0.0.1"
PORT = 8000

# --- 主程序入口 ---
if __name__ == "__main__":
    print(f"--- 本地 Flask 测试服务器 ---")
    print(f"项目根目录: {PROJECT_ROOT_DIR}")

    # 确保 Markdown 目录存在 (这仍然是个好习惯，即使不创建文件)
    markdown_dir_v1 = os.path.join(PROJECT_ROOT_DIR, "markdown_files_v1")
    markdown_dir_v2 = os.path.join(PROJECT_ROOT_DIR, "markdown_files_v2")
    os.makedirs(markdown_dir_v1, exist_ok=True)
    os.makedirs(markdown_dir_v2, exist_ok=True)
    print(f"[INFO] 确保 'markdown_files_v1' 和 'markdown_files_v2' 目录存在。")
    print(f"[INFO] 请在这些目录中放置你的 .md 文件进行测试。")
    print(f"--------------------------------------------------")

    print(f"[INFO] 启动 Flask 开发服务器...")
    print(f"[INFO] Flask 应用 ('app') 从 'api.index' 模块加载。")
    print(f"[INFO] 服务器正在监听 http://{HOST}:{PORT}")
    print(f"[INFO] 你可以通过以下 URL 格式访问你的接口:")
    print(f"       V1接口: http://{HOST}:{PORT}/prompt/v1/api/markdown/<your_filename_in_v1_dir>")
    print(f"       V2接口: http://{HOST}:{PORT}/prompt/v2/api/markdown/<your_filename_in_v2_dir>")
    print(
        f"       (例如，如果 'markdown_files_v1' 中有 'example.md', 访问: http://{HOST}:{PORT}/prompt/v1/api/markdown/example )")
    print(f"[INFO] 按下 CTRL+C 停止服务器。")
    print(f"--------------------------------------------------")

    try:
        app.run(host=HOST, port=PORT, debug=True)
    except Exception as e:
        print(f"[错误] 启动 Flask 服务器失败: {e}")
    finally:
        print("\n[INFO] 服务器已关闭。")