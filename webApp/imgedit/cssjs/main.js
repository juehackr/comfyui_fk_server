// 核心变量
let canvas;
let bgWidth;  // 背景图原始宽度
let bgHeight; // 背景图原始高度
let scaleRatio = 1; // 画布当前缩放比例
let fgImages = [];  // 前景图对象数组，支持多个前景图
let activeFgIndex = 0; // 当前活动的前景图索引
let token = '';
// 图片资源
let bgImageUrl = 'https://placehold.co/800x600/000/darkviolet/png?text=Background';
let fgImageUrls = [
    'https://placehold.co/200x200/fff/orange/png?text=Foreground'
]; // 支持两个前景图

function geturlcan(param) { //获取当前URL中的指定参数
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}
let ifid = geturlcan('ifid'); //获取当前URL中的ifid参数

// 初始化函数
function init() {

    try {
        postMessageToParent({
            type: 'setToken'
        });
    } catch (error) {

    }

    // 创建画布元素
    const canvasContainer = document.getElementById('canvas-container');
    const canvasElement = document.createElement('canvas');
    canvasElement.id = 'fabric-canvas';
    canvasContainer.appendChild(canvasElement);

    // 初始化Fabric画布
    canvas = new fabric.Canvas('fabric-canvas', {
        preserveObjectStacking: true,
        centeredScaling: true
    });

    // 加载背景图
    fabric.Image.fromURL(bgImageUrl, async function (bgImg) {
        // 保存背景图原始尺寸
        bgWidth = bgImg.width;
        bgHeight = bgImg.height;

        // 设置背景图（不可选中）
        bgImg.selectable = false;
        canvas.setBackgroundImage(bgImg, canvas.renderAll.bind(canvas));

        // 设置画布初始尺寸
        canvas.setWidth(bgWidth);
        canvas.setHeight(bgHeight);

        // 加载两个前景图
        await loadForegroundImage(0);
        await loadForegroundImage(1);

        // 初始化缩放
        resizeCanvas();

        // 绑定事件
        bindEvents();

        // 关键修复：确保所有前景图可以被点击
        ensureClickableForegrounds();
        if (!bgImageUrl.includes('placehold.co')) {
            loadshuxing();//加载所有前景图位置及尺寸属性
        }

    }, { crossOrigin: 'anonymous' });
    // 窗口大小变化监听
    window.addEventListener('resize', resizeCanvas);
    // 按钮事件
    document.getElementById('reset-btn').addEventListener('click', resetView);
    document.getElementById('download-btn').addEventListener('click', downloadCanvas);
    //鼠标经过画布
    canvasContainer.addEventListener('mouseover', (e) => {
        // console.log("鼠标经过画布");
        try {
            postMessageToParent({
                type: 'setToken'
            });
        } catch (error) {

        }
    });
}

// 确保前景图可点击的辅助函数
function ensureClickableForegrounds() {
    // 强制重新计算所有前景图的边界框并重新渲染
    setTimeout(() => {
        // 确保canvas和前景图存在
        if (!canvas || !fgImages || fgImages.length === 0) return;

        fgImages.forEach(img => {
            if (img) {
                // 确保设置为可选中
                img.selectable = true;
                // 强制重新计算边界框，这是修复点击区域问题的关键
                img.setCoords();
            }
        });

        // 重新渲染画布
        canvas.renderAll();

        // 额外延迟确保DOM更新完成后再尝试选中
        setTimeout(() => {
            // 确保第一个前景图被选中
            if (fgImages[0]) {
                // 先取消当前选中状态
                canvas.discardActiveObject();
                // 重新选中第一个前景图
                canvas.setActiveObject(fgImages[0]);
                activeFgIndex = 0;
                canvas.renderAll();
            }
        }, 50);
    }, 200);
}

// 选择指定的前景图
function selectForegroundImage(index) {
    if (fgImages[index]) {
        canvas.setActiveObject(fgImages[index]);
        activeFgIndex = index;
        // 更新透明度和叠加模式控件值为当前选中前景图的值
        const opacitySlider = document.getElementById('opacity-slider');
        const blendModeSelect = document.getElementById('blend-mode-select');

        opacitySlider.value = fgImages[index].opacity || 1;
        blendModeSelect.value = fgImages[index].globalCompositeOperation || 'source-over';
    }
}


