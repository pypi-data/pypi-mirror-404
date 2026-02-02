

/**
 * 选择窗口
 */
function selectWindow(displayText, hwnd, window_title) {
    // 1. 更新全局变量
    window.hwnd = hwnd;
    window.window_title = window_title;
    window.gp.window.hwnd = hwnd;
    window.gp.window.title = window_title;

    // 2. 更新主按钮 UI
    $('#windowSelector').attr('data-current-hwnd', hwnd);
    $('#windowSelector_content').text(displayText);

    // 3. 更新列表中的 active 状态
    $('#windowList .dropdown-item').removeClass('active');
    $(`#windowList .dropdown-item[data-hwnd="${hwnd}"]`).addClass('active');

    // 4. 执行截图逻辑
    capture_window_image();
}

async function capture_window_image() {
    const loader = document.getElementById('imagelist_loading');
    const startTime = Date.now(); // 记录开始时间

    // 1. 显示 Loading
    loader.classList.remove('d-none');

    try {
        const imageElement = document.getElementById('img_preview');
        // 执行截图操作
        let res = await eel.colors_tool_screenshot(window.hwnd)();

        if (res.status === "success") {
            showImg(res.save_info.path);

            if (typeof getImgList === "function") {
                getImgList();
            }
        }
    } catch (error) {
        window.gp.info.error("截图失败", "请确保目标窗口存在且未被最小化。\n错误详情已记录到控制台。\n"+error);
        console.error("截图失败:", error);
    } finally {
        // 2. 延时取消 Loading
        const minLoadingTime = 300; // 设置最小等待时长 (毫秒)
        const elapsedTime = Date.now() - startTime;
        const remainingTime = Math.max(0, minLoadingTime - elapsedTime);

        setTimeout(() => {
            loader.classList.add('d-none');
        }, remainingTime);
    }
}

/**
 * 调用 Python 打开本地文件夹
 * @param {string} path 文件夹的路径
 */
function openLocalFolder(path) {
    if (eel) {
        // 直接调用 Python 中定义的 open_folder
        eel.open_folder(path)((success) => {
            if (success) {
                console.log("文件夹已成功打开");
            } else {
                console.error("打开文件夹失败，请检查路径");
                alert("无法打开文件夹：" + path);
            }
        });
    }
}

// 监听点击事件
$('#cache_imgs_path').on('click', function (e) {
    e.preventDefault(); // 阻止默认的超链接跳转行为
    // 获取当前标签里的文字（即路径 C://abc）
    // 或者你可以直接写死路径，取决于你的需求
    let folderPath = $(this).text();

    // 调用 Python 暴露给 Eel 的方法
    if (typeof eel !== 'undefined') {
        eel.open_folder(folderPath)((success) => {
            if (!success) {
                console.error("无法打开文件夹:", folderPath);
            }
        });
    }
});

$('#toolbar_img_delall').on('click', async function () {
    const $btn = $(this);
    const $text = $('#delall_text');
    const $spinner = $('#delall_spinner');
    const pathToDelete = $('#cache_imgs_path').text(); // 获取当前显示的路径

    if (!pathToDelete || pathToDelete === "C://abc") {
        alert("无效的路径");
        return;
    }

    if (confirm("确定要永久删除该文件夹下的所有内容吗？")) {
        // --- 1. 进入 Loading 状态 ---
        $btn.prop('disabled', true); // 禁用按钮防止重复点击
        $text.text('处理中...');
        $spinner.show();

        try {
            // --- 2. 调用 Python 后端 ---
            const success = await eel.file_delete(pathToDelete)();

            if (success) {
                // --- 3. 成功处理 ---
                $(".screen-img-list").empty(); // 清空前端图片网格
                $('.imglist_size').text('0');  // 重置计数
                console.log("清理成功");
            } else {
                alert("删除失败，请检查文件是否被占用。");
            }
        } catch (err) {
            console.error("调用 Python 出错:", err);
        } finally {
            // --- 4. 恢复按钮状态 ---
            $btn.prop('disabled', false);
            $text.text('清空');
            $spinner.hide();
        }
    }
});

/**
 * 更新右侧的临时通知 (类似 PyCharm 风格)
 * @param {string} msg 消息内容
 * @param {boolean} isError 是否为错误提示
 */
let bottomNotifTimer = null;

function showBottomNotif(msg, isError = false) {
    const $notif = $('#status_notification');
    const $dot = $('#status_dot');

    if (bottomNotifTimer) clearTimeout(bottomNotifTimer);

    // 1. 设置内容
    $notif.text(msg);

    // 2. 切换到活跃颜色 (适配主题)
    if (isError) {
        $notif.removeClass('status-active').addClass('status-error');
        $dot.show().removeClass('text-primary').addClass('text-danger');
    } else {
        $notif.removeClass('status-error').addClass('status-active');
        $dot.show().removeClass('text-danger').addClass('text-primary');
    }

    // 3. 3秒后恢复到 VSCode 风格的低调灰色
    bottomNotifTimer = setTimeout(() => {
        $notif.text('就绪').removeClass('status-active status-error');
        $dot.fadeOut(500); // 圆点慢慢消失
    }, 3000);
}

