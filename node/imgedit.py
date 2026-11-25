import base64
import hashlib
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageSequence
import torch
import numpy as np  
import folder_paths
import time
import random
from server import PromptServer, BinaryEventTypes
import logging
import comfy.model_management
import node_helpers
tempfolder = os.path.join(folder_paths.get_temp_directory(),"fkimgedit")
if not os.path.exists(tempfolder):
    os.makedirs(tempfolder)

def ensure_tempfolder():
    if not os.path.isdir(tempfolder):
        os.makedirs(tempfolder, exist_ok=True)
def pil2tensor(image):
  return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)    
def image2mask(image_path,channel="A"):   
    i = node_helpers.pillow(Image.open, image_path)
    i = node_helpers.pillow(ImageOps.exif_transpose, i)
    if i.getbands() != ("R", "G", "B", "A"):
        if i.mode == 'I':
            i = i.point(lambda i: i * (1 / 255))
        i = i.convert("RGBA")
    mask = None
    c = channel[0].upper()
    if c in i.getbands():
        mask = np.array(i.getchannel(c)).astype(np.float32) / 255.0
        mask = torch.from_numpy(mask)
        if c == 'A':
            mask = 1. - mask
    else:
        mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
    return mask.unsqueeze(0) 
def getimg(img_path):  
    try:
        i = Image.open(img_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return image
    except Exception as e:
        logging.error(f"Error loading image {img_path}: {e}")
        return None
def gtoken(length):   
    random_number = random.randint(0, 1000000)
    random_number_str = str(random_number)
    hash_value = hashlib.md5(random_number_str.encode()).hexdigest()
    token = hash_value[:length]
    return token + time.strftime("%Y%m%d%H%M%S", time.localtime())

class FKImgEditNode: 
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "background": ("IMAGE",),
                "foreground": ("IMAGE",),                
                "token": ("STRING", {"default":gtoken(15)})
            }, "optional": {
               "foregroundMask": ("MASK",),
               "foreground2": ("IMAGE",),                
               "foreground2Mask": ("MASK",),
            }, "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("IMAGE","MASK")
    RETURN_NAMES = ("output","Mask")
    FUNCTION = "compose_images"
    CATEGORY = "FK_Nodes"  
    def compose_images(self, background=None, foreground=None,foregroundMask=None,foreground2=None,foreground2Mask=None,token=None, unique_id=None):
        ensure_tempfolder()
        tstoken = "FKimgedit_" + gtoken(15)  
        foregroundimg = ""
        foreground2img = ""
        if foreground is not None and foregroundMask is not None:
            try:
                texture_array = foreground.cpu().numpy()[0]          
                if texture_array.shape[-1] == 4:
                    foregroundimg = self.save_image(foreground) or ""
                else:
                    try:
                        mask_array = foregroundMask.cpu().numpy()
                        if len(mask_array.shape) == 3:
                            mask_array = mask_array[0]  
                        if mask_array.shape[:2] != texture_array.shape[:2]:
                            raise ValueError("遮罩尺寸与前景图尺寸不匹配")                        
                        mask_array = 1.0 - mask_array    
                        rgba = np.zeros((*texture_array.shape[:2], 4), dtype=np.uint8)
                        rgba[..., :3] = np.clip(texture_array * 255, 0, 255).astype(np.uint8)  
                        rgba[..., 3] = np.clip(mask_array * 255, 0, 255).astype(np.uint8)                      
                        texture_with_mask = Image.fromarray(rgba, 'RGBA')                        
                        # 保存到指定目录
                        imgname = "F1" + gtoken(20) + ".png"
                        save_path = os.path.join(tempfolder, imgname)
                        texture_with_mask.save(save_path, format="PNG")
                        foregroundimg = imgname
                        
                    except Exception as e:            
                        foregroundimg = self.save_image(foreground) or ""            
            except Exception as e:
                raise ValueError(f"前景图处理错误: {str(e)}")   
        else:
           foregroundimg = self.save_image(foreground) or ""

        if foreground2 is not None and foreground2Mask is not None:
            try:
                texture_array = foreground2.cpu().numpy()[0]          
                if texture_array.shape[-1] == 4:
                    foreground2img = self.save_image(foreground2) or ""
                else:
                    try:
                        mask_array = foreground2Mask.cpu().numpy()
                        if len(mask_array.shape) == 3:
                            mask_array = mask_array[0]                          
                        if mask_array.shape[:2] != texture_array.shape[:2]:
                            raise ValueError("遮罩尺寸与前景图尺寸不匹配")                        
                        mask_array = 1.0 - mask_array    
                        rgba = np.zeros((*texture_array.shape[:2], 4), dtype=np.uint8)
                        rgba[..., :3] = np.clip(texture_array * 255, 0, 255).astype(np.uint8)  
                        rgba[..., 3] = np.clip(mask_array * 255, 0, 255).astype(np.uint8)                      
                        texture_with_mask = Image.fromarray(rgba, 'RGBA')                    
                        
                        # 保存到指定目录
                        imgname = "F2" + gtoken(20) + ".png"
                        save_path = os.path.join(tempfolder, imgname)
                        texture_with_mask.save(save_path, format="PNG")
                        foreground2img = imgname 
                    except Exception as e:            
                        foreground2img = self.save_image(foreground2) or ""            
            except Exception as e:
                raise ValueError(f"前景图处理错误: {str(e)}")   
        elif foreground2 is not None:
            foreground2img = self.save_image(foreground2) or "" 
        else:
           foreground2img =  "" 
        server = PromptServer.instance
        server.send_sync(
                "executed",
               {"node_id": unique_id,"node": unique_id,"display_node":unique_id,"output":{
                "background":self.save_image(background),"foreground":foregroundimg,"foreground2":foreground2img,"token":tstoken
               }},
                server.client_id,
            ) 
        
        img_path = os.path.join(tempfolder, tstoken + ".png")
        while not os.path.exists(img_path) and not comfy.model_management.processing_interrupted(): 
            time.sleep(3) 
       
        if comfy.model_management.processing_interrupted():
            return (background,foreground,)       
        image = getimg(img_path)
        mask_path = os.path.join(tempfolder, tstoken + "_mask.png")
        mask = image2mask(mask_path)
        return (image,mask,)

    def save_image(self, image):
        imgname = "F" + gtoken(20) + ".png"
        try:
            if image is not None:
                img = image.cpu().numpy()[0]
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
                if img.shape[-1] == 4:
                    img = Image.fromarray(img, 'RGBA')
                else:
                    img = Image.fromarray(img, 'RGB')                
                img.save(os.path.join(tempfolder,imgname ), format="PNG")
                return imgname
        except Exception as e:
            return ""

