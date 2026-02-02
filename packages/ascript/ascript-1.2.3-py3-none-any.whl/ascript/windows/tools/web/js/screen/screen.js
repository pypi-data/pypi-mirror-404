
// var image = document.getElementById('img_preview');
var img_deleft_dom;
var conimg = $("#container_img");
var image_data_object;
const uploadDir = "~/data/screenshot/"

var mouse_move_xyc = {};
var is_mouse_downed = false;
var is_show_box = false;
var part_box = $("#part_box");

var source_path = null;

var gp_path = null

var gpobj = undefined;

var image_list_res = undefined;

var image_list_max_show = 5

var is_imgcon_mouse_down = false
var is_iframecon_mouse_down = false

// var device_id = getQueryString('device_id')

$(document).ready(function () {
    // initImgLogic()
    getImgList(true)
    initImageListLogic()


    // 
    // $('[data-toggle="tooltip"]').tooltip()
    // init_Image_Mouse()
    // init_key_logic()
    // init_as_moduls()
    // getGpLineList()
    dragChangeContainer()


    // refreshWindows();

});

// function gpiframeout(){
//     var iframe = document.querySelector('iframe');  
//     iframe.onload = function() {  
//         if (iframe.contentWindow && iframe.contentWindow.document) {  
//             // 注意：这仅在同源时有效  
//             iframe.contentWindow.document.addEventListener('keydown', function(event) {  
//                 console.log('Keydown event inside iframe (if same-origin):', event.key);  
//             });  
//         }  
//     };  
// }

function dragChangeContainer() {
    var src_posi_Y = 0, src_posi_X = 0, dest_posi_Y = 0, dest_posi_X = 0, move_Y = 0, destHeight = 0, destWidth = 0, moveed = false, right = 0, bottom = 0, consleHeight, height = 0;

    $(".touch_slide")
        .mousedown(function (e) {
            is_imgcon_mouse_down = true;
            src_posi_Y = e.pageY;
            src_posi_X = e.pageX;
            // alert(right);
            right = $(".screen-img-container").width()
            // e.stopPropagation()
        });

    $(".gp_touch_bar")
        .mousedown(function (e) {
            is_iframecon_mouse_down = true;
            src_posi_Y = e.pageY;
            src_posi_X = e.pageX;
            // alert(right);
            height = $(".coder-iframe").height()
            // e.stopPropagation()
        });

    $(document).bind("click mouseup", function (e) {
        if (is_imgcon_mouse_down) {
            is_imgcon_mouse_down = false;
            moveed = false;
        }

        if (is_iframecon_mouse_down) {
            is_iframecon_mouse_down = false;
            moveed = false;
        }
    })
        .mousemove(function (e) {

            if (is_imgcon_mouse_down) {

                dest_posi_Y = e.pageY;
                dest_posi_X = e.pageX;
                move_X = dest_posi_X - src_posi_X;
                move_Y = dest_posi_Y - src_posi_Y;

                // alert(right + move_X)
                if (right + move_X > 20) {
                    // console.log(right + move_X + "px")
                    $(".screen-img-container").width(right + move_X + "px");
                }

                moveed = true;

                e.preventDefault();
            }

            if (is_iframecon_mouse_down) {

                dest_posi_Y = e.pageY;
                dest_posi_X = e.pageX;
                move_X = dest_posi_X - src_posi_X;
                move_Y = dest_posi_Y - src_posi_Y;

                // alert(right + move_X)
                if (height + move_Y > 20) {
                    // console.log(right + move_X + "px")
                    $(".coder-iframe").height(height + move_Y + "px");
                }

                moveed = true;

                e.preventDefault();
            }


        });
}






async function  getImgList() {
    // 1. UI 状态准备
    $(".screen-img-list").empty();

    try {
        // 2. 调用刚才写的 Eel 方法
        // 注意：Python 端方法名为 colors_tool_screenshot_files
        let res = await eel.colors_tool_screenshot_files()();



        if (res.status === "success") {
            // 兼容你原来的变量逻辑
            image_list_res = res;

            // 设置路径
            $("#cache_imgs_path").text(res.path)

            // 调用你原来的渲染函数
            fill_imagelist_items(res);

            // 更新显示数量
            $(".imglist_size").text(res.data.length);
        } else {
            console.error("获取文件列表失败:", res.message);
        }

    } catch (err) {
        console.error("Eel 调用异常:", err);
        alert("通讯异常: " + err);
    }
}

function mk_image_show_no() {
    var curren_no = image_list_max_show;
    var max_no = image_list_res.data.length;
    $("#screen-imglist-bar-no").text(`${curren_no}/${max_no}`)
}


// 假设你有一个拖动条的监听事件
// function onSidebarResize(newWidthPx) {
//     // 将新的宽度同步给 CSS 变量，画廊面板会自动跟随移动并伸缩
//     document.documentElement.style.setProperty('--left-width', newWidthPx + 'px');
// }


