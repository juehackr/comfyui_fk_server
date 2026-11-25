import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(BASE_DIR, "server")
NODE_TXT = os.path.join(SERVER_DIR, "node.txt")
PACKAGE_JSON = os.path.join(SERVER_DIR, "package.json")
NODE_MODULES = os.path.join(SERVER_DIR, "node_modules")
SR_JSON = os.path.join(SERVER_DIR, "sr.json")
INI_JSON = os.path.join(BASE_DIR, "ini.json")

NPM_REGISTRIES = ("https://registry.npmmirror.com", "https://registry.npmjs.org")
REQUIRED_MODULES = ("axios", "form-data", "pngjs", "qiniu", "socket.io-client", "ws", "mime-types")
INSTALL_TIMEOUT = 300
RETRY_DELAY = 10


class Cancelled(Exception):
    pass


def _log(message):
    print(f"\33[93mFKServer: {message}\33[0m", flush=True)


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            return file.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return ""


def string_2_json(json_string):
    try:
        return json.loads(json_string)
    except (TypeError, json.JSONDecodeError):
        return None


def get_python_interpreter_path():
    return sys.executable


def get_nodejs_path():
    found = shutil.which("node")
    if found:
        return found

    exe = "node.exe" if platform.system() == "Windows" else "node"
    candidates = []
    if platform.system() == "Windows":
        candidates.extend([
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", exe),
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "nodejs", exe),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", exe),
        ])
    else:
        candidates.extend([
            "/usr/local/bin/node",
            "/usr/bin/node",
            "/opt/homebrew/bin/node",
            "/opt/local/bin/node",
        ])
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


node_lujin = "node"


def setnev(node_path):
    global node_lujin
    if not node_path:
        return
    node_dir = os.path.dirname(node_path) if os.path.isfile(node_path) else node_path
    if not node_dir:
        return
    separator = ";" if platform.system() == "Windows" else ":"
    current_path = os.environ.get("PATH", "")
    if node_dir not in current_path.split(separator):
        os.environ["PATH"] = node_dir + separator + current_path
    node_lujin = "node"


def run_node_program(nodepdth, node_script_path, argv=[]):
    return _start_script(nodepdth, node_script_path, list(argv))


def _resolve_node():
    node_path = get_nodejs_path()
    configured = read_file(NODE_TXT).strip().strip('"\'').lstrip("\ufeff")
    if configured:
        path = configured
        if os.path.isdir(path):
            path = os.path.join(path, "node.exe" if platform.system() == "Windows" else "node")
        if os.path.isfile(path):
            setnev(path)
            return path
        if node_path:
            _log(f"node.txt 中配置的路径无效，改用系统 NodeJs：{configured}")
    return node_path


def _npm_path(node_path):
    found = shutil.which("npm")
    if found:
        return found
    names = ["npm.cmd", "npm.exe"] if platform.system() == "Windows" else ["npm"]
    for directory in filter(None, [os.path.dirname(node_path or "")]):
        for name in names:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate):
                return candidate
    return None


def _package_dependencies():
    data = string_2_json(read_file(PACKAGE_JSON))
    if isinstance(data, dict) and isinstance(data.get("dependencies"), dict):
        return list(data["dependencies"].keys())
    return []


def _missing_modules():
    required = list(REQUIRED_MODULES)
    for name in _package_dependencies():
        if name not in required:
            required.append(name)
    missing = []
    for name in required:
        module_path = os.path.join(NODE_MODULES, *name.split("/"))
        if not os.path.isdir(module_path):
            missing.append(name)
    return missing


