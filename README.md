
**✅翻译功能：这是我理想中的Comfyui翻译插件（不再需要添加各种节点,直接在原有节点上加入翻译功能），让comfyui任意长文本输入框支持中文输入并自动翻译（调用百度翻译），同时加入报错翻译功能，实现翻译自由**

**✅模型引用修复功能：我们平时会使用很多别人的工作流，但往往他们工作流调用的模型文件夹路径跟自己电脑上的模型文件夹路径不一致的，这个时候使用一键修复就可以快速纠正（大大提升工作流模型调用纠正效率）（基于模型名称匹配）**

## 使用说明

**需要用到百度翻译密钥,免费申请入口：https://fanyi-api.baidu.com/ `再次注意:必须要申请一个应用才有翻译权限`**

填写好后重启comfyui **❗❗❗双击任意长文本输入框即可启用自动翻译模式❗❗❗**

tips：输入中文后，鼠标移开或点击任意区域即可自动翻译

**使用有疑问或者建议请提交Issues反馈**

## 演示视频(双击输入框进入自动翻译模式)

https://github.com/juehackr/comfyui_fk_server/assets/85547436/666a1f7f-ca75-4a38-88c9-81bbb616b92f

## 模型引用修复演示（最大程度提高工作流调用效率）

https://github.com/juehackr/comfyui_fk_server/assets/85547436/dac4fe07-212b-495e-b99f-298194319aaf

## 报错翻译演示视频（选择报错内容点击出现的翻译按钮）

https://github.com/juehackr/comfyui_fk_server/assets/85547436/c9eab88b-27f7-4b1a-bb1d-c7993d89cf3b

## 插件安装方法

- 进入comfyui插件目录 `/ComfyUI/custom_nodes/` 
  - 执行 `git clone https://github.com/juehackr/comfyui_fk_server.git`  
  - 重启 ComfyUI