// 初始化观察器：当图片进入视口时才真正请求加载数据
/**
 * 懒加载观察器
 * 当图片条目滚动到可见区域时，才调用 load_item_image 加载真实内容
 */
/**
 * 1. 懒加载观察器重构
 */
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const $item = $(entry.target);
            // 改为从 data-filepath 获取完整路径
            const filepath = $item.attr('data-filepath');
            const $img = $item.find('.img-content');

            // 触发异步加载：建议在 load_item_image 内部实现压缩或按需加载
            if (typeof load_item_image === "function") {
                load_item_image($img, filepath);
            }

            // 加载后取消观察
            observer.unobserve(entry.target);
        }
    });
}, {
    root: document.querySelector('.screen-img-list'),
    rootMargin: '200px' // 稍微增大边距，减少用户滚动时的白块感
});

let first_entger_load_histroy = true;

/**
 * 2. 填充图片列表重构
 * @param {Object} res 格式要求: { data: ["C:/path/1.jpg", "C:/path/2.jpg"] }
 */
async function fill_imagelist_items(res) {
    if (!res || !res.data) return;

    const $listContainer = $(".screen-img-list");
    $listContainer.empty();
    
    // 确保容器拥有网格布局类
    $listContainer.addClass("row row-cols-2 row-cols-md-3 row-cols-lg-4 row-cols-xl-6 g-2 m-0");

    res.data.forEach((filepath, index) => {
        // 从完整路径中提取文件名用于显示
        const displayFilename = filepath.split(/[\\\/]/).pop();

        // 构建 HTML 结构，使用 data-filepath 存储完整路径
        const $item = $(`
            <div class="col screen-img-item-wrapper" data-filepath="${filepath}">
                <div class="img-card shadow-sm border rounded">
                    <img class="img-content" 
                         src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
                         alt="${displayFilename}">
                    <div class="img-name text-truncate" title="${displayFilename}">${displayFilename}</div>
                    <button class="btn-del btn btn-danger">
                        <i class="bi bi-trash3"></i>
                    </button>
                </div>
            </div>
        `);

        // 首次进入默认加载第一张预览
        if (first_entger_load_histroy && index === 0) {
            if (typeof showImg === "function") showImg(filepath);
            first_entger_load_histroy = false;
        }

        // 3. 绑定点击预览事件
        $item.on('click', function () {
            $('.img-card').removeClass('border-primary shadow-lg');
            $(this).find('.img-card').addClass('border-primary shadow-lg');

            // 直接使用当前循环作用域内的 filepath
            if (typeof showImg === "function") {
                showImg(filepath);
            }
        });

        // 4. 绑定单个删除事件 (直接使用 filepath，不再拼接)
        $item.find('.btn-del').on('click', function (e) {
            e.stopPropagation(); 

            // 立即反馈 UI
            $item.css({
                'opacity': '0.3',
                'pointer-events': 'none',
                'transition': 'all 0.2s'
            });

            if (typeof eel !== 'undefined') {
                // 直接传递 filepath 给后端
                eel.file_delete(filepath)((success) => {
                    if (success) {
                        $item.css('transform', 'scale(0.8)');
                        $item.fadeOut(250, function () {
                            $(this).remove();
                            // 更新数量统计
                            $('.imglist_size').text($('.screen-img-item-wrapper').length);
                        });
                    } else {
                        // 失败恢复
                        $item.find('.img-card').addClass('border-danger');
                        setTimeout(() => {
                            $item.css({ 'opacity': '1', 'pointer-events': 'auto' });
                            $item.find('.img-card').removeClass('border-danger');
                        }, 500);
                        console.error("删除失败: " + filepath);
                    }
                });
            }
        });

        // 5. 添加并启动观察
        $listContainer.append($item);
        imageObserver.observe($item[0]);
    });

    // 6. 更新计数器
    $('.imglist_size').text(res.data.length);
}

// 全局加载队列控制，防止一瞬间发给 Python 几百个请求导致 Eel 消息堵塞
const loadQueue = {
    activeCount: 0,
    maxConcurrent: 5, // 同时最多只处理 5 个图片请求
    queue: [],
    
    add(task) {
        this.queue.push(task);
        this.run();
    },
    
    run() {
        if (this.activeCount < this.maxConcurrent && this.queue.length > 0) {
            const task = this.queue.shift();
            this.activeCount++;
            task().finally(() => {
                this.activeCount--;
                this.run();
            });
        }
    }
};

// 重构后的 load_item_image
function load_item_image($img, filepath) {
    loadQueue.add(async () => {
        return new Promise((resolve) => {
            eel.ascript_get_image(filepath, 300)((res) => {
                if (res.status === "success") {
                    $img.attr('src', res.data);
                }
                resolve();
            });
        });
    });
}