/**
 * 拷贝文本到剪贴板
 * @param {string} text 需要拷贝的内容
 * @param {string} successMsg 成功后的提示文字（可选）
 */
async function copyToClipboard(text, successMsg = "已复制到剪贴板") {
    // 1. 优先使用现代 Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
        try {
            await navigator.clipboard.writeText(text);
            showBottomNotif(text + successMsg, false); // 调用你之前的消息通知函数
            return true;
        } catch (err) {
            console.error("Clipboard API 失败，尝试降级方案", err);
        }
    }

    // 2. 降级方案：创建隐藏的 textarea 使用 execCommand
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // 确保 textarea 在移动端和各种布局下不可见
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);

    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showBottomNotif(successMsg, false);
        } else {
            showBottomNotif("复制失败", true);
        }
    } catch (err) {
        showBottomNotif("无法访问剪贴板", true);
        console.error("降级方案也失败了:", err);
    }

    document.body.removeChild(textArea);
}


// 全局存储当前在线的 HWND 列表，方便对比
let currentOnlineHwnds = new Set();

$(document).ready(function () {
    const $backdrop = $('#dropdownBackdrop');
    const $selectorBtn = $('#windowSelector');
    const $dropdownParent = $selectorBtn.parent();

    // --- A. 初始化：监听下拉框状态 ---
    $dropdownParent.on('show.bs.dropdown', function () {
        $backdrop.addClass('show').fadeIn(200);
        refreshWindowsInPlace();
    });

    $dropdownParent.on('hide.bs.dropdown', function () {
        $backdrop.removeClass('show').fadeOut(200);
    });

    // --- B. 关键点：进入页面自动弹出 ---
    // 我们先静默刷新一次，然后显示。
    // 使用 setTimeout 确保 DOM 和 Eel 已经完全准备就绪
    // setTimeout(() => {
    //     const dropdownInstance = new bootstrap.Dropdown($selectorBtn[0]);
    //     dropdownInstance.show();
    // }, 300); // 300ms 延迟可以避免页面加载时的闪烁

});

async function refreshWindowsInPlace() {
    let response = await eel.get_online_windows()();

    if (response.status === "success") {
        const $menu = $('#windowList');
        const newData = response.data;
        const newHwnds = newData.map(win => String(win.hwnd));
        
        // 获取除了“全屏”以外的所有项
        const domItems = $menu.find('.dropdown-item').not('[data-hwnd="null"]');

        // 1. 处理已消失项 (跳过全屏项)
        domItems.each(function () {
            const $item = $(this);
            const itemHwnd = String($item.attr('data-hwnd'));
            if (!newHwnds.includes(itemHwnd)) {
                $item.addClass('inst-disabled text-decoration-line-through');
                $item.find('.win-title-text').html($item.attr('data-display') + ' <small>(已消失)</small>');
            }
        });

        // 2. 检查全屏项是否存在，不存在则初始化
        if ($menu.find('[data-hwnd="null"]').length === 0) {
            const fullScreenHtml = generateWindowItemHtml({ display: '全屏截图', hwnd: 'null', title: 'Full Screen' });
            $menu.prepend(fullScreenHtml + '<li><hr class="dropdown-divider"></li>');
        }

        // 3. 更新/同步现有项
        let hasNewHeader = false;
        newData.forEach(win => {
            const winHwnd = String(win.hwnd);
            const $existingItem = $menu.find(`[data-hwnd="${winHwnd}"]`);

            if ($existingItem.length === 0) {
                if (!hasNewHeader && domItems.length > 0) {
                    $menu.append('<li><hr class="dropdown-divider"></li>');
                    $menu.append('<li><h6 class="dropdown-header text-primary">新增窗口</h6></li>');
                    hasNewHeader = true;
                }
                $menu.append(generateWindowItemHtml(win, false));
            } else {
                $existingItem.removeClass('inst-disabled text-decoration-line-through');
                $existingItem.find('.win-title-text').text(win.display);
                
                // 处理 Active 状态 (支持 null 的比较)
                const currentSelection = window.hwnd === null ? "null" : String(window.hwnd);
                if (winHwnd === currentSelection) {
                    $existingItem.addClass('active');
                } else {
                    $existingItem.removeClass('active');
                }
            }
        });

        // 额外处理：如果当前选中的是全屏，确保全屏项 active
        if (window.hwnd === null) {
            $menu.find('[data-hwnd="null"]').addClass('active');
        } else {
            $menu.find('[data-hwnd="null"]').removeClass('active');
        }
    }
}