// 加载前景图并设置特殊属性 - 返回Promise以确保正确的异步处理
async function loadForegroundImage(index = 0) {
    return new Promise((resolve) => {
        fabric.Image.fromURL(fgImageUrls[index], function (fgImg) {
            // 先设置中心点坐标系统 - 确保点击区域以图像中心计算
            fgImg.set({
                originX: 'center',
                originY: 'center'
            });

            // 当前景图大小超出背景图大小时，等比例缩放到可以完全显示
            let initialScale = 1;
            if (fgImg.width > bgWidth || fgImg.height > bgHeight) {
                // 计算缩放比例（取宽和高中的最小比值）
                const scaleByWidth = bgWidth / fgImg.width;
                const scaleByHeight = bgHeight / fgImg.height;
                initialScale = Math.min(scaleByWidth, scaleByHeight);
            }

            // 初始位置：画布中心或偏移位置，考虑scaleRatio
            const normalizedLeft = 0.5 + (index * 0.1 - 0.05); // 为第二个前景图偏移一些位置
            const normalizedTop = 0.5;  // 直接设置为中心点

            // 设置前景图样式属性和位置，考虑scaleRatio和等比例缩放
            fgImg.set({
                left: normalizedLeft * bgWidth * scaleRatio,
                top: normalizedTop * bgHeight * scaleRatio,
                scaleX: scaleRatio * initialScale,
                scaleY: scaleRatio * initialScale,
                cornerSize: 10,
                borderColor: '#3B82F6',
                cornerColor: index === 0 ? 'yellow' : 'green', // 不同前景图使用不同颜色标识
                cornerStyle: 'circle', // 设置为圆角控件
                transparentCorners: false,
                // 关键点：设置selectable为true以确保点击区域正确
                selectable: true
            });

            // 关键：存储相对于背景图的比例位置 (0-1)
            fgImg.set({
                normalizedLeft: normalizedLeft,
                normalizedTop: normalizedTop,
                normalizedScaleX: 1,
                normalizedScaleY: 1,
                normalizedAngle: 0,
                normalizedOpacity: 1,
                normalizedBlendMode: 'source-over'
            });

            // 添加到画布
            canvas.add(fgImg);

            // 强制重新计算边界框，确保点击区域与显示区域一致
            fgImg.setCoords();

            // 设置为活动对象
            canvas.setActiveObject(fgImg);
            canvas.renderAll();

            // 保存前景图对象引用
            fgImages[index] = fgImg;
            activeFgIndex = index;

            resolve();
        }, { crossOrigin: 'anonymous' });
    });
}

// 动态更新背景图
async function updateBackgroundImage(img = "") {
    // 修复：正确返回Promise以确保调用者能正确处理异步操作
    return new Promise(async (resolve, reject) => {
        const bgImageFileInput = document.getElementById('bg-image-file');
        let isLocalFile = false;
        let newImageSrc = "";
        // 检查是否有上传的文件
        if (img) {
            newImageSrc = img;
            isLocalFile = true;
        } else if (bgImageFileInput.files && bgImageFileInput.files[0]) {
            const file = bgImageFileInput.files[0];
            newImageSrc = URL.createObjectURL(file);
            isLocalFile = true;
        } else if (!img && !newImageSrc) {
            return;
        }

        //  console.log("更新背景图", newImageSrc);

        // 保存所有前景图的标准化属性
        let fgProperties = [];
        fgImages.forEach((fgImg, index) => {
            if (fgImg) {
                fgProperties[index] = {
                    normalizedLeft: fgImg.normalizedLeft,
                    normalizedTop: fgImg.normalizedTop,
                    normalizedScaleX: fgImg.normalizedScaleX,
                    normalizedScaleY: fgImg.normalizedScaleY,
                    normalizedAngle: fgImg.normalizedAngle,
                    normalizedOpacity: fgImg.normalizedOpacity,
                    normalizedBlendMode: fgImg.normalizedBlendMode
                };
            }
        });

        // 加载新的背景图
        fabric.Image.fromURL(newImageSrc, function (bgImg) {
            // 清除之前的前景图
            canvas.forEachObject(function (obj) {
                if (obj !== canvas.backgroundImage) {
                    canvas.remove(obj);
                }
            });

            // 保存新的背景图原始尺寸
            bgWidth = bgImg.width;
            bgHeight = bgImg.height;

            // 设置新的背景图
            bgImg.selectable = false;
            canvas.setBackgroundImage(bgImg, canvas.renderAll.bind(canvas));
            // 更新画布尺寸
            canvas.setWidth(bgWidth);
            canvas.setHeight(bgHeight);

            // 清空前景图数组
            fgImages = [];

            // 立即清除所有选中状态，确保从头开始
            canvas.discardActiveObject();
            canvas.renderAll();

            // 创建一个异步函数来处理前景图加载，并确保它完成后再resolve Promise
            (async () => {
                try {
                    // 直接加载前景图，避免多余的等待
                    // 加载第一个前景图
                    if (fgImageUrls[0]) {
                        await loadForegroundImage(0);
                    }

                    // 加载第二个前景图
                    if (fgImageUrls[1]) {
                        await loadForegroundImage(1);
                    }

                    await loadshuxing();

                    // 强制渲染一次确保所有前景图都正确显示
                    canvas.renderAll();

                    // 关键步骤：确保前景图可点击
                    if (fgImages.length > 0) {
                        // 最后选中第一个前景图
                        if (fgImages[0]) {
                            canvas.setActiveObject(fgImages[0]);
                            fgImages[0].setCoords();
                            activeFgIndex = 0;
                            canvas.renderAll();
                        }
                    }

                    // 重新调整画布大小
                    resizeCanvas();
                    if (sessionStorage.getItem("autoxzkfk" + ifid) == "1" && !bgImageUrl.includes('placehold.co')) {
                        setTimeout(() => {
                            downloadCanvas();
                        }, 2000);
                    }
                } catch (error) {
                    //   console.error('处理前景图时出错:', error);
                } finally {
                    // 确保前景图可点击
                    ensureClickableForegrounds();
                    // 最后调用resolve，确保Promise正确完成
                    resolve();
                }
            })();
        }, { crossOrigin: isLocalFile ? '' : 'anonymous' });
    });
}

