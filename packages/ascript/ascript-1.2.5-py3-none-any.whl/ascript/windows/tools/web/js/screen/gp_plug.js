window.gp = {
    window: {
        title: null,
        hwnd: null
    },
    image: {
        path: null,
        selection: [],
        load: null
    },
    marks: {
        clear: null,
        add_point: null,
        add_rect: null,
        high_light:null,
        high_light_clear:null
    },
    iframe: {
        window: null,
        on_area_selected: null,
        on_color_picked: null,
        on_image_loaded: null  
    },
    info:{
        error:null,
        noti:null
    },
    call_python: async function callPython(code) {
        const res = await eel.python_executor(code)();

        if (!res.success) {
            console.error(`[%c${res.error.type}%c]: ${res.error.message}`, "color: red; font-weight: bold", "");
            console.groupCollapsed("查看完整堆栈信息 (Traceback)");
            console.log(res.error.traceback);
            console.groupEnd();

            // 也可以弹出 UI 提示
            // MyUI.showError(res.error.message);
            // alert(`错误类型: ${res.error.type}\n错误信息: ${res.error.message}`);
            window.gp.info.error(`执行Python异常`, `错误类型: ${res.error.type}\n错误信息: ${res.error.message}\n${res.error.traceback}`);
            return null;
        }
        return res.data;
    }
}

$(document).ready(function () {
    window.gp.image.load = showImg;
    window.gp.marks.add_point = window.addPointMark;
    window.gp.marks.add_rect = window.addRectMark;
    window.gp.marks.clear = window.clearAllMarks;
    window.gp.marks.high_light = window.highlightMark;
    window.gp.marks.high_light_clear = window.clearHighlight;
    window.gp.info.error = window.showError;
    window.gp.info.noti = window.showBottomNotif;

    window.gp.iframe.on_area_selected = function () {
        // 1. 获取全局变量 box
        var b = box;
        if (!b) {
            console.warn("Global 'box' is not defined yet.");
            return;
        }

        // 2. 根据日志显示的属性名 {x, y, w, h} 进行提取
        // 使用 Math.floor 向下取整
        var left = Math.floor(b.x || 0);
        var top = Math.floor(b.y || 0);
        var width = Math.floor(b.w || 0);
        var height = Math.floor(b.h || 0);

        // 3. 转换为 LTRB 格式
        var ltrbBox = {
            l: left,
            t: top,
            r: left + width,
            b: top + height
        };

        console.log("Corrected LTRB:", ltrbBox);

        // 4. 更新全局状态
        window.gp.image.selection = ltrbBox;

        // 5. 传给 iframe 内部
        if (window.gp.iframe.window && typeof window.gp.iframe.window.on_area_selected === 'function') {
            return window.gp.iframe.window.on_area_selected(ltrbBox);
        }
    };

    window.gp.iframe.on_color_picked = function (...args) {
        window.gp.image.selection = box;
        if (window.gp.iframe.window && typeof window.gp.iframe.window.on_color_picked === 'function') {
            return window.gp.iframe.window.on_color_picked(...args);
        }
    }

    window.gp.iframe.on_image_loaded = function (...args) {
        window.gp.image.selection = box;
        if (window.gp.iframe.window && typeof window.gp.iframe.window.on_image_loaded === 'function') {
            return window.gp.iframe.window.on_image_loaded(...args);
        }
    }


    // window.addPointMark("1",100,100)

});