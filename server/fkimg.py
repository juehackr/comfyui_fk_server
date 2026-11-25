import os
from PIL import Image, ImageOps #所属依赖 pillow
import sys
if len(sys.argv) != 3:
    sys.exit(1)
file = sys.argv[1]
filemask = sys.argv[2]
def mask_image(file, filemask):
    if os.path.isfile(file):
        # print(f'Processing {file}')
        with Image.open(file) as original_pil:    
            original_pil = original_pil.convert('RGBA')                       
            mask_pil = Image.open(filemask).convert('RGBA')
            # alpha copy and resize to match original
            new_alpha = mask_pil.getchannel('A')
            new_alpha = new_alpha.resize(original_pil.size)
        original_pil.putalpha(new_alpha)
        # 覆盖保存 filemask
        os.remove(filemask)
        original_pil.save(filemask, compress_level=4)
        return filemask
    return None
filemask = mask_image(file, filemask)