// 动态更新前景图 - 支持指定前景图索引
async function updateForegroundImage(img = "", index = 0) {
    // 确保索引有效
    if (index < 0 || index > 1) {
        //  console.warn('无效的前景图索引:', index);
        return;
    }

    // 如果没有指定索引，使用当前活动的前景图索引
    if (index === undefined) {
        index = activeFgIndex;
    }

    let newImageSrc = "";
    const fgImageFileInput = index === 0 ?
        document.getElementById('fg-image-file-1') :
        document.getElementById('fg-image-file-2');
    let isLocalFile = false;

    // 检查是否有上传的文件
    if (img) {
        newImageSrc = img;
        isLocalFile = true;
    } else if (fgImageFileInput && fgImageFileInput.files && fgImageFileInput.files[0]) {
        const file = fgImageFileInput.files[0];
        newImageSrc = URL.createObjectURL(file);
        isLocalFile = true;
    } else if (!img && !newImageSrc) {
        return;
    }
    //  console.log(`更新前景图 ${index + 1}`, newImageSrc);

    // 保存前景图的属性
    let fgProperties = null;
    if (fgImages[index]) {
        fgProperties = {
            normalizedLeft: fgImages[index].normalizedLeft,
            normalizedTop: fgImages[index].normalizedTop,
            normalizedScaleX: fgImages[index].normalizedScaleX,
            normalizedScaleY: fgImages[index].normalizedScaleY,
            normalizedAngle: fgImages[index].normalizedAngle,
            normalizedOpacity: fgImages[index].normalizedOpacity,
            normalizedBlendMode: fgImages[index].normalizedBlendMode
        };
        // 移除旧的前景图
        canvas.remove(fgImages[index]);
        // 确保数组中移除引用
        fgImages[index] = null;
    }

    // 加载新的前景图
    fabric.Image.fromURL(newImageSrc, function (fgImg) {
        // 先设置中心点坐标系统
        fgImg.set({
            originX: 'center',
            originY: 'center'
        });

        // 设置前景图样式属性
        fgImg.set({
            cornerSize: 10,
            borderColor: '#3B82F6',
            cornerColor: index === 0 ? 'yellow' : 'green', // 不同前景图使用不同颜色标识
            cornerStyle: 'circle', // 设置为圆角控件
            transparentCorners: false,
            // 关键点：设置selectable为true以确保点击区域正确
            selectable: true
        });

        // 应用保存的属性或使用默认值
        if (fgProperties) {
            fgImg.set({
                normalizedLeft: fgProperties.normalizedLeft,
                normalizedTop: fgProperties.normalizedTop,
                normalizedScaleX: fgProperties.normalizedScaleX,
                normalizedScaleY: fgProperties.normalizedScaleY,
                normalizedAngle: fgProperties.normalizedAngle,
                normalizedOpacity: fgProperties.normalizedOpacity,
                normalizedBlendMode: fgProperties.normalizedBlendMode,
                opacity: fgProperties.normalizedOpacity,
                globalCompositeOperation: fgProperties.normalizedBlendMode,
                angle: fgProperties.normalizedAngle,
                left: fgProperties.normalizedLeft * bgWidth * scaleRatio,
                top: fgProperties.normalizedTop * bgHeight * scaleRatio,
                scaleX: fgProperties.normalizedScaleX * scaleRatio,
                scaleY: fgProperties.normalizedScaleY * scaleRatio
            });
        } else {
            // 初始位置：画布中心或偏移位置
            const initialLeft = (bgWidth / 2 + (index * 50 - 25)) * scaleRatio;
            const initialTop = bgHeight / 2 * scaleRatio;
            fgImg.set({
                left: initialLeft,
                top: initialTop,
                scaleX: scaleRatio,
                scaleY: scaleRatio,
                normalizedLeft: 0.5 + (index * 0.1 - 0.05),
                normalizedTop: 0.5,
                normalizedScaleX: 1,
                normalizedScaleY: 1,
                normalizedAngle: 0,
                normalizedOpacity: 1,
                normalizedBlendMode: 'source-over'
            });
        }

        // 添加到画布
        canvas.add(fgImg);

        // 强制重新计算边界框，确保点击区域与显示区域一致
        fgImg.setCoords();

        // 设置为活动对象
        canvas.setActiveObject(fgImg);
        canvas.renderAll();

        // 更新前景图引用
        fgImages[index] = fgImg;
        activeFgIndex = index;

    }, { crossOrigin: isLocalFile ? '' : 'anonymous' });
}

