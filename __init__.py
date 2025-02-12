import sys, os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from .fk_server import Cancelled
from .server import Cancelled
from .node.tietu_node import FKTietuNode,FKShowBaseText


NODE_CLASS_MAPPINGS = {
    "FK_Node": FKTietuNode,
    "FK_ShowBaseNode": FKShowBaseText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FK_Node": "FK_图片编码转换",
    "FK_ShowBaseNode": "FK_高级贴图编辑器",
}

WEB_DIRECTORY = "web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
VERSION = "1.2.9"