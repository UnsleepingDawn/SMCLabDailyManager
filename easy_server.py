from source_code.server import SMCLabServer, manage_server
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        manage_server(action)
    else:
        # 默认行为：直接运行
        server = SMCLabServer()
        server.main_loop()