// 绑定所有交互事件
function bindEvents() {
    // 监听对象移动 - 更新标准化位置
    canvas.on('object:moved', function (e) {
        const obj = e.target;
        obj.normalizedLeft = obj.left / (bgWidth * scaleRatio);
        obj.normalizedTop = obj.top / (bgHeight * scaleRatio);
        // 更新活动前景图索引
        updateActiveFgIndex();
    });

    // 监听对象缩放 - 更新标准化缩放
    canvas.on('object:scaled', function (e) {
        const obj = e.target;
        obj.normalizedScaleX = obj.scaleX / scaleRatio;
        obj.normalizedScaleY = obj.scaleY / scaleRatio;
        // 同时更新位置，因为缩放可能导致位置变化
        obj.normalizedLeft = obj.left / (bgWidth * scaleRatio);
        obj.normalizedTop = obj.top / (bgHeight * scaleRatio);

        // 更新活动前景图索引
        updateActiveFgIndex();

    });

    // 监听对象旋转 - 更新标准化角度
    canvas.on('object:rotated', function (e) {
        const obj = e.target;
        obj.normalizedAngle = obj.angle;

        // 更新活动前景图索引
        updateActiveFgIndex();

    });

    // 透明度控制滑块事件
    const opacitySlider = document.getElementById('opacity-slider');
    opacitySlider.addEventListener('input', function (e) {
        // 优先使用选中对象，否则使用当前活动的前景图
        const targetObj = canvas.getActiveObject() || fgImages[activeFgIndex];
        if (!targetObj) return;
        // 设置对象透明度
        targetObj.opacity = parseFloat(e.target.value);
        // 保存标准化透明度
        if (!targetObj.normalizedOpacity) {
            targetObj.normalizedOpacity = 1;
        }
        targetObj.normalizedOpacity = parseFloat(e.target.value);
        canvas.renderAll();
        updateActiveFgIndex();

    });

    // 叠加模式选择器事件
    const blendModeSelect = document.getElementById('blend-mode-select');
    blendModeSelect.addEventListener('change', function (e) {
        // 优先使用选中对象，否则使用当前活动的前景图
        const targetObj = canvas.getActiveObject() || fgImages[activeFgIndex];
        if (!targetObj) return;
        // 设置对象叠加模式
        targetObj.globalCompositeOperation = e.target.value;
        // 保存标准化叠加模式
        if (!targetObj.normalizedBlendMode) {
            targetObj.normalizedBlendMode = 'source-over';
        }
        targetObj.normalizedBlendMode = e.target.value;
        canvas.renderAll();
        updateActiveFgIndex();

    });

    // 监听对象选择事件，更新控件值
    canvas.on('selection:created', function (e) {
        const selectedObj = e.target;
        if (selectedObj && selectedObj.type === 'image') {
            // 更新透明度滑块
            opacitySlider.value = selectedObj.opacity || 1;
            opacitySlider.style.opacity = 1;
            // 更新叠加模式选择器
            blendModeSelect.value = selectedObj.globalCompositeOperation || 'source-over';
            blendModeSelect.style.opacity = 1;

            // 更新活动前景图索引
            updateActiveFgIndex();
        } else {
            // 未选中对象时，控件仍可使用，不降低透明度
            opacitySlider.style.opacity = 1;
            blendModeSelect.style.opacity = 1;
        }
    });

    canvas.on('selection:updated', function (e) {
        const selectedObj = e.target;
        if (selectedObj && selectedObj.type === 'image') {
            // 更新透明度滑块
            opacitySlider.value = selectedObj.opacity || 1;
            opacitySlider.style.opacity = 1;

            // 更新叠加模式选择器
            blendModeSelect.value = selectedObj.globalCompositeOperation || 'source-over';
            blendModeSelect.style.opacity = 1;

            // 更新活动前景图索引
            updateActiveFgIndex();

        } else {
            // 未选中对象时，控件仍可使用，不降低透明度
            opacitySlider.style.opacity = 1;
            blendModeSelect.style.opacity = 1;
        }
    });

    canvas.on('selection:cleared', function () {
        // 清除选择后，控件仍可使用，不降低透明度
        opacitySlider.style.opacity = 1;
        blendModeSelect.style.opacity = 1;

        // 但恢复滑块值为当前活动前景图的值
        if (fgImages[activeFgIndex]) {
            opacitySlider.value = fgImages[activeFgIndex].opacity || 1;
            blendModeSelect.value = fgImages[activeFgIndex].globalCompositeOperation || 'source-over';
        }
    });

    // 更新活动前景图索引
    function updateActiveFgIndex() {
        const activeObj = canvas.getActiveObject();
        if (activeObj && activeObj.type === 'image') {
            // 查找当前选中对象在前景图数组中的索引
            for (let i = 0; i < fgImages.length; i++) {
                if (fgImages[i] === activeObj) {
                    activeFgIndex = i;
                    break;
                }
            }
        }
    }

    // 键盘控制
    document.addEventListener('keydown', function (e) {
        const activeObj = canvas.getActiveObject();
        if (!activeObj) return;

        // 计算基于当前缩放的移动步长
        const step = 2 / scaleRatio;

        // 根据方向键移动
        switch (e.key) {
            case 'ArrowUp':
                activeObj.top -= step;
                e.preventDefault();
                break;
            case 'ArrowDown':
                activeObj.top += step;
                e.preventDefault();
                break;
            case 'ArrowLeft':
                activeObj.left -= step;
                e.preventDefault();
                break;
            case 'ArrowRight':
                activeObj.left += step;
                e.preventDefault();
                break;
            default:
                return;
        }

        // 立即更新标准化位置
        activeObj.normalizedLeft = activeObj.left / (bgWidth * scaleRatio);
        activeObj.normalizedTop = activeObj.top / (bgHeight * scaleRatio);
        canvas.renderAll();
        updateActiveFgIndex();

    });

    // 鼠标滚轮缩放前景图
    canvas.on('mouse:wheel', function (opt) {
        const activeObj = canvas.getActiveObject();
        // 只在有选中对象且是图片类型时处理滚轮事件
        if (!activeObj || activeObj.type !== 'image') return;

        const delta = opt.e.deltaY;
        // 计算缩放因子，负delta表示向上滚动（放大），正delta表示向下滚动（缩小）
        const zoomFactor = delta > 0 ? 0.95 : 1.05;

        // 保存当前缩放值
        const currentScaleX = activeObj.scaleX;
        const currentScaleY = activeObj.scaleY;

        // 应用新的缩放值
        activeObj.scaleX = currentScaleX * zoomFactor;
        activeObj.scaleY = currentScaleY * zoomFactor;

        // 同时更新标准化缩放属性
        activeObj.normalizedScaleX = activeObj.scaleX / scaleRatio;
        activeObj.normalizedScaleY = activeObj.scaleY / scaleRatio;

        // 强制重新计算边界框
        activeObj.setCoords();

        // 渲染更新后的画布
        canvas.renderAll();

        // 阻止默认的滚轮行为（如页面滚动）
        opt.e.preventDefault();

        // 更新活动前景图索引
        updateActiveFgIndex();

    });
}