function imagelist_mouseover(e) {

    var srch = $(this).attr("srch")
    if (srch.length > 0) {
        $(this).attr("src", srch)
        $(this).attr("srch", "");
    }


    $("#delect_img").show();
    // alert("")

    // alert($(e.target).attr('src'))
    var dom = $(e.target);
    img_deleft_dom = $(e.target);
    var left = dom.width() + dom.position().left - dom.scrollLeft() - $("#delect_img").width() + 13;
    // alert(left)
    $("#delect_img").css("left", left + "px");
}



function getImageData() {
    $(image).css("height", "auto");
    $(image).css("width", "auto");
    var cvs = document.getElementById('preview_img_canvas');
    cvs.width = image.width;
    cvs.height = image.height;
    var ctx = cvs.getContext('2d');
    var dimImage = document.getElementById('img_preview')
    ctx.drawImage(dimImage, 0, 0);
    return ctx.getImageData(0, 0, dimImage.width, dimImage.height);
}

var image_list_filled = false
function initImageListLogic() {
    // $(".screen-img-list-con").fadeIn(100);
    // $(".history-btn").mouseover(function () {
    //     // alert('123')
    //     openGallery();
    // })

    // $("#imageGallery").mouseleave(function () {
    //     closeGallery();
    // })
}

function uploadFile(p) {
    $("#fileupload").trigger('click');
    $("#fileupload").change(function (e) {
        // alert($('#fileupload')[0].files.length)
        if ($('#fileupload')[0].files.length >= 1) {
            var formData = new FormData();
            var fName = $('#fileupload')[0].files[0].name;
            // var fName = new Date().getTime()+".png"
            formData.append("data", e.target.files[0]);
            // formData.append("path", uploadDir+fName);
            $.ajax({
                url: baseUrl + '/api/file/upload?path=' + (uploadDir + fName),
                type: 'POST',
                cache: false,
                data: formData,
                processData: false,
                contentType: false
            }).done(function (res) {
                // $("#upload_pic").text("导入图片");
                // addPicCacheListItem(fName,false)
                getImgList(false)

            }).fail(function (res) {
                // getFilesList();
                // $("#upload_pic").text("导入图片");
                alert("上传失败")
            });
        } else {
            // $("#upload_pic").text("导入图片");
        }

    });
}


function init_key_logic() {
    $(document).keypress(function (e) {
        // alert("22")
        var keynumber = e.keyCode - 48;
        if (keynumber > 0 && keynumber < 10 ) {

            gpframe = document.getElementById("gpiframe")

            // alert(JSON.stringify(mouse_move_xyc))
            // $("#header_color_current").val(`${mouse_move_xyc.x},${mouse_move_xyc.y},#${mouse_move_xyc.c}`)

            copyToClipboard(`${mouse_move_xyc.x},${mouse_move_xyc.y},#${mouse_move_xyc.c}`, "  已将此取色数据已复制到剪贴板")

            if (gpframe && gpframe.contentWindow.gp) {
                gpframe.contentWindow.on_color_picked(keynumber, mouse_move_xyc)

            }
            // alert("1")
            // on_color

            // var cdom = $("#choose_colors_item_"+keynumber);
            // cdom.find(".choose_colors_item_input").val(mouse_move_xyc.x+","+mouse_move_xyc.y+" #"+mouse_move_xyc.c)
            // cdom.find(".choose_colors_item_bgcolor").css("background-color","#"+mouse_move_xyc.c)
            // chooseColors[keynumber] = mouse_move_xyc;
            // makeFindColorsStr();

            // var bgitemdom = cdom.find(".choose_colors_item_bgcolor")

        }

        // print(cdom.val())
    });

}

function init_as_moduls() {
    gpapi.module.get_all(function (data) {
        $(".as_modules").empty();
        // if(data.data.length<1){
        //     $("#model_create").click();
        //     return;
        // }
        data.data.forEach(function (e, index) {
            if (index == 0) {
                gpapi.module.current = e
                // alert(JSON.stringify(e))
            }
            var item = $(`<option value="${index}">${e.name}</option>`);
            $(".as_modules").append(item);

        });
        gpapi.module.all = data.data;
    })

    $(".as_modules").change(function () {
        // alert($(this).val())
        gpapi.module.current = gpapi.module.all[Number($(this).val())];

        // alert(gpapi.module.current.name)
    })

}

function delect_gptest_module(m_name) {
    // alert(m_name)
    $.ajax({
        url: `${baseUrl}/api/gp/test/remove`,
        type: 'post',
        data: { name: m_name },
        async: true,
        success: function (res) {
            if (res.code == 1) {
                // alert("成功")
            } else {
                alert(res.msg)
            }
        },
        error: function (err) {
            alert(err)
        }
    })
}

