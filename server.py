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
    node_script_path = os.path.join(os.path.dirname(__file__), 'server/suanli.js')
    run_node_program(node_script_path)
else:
    print("系统未安装Node.js，无法运行FKServer云服务")