// 调整画布大小以适应窗口
function resizeCanvas() {
    if (!bgWidth || !bgHeight) return;

    // 获取容器尺寸
    const container = document.getElementById('canvas-container');
    const containerWidth = container.clientWidth;
    const containerHeight = window.innerHeight * 0.9;

    // 计算新的缩放比例
    const newScale = Math.min(
        containerWidth / bgWidth,
        containerHeight / bgHeight
    );

    // 保存当前缩放比例用于计算
    const oldScale = scaleRatio;

    // 更新画布尺寸
    canvas.setWidth(bgWidth * newScale);
    canvas.setHeight(bgHeight * newScale);

    // 调整背景图
    if (canvas.backgroundImage) {
        canvas.backgroundImage.scaleX = newScale;
        canvas.backgroundImage.scaleY = newScale;
    }

    // 调整所有对象位置和大小
    canvas.forEachObject(function (obj) {
        // 初始化场景检测优化 - 更宽松的条件确保前景图在中心位置
        if (oldScale === 1 && Math.abs(obj.normalizedLeft - 0.5) < 0.01 && Math.abs(obj.normalizedTop - 0.5) < 0.01) {
            // 初始化时直接使用标准化坐标计算位置
            obj.set({
                left: bgWidth * 0.5 * newScale,
                top: bgHeight * 0.5 * newScale,
                scaleX: newScale,
                scaleY: newScale,
                angle: obj.angle
            });
        } else {
            // 正常情况下使用比例计算
            obj.set({
                left: (obj.left / oldScale) * newScale,
                top: (obj.top / oldScale) * newScale,
                scaleX: (obj.scaleX / oldScale) * newScale,
                scaleY: (obj.scaleY / oldScale) * newScale,
                angle: obj.angle
            });
        }

        // 同时更新标准化位置
        obj.normalizedLeft = obj.left / (bgWidth * newScale);
        obj.normalizedTop = obj.top / (bgHeight * newScale);
        obj.normalizedScaleX = obj.scaleX / newScale;
        obj.normalizedScaleY = obj.scaleY / newScale;
    });

    // 更新当前缩放比例
    scaleRatio = newScale;

    canvas.renderAll();

    // 确保窗口大小改变后前景图仍然可点击
    ensureClickableForegrounds();
}

// 重置视图
function resetView() {
    canvas.forEachObject(function (obj) {
        // 重置到中心位置或偏移位置
        let index = fgImages.indexOf(obj);
        let normalizedLeft = 0.5;
        let normalizedTop = 0.5;

        // 为第二个前景图设置稍微不同的位置
        if (index === 1) {
            normalizedLeft = 0.55;
        }

        // 重置属性
        obj.normalizedLeft = normalizedLeft;
        obj.normalizedTop = normalizedTop;
        obj.normalizedScaleX = 1;
        obj.normalizedScaleY = 1;
        obj.normalizedAngle = 0;
        // 重置叠加模式和透明度
        obj.normalizedBlendMode = 'source-over';
        obj.normalizedOpacity = 1;
        // 应用新位置和属性
        obj.set({
            left: bgWidth * normalizedLeft * scaleRatio,
            top: bgHeight * normalizedTop * scaleRatio,
            scaleX: scaleRatio,
            scaleY: scaleRatio,
            angle: 0,
            globalCompositeOperation: 'source-over',
            opacity: 1
        });
    });

    // 设置第一个前景图为活动对象，确保重置后可以被选中
    if (fgImages[0]) {
        canvas.setActiveObject(fgImages[0]);
        activeFgIndex = 0;
    }

    // 更新UI控件显示
    document.getElementById('opacity-slider').value = 1;
    document.getElementById('blend-mode-select').value = 'source-over';

    // 确保最后渲染，保证所有更改都生效
    canvas.renderAll();
}