function delect_gpline_module(m_name) {
    // alert(m_name)
    $.ajax({
        url: `${baseUrl}/api/gp/plug/remove`,
        type: 'post',
        data: { name: m_name },
        async: true,
        success: function (res) {
            if (res.code == 1) {
                // alert("成功")
            } else {
                alert(res.msg)
            }
        },
        error: function (err) {
            alert(err)
        }
    })
}

function getGpLineList() {
    var url = "http://py.airscript.cn/api/web/plug/list?limit=10000&gp=1";
    $.ajax({
        url: url,
        type: 'get',
        data: {},
        async: true,
        success: function (res) {
            if (res.code == 1) {
                // alert(res)
                fill_GPLineList(res)
            } else {
                alert(res.msg)
            }
        },
        error: function (err) {
            alert(err)
        }
    })
}

function fill_GPLineList(res) {
    res.data.forEach((item, index) => {
        // gp_line_list
        var dom = $("#gp_line_list_item").clone()
        dom.find(".gp_id").text(item.name + ":" + item.version)
        dom.find(".gp_author").text(item.auth);
        dom.find(".gp_hot").text(item.download);
        dom.find(".gp_add").click(function () {
            $(this).addClass("gploading")
            $(this).text("加载中")
            $(this).prop('disabled', true);
            add_line_gp(item.name + ":" + item.version, function (is_success) {
                $(".gploading").prop('disabled', false);
                if (is_success) {
                    $(".gploading").text("已加载")
                } else {
                    $(".gploading").text("重试")
                }
                $(".gploading").removeClass("gploading")

            })

            // $(this).prop('disabled', true);

        })

        dom.find(".gp_info").click(function () {
            window.open(`http://dev.airscript.cn/plug?id=${item.id}`, "_blank")
        })

        var domcs = dom.find(".gp_line_childs");

        item.gp.forEach((citem, index) => {
            var domc = $("#gp_line_list_item_child").clone()
            domc.find(".gp_line_id").text(citem.id)
            domc.find(".gp_line_des").text(citem.des)
            domc.appendTo(domcs)
        });


        dom.appendTo("#gp_line_list")
    });
}

function add_line_gp(gp_name, listener) {
    $.ajax({
        url: `${baseUrl}/api/gp/plug`,
        type: 'post',
        data: { name: gp_name },
        async: true,
        success: function (res) {
            if (res.code == 1) {
                get_gpplug_list()
                if (listener) {
                    listener(true)
                }
                // alert("成功")
                // get_gpplug_list()
                // $("#gp_test_modal").modal("hide")
            } else {
                if (listener) {
                    listener(true)
                }
                alert(res.msg)
            }
        },
        error: function (err) {
            alert(err)
        }
    })
}



function openGallery() {
    const $gallery = $('#imageGallery');

    // 1. 判断当前是否已经是显示状态
    // 如果不包含 d-none，说明已经是开启状态，则执行关闭逻辑
    if (!$gallery.hasClass('d-none')) {
        closeGallery();
        return;
    }

    // 2. 如果是隐藏状态，执行开启逻辑
    $gallery.removeClass('d-none').addClass('d-flex');

    // 3. 性能优化：同步侧边栏宽度
    const sidebarWidth = $('.screen-img-container').outerWidth();
    document.documentElement.style.setProperty('--left-width', sidebarWidth + 'px');

    // 4. 可选：刷新数据
    // if (typeof refreshImageData === 'function') refreshImageData();
}

/**
 * 关闭画廊 (保持独立，方便其他地方调用)
 */
function closeGallery() {
    $('#imageGallery').removeClass('d-flex').addClass('d-none');
}

/**
 * 关闭画廊
 */
function closeGallery() {
    // 恢复 d-none 隐藏面板
    $('#imageGallery').removeClass('d-flex').addClass('d-none');
}

// 全局按键监听
$(document).on('mousedown', function (e) {
    const $gallery = $('#imageGallery');
    const $openBtn = $('.history-btn'); // 假设这是你打开画廊的那个图标按钮的类名

    // 逻辑判断：
    // 1. 面板当前必须是显示的
    // 2. 点击的目标不是面板本身，也不是面板内部的元素
    // 3. 点击的目标不是那个触发打开的按钮（防止刚打开就触发关闭）
    if (!$gallery.hasClass('d-none')) {
        if (!$gallery.is(e.target) &&
            $gallery.has(e.target).length === 0 &&
            !$openBtn.is(e.target) &&
            $openBtn.has(e.target).length === 0) {

            closeGallery();
        }
    }
});

// 刚才的 Esc 键监听保持不变
$(document).on('keydown', function (e) {
    if ((e.key === "Escape" || e.keyCode === 27) && !$('#imageGallery').hasClass('d-none')) {
        closeGallery();
    }
});