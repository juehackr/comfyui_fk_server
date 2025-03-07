import os
from server import PromptServer
from aiohttp import web
import json
import folder_paths

class Cancelled(Exception):
    pass
def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return '{}'
    except Exception as e:
         return '{}'
    return None
def string_to_json(json_string):
    try:
        json_object = json.loads(json_string)
        return json_object
    except json.JSONDecodeError as e:
        return None
    
current_path = os.path.abspath(os.path.dirname(__file__))
@PromptServer.instance.routes.get('/fk_server/app/{filename:.*}')
async def static_file_handler(request):
    filename = request.match_info['filename']
    file_path = os.path.join(current_path, "webApp", filename)
    #print(file_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 定义二进制文件类型
        binary_types = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp'}
        # 定义内容类型映射
        content_types = {
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.ico': 'image/x-icon',
            '.bmp': 'image/bmp'
        }
        
        # 获取文件扩展名
        file_ext = os.path.splitext(filename)[1].lower()
        content_type = content_types.get(file_ext, 'application/octet-stream')
        
        # 根据文件类型选择不同的读取模式
        if file_ext in binary_types:
            # 二进制模式读取
            with open(file_path, 'rb') as f:
                file_data = f.read()
                return web.Response(body=file_data, content_type=content_type)
        else:
            # 文本模式读取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_data = f.read()
                return web.Response(text=file_data, content_type=content_type)
    else:
        return web.Response(text="File not found", status=404)


def find_image_files(directory,qianzhui):
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    result = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in image_extensions:
                relative_path = os.path.relpath(root, directory)
                if relative_path not in result:
                    result[relative_path] = {"dir":os.path.join(qianzhui, relative_path), "files": []}
                result[relative_path]["files"].append({"u":"", "name": file})      
    return json.dumps(result, indent=4)
@PromptServer.instance.routes.get("/fk_server")
async def fksapi(request):
         tget = request.rel_url.query
         gtype =  tget['type']         
         if gtype == "getpz":
                config_path = os.path.join(os.path.dirname(__file__), "ini.json")
                pznr = string_to_json(read_file_content(config_path))
                if pznr=={}:
                     pznr = {"appid": "","key": "","zhitsc": "请你根据我输入的AI绘画提示词，进行专业的润色，并用中文直接输出结果（输出结果不要附带任何无关内容），以下是我的AI绘画提示词：","zhipukey": "","slkg":False}
                     with open(config_path, 'w', encoding='utf-8') as file:
                        json.dump(pznr, file, ensure_ascii=False, indent=4)               
                return web.json_response(pznr, content_type='application/json')
         elif gtype == "getslpz":
                config_path = os.path.join(os.path.dirname(__file__), "server/data.json")
                return web.json_response(string_to_json(read_file_content(config_path)), content_type='application/json')
         elif gtype == "getdir":                
                if tget['dir'] =="input":
                    config_path = folder_paths.get_input_directory()
                elif tget['dir'] == "temp":
                    config_path = folder_paths.get_temp_directory()
                elif tget['dir'] == "output":
                    config_path = folder_paths.get_output_directory()
                else:
                    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) , tget['dir'])   
                return web.json_response({"dir":config_path}, content_type='application/json')
         elif gtype == "getmoban": 
               config_path = os.path.join(folder_paths.get_input_directory(), "moban")
               json_output = '{}'
               if 'dir' in tget:
                 json_output = find_image_files(os.path.join(config_path, tget['dir']),os.path.join("moban", tget['dir']))
                 return web.json_response(string_to_json(json_output), content_type='application/json')
               elif 'dira' in tget:
                 dira = tget['dira'].split("|")
                 alrrjs = {}
                 for dir in dira:
                    alrrjs[dir] =string_to_json(find_image_files(os.path.join(config_path, dir),os.path.join("moban", dir)))
                 return web.json_response(alrrjs, content_type='application/json')    
               
         elif gtype == "delslpz":
               config_path = os.path.join(os.path.dirname(__file__), "server/data.json")
               try:
                   os.remove(config_path)
                   return web.json_response({"v":gtype}, content_type='application/json')
               except OSError:
                  return web.json_response({"v":gtype}, content_type='application/json') 
         else:
             return web.json_response({"v":gtype}, content_type='application/json')
@PromptServer.instance.routes.get("/fkhome")
async def fkweb(request): 
         return web.Response(
                text="hi",
                content_type="text/html",
            )
@PromptServer.instance.routes.post('/fk_server')
async def fkpostapi(request):
        tget = request.rel_url.query
        gtype =  tget['type'] 
        post = await request.post()
        if gtype == "setpz":            
            bdappid = post.get("bdappid")
            bdappkey = post.get("appbdkey") 
            zhitsc = post.get("zhitsc")
            zhipukey = post.get("zhipukey") 
            if bdappid and bdappkey:
                config_path = os.path.join(os.path.dirname(__file__), "ini.json")
                config_data = string_to_json(read_file_content(config_path))
                print(f"Comfyui_fk_server：密钥设置成功")
                config_data["appid"] = bdappid
                config_data["key"] = bdappkey
                config_data["zhitsc"] = zhitsc
                config_data["zhipukey"] = zhipukey
                with open(config_path, 'w', encoding='utf-8') as file:
                    json.dump(config_data, file, ensure_ascii=False, indent=4)
        elif gtype == "setslkg":
                config_path = os.path.join(os.path.dirname(__file__), "ini.json")
                config_data = string_to_json(read_file_content(config_path))
                config_data["slkg"] = post.get("slkg")
                with open(config_path, 'w', encoding='utf-8') as file:
                    json.dump(config_data, file, ensure_ascii=False, indent=4)
                return web.json_response({}, content_type='application/json')
        return web.json_response({}, content_type='application/json')


print(f"\33[93m》===>====>========>Fk_Server:OK！<========<====<===《\33[0m")