function generateWindowItemHtml(win, isDisabled = false) {
    const isMatched = (window.hwnd && String(win.hwnd) === String(window.hwnd));
    const activeClass = isMatched ? 'active' : '';
    const disabledClass = isDisabled ? 'inst-disabled text-decoration-line-through' : '';
    const statusText = isDisabled ? ' <small>(已消失)</small>' : '';

    return `
    <li>
        <a class="dropdown-item ${activeClass} ${disabledClass} window-item-link" 
           href="javascript:void(0)"
           data-hwnd="${win.hwnd}"
           data-display="${win.display}"
           onclick="selectWindow('${win.display}', ${win.hwnd}, '${win.title}')">
           
           <span class="win-title-text">${win.display}${statusText}</span>
           <span class="win-hwnd-num">${win.hwnd}</span>
        </a>
    </li>`;
}
/**
 * 彻底刷新：当列表关闭后，重新构建干净的列表，以便下次打开是整洁的
 */
async function cleanUpWindowList() {
    let response = await eel.get_online_windows()();
    if (response.status === "success") {
        const $menu = $('#windowList');
        $menu.empty();
        $menu.append('<li><h6 class="dropdown-header">运行中的应用</h6></li>');

        response.data.forEach(win => {
            let isMatched = (window.hwnd && String(win.hwnd) === String(window.hwnd));
            let item = `<li>
                <a class="dropdown-item ${isMatched ? 'active' : ''}" 
                   href="javascript:void(0)"
                   data-hwnd="${win.hwnd}"
                   data-display="${win.display}"
                   onclick="selectWindow('${win.display}', ${win.hwnd}, '${win.title}')">
                   ${win.display}
                </a>
            </li>`;
            $menu.append(item);
        });
    }
}

$(document).ready(function () {
    const $container = $('.screen-img-container');
    const $handle = $('.touch_slide');
    let isResizing = false;

    $handle.on('mousedown', function (e) {
        isResizing = true;
        $handle.addClass('active');

        // 防止拖拽过程中选中文字
        $('body').css('user-select', 'none');

        // 记录初始位置（如果需要计算 offset 可以用，这里直接用 clientX 即可）
        $(document).on('mousemove', handleMouseMove);
        $(document).on('mouseup', stopResizing);
    });

    function handleMouseMove(e) {
        if (!isResizing) return;

        // 关键修正：鼠标位置 - 容器左边缘距离视口的距离 = 容器内部的实际宽度
        const containerOffsetLeft = $container[0].getBoundingClientRect().left;
        let newWidthPx = e.clientX - containerOffsetLeft;

        // 设定限制范围
        const minWidth = 300;
        const maxWidth = window.innerWidth * 0.8;

        if (newWidthPx >= minWidth && newWidthPx <= maxWidth) {
            $container.css('width', newWidthPx + 'px');

            // 这里的联动很重要：如果左侧有 left: -40px 这种偏移，
            // 宽度太小时需要处理，防止 UI 溢出
        }
    }

    function stopResizing() {
        if (isResizing) {
            isResizing = false;
            $handle.removeClass('active');
            $('body').css('user-select', '');
            $(document).off('mousemove', handleMouseMove);
            $(document).off('mouseup', stopResizing);

            // 拖拽停止后，可能需要强制让图片自适应一次
            if (typeof resetViewToFit === 'function') {
                resetViewToFit(0);
            }
        }
    }
});

function showError(title, content) {
    const modalElement = document.getElementById('errorModal');
    const msgElement = document.getElementById('errorModalMsg');
    const titleElement = document.getElementById('codeWindowTitle');

    // 更新模拟窗口的标题栏文字
    titleElement.innerText = (title || "SYSTEM ERROR").toUpperCase();

    // 判断内容类型
    const isSimple = content && content.length < 60 && !content.includes('\n');
    
    if (isSimple) {
        msgElement.classList.add('simple-msg');
        msgElement.innerText = content;
    } else {
        msgElement.classList.remove('simple-msg');
        msgElement.innerText = content || "No error details found.";
    }

    bootstrap.Modal.getOrCreateInstance(modalElement).show();
}

// 顺便写个复制功能，方便用户反馈 Bug
function copyTraceback() {
    const text = document.getElementById('errorModalMsg').innerText;
    navigator.clipboard.writeText(text).then(() => {
        // alert("已复制到剪贴板");
        bootstrap.Modal.getInstance(document.getElementById('errorModal')).hide();
        window.gp.info.noti("错误信息已复制到剪贴板", false);
    });
}



/**
 * 当用户按下全局快捷键时，Python 会调用此函数
 */
function triggerScreenshotUI() {
    console.log("快捷键已触发：准备截图");

    capture_window_image();
}

eel.expose(triggerScreenshotUI);
