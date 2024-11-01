import subprocess
import os
import threading

class Cancelled(Exception):
    pass

def run_node_program(node_script_path):
    def shuchu(a): 
        if(str(a).find("fkhides")==-1):
            print(a)            
    def _run_node_program():
        try:
            command = ['node', node_script_path]        
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


def is_node_installed():
    try:
        result = subprocess.run(['node', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:        
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
 
if (is_node_installed()):
    serpath = os.path.join(os.path.dirname(__file__), 'server/')
    if (os.path.exists(serpath+'node_modules')==True):
        node_script_path = os.path.join(serpath, 'suanli.js')
        run_node_program(node_script_path)
    else:
        print('正在安装算力环境...')      
        os.chdir(serpath)
        result = subprocess.run('npm install --registry=https://registry.npmmirror.com', shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            node_script_path = os.path.join(serpath, 'suanli.js')
            run_node_program(node_script_path)
        else:
            print('算力环境自动安装失败：请在server目录下执行 npm install 命令安装算力环境')

else:
    print("系统未安装Node.js，无法运行FKServer云算力环境")