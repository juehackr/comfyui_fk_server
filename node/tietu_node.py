import base64
from io import BytesIO
from PIL import Image
import numpy as np  
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
                print(f"Texture处理错误: {str(e)}")        
        base64_image1 = self.encode_image(background) or ""
        base64_image2 = self.encode_image(Depth) or ""        
        return {
            "ui": {
                "backgroundcode": [base64_image1],
                "Depthcode": [base64_image2],
                "Texturecode": [base64_image3]
            }, 
            "result": (base64_image1, base64_image2, base64_image3)
        }
    
    def encode_image(self, image):
        try:
            if image is not None:
                img = image.cpu().numpy()[0]
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
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