// ==========================================
// 1. 基础配置与常量
// ==========================================
const DEBUG_STORAGE_KEY = 'gp_debug_tools';

// 切换折叠状态
function toggleGroup(targetId, iconId) {
    const el = document.getElementById(targetId);
    const icon = document.getElementById(iconId);

    if (el.classList.contains('show')) {
        el.classList.remove('show');
        icon.classList.replace('bi-chevron-down', 'bi-chevron-right');
    } else {
        el.classList.add('show');
        icon.classList.replace('bi-chevron-right', 'bi-chevron-down');
    }
}

// ==========================================
// 2. 核心交互逻辑 (严格保持你原来的赋值方式)
// ==========================================

/**
 * 核心逻辑：处理插件点击与选中状态
 */
function handlePlugClick(element, plugData) {
    // 1. 清除同组所有插件的选中状态
    const allItems = document.querySelectorAll('.plug-item');
    allItems.forEach(item => item.classList.remove('active'));

    // 2. 给当前点击的元素添加选中样式
    element.classList.add('active');

    // 3. 执行你的 Iframe 加载逻辑
    console.log("准备加载插件:", plugData.name);
    loadIframeAction(plugData.entry_html, plugData.class_name);
}

/**
 * 抽取出的 Iframe 加载方法 (严格对应你原有的 window.gp 赋值逻辑)
 */
function loadIframeAction(url, pluginId) {
    const iframe = document.getElementById('gpiframe'); // 确保 ID 一致
    if (iframe) {
        // --- 保持你原来的逻辑开始 ---
        if (window.gp && window.gp.iframe) {
            window.gp.iframe.window = iframe.contentWindow;
        }
        iframe.src = url;
        // --- 保持你原来的逻辑结束 ---
        console.log(`Iframe 已切换至: ${url}`);
    }
}

// ==========================================
// 3. 渲染函数 (createPlugItem 保持不变，新增调试专用渲染)
// ==========================================

/**
 * 原有渲染函数
 */
