// --- 状态变量 ---
let scale = 1, offsetX = 0, offsetY = 0;
let mode = null, activeHandle = null;
let startX, startY, box = { x: 0, y: 0, w: 0, h: 0 };
let mouseImgX = 0, mouseImgY = 0;
let dragCounter = 0; // 解决拖拽闪烁计数器

const container = document.getElementById('container_img');
const transBox = document.getElementById('transform_container');
const img = document.getElementById('img_preview');
const svg = document.getElementById('svg_layer');
const canvas = document.getElementById('color_picker_canvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });

// --- 外部调用接口 ---

window.addPointMark = function (label, x, y) {
    const g = createSVGElement('g', { 
        transform: `translate(${x}, ${y})`,
        class: 'mark-group' 
    });

    const circle = createSVGElement('circle', { 
        cx: 0, cy: 0, 
        class: 'mark-point dynamic-circle' 
    });

    const text = createSVGElement('text', { 
        x: 0, 
        y: 0, 
        class: 'mark-text dynamic-text',
        'text-anchor': 'middle',
        'dominant-baseline': 'middle' 
    });
    text.setAttribute('style', 'transform: translateY(-15px); transform-box: fill-box; transform-origin: center;');
    
    text.textContent = label;
    g.appendChild(circle);
    g.appendChild(text);

    const layer = document.getElementById('mark_points_layer');
    if (layer) {
        layer.appendChild(g);
        updateStyleLock(); 
    }
};

window.addRectMark = function (label, l, t, r, b) {
    const layer = document.getElementById('mark_rects_layer');
    if (!layer) return;

    // 1. 显式转换为数字
    const left = Number(l);
    const top = Number(t);
    const right = Number(r);
    const bottom = Number(b);

    const width = right - left;
    const height = bottom - top;

    // 2. 参考 addPointMark：创建一个 g 标签并直接平移到左上角 (left, top)
    // 这样 g 内部的所有元素就以 (left, top) 为原点 (0,0) 了
    const g = createSVGElement('g', {
        transform: `translate(${left}, ${top})`,
        class: 'mark-group'
    });

    // 3. 创建矩形：坐标改为 0, 0
    const rect = createSVGElement('rect', {
        x: 0,
        y: 0,
        width: width,
        height: height,
        class: 'mark-rect dynamic-rect'
    });

    // 4. 文字属性：坐标也改为 0, 0
    const text = createSVGElement('text', {
        x: 0,
        y: 0,
        class: 'mark-text dynamic-text',
        'text-anchor': 'start', // 靠左对齐
        'dominant-baseline': 'alphabetical' 
    });
    
    // 参照 addPointMark 的样式处理，向上平移一点点防止压线
    text.setAttribute('style', 'transform: translateY(-5px); transform-box: fill-box; transform-origin: left bottom;');
    text.textContent = label;

    g.appendChild(rect);
    g.appendChild(text);
    layer.appendChild(g);

    // 5. 刷新样式
    updateStyleLock();
};

window.clearAllMarks = function () {
    const pointsLayer = document.getElementById('mark_points_layer');
    const rectsLayer = document.getElementById('mark_rects_layer');
    if (pointsLayer) pointsLayer.innerHTML = '';
    if (rectsLayer) rectsLayer.innerHTML = '';
    console.log("所有标记已清除");
};

window.highlightMark = function (label) {
    window.clearHighlight();
    const allGroups = document.querySelectorAll('#mark_points_layer g, #mark_rects_layer g');

    allGroups.forEach(g => {
        const textNode = g.querySelector('.mark-text');
        if (textNode && textNode.textContent === label) {
            g.classList.add('highlighted-mark');
        }
    });
};

window.clearHighlight = function () {
    const highlighted = document.querySelectorAll('.highlighted-mark');
    highlighted.forEach(el => el.classList.remove('highlighted-mark'));
};

window.clearSelection = function () {
    box = { x: 0, y: 0, w: 0, h: 0 };
    updateSelectionUI(); 
};

function createSVGElement(tag, attrs = {}) {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (let k in attrs) {
        el.setAttribute(k, attrs[k]);
    }
    return el;
}

function updateStyleLock() {
    transBox.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    const invScale = 1 / scale;

    document.querySelectorAll('.dynamic-text').forEach(el => {
        el.style.fontSize = "14px"; 
        // 核心修改：确保缩放是以左下角/起始点为基准，这样位置才不会飘
        el.setAttribute('transform', `scale(${invScale})`);
        
        // 如果你使用了 transform-origin，请确保它是起始点
        el.style.transformOrigin = "left bottom"; 
        
        el.setAttribute('stroke-width', (2 * invScale) + "px");
        el.style.paintOrder = "stroke";
    });

    // ... 其余圆点、矩形粗细、手柄的逻辑保持不变 ...
    document.querySelectorAll('.dynamic-circle').forEach(el => {
        el.setAttribute('r', 4 * invScale); 
        el.setAttribute('stroke-width', (1.5 * invScale) + "px");
    });

    const sw = Math.max(1, 1.5 * invScale);
    document.querySelectorAll('.dynamic-rect').forEach(el => el.setAttribute('stroke-width', sw));
    
    document.querySelectorAll('.handle').forEach(h => {
        h.setAttribute('r', 5 * invScale);
        h.style.strokeWidth = (10 * invScale) + "px";
    });
}

function getImgCoords(e) {
    const rect = container.getBoundingClientRect();
    const x = (e.clientX - rect.left - offsetX) / scale;
    const y = (e.clientY - rect.top - offsetY) / scale;
    return {
        x: Math.max(0, Math.min(x, img.naturalWidth)),
        y: Math.max(0, Math.min(y, img.naturalHeight))
    };
}

img.onload = () => {
    img.style.willChange = "transform";
    svg.style.willChange = "transform";
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    ctx.drawImage(img, 0, 0);
    svg.setAttribute('viewBox', `0 0 ${img.naturalWidth} ${img.naturalHeight}`);
    updateStyleLock();
};

container.onwheel = (e) => {
    e.preventDefault();
    const zoomSpeed = 0.1;
    const delta = e.deltaY > 0 ? 1 - zoomSpeed : 1 + zoomSpeed;
    const newScale = scale * delta;
    if (newScale < 0.05 || newScale > 100) return;

    const rect = container.getBoundingClientRect();
    const c = getImgCoords(e);
    scale = newScale;
    offsetX = (e.clientX - rect.left) - c.x * scale;
    offsetY = (e.clientY - rect.top) - c.y * scale;
    updateStyleLock();
};

// --- 修改点 1: 多模式拖拽触发 ---
container.onmousedown = (e) => {
    const c = getImgCoords(e);
    e.preventDefault();

    // 允许 右键(2) / 中键(1) / Ctrl+左键(0) 平移
    if (e.button === 2 || e.button === 1 || (e.button === 0 && e.ctrlKey)) {
        mode = 'panning';
        startX = e.clientX;
        startY = e.clientY;
        container.classList.add('grabbing');
    }
    else if (e.button === 0) {
        if (e.target.classList.contains('handle')) {
            mode = 'resizing';
            activeHandle = e.target.id.replace('h_', '');
        } else if (e.target.id === 'selection_rect') {
            mode = 'moving';
            container.classList.add('grabbing');
        } else {
            mode = 'drawing';
            box = { x: c.x, y: c.y, w: 0, h: 0 };
            updateSelectionUI();
            document.getElementById('selection_group').style.visibility = 'visible';
        }
        startX = c.x;
        startY = c.y;
    }
};

const rgbToHex = (r, g, b) => {
    const toHex = (c) => c.toString(16).padStart(2, '0').toUpperCase();
    return "#" + toHex(r) + toHex(g) + toHex(b);
};

window.onmousemove = (e) => {
    const hud = document.getElementById('mouse_hud');
    const containerRect = container.getBoundingClientRect();

    const isInsideView = (
        e.clientX >= containerRect.left &&
        e.clientX <= containerRect.right &&
        e.clientY >= containerRect.top &&
        e.clientY <= containerRect.bottom
    );

    const c = getImgCoords(e);
    mouseImgX = c.x;
    mouseImgY = c.y;

    const posX = Math.floor(c.x);
    const posY = Math.floor(c.y);
    const W = img.naturalWidth;
    const H = img.naturalHeight;

    if (isInsideView && posX >= 0 && posX < W && posY >= 0 && posY < H) {
        if (hud.style.display !== 'flex') hud.style.display = 'flex';
        hud.style.left = (e.clientX + 15) + 'px';
        hud.style.top = (e.clientY + 15) + 'px';

        try {
            const p = ctx.getImageData(posX, posY, 1, 1).data;
            const hexStr = rgbToHex(p[0], p[1], p[2]);
            document.getElementById('hud_coords').textContent = `${posX}, ${posY}`;
            document.getElementById('hud_hex').textContent = hexStr;
            document.getElementById('hud_color_swatch').style.backgroundColor = hexStr;
        } catch (err) {}
    } else {
        if (hud.style.display !== 'none') hud.style.display = 'none';
    }

    if (mode === 'panning') {
        offsetX += (e.clientX - startX);
        offsetY += (e.clientY - startY);
        startX = e.clientX;
        startY = e.clientY;
        updateStyleLock();
        return;
    }

    if (!mode) return;

    const dx = c.x - startX, dy = c.y - startY;

    if (mode === 'drawing') {
        const endX = Math.max(0, Math.min(c.x, W));
        const endY = Math.max(0, Math.min(c.y, H));
        box.w = endX - box.x;
        box.h = endY - box.y;
    }
    else if (mode === 'moving') {
        let newX = box.x + dx;
        let newY = box.y + dy;
        if (newX < 0) newX = 0;
        else if (newX + box.w > W) newX = W - box.w;
        if (newY < 0) newY = 0;
        else if (newY + box.h > H) newY = H - box.h;
        box.x = newX;
        box.y = newY;
        startX = c.x; startY = c.y;
    }
    else if (mode === 'resizing') {
        if (activeHandle.includes('e')) box.w = Math.max(0, Math.min(c.x, W) - box.x);
        if (activeHandle.includes('w')) {
            const oldRight = box.x + box.w;
            box.x = Math.max(0, Math.min(c.x, oldRight));
            box.w = oldRight - box.x;
        }
        if (activeHandle.includes('s')) box.h = Math.max(0, Math.min(c.y, H) - box.y);
        if (activeHandle.includes('n')) {
            const oldBottom = box.y + box.h;
            box.y = Math.max(0, Math.min(c.y, oldBottom));
            box.h = oldBottom - box.y;
        }
        startX = c.x; startY = c.y;
    }
    updateSelectionUI();
};

let lastBoxState = { x: 0, y: 0, w: 0, h: 0 };

window.onmouseup = () => {
    container.classList.remove('grabbing');

    if (mode && mode !== 'panning') {
        if (box.w < 0) { box.x += box.w; box.w = Math.abs(box.w); }
        if (box.h < 0) { box.y += box.h; box.h = Math.abs(box.h); }

        const isChanged = box.x !== lastBoxState.x ||
            box.y !== lastBoxState.y ||
            box.w !== lastBoxState.w ||
            box.h !== lastBoxState.h;

        if (isChanged) {
            if (box.w < 2 || box.h < 2) {
                box = { x: 0, y: 0, w: 0, h: 0 };
                updateSelectionUI();
            }
            if (window.onSelectionFinalized) window.onSelectionFinalized({ ...box });
            if (typeof window.gp.iframe.on_area_selected === 'function') {
                window.gp.iframe.on_area_selected();
            }
            lastBoxState = { ...box };
        }
    }
    mode = null;
};

function updateSelectionUI() {
    const ux = box.w < 0 ? box.x + box.w : box.x;
    const uy = box.h < 0 ? box.y + box.h : box.y;
    const uw = Math.abs(box.w);
    const uh = Math.abs(box.h);

    const sRect = document.getElementById('selection_rect');
    sRect.setAttribute('x', ux);
    sRect.setAttribute('y', uy);
    sRect.setAttribute('width', uw);
    sRect.setAttribute('height', uh);

    const hPos = {
        nw: [ux, uy], n: [ux + uw / 2, uy], ne: [ux + uw, uy],
        e: [ux + uw, uy + uh / 2], se: [ux + uw, uy + uh],
        s: [ux + uw / 2, uy + uh], sw: [ux, uy + uh], w: [ux, uy + uh / 2]
    };
    for (let id in hPos) {
        const h = document.getElementById('h_' + id);
        if (h) { h.setAttribute('cx', hPos[id][0]); h.setAttribute('cy', hPos[id][1]); }
    }

    const selGroup = document.getElementById('selection_group');
    const infoPanel = document.getElementById('info_selection_box');

    if (uw >= 3 && uh >= 3) {
        selGroup.style.visibility = 'visible'; 
        if (infoPanel) infoPanel.style.display = 'block'; 

        document.getElementById('sel_start').textContent = `${Math.floor(ux)}, ${Math.floor(uy)}`;
        document.getElementById('sel_size').textContent = `${Math.floor(uw)} × ${Math.floor(uh)}`;
    } else {
        selGroup.style.visibility = 'hidden';
        if (infoPanel) infoPanel.style.display = 'none';
    }
}

container.oncontextmenu = (e) => e.preventDefault();

// --- 修改点 2: 键盘事件增加 Ctrl 反馈 ---
window.addEventListener('keydown', (e) => {
    // 按下 Ctrl 时变成抓取手势
    if (e.key === 'Control') {
        container.style.cursor = 'grab';
    }
    if (e.key >= '0' && e.key <= '9') {
        const x = Math.floor(mouseImgX);
        const y = Math.floor(mouseImgY);
        const p = ctx.getImageData(x, y, 1, 1).data;
        const hexColor = rgbToHex(p[0], p[1], p[2]);
        const colorData = { key: e.key, pos: [x, y], color: hexColor };
        if (typeof window.gp.iframe.on_color_picked === 'function') {
            window.gp.iframe.on_color_picked(colorData);
        }

        // window.gp.info.noti(`取色键 [${e.key}]`, `位置: ${x}, ${y}\n颜色: ${hexColor}`, 2000);

        copyToClipboard(`${x},${y},${hexColor}`, "  已将此取色数据已复制到剪贴板");
        

        if (window.onKeyPicker) window.onKeyPicker(e.key, x, y, p);
    }
});

window.addEventListener('keyup', (e) => {
    if (e.key === 'Control') {
        container.style.cursor = ''; 
    }
});

// --- 图片重置与加载 (其余所有逻辑保持不变) ---
window.resetViewToFit = function (padding = 10) {
    const containerRect = container.getBoundingClientRect();
    if (!img.naturalWidth || !img.naturalHeight || containerRect.width === 0) return;

    const availableW = containerRect.width - padding * 2;
    const availableH = containerRect.height - padding * 2;

    const scaleW = availableW / img.naturalWidth;
    const scaleH = availableH / img.naturalHeight;
    scale = Math.min(scaleW, scaleH, 1);

    offsetX = (containerRect.width - img.naturalWidth * scale) / 2;
    offsetY = padding;

    updateStyleLock();
};

document.getElementById('selection_rect').ondblclick = (e) => {
    e.stopPropagation();
    const transformTarget = document.getElementById('transform_container');
    const containerRect = container.getBoundingClientRect();
    const uw = Math.abs(box.w);
    const uh = Math.abs(box.h);
    if (uw < 5 || uh < 5) return;

    const ux = box.w < 0 ? box.x + box.w : box.x;
    const uy = box.h < 0 ? box.y + box.h : box.y;
    const centerX = ux + uw / 2;
    const centerY = uy + uh / 2;

    const padding = 40;
    const targetScale = Math.min((containerRect.width - padding) / uw, (containerRect.height - padding) / uh, 20);
    const targetOffsetX = containerRect.width / 2 - centerX * targetScale;
    const targetOffsetY = containerRect.height / 2 - centerY * targetScale;

    const isAlreadyAligned =
        Math.abs(scale - targetScale) < 0.01 &&
        Math.abs(offsetX - targetOffsetX) < 2 &&
        Math.abs(offsetY - targetOffsetY) < 2;

    transformTarget.style.transition = "all 0.4s cubic-bezier(0.25, 1, 0.5, 1)";
    if (!isAlreadyAligned) {
        scale = targetScale;
        offsetX = targetOffsetX;
        offsetY = targetOffsetY;
    } else {
        window.resetViewToFit(10);
    }
    updateStyleLock();
    setTimeout(() => { transformTarget.style.transition = "none"; }, 400);
};

container.ondblclick = (e) => {
    if (e.target.id === 'container_img' || e.target.classList.contains('screen-img-shower')) {
        window.resetViewToFit(10);
    }
};

async function showImg(url) {
    window.gp.image.path = url;
    $("#selection_group").css("visibility", "hidden");
    $("#mark_points_layer").empty();
    $("#mark_rects_layer").empty();
    $("#image_loading").show();

    try {
        let res = await eel.ascript_get_image(url)();
        if (res.status === "success") {
            let image = document.getElementById('img_preview');
            image.onload = () => {
                svg.setAttribute('viewBox', `0 0 ${image.naturalWidth} ${image.naturalHeight}`);
                canvas.width = image.naturalWidth;
                canvas.height = image.naturalHeight;
                ctx.drawImage(image, 0, 0);
                window.resetViewToFit(10);
                const selPanel = document.getElementById('info_selection_box');
                if (selPanel) selPanel.style.display = 'none';
                $('#header_pixels').text(`${image.naturalWidth} x ${image.naturalHeight}`);
                window.gp.iframe.on_image_loaded({ width: image.naturalWidth, height: image.naturalHeight, path: url });
            };
            image.src = res.data;
            $(image).attr('path', url);
            if ($(".zoomWindow").length > 0) {
                $(".zoomWindow").css("background-image", `url('${res.data}')`);
            }
            $('#status_file_path').text(url).attr('title', url);
        }
    } catch (err) {
        $('#status_file_path').text("读取图片失败: " + err).attr('title', url);
    } finally {
        $("#image_loading").hide();
    }
}

container.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dragCounter++;
    if (dragCounter === 1) container.classList.add('drag-active');
});

container.addEventListener('dragover', (e) => { e.preventDefault(); });

container.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter === 0) container.classList.remove('drag-active');
});

container.addEventListener('drop', async (e) => {
    e.preventDefault();
    dragCounter = 0;
    container.classList.remove('drag-active');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (!file.type.startsWith('image/')) return;
        $("#image_loading").show();
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = async (event) => {
            try {
                let res = await eel.save_dropped_image(event.target.result, file.name)();
                if (res.status === "success") await showImg(res.path);
            } catch (err) { console.error(err); } finally { $("#image_loading").hide(); }
        };
    }
});