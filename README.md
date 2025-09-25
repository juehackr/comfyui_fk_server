## 功能说明

**✅翻译功能：这是我理想中的Comfyui翻译插件（不再需要添加各种节点,直接在原有节点上加入翻译功能），让comfyui任意长文本输入框支持中文输入并自动翻译（调用百度翻译），同时加入报错翻译功能，实现翻译自由**

**✅提示词润色功能：输入简单的关键词帮你写出专业的AI绘画提示词（调用智谱AI大模型）**

**✅模型引用修复功能：我们平时会使用很多别人的工作流，但往往他们工作流调用的模型文件夹路径跟自己电脑上的模型文件夹路径不一致的，这个时候使用一键修复就可以快速纠正（大大提升工作流模型调用纠正效率）（基于模型名称匹配）**

**✅FK高级贴图编辑器：支持融合深度图的高级贴图编辑工具，同时内置多种属性可调整参数（使用方法请看视频或参考此项目参考工作流），这算是我开发的第一个正式节点，希望大家喜欢**

**✅3D姿态编辑器(3D Openpose Editor)：简单好用的3D姿态编辑器节点**

**✅简易图片合成编辑器节点：这才是真正的图片合成编辑节点，修改图片位置后点击确定直接往下执行后续节点无需再次重新执行工作流，算是填补了当前comfyui此类节点的一个空白（至少我还没有发现有其他节点实现此功能）**

**✅PS互通插件：一键实现comfyUI与PS互通交互，支持win和mac系统（PS端插件下载：https://pan.baidu.com/s/1Kw8FktevCxjuuppIT-BGig?pwd=fkai）**

**✅云算力环境配置**

## 使用说明

**翻译功能需要用到百度翻译密钥,免费申请入口：https://fanyi-api.baidu.com/ `再次注意:必须要申请一个应用才有翻译权限,每月免费额度100W真的够用了`**

**提示词润色功能需要用到智谱AI的APIKEY,免费申请入口：https://open.bigmodel.cn/overview `（有很多免费额度）`**

填写好后重启comfyui **❗❗❗双击任意长文本输入框即可启用自动翻译模式及显示提示词润色功能❗❗❗**

tips：输入中文后，鼠标移开或点击任意区域即可自动翻译

**使用有疑问或者建议请提交Issues反馈**

## FK_简易图片合成编辑器节点演示

https://github.com/user-attachments/assets/5214b1af-bb19-4eec-a28e-d64b5e221062

## FK_3D姿态编辑器(3D Openpose Editor)节点演示

https://github.com/user-attachments/assets/06c358b7-6264-4c7a-bbcf-25ea49391bda

## FK高级贴图编辑器功能及操作演示

https://github.com/user-attachments/assets/e9668841-4bac-455e-b150-df33a84e1315

## 自动翻译演示视频(双击输入框进入自动翻译模式)

https://github.com/juehackr/comfyui_fk_server/assets/85547436/666a1f7f-ca75-4a38-88c9-81bbb616b92f

## 提示词润色演示(双击输入框进入自动翻译模式后可用润色功能)

https://github.com/juehackr/comfyui_fk_server/assets/85547436/5b0b1135-7c35-44e7-ba6e-54727da1592d

## 模型引用修复演示（最大程度提高工作流调用效率）

https://github.com/juehackr/comfyui_fk_server/assets/85547436/dac4fe07-212b-495e-b99f-298194319aaf

## 报错翻译演示视频（选择报错内容点击出现的翻译按钮）

https://github.com/juehackr/comfyui_fk_server/assets/85547436/c9eab88b-27f7-4b1a-bb1d-c7993d89cf3b

## 插件安装方法

- 进入comfyui插件目录 `/ComfyUI/custom_nodes/` 
  - 执行 `git clone https://github.com/juehackr/comfyui_fk_server.git`
  - 依赖安装步骤：进入comfyui的python环境目录（一般是*:comfyui目录\python_embeded\）执行如下命令
  - python.exe -m pip install -r {comfyui路径}/custom_nodes/comfyui_fk_server/requirements.txt
  - 重启 ComfyUI