def _run_npm(npm_path, args, registry):
    env = os.environ.copy()
    env["npm_config_registry"] = registry
    env["npm_config_fetch_retries"] = "2"
    env["npm_config_fetch_timeout"] = "60000"
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"

    if platform.system() == "Windows":
        command = f'"{npm_path}" ' + " ".join(args)
    else:
        command = [npm_path] + args

    try:
        result = subprocess.run(
            command,
            shell=platform.system() == "Windows",
            cwd=SERVER_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=INSTALL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        _log(f"npm install 超时（{registry}）")
        return False, ""
    except OSError as error:
        _log(f"npm install 无法执行：{error}")
        return False, ""

    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return result.returncode == 0, output


def _ensure_dependencies(node_path):
    missing = _missing_modules()
    if not missing:
        return True

    _log(f"检测到 NodeJs 依赖缺失：{', '.join(missing)}，正在自动安装...")
    npm_path = _npm_path(node_path)
    if not npm_path:
        _log("未找到 npm，请在 server 目录手动执行 npm install")
        return False

    install_args = ["install", "--no-audit", "--no-fund", "--loglevel=error", "--no-package-lock"]
    extra_args = install_args + ["--no-save"]
    last_output = ""

    for registry in NPM_REGISTRIES:
        ok, output = _run_npm(npm_path, install_args, registry)
        last_output = output or last_output
        if ok:
            still_missing = _missing_modules()
            if not still_missing:
                _log("NodeJs 依赖安装完成")
                return True
            ok, output = _run_npm(npm_path, extra_args + still_missing, registry)
            last_output = output or last_output
            if ok and not _missing_modules():
                _log("NodeJs 依赖安装完成")
                return True

    remaining = _missing_modules()
    _log(f"依赖自动安装失败，仍缺少：{', '.join(remaining)}")
    if last_output:
        tail = "\n".join(last_output.splitlines()[-8:])
        _log(f"npm 输出：{tail}")
    _log("请进入 server 目录手动执行：npm install")
    return False


def _ensure_sr_json():
    data = string_2_json(read_file(SR_JSON))
    if not isinstance(data, dict):
        data = {}
    if isinstance(data.get("qiniu"), dict):
        return True
    data["qiniu"] = {"appid": "", "appkey": "", "name": "", "url": "", "hz": ""}
    try:
        with open(SR_JSON, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        _log("已补齐 sr.json 的 qiniu 配置字段，避免上传服务启动失败")
        return True
    except OSError as error:
        _log(f"写入 sr.json 失败：{error}")
        return False


def _fkhttp_port():
    data = string_2_json(read_file(SR_JSON))
    if isinstance(data, dict):
        try:
            return int(data.get("PORT", 3059))
        except (TypeError, ValueError):
            pass
    return 3059


def _port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _run_node_once(node_path, script_path, argv, name):
    command = [node_path, script_path] + list(argv)
    process = subprocess.Popen(
        command,
        cwd=SERVER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    for line in process.stdout:
        text = line.strip()
        if text and "fkhides" not in text:
            _log(f"{name}: {text}")
    process.stdout.close()
    return process.wait()


def _supervise(node_path, script_path, argv, name):
    retries = 1
    while True:
        try:
            code = _run_node_once(node_path, script_path, argv, name)
        except OSError as error:
            _log(f"{name} 启动失败：{error}")
            code = -1

        if code == 0:
            _log(f"{name} 已退出")
            return
        if retries <= 0:
            _log(f"{name} 异常退出（代码 {code}），已停止重试")
            return
        retries -= 1
        _log(f"{name} 异常退出（代码 {code}），{RETRY_DELAY} 秒后重试一次")
        time.sleep(RETRY_DELAY)


def _start_script(node_path, script_path, argv=None, name=None):
    if not node_path:
        return None
    if not os.path.isfile(script_path):
        _log(f"未找到脚本 {script_path}，跳过启动")
        return None
    name = name or os.path.basename(script_path)
    thread = threading.Thread(
        target=_supervise,
        args=(node_path, script_path, list(argv or []), name),
        name=f"fk-{name}",
        daemon=True,
    )
    thread.start()
    return thread


def _bootstrap():
    time.sleep(1)
    try:
        if slkg:
            _log("设置中已关闭云算力功能，跳过启动")
            return

        if not isinstance(pzdata, dict):
            _log("未找到 ini.json，按默认配置启动算力环境")

        node_path = _resolve_node()
        if not node_path:
            _log(f"未检测到 NodeJs，可在 {NODE_TXT} 中写入 node 程序路径")
            return
        _log(f"NodeJs 路径：{node_path}")

        if not _ensure_dependencies(node_path):
            return

        _ensure_sr_json()

        _start_script(node_path, os.path.join(SERVER_DIR, "suanli.js"))

        port = _fkhttp_port()
        if _port_in_use(port):
            _log(f"端口 {port} 已被占用，跳过 fkhttp.js（可能是上一次运行残留）")
        else:
            _start_script(
                node_path,
                os.path.join(SERVER_DIR, "fkhttp.js"),
                ["--py", get_python_interpreter_path()],
            )
    except Exception as error:
        _log(f"云算力环境启动失败：{error}")


pzpath = INI_JSON
pzdata = string_2_json(read_file(pzpath))
slkg = False
if isinstance(pzdata, dict):
    slkg = str(pzdata.get("slkg", False)).strip().lower() in ("true", "1", "yes")

if __name__ != "__main__":
    threading.Thread(target=_bootstrap, name="fk-bootstrap", daemon=True).start()
