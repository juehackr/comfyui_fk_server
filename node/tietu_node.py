import base64
import hashlib
import os
from io import BytesIO
from PIL import Image
import torch
import numpy as np  
import folder_paths

class FK3DPOSENode(object):
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(self):
        temp_dir = folder_paths.get_temp_directory()
        temp_dir = os.path.join(temp_dir, '3dposeeditor')
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)
        return {
            "required": {
                "pose": ("STRING", ),
                "depth": ("STRING", ),
                "normal": ("STRING", ),
                "canny": ("STRING", ),
            },
        } 

    RETURN_TYPES = ("IMAGE","IMAGE","IMAGE","IMAGE","INT", "INT",)
    RETURN_NAMES = ("OpenPose", "Depth", "Normal", "Canny","Width", "Height",)
    FUNCTION = "get_pose"
    CATEGORY = "FK_Nodes"

    def get_pose(self, pose=None, depth=None, normal=None, canny=None):
        if pose is None:
            raise ValueError("请先进行姿态编辑")

        temp_dir = folder_paths.get_temp_directory()
        temp_dir = os.path.join(temp_dir, '3dposeeditor')
        image_path = os.path.join(temp_dir, pose)
        i = None
        try:
            i = Image.open(image_path)
        except:
            raise ValueError("请先进行姿态编辑")            
        
        poseImage = i.convert("RGB")
        poseImage = np.array(poseImage).astype(np.float32) / 255.0
        poseImage = torch.from_numpy(poseImage)[None,]

        image_path = os.path.join(temp_dir, depth)

        i = Image.open(image_path)
        depthImage = i.convert("RGB")
        depthImage = np.array(depthImage).astype(np.float32) / 255.0
        depthImage = torch.from_numpy(depthImage)[None,]

        image_path = os.path.join(temp_dir, normal)

        i = Image.open(image_path)
        normalImage = i.convert("RGB")
        normalImage = np.array(normalImage).astype(np.float32) / 255.0
        normalImage = torch.from_numpy(normalImage)[None,]

        image_path = os.path.join(temp_dir, canny)

        i = Image.open(image_path)
        cannyImage = i.convert("RGB")
        cannyImage = np.array(cannyImage).astype(np.float32) / 255.0
        cannyImage = torch.from_numpy(cannyImage)[None,]
        width, height = i.size
        return (poseImage, depthImage, normalImage, cannyImage,width, height)

    @staticmethod
    def IS_CHANGED(self, pose=None, depth=None, normal=None, canny=None):
        if pose is None:
            return False

        temp_dir = folder_paths.get_temp_directory()
        temp_dir = os.path.join(temp_dir, '3dposeeditor')
        image_path = os.path.join(temp_dir, pose)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()
  
class FKTietuNode:
    INPUT_TYPES = {
         "required": {
                "background": ("IMAGE",),
                "Depth": ("IMAGE",),
                "Texture": ("IMAGE",),
                "TextureMask": ("MASK",),
            }
    }
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("background", "Depth", "Texture")
    FUNCTION = "process"
    OUTPUT_NODE = True  
    CATEGORY = "FK_Nodes" 
    def process(self, background=None, Depth=None, Texture=None, TextureMask=None):     
        base64_image3 = ""        
        if Texture is not None and TextureMask is not None:
            try:
                texture_array = Texture.cpu().numpy()[0]          
                if texture_array.shape[-1] == 4:
                    base64_image3 = self.encode_image(Texture) or ""
                else:
                    try:
                        mask_array = TextureMask.cpu().numpy()
                        if len(mask_array.shape) == 3:
                            mask_array = mask_array[0]  
                        
                        if mask_array.shape[:2] != texture_array.shape[:2]:
                            raise ValueError("遮罩尺寸与图像不匹配")                        
                        mask_array = 1.0 - mask_array    
                        rgba = np.zeros((*texture_array.shape[:2], 4), dtype=np.uint8)
                        rgba[..., :3] = np.clip(texture_array * 255, 0, 255).astype(np.uint8)  
                        rgba[..., 3] = np.clip(mask_array * 255, 0, 255).astype(np.uint8)                      
                        texture_with_mask = Image.fromarray(rgba, 'RGBA')                    
                        buffered = BytesIO()
                        texture_with_mask.save(buffered, format="PNG")
                        base64_image3 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    except Exception as e:                    
                        base64_image3 = self.encode_image(Texture) or ""
            except Exception as e:
                raise ValueError(f"Texture处理错误: {str(e)}")        
        base64_image1 = self.encode_image(background) or ""
        base64_image2 = self.encode_image(Depth) or ""        
        return {"result": (base64_image1, base64_image2, base64_image3)}
    
    def encode_image(self, image):
        try:
            if image is not None:
                img = image.cpu().numpy()[0]
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
                if img.shape[-1] == 4:
                    img = Image.fromarray(img, 'RGBA')
                else:
                    img = Image.fromarray(img, 'RGB')
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"图片转换错误: {str(e)}")
        return None
    @classmethod
    def INPUT_TYPES(s):
        return {
         "required": {
                "background": ("IMAGE",),
                "Depth": ("IMAGE",),
                "Texture": ("IMAGE",),
                "TextureMask": ("MASK",),
            }
        }
class FKShowBaseText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "background": ("STRING", {"forceInput": True}),
                "depth": ("STRING", {"forceInput": True}),
                "Texture": ("STRING", {"forceInput": True}),
                "backgroundcode": ("STRING", {"multiline": True, "placeholder": "背景图代码，无需填写自动生成", "tooltip": "使用 FK_图片编码转换 节点自动生成"}),
                "depthcode": ("STRING", {"multiline": True, "placeholder": "深度图代码，无需填写自动生成", "tooltip": "使用 FK_图片编码转换 节点自动生成"}),
                "Texturecode": ("STRING", {"multiline": True, "placeholder": "贴图代码，无需填写自动生成", "tooltip": "使用 FK_图片编码转换 节点自动生成"})
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "notify"
    OUTPUT_NODE = True
    CATEGORY = "FK_Nodes"
    def notify(self, background, depth, Texture, backgroundcode, depthcode, Texturecode,unique_id=None):
        return {"ui": {"backgroundcode": [background], "depthcode": [depth], "Texturecode": [Texture]}, "result": ([background], [depth], [Texture])}    