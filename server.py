import subprocess
import os
import threading
import platform
import json
import sys

class Cancelled(Exception):
    pass


def get_nodejs_path():
    system = platform.system()    
    if system == "Windows":
        try:
            node_path = subprocess.check_output(["where", "node"]).decode().strip()
            if node_path:
                return node_path.split("\n")[0]
        except subprocess.CalledProcessError:
            return None
    elif system == "Linux":
        try:
            node_path = subprocess.check_output(["which", "node"]).decode().strip()
            if node_path:
                return node_path
        except subprocess.CalledProcessError:
            return None
    else:
        return None

    return None
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return ""
def run_node_program(nodepdth,node_script_path,argv=[]):
    def shuchu(a): 
        if(str(a).find("fkhides")==-1):
            print(a)            
    def _run_node_program():
        try:
            command = [nodepdth, node_script_path] 
            if argv:
                command.extend(argv)
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  
                text=True,  
                encoding='utf-8',  
                errors='replace' 
              )

            while True:
                output = process.stdout.readline().strip()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    shuchu(f"\33[93mFKServer: {output}\33[0m")

        
            error = process.stderr.read().strip()
            if error:
                shuchu(f"FKServer: {error}")

            if process.returncode!= 0:
                print(f"FKServer: {process.returncode}")

        except Exception as e:
            print(f"FKServer error occurred: {e}")

    thread = threading.Thread(target=_run_node_program)
    thread.start()
node_lujin = "node"
def setnev(nd):
    global node_lujin
    if nd:       
        system = platform.system() 
        current_path = os.environ.get('PATH', '')        
        nlijin = nd  # 初始化 nlijin 变量
        if system == "Windows":
            nlijin = nd.replace(f'\\node.exe',f'')            
            nlijin = nlijin.replace(f'/node.exe',f'')  
            os.environ["PATH"] = nlijin + ";" + current_path
        else:
            nlijin = nlijin.replace(f'/bin/node',f'/bin')            
            nlijin = nlijin.replace(f'\\bin/node',f'\\bin')
            os.environ["PATH"] = nlijin + ":" + current_path
        node_lujin = "node"
def string_2_json(json_string):
    try:
        json_object = json.loads(json_string)
        return json_object
    except json.JSONDecodeError as e:
        return None
def get_python_interpreter_path():
        return sys.executable
pzpath = os.path.join(os.path.dirname(__file__), 'ini.json')
pzdata = string_2_json(read_file(pzpath))
slkg = False
if pzdata:
    slkg = pzdata.get('slkg', False)
    if slkg==False or slkg=="false":
        node_lujin = get_nodejs_path()
        if(not node_lujin):
            ndpath = os.path.join(os.path.dirname(__file__), 'server/node.txt')
            node_lujin = read_file(ndpath)
            setnev(node_lujin)

        if (node_lujin):
            node_lujin = node_lujin.strip()
        else:   
            ndpath = os.path.join(os.path.dirname(__file__), 'server/node.txt')
            print(f'未检测到NodeJs，你可以在 {ndpath} 文件中写入node程序路径，手动配置NodeJs路径')
            node_lujin = ""

        if (node_lujin):
            serpath = os.path.join(os.path.dirname(__file__), 'server/')
            if (os.path.exists(serpath+'node_modules')==True):
                node_script_path = os.path.join(serpath, 'suanli.js')
                run_node_program(node_lujin,node_script_path)
                node_FKHTTP = os.path.join(serpath, 'fkhttp.js')
                run_node_program(node_lujin,node_FKHTTP,['--py',get_python_interpreter_path()])

            else:
                print(f'正在安装算力环境...')      
                os.chdir(serpath)
                result = subprocess.run('npm install --registry=https://registry.npmmirror.com', shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    node_script_path = os.path.join(serpath, 'suanli.js')
                    run_node_program(node_lujin,node_script_path)
                    node_FKHTTP = os.path.join(serpath, 'fkhttp.js')
                    run_node_program(node_lujin,node_FKHTTP,['--py',get_python_interpreter_path()])
                else:
                    print(f'算力环境自动安装失败：请在server目录下执行 npm install 命令安装算力环境')

        else:
            config_path = os.path.join(os.path.dirname(__file__), "server/data.json")
            try:
                os.remove(config_path)
            except Exception as e:
                pass
            print(f"系统未安装NodeJs，无法运行FKServer云算力环境")  