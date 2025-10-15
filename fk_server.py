import os
import comfy.utils
from server import PromptServer
from aiohttp import web
from PIL import Image
import json
import folder_paths
from folder_paths import map_legacy, filter_files_extensions, filter_files_content_types
base_path = os.path.dirname(os.path.realpath(__file__))
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
    if os.path.exists(file_path) and os.path.isfile(file_path):
        binary_types = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp'}
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
        
        file_ext = os.path.splitext(filename)[1].lower()
        content_type = content_types.get(file_ext, 'application/octet-stream')
        
        if file_ext in binary_types:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                return web.Response(body=file_data, content_type=content_type)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_data = f.read()
                return web.Response(text=file_data, content_type=content_type)
    else:
        return web.Response(text="File not found", status=404)


def resize_and_save_image(img_path, width):  
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    if os.path.splitext(img_path)[1].lower() not in image_extensions:
        return None
    original_dir = os.path.dirname(img_path)
    save_dir = os.path.join(original_dir, "fenmian")    
    filename = os.path.basename(img_path)
    name, ext = os.path.splitext(filename)
    target_filename = f"{name}_w{width}{ext}"
    target_path = os.path.join(save_dir, target_filename)    
    if os.path.exists(target_path):
        return target_path    
    os.makedirs(save_dir, exist_ok=True)    
    try:
        with Image.open(img_path) as img:
            original_width, original_height = img.size
            ratio = width / original_width
            new_height = int(original_height * ratio)            
            resized_img = img.resize((width, new_height), Image.LANCZOS)
            resized_img.save(target_path, quality=85)
            return target_path
    except Exception as e:
        return None

def find_image_files(directory, qianzhui):
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    
    dir_structure = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(
            [d for d in dirs if d != 'fenmian'],
            key=lambda x: x.lower()
        )        
        files = sorted(
            files,
            key=lambda x: os.path.splitext(x)[0].lower()
        )
        
        relative_path = os.path.relpath(root, directory)
        current_files = []
        if relative_path != '.':
            current_files = [
                {"u": "", "name": f}
                for f in files
                if os.path.splitext(f)[1].lower() in image_extensions
            ]
        
        dir_structure[relative_path] = {
            "files": current_files,
            "subdirs": dirs
        }
    def build_nested(path):
        current_dir = qianzhui if path == '.' else os.path.join(qianzhui, path)        
        node = {
            "dir": current_dir,
            "names":os.path.basename(path),
            "files": dir_structure[path]["files"],
            "zidir": []
        }
        
        for subdir in dir_structure[path]["subdirs"]:
            sub_path = os.path.join(path, subdir) if path != '.' else subdir
            node["zidir"].append(build_nested(sub_path))
        
        return node
    
    return json.dumps(build_nested('.'), indent=4)
@PromptServer.instance.routes.get("/fkimgview")
async def fksapi(request):
         tget = request.rel_url.query
         tpath =  tget['path']
         tsize =  tget['size']         
         imglj = os.path.join(base_path, tpath)
         if os.path.exists(imglj):
            img = resize_and_save_image(imglj, int(tsize))
            if img:
                 file_ext = os.path.splitext(img)[1].lower()
                 content_types = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.webp': 'image/webp',
                        '.bmp': 'image/bmp'
                    }
                 content_type = content_types.get(file_ext, 'image/png')                    
                 return web.Response(
                        body=open(img, 'rb').read(),
                        content_type=content_type
                    )
            else:
                return web.Response(body=open(imglj, 'rb').read() ,content_type="application/octet-stream")
         else:
            return web.Response(text="文件不存在",content_type="text/html")
   
@PromptServer.instance.routes.get("/fkmodimg")
async def getmdoimg(request):        
         tget = request.rel_url.query
         folder_name = tget['dir']
         folders = folder_paths.folder_names_and_paths[folder_name]
         mx = tget['mx']       
         mxpic = os.path.splitext(mx)[0] + ".preview.png"
         mxpic2 = os.path.splitext(mx)[0] + ".png"
         mxpic3 = os.path.splitext(mx)[0] + ".jpg"
         mxpic4 = os.path.splitext(mx)[0] + ".preview.jpg"


         for index, folder in enumerate(folders[0]):
           fm1 = os.path.join(folder, mxpic)
           fm2 = os.path.join(folder, mxpic2)
           fm3 = os.path.join(folder, mxpic3)
           fm4 = os.path.join(folder, mxpic4)
           if os.path.exists(fm1):
                return web.Response(body=open(fm1, 'rb').read() ,content_type="image/png")
           elif os.path.exists(fm2):
                return web.Response(body=open(fm2, 'rb').read() ,content_type="image/png")
           elif os.path.exists(fm3):
                return web.Response(body=open(fm3, 'rb').read() ,content_type="image/jpeg")
           elif os.path.exists(fm4):
                return web.Response(body=open(fm4, 'rb').read() ,content_type="image/jpeg")
           else:
            notpic = os.path.join(os.path.dirname(__file__), "web/cssjs/notpic.jpg")
            if os.path.exists(notpic):
                return web.Response(body=open(notpic, 'rb').read() ,content_type="image/jpeg")
            else:
                return web.Response(text="封面文件不存在",content_type="text/html")
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
         elif gtype == "getuppz":
                config_path = os.path.join(os.path.dirname(__file__), "server/sr.json")
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
               config_path = os.path.join(base_path, "moban")
               json_output = '{}'
               if 'dir' in tget:
                 json_output = find_image_files(os.path.join(config_path, tget['dir']),os.path.join(config_path, tget['dir']))
                 return web.json_response(string_to_json(json_output), content_type='application/json')
               elif 'dira' in tget:
                 dira = tget['dira'].split("|")
                 alrrjs = {}
                 for dir in dira:
                    alrrjs[dir] =string_to_json(find_image_files(os.path.join(config_path, dir),os.path.join(config_path, dir)))
                 return web.json_response(alrrjs, content_type='application/json')    
               
         elif gtype == "delslpz":
               config_path = os.path.join(os.path.dirname(__file__), "server/data.json")
               try:
                   os.remove(config_path)
                   return web.json_response({"v":gtype}, content_type='application/json')
               except OSError:
                  return web.json_response({"v":gtype}, content_type='application/json') 
         else:
             return web.json_response({"v":gtype,"bb":"3.0"}, content_type='application/json')
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
            config_path = os.path.join(os.path.dirname(__file__), "ini.json")
            config_data = string_to_json(read_file_content(config_path))
            print(f"Comfyui_fk_server：密钥设置成功")
            config_data["appid"] = bdappid
            config_data["key"] = bdappkey
            config_data["zhitsc"] = zhitsc
            config_data["zhipukey"] = zhipukey
            config_data["fanyitype"] = post.get("fanyitype")
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

def setupapipz():
    config_path = os.path.join(os.path.dirname(__file__), "server/sr.json")
    config_data = string_to_json(read_file_content(config_path))
    get_output = folder_paths.get_output_directory()
    config_data["dir"] = get_output
    with open(config_path, 'w', encoding='utf-8') as file:
        json.dump(config_data, file, ensure_ascii=False, indent=4)
setupapipz()
print(f"\33[93m》===>====>========>Fk_Server:OK！<========<====<===《\33[0m")