//去除背景只保存前景图的mask
async function downloadCanvasmask() {
    // 隐藏所有控件，确保不被包含在下载的图片中
    const controls = document.querySelector('.controls');
    const hint = document.querySelector('.keyboard-hint');
    const imageInputContainer = document.querySelector('.image-input-container');
    const originalControlsDisplay = controls.style.display;
    const originalHintDisplay = hint ? hint.style.display : '';
    const originalImageInputDisplay = imageInputContainer ? imageInputContainer.style.display : '';

    controls.style.display = 'none';
    if (hint) hint.style.display = 'none';
    if (imageInputContainer) imageInputContainer.style.display = 'none';

    // 渲染一次以确保控件隐藏
    canvas.renderAll();

    // 确保所有对象的标准化属性都是最新的
    canvas.forEachObject(function (obj) {
        obj.normalizedLeft = obj.left / (bgWidth * scaleRatio);
        obj.normalizedTop = obj.top / (bgHeight * scaleRatio);
        obj.normalizedScaleX = obj.scaleX / scaleRatio;
        obj.normalizedScaleY = obj.scaleY / scaleRatio;
        obj.normalizedAngle = obj.angle;
    });

    // 创建一个新的临时canvas元素用于导出前景图
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    // 设置临时画布尺寸为原始背景图尺寸
    tempCanvas.width = bgWidth;
    tempCanvas.height = bgHeight;

    // 不绘制背景图，只绘制前景对象
    canvas.getObjects().forEach(function (obj) {
        if (obj.type === 'image' && obj._element) {
            // 保存当前上下文状态
            tempCtx.save();

            // 计算实际位置 - 考虑背景图尺寸和标准化位置
            const actualLeft = obj.normalizedLeft * bgWidth;
            const actualTop = obj.normalizedTop * bgHeight;

            // 计算实际尺寸 - 考虑原始图片尺寸和标准化缩放
            const actualWidth = obj.width * obj.normalizedScaleX;
            const actualHeight = obj.height * obj.normalizedScaleY;

            // 计算旋转角度（弧度）
            const rotationInRadians = (obj.normalizedAngle || 0) * Math.PI / 180;

            // 应用变换
            tempCtx.translate(actualLeft, actualTop); // 移动到中心点
            tempCtx.rotate(rotationInRadians); // 应用旋转

            // 设置透明度
            tempCtx.globalAlpha = obj.normalizedOpacity || obj.opacity || 1;

            // 设置叠加模式
            tempCtx.globalCompositeOperation = obj.normalizedBlendMode || obj.globalCompositeOperation || 'source-over';

            // 绘制图片 - 从中心点向四周绘制
            tempCtx.drawImage(
                obj._element,
                -actualWidth / 2,  // 向左偏移一半宽度
                -actualHeight / 2, // 向上偏移一半高度
                actualWidth,       // 使用计算出的实际宽度
                actualHeight       // 使用计算出的实际高度
            );

            // 恢复默认设置
            tempCtx.globalAlpha = 1;
            tempCtx.globalCompositeOperation = 'source-over';

            // 恢复上下文状态
            tempCtx.restore();
        }
    });

    // 将前景图转换为base64格式（PNG格式自动包含透明度）
    let maskBase64 = tempCanvas.toDataURL({
        format: 'png',
        quality: 1.0
    });

    // 转换为blob
    let maskBlob = await (await fetch(maskBase64)).blob();

    // 生成文件名
    const filename = `${token}_mask.png`;

    // 创建表单数据并上传
    let formData = new FormData();
    formData.append('image', maskBlob, filename);
    formData.append('overwrite', 'true');
    formData.append('type', 'temp');
    formData.append('subfolder', 'fkimgedit');

    const resp = await fetch('/upload/image', {
        method: 'POST',
        body: formData,
    });

    if (resp.status === 200) {
        const data = await resp.json();
        //  console.log('前景图已成功保存:', data);
    }

    try {
        postMessageToParent({
            type: 'setToken'
        });
    } catch (error) {

    }

}