function createPlugItem(plug, isCloud = false) {
    const plugJson = JSON.stringify(plug).replace(/"/g, '&quot;');
    const iconPath = plug.icon; 

    const iconHtml = `
        <div class="plug-icon-mask me-2 mt-1" 
             style="--icon-url: url('/${iconPath}');">
        </div>`;

    return `
    <li class="plug-item list-group-item border-0 bg-transparent" onclick="handlePlugClick(this, ${plugJson})">
        <div class="d-flex align-items-start text-body">
            ${iconHtml}
            <div class="flex-grow-1 overflow-hidden">
                <div class="plug-title text-truncate">${plug.name}</div>
                <div class="plug-desc text-body-secondary small">${plug.description || '暂无描述'}</div>
            </div>
        </div>
    </li>`;
}

/**
 * 调试条目渲染函数 (适配你的样式并加入删除按钮)
 */
function createDebugItem(plug) {
    const plugJson = JSON.stringify(plug).replace(/"/g, '&quot;');
    return `
    <li class="plug-item list-group-item border-0 bg-transparent position-relative" onclick="handlePlugClick(this, ${plugJson})">
        <div class="d-flex align-items-start text-body">
            <div class="me-2 mt-1 d-flex align-items-center justify-content-center bg-light rounded border" 
                 style="width: 32px; height: 32px; flex-shrink: 0;">
                <i class="bi bi-bug text-primary"></i>
            </div>
            <div class="flex-grow-1 overflow-hidden">
                <div class="plug-title text-truncate">${plug.name}</div>
                <div class="plug-desc text-body-secondary small text-truncate">${plug.entry_html}</div>
            </div>
            <button class="btn btn-link btn-sm text-danger position-absolute end-0 top-0 mt-2 opacity-50" 
                    onclick="event.stopPropagation(); deleteDebugPlug('${plug.id}')">
                <i class="bi bi-x-circle"></i>
            </button>
        </div>
    </li>`;
}

// ==========================================
// 4. 数据加载逻辑
// ==========================================

// 3. 加载本地系统工具
async function loadSystemPlugs() {
    const plugs = await eel.ascript_plug_list()();
    const container = document.getElementById('group_plug_system');

    // 渲染数据
    container.innerHTML = plugs.map(p => createPlugItem(p)).join('');

    // 关键：如果折叠还是不工作，尝试手动实例化
    const collapseElements = document.querySelectorAll('.collapse');
    collapseElements.forEach(el => {
        new bootstrap.Collapse(el, { toggle: false });
    });
}

// 4. 模拟 AJAX 加载云端插件
function loadCloudPlugs() {
    const cloudContainer = document.getElementById('cloud-group');
    const fakeCloudData = [
        { name: "背景消除 (AI)", entry_html: "#", description: "云端算力支持" },
        { name: "图片高清化", entry_html: "#", description: "基于超分辨率模型" }
    ];

    setTimeout(() => {
        cloudContainer.innerHTML = fakeCloudData.map(p => {
            return `
            <li class="list-group-item list-group-item-action border-0 py-2 ps-3 text-muted" style="font-size: 14px;">
                <i class="bi bi-cloud-arrow-down me-2"></i>
                ${p.name} <small class="badge bg-light text-dark">待下载</small>
            </li>`;
        }).join('');
    }, 500); 
}

// ==========================================
// 5. 调试工具业务逻辑
// ==========================================

/**
 * 触发模态框显示
 */
function promptAddDebugPlug() {
    const modal = new bootstrap.Modal(document.getElementById('addDebugModal'));
    modal.show();
}

/**
 * 调用 Python 接口选择文件夹
 */
async function handleSelectFolder() {
    // 调用 Python 的 select_folder 函数
    const path = await eel.select_folder()(); 
    if (path) {
        document.getElementById('dbg_root').value = path;
    }
}

/**
 * 处理保存：拼接 URL 并存入 LocalStorage
 */
async function handleSaveDebugPlug() {
    const name = document.getElementById('dbg_name').value.trim();
    let root = document.getElementById('dbg_root').value.trim();
    const file = document.getElementById('dbg_file').value.trim() || 'index.html';

    if (!name || !root) {
        alert("请填写名称并选择根目录");
        return;
    }

    // 统一处理 Windows 路径斜杠，防止转义问题
    root = root.replace(/\\/g, '/');

    // 使用 btoa 进行 Base64 编码 (处理中文需 encodeURIComponent)
    const base64Root = btoa(encodeURIComponent(root));
    const virtualUrl = `/external/${base64Root}/${file}`;

    const newPlug = {
        name: name,
        entry_html: virtualUrl,
        description: `本地目录: ${root}`,
        id: 'debug_' + Date.now(),
        class_name: 'debug-plugin'
    };

    const list = JSON.parse(localStorage.getItem(DEBUG_STORAGE_KEY) || '[]');
    list.push(newPlug);
    localStorage.setItem(DEBUG_STORAGE_KEY, JSON.stringify(list));

    renderDebugPlugs();
    bootstrap.Modal.getInstance(document.getElementById('addDebugModal')).hide();
    
    // 清空
    document.getElementById('dbg_name').value = '';
    document.getElementById('dbg_root').value = '';
}

/**
 * 删除调试插件
 */
function deleteDebugPlug(id) {
    if (!confirm("确定删除该调试条目？")) return;
    let list = JSON.parse(localStorage.getItem(DEBUG_STORAGE_KEY) || '[]');
    list = list.filter(p => p.id !== id);
    localStorage.setItem(DEBUG_STORAGE_KEY, JSON.stringify(list));
    renderDebugPlugs();
}

/**
 * 渲染调试工具列表
 */
function renderDebugPlugs() {
    const list = JSON.parse(localStorage.getItem(DEBUG_STORAGE_KEY) || '[]');
    const container = document.getElementById('group_plug_debug');
    const wrapper = document.getElementById('debug_group_wrapper');

    if (!container || !wrapper) return;

    if (list.length === 0) {
        wrapper.style.display = 'none';
        return;
    }

    wrapper.style.display = 'block';
    container.innerHTML = list.map(p => createDebugItem(p)).join('');
}

// ==========================================
// 6. 初始化
// ==========================================
window.onload = () => {
    loadSystemPlugs();
    loadCloudPlugs();
    renderDebugPlugs(); // 页面加载时检查 LocalStorage
};