class FKTietuNode2:
    @classmethod
    def INPUT_TYPES(s):
        return {
          "required": {
                "background": ("IMAGE",),
                "Depth": ("IMAGE",),
                "Texture": ("IMAGE",),                
                "token": ("STRING", {"default":gtoken(15)}),
                "img": ("STRING", {"default":"等待传入数据..."}),
            } ,"optional": {
                "TextureMask": ("MASK",),
            }, "hidden": {"unique_id": "UNIQUE_ID"}
        }    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process"
    OUTPUT_NODE = True  
    CATEGORY = "FK_Nodes" 
    def process(self, background=None, Depth=None, Texture=None, TextureMask=None,img=None, unique_id=None,token=None):     
        ensure_tempfolder()
        base64_image3 = ""       
        tstoken = "FKimghc_" + gtoken(16)  
        if Texture is not None and TextureMask is not None:
            try:
                texture_array = Texture.cpu().numpy()[0]          
                if texture_array.shape[-1] == 4:
                    base64_image3 = self.save_image(Texture) or ""
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
                        # 保存到指定目录
                        imgname = "FA1" + gtoken(20) + ".png"
                        save_path = os.path.join(tempfolder, imgname)
                        texture_with_mask.save(save_path, format="PNG")
                        base64_image3 = imgname
                    except Exception as e: 
                        base64_image3 = self.save_image(Texture) or ""
            except Exception as e:
                raise ValueError(f"Texture处理错误: {str(e)}")        
        else:
            base64_image3 = self.save_image(Texture) or ""

        base64_image1 = self.save_image(background) or ""
        base64_image2 = self.save_image(Depth) or ""        

        server = PromptServer.instance
        server.send_sync(
                "executed",
               {"node_id": unique_id,"node": unique_id,"display_node":unique_id,"output":{
                "backgroundcode":base64_image1,"depthcode":base64_image2,"Texturecode":base64_image3,"token":tstoken
               }},
                server.client_id,
            ) 
        
        img_path = os.path.join(tempfolder, tstoken + ".png")
        while not os.path.exists(img_path) and not comfy.model_management.processing_interrupted(): 
            time.sleep(3) 
       
        if comfy.model_management.processing_interrupted():
            return (background,)
        i = Image.open(img_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]      
        return (image,)

    
    def save_image(self, image):
        imgname = "F" + gtoken(20) + ".png"
        try:
            if image is not None:
                img = image.cpu().numpy()[0]
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
                if img.shape[-1] == 4:
                    img = Image.fromarray(img, 'RGBA')
                else:
                    img = Image.fromarray(img, 'RGB')                
                img.save(os.path.join(tempfolder,imgname ), format="PNG")
                return imgname
        except Exception as e:
            return ""
        