// 下载画布内容 - 彻底重写以确保导出内容与编辑结果完全一致
async function downloadCanvas() {
    await downloadCanvasmask();//先存储遮罩
    // 隐藏所有控件，确保不被包含在下载的图片中
    const controls = document.querySelector('.controls');
    const hint = document.querySelector('.keyboard-hint');
    const imageInputContainer = document.querySelector('.image-input-container');
    const originalControlsDisplay = controls.style.display;
    const originalHintDisplay = hint ? hint.style.display : '';
    const originalImageInputDisplay = imageInputContainer ? imageInputContainer.style.display : '';

    controls.style.display = 'none';
    if (hint) hint.style.display = 'none';
    if (imageInputContainer) imageInputContainer.style.display = 'none';

    // 渲染一次以确保控件隐藏
    canvas.renderAll();

    // 关键点1: 在导出前确保所有对象的标准化属性都是最新的
    canvas.forEachObject(function (obj) {
        obj.normalizedLeft = obj.left / (bgWidth * scaleRatio);
        obj.normalizedTop = obj.top / (bgHeight * scaleRatio);
        obj.normalizedScaleX = obj.scaleX / scaleRatio;
        obj.normalizedScaleY = obj.scaleY / scaleRatio;
        obj.normalizedAngle = obj.angle;
    });

    // 创建一个新的临时canvas元素用于导出
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    // 设置临时画布尺寸为原始背景图尺寸
    tempCanvas.width = bgWidth;
    tempCanvas.height = bgHeight;
    // 1. 绘制背景图
    if (canvas.backgroundImage && canvas.backgroundImage._element) {
        const bgImg = canvas.backgroundImage._element;
        tempCtx.drawImage(bgImg, 0, 0, bgWidth, bgHeight);
    }
    // 2. 绘制所有前景对象
    canvas.getObjects().forEach(function (obj) {
        if (obj.type === 'image' && obj._element) {
            // 保存当前上下文状态
            tempCtx.save();
            // 关键点2: 计算实际位置 - 考虑背景图尺寸和标准化位置
            const actualLeft = obj.normalizedLeft * bgWidth;
            const actualTop = obj.normalizedTop * bgHeight;

            // 关键点3: 计算实际尺寸 - 考虑原始图片尺寸和标准化缩放
            const actualWidth = obj.width * obj.normalizedScaleX;
            const actualHeight = obj.height * obj.normalizedScaleY;

            // 关键点4: 计算旋转角度（弧度）
            const rotationInRadians = (obj.normalizedAngle || 0) * Math.PI / 180;

            // 应用变换
            tempCtx.translate(actualLeft, actualTop); // 移动到中心点
            tempCtx.rotate(rotationInRadians); // 应用旋转

            // 设置叠加模式
            tempCtx.globalCompositeOperation = obj.normalizedBlendMode || obj.globalCompositeOperation || 'source-over';

            // 设置透明度
            tempCtx.globalAlpha = obj.normalizedOpacity || obj.opacity || 1;

            // 绘制图片 - 从中心点向四周绘制
            tempCtx.drawImage(
                obj._element,
                -actualWidth / 2,  // 向左偏移一半宽度
                -actualHeight / 2, // 向上偏移一半高度
                actualWidth,       // 使用计算出的实际宽度
                actualHeight       // 使用计算出的实际高度
            );

            // 恢复默认设置
            tempCtx.globalAlpha = 1;
            tempCtx.globalCompositeOperation = 'source-over';
            // 恢复上下文状态
            tempCtx.restore();
        }
    });
    let hbbase64 = tempCanvas.toDataURL({
        format: 'png',
        quality: 1.0
    });
    let newblob = await (await fetch(hbbase64)).blob();

    const filename = `${token}.png`;
    let formData = new FormData()
    formData.append('image', newblob, filename)
    formData.append('overwrite', 'true')
    formData.append('type', 'temp')
    formData.append('subfolder', 'fkimgedit')
    const resp = await fetch('/upload/image', {
        method: 'POST',
        body: formData,
    })
    if (resp.status === 200) {
        const data = await resp.json()
        //   console.log(data)
        savshuxing();//存储所有前景图位置及尺寸属性用于下次读取

    }
    // 恢复控件显示
    /*   setTimeout(() => {
           controls.style.display = originalControlsDisplay;
           if (hint) hint.style.display = originalHintDisplay;
           if (imageInputContainer) imageInputContainer.style.display = originalImageInputDisplay;
       }, 100);*/


    try {
        postMessageToParent({
            type: 'setToken'
        });
    } catch (error) {

    }
}

async function savshuxing() { //存储所有前景图位置及尺寸属性用于下次读取
    try {
        // 确保所有对象的标准化属性都是最新的
        canvas.forEachObject(function (obj) {
            if (obj.type === 'image' && obj !== canvas.backgroundImage) {
                obj.normalizedLeft = obj.left / (bgWidth * scaleRatio);
                obj.normalizedTop = obj.top / (bgHeight * scaleRatio);
                obj.normalizedScaleX = obj.scaleX / scaleRatio;
                obj.normalizedScaleY = obj.scaleY / scaleRatio;
                obj.normalizedAngle = obj.angle;
                obj.normalizedOpacity = obj.opacity || 1;
                obj.normalizedBlendMode = obj.globalCompositeOperation || 'source-over';
            }
        });
        // 收集所有前景图的属性
        const fgProperties = [];
        fgImages.forEach((fgImg, index) => {
            if (fgImg && fgImg.type === 'image') {
                fgProperties.push({
                    index: index,
                    normalizedLeft: fgImg.normalizedLeft || 0.5,
                    normalizedTop: fgImg.normalizedTop || 0.5,
                    normalizedScaleX: fgImg.normalizedScaleX || 1,
                    normalizedScaleY: fgImg.normalizedScaleY || 1,
                    normalizedAngle: fgImg.normalizedAngle || 0,
                    normalizedOpacity: fgImg.normalizedOpacity || 1,
                    normalizedBlendMode: fgImg.normalizedBlendMode || 'source-over'
                });
            }
        });
        // 将属性存储为JSON字符串
        const propertiesJSON = JSON.stringify(fgProperties);
        // 保存到localStorage
        localStorage.setItem('fkimage_sx' + ifid, propertiesJSON);
        // 同时保存到全局变量，方便页面内使用
        window.fgProperties = fgProperties;
        //  console.log(fgProperties);
        // 如果需要，也可以返回保存的数据
        return fgProperties;
    } catch (error) {
        return null;
    }
}

