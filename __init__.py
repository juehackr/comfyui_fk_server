import sys, os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from .fk_server import Cancelled
from .server import Cancelled
from .node.tietu_node import FKTietuNode,FKShowBaseText,FK3DPOSENode
from .node.imgedit import FKImgEditNode,FKTietuNode2
NODE_CLASS_MAPPINGS = {
    "FK_Node": FKTietuNode,
    "FK_gjttNode2": FKTietuNode2,
    "FK_ShowBaseNode": FKShowBaseText,
    "FK_3dpose": FK3DPOSENode,
    "FK_imgedit": FKImgEditNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FK_Node": "FK_图片编码转换",
    "FK_gjttNode2": "FK_高级贴图编辑器(新)",
    "FK_ShowBaseNode": "FK_高级贴图编辑器(旧)",
    "FK_3dpose": "FK_3D姿态编辑器(3D Openpose Editor)",
    "FK_imgedit": "FK_简易图片合成编辑器",
}

WEB_DIRECTORY = "web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
VERSION = "1.3.0"