async function loadshuxing() { //读取存储的前景图位置及尺寸属性更新到画布
    try {
        // 从localStorage读取保存的属性数据
        const propertiesJSON = localStorage.getItem('fkimage_sx' + ifid);

        // 检查是否存在保存的数据
        if (!propertiesJSON) {
            return false;
        }

        // 解析JSON数据
        const fgProperties = JSON.parse(propertiesJSON);

        // 检查解析结果是否为数组
        if (!Array.isArray(fgProperties)) {
            return false;
        }

        // 将属性应用到对应的前景图对象
        fgProperties.forEach(props => {
            // 确保索引有效且对应的前景图对象存在
            if (props.index !== undefined &&
                props.index >= 0 &&
                props.index < fgImages.length &&
                fgImages[props.index]) {

                const fgImg = fgImages[props.index];

                // 应用标准化属性
                fgImg.normalizedLeft = props.normalizedLeft || 0.5;
                fgImg.normalizedTop = props.normalizedTop || 0.5;
                fgImg.normalizedScaleX = props.normalizedScaleX || 1;
                fgImg.normalizedScaleY = props.normalizedScaleY || 1;
                fgImg.normalizedAngle = props.normalizedAngle || 0;
                fgImg.normalizedOpacity = props.normalizedOpacity || 1;
                fgImg.normalizedBlendMode = props.normalizedBlendMode || 'source-over';

                // 计算实际的位置、缩放、旋转等属性并应用
                fgImg.set({
                    left: fgImg.normalizedLeft * bgWidth * scaleRatio,
                    top: fgImg.normalizedTop * bgHeight * scaleRatio,
                    scaleX: fgImg.normalizedScaleX * scaleRatio,
                    scaleY: fgImg.normalizedScaleY * scaleRatio,
                    angle: fgImg.normalizedAngle,
                    opacity: fgImg.normalizedOpacity,
                    globalCompositeOperation: fgImg.normalizedBlendMode
                });

                // 更新控件的值
                if (props.index === activeFgIndex) {
                    const opacitySlider = document.getElementById('opacity-slider');
                    const blendModeSelect = document.getElementById('blend-mode-select');

                    if (opacitySlider) opacitySlider.value = fgImg.normalizedOpacity;
                    if (blendModeSelect) blendModeSelect.value = fgImg.normalizedBlendMode;
                }
            }
        });

        // 保存到全局变量
        window.fgProperties = fgProperties;

        // 渲染画布以更新显示
        canvas.renderAll();

        // 确保前景图可点击
        ensureClickableForegrounds();

        return true;
    } catch (error) {
        return false;
    }
}

// 页面加载完成后初始化
window.addEventListener('load', init);

//传消息给父窗口
function postMessageToParent(message) {
    window.parent.postMessage(message, '*');
}

// 接收消息
window.addEventListener('message', async function (event) {
    //   console.log('收到父窗口消息:', event.data);
    if (event.data.type === 'populate') {
        // 处理数据
        //   console.log('处理数据:', event.data.data);
        bgImageUrl = event.data.data.background.indexOf("base64") == -1 ? `/api/view?type=temp&filename=${event.data.data.background}&subfolder=fkimgedit` : await base64ToBlobURL(event.data.data.background);
        fgImageUrls = []

        // 处理前景图数据 - 支持两个前景图
        if (event.data.data.foreground) {
            fgImageUrls[0] = event.data.data.foreground.indexOf("base64") == -1 ? `/api/view?type=temp&filename=${event.data.data.foreground}&subfolder=fkimgedit` : await base64ToBlobURL(event.data.data.foreground);
        }
        if (event.data.data.foreground2) {
            fgImageUrls[1] = event.data.data.foreground2.indexOf("base64") == -1 ? `/api/view?type=temp&filename=${event.data.data.foreground2}&subfolder=fkimgedit` : await base64ToBlobURL(event.data.data.foreground2);
        }

        token = event.data.data.token;
        // 优化初始化机制，简化延迟逻辑
        // 修复：移除多余的延迟参数，确保正确的Promise链执行
        updateBackgroundImage(bgImageUrl).then(() => {
            // 确保前景图可点击
            ensureClickableForegrounds();
        });
        // 显示控件
        document.querySelector('.controls').style.display = 'flex';
        document.querySelector('.image-input-container').style.display = 'flex';

    }
});

//base64转blobURL
async function base64ToBlobURL(base64) {
    let binary = atob(base64);
    let array = [];
    for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
    }
    return URL.createObjectURL(new Blob([new Uint8Array(array)], { type: 'image/png' }));
}

setInterval(() => {
    if (!bgImageUrl.includes('placehold.co')) {
        savshuxing(); // 保存所有前景图位置及尺寸属性
    }
}, 3000);

