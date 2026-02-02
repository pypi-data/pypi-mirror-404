var info_RGB = $("#header_cur_rgb");
var info_color = $("#header_cur_colrshow");
var scope_pos = [null, null];
var part_box = $("#part_box");
var conimg = $("#container_img");

var part_control_i = [$("#p_i_l"), $("#p_i_t"), $("#p_i_r"), $("#p_i_b")]
var part_control_c = [$("#p_b_l_c"), $("#p_b_t_c"), $("#p_b_r_c"), $("#p_b_b_c")]
var part_control_a = [$("#p_b_l_a"), $("#p_b_t_a"), $("#p_b_r_a"), $("#p_b_b_a")]

var hasFocus = true;

$(".pb_con").hide()

window.addEventListener('blur', function() {
    hasFocus = false;
});

window.addEventListener('focus', function() {
    hasFocus = true;
});


//获取鼠标在图片上的位置及颜色（像素级）
function getPointOfImage() {
    //获取鼠标相对于整个页面的位置
    var pos = mousePos();
    var page_mouse_x = pos.x
    var page_mouse_y = pos.y;
    //获取图片元素的左上角的位置
    var img_x = getLeft(image);
    var img_y = getTop(image);
    //获取容器滚动条滚动的距离
    var distance_scroll_x = $("#container_img").scrollLeft();
    var distance_scroll_y = $("#container_img").scrollTop();
    //获取图片元素的宽度（实际的，而不仅是显示的）
    var img_width = image.offsetWidth;
    img_height = image.offsetHeight;
    //计算鼠标所在的图片上的位置距离左上角起始点的距离占宽高的百分比
    var percent_x = (page_mouse_x - img_x + distance_scroll_x) / img_width;
    var percent_y = (page_mouse_y - img_y + distance_scroll_y) / img_height;
    //获取图片的原始像素级坐标和颜色
    var pos_pixel_x = image_data_object.width * percent_x;
    var pos_pixel_y = image_data_object.height * percent_y;
    pos_pixel_x = Math.floor(pos_pixel_x);
    // pos_pixel_x = toInt(pos_pixel_x, 0.9);
    pos_pixel_y = Math.floor(pos_pixel_y);
    // pos_pixel_y = toInt(pos_pixel_y, 0.9);
    var index = (pos_pixel_x + 1 + (pos_pixel_y) * image_data_object.width - 1) * 4;
    var pos_pixel_color = {
        r: image_data_object.data[index],
        g: image_data_object.data[index + 1],
        b: image_data_object.data[index + 2],
        a: image_data_object.data[index + 3]
    };
    return { x: pos_pixel_x, y: pos_pixel_y, color: pos_pixel_color };
}

function mousePos() {
    var x, y;
    var e = window.event;
    return {
        x: e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft,
        y: e.clientY + document.body.scrollTop + document.documentElement.scrollTop
    };
};

//获取元素的纵坐标
function getTop(e) {
    var offset = e.offsetTop;
    if (e.offsetParent != null) offset += getTop(e.offsetParent);
    return offset;
}

//获取元素的横坐标
function getLeft(e) {
    var offset = e.offsetLeft;
    if (e.offsetParent != null) offset += getLeft(e.offsetParent);
    return offset;
}


function img_mousemove(e) {

    if(!hasFocus){
        return true;
    }

    if(is_imgcon_mouse_down){
        return true
    }

    // if(!$("#img_preview").is(':focus')){
    //     $("#img_preview").focus()
    //     // alert("1")
    //     console.log("focus -img ")
    //     $('#screen_logo').click();

    // }

    //处理显示鼠标坐标点图色信息的逻辑
    is_image_mouseover = true;
    // $(".choose_colors_item_input").blur()

    var current_pos = getPointOfImage();

    showZoomCon(current_pos)
    pos_current = current_pos;

    $("#header_cur_xy").text("x:" + current_pos.x + " y:" + current_pos.y);

    // im.focus(); 
    
    // alert(current_pos.y+"?"+current_pos.x)

    // info_Y.text("Y：" + current_pos.y);
    var r = current_pos.color.r.toString(16);
    var g = current_pos.color.g.toString(16);
    var b = current_pos.color.b.toString(16);
    r = r.length > 1 ? r : "0" + r;
    g = g.length > 1 ? g : "0" + g;
    b = b.length > 1 ? b : "0" + b;
    var rgb_str = r.toUpperCase() + g.toUpperCase() + b.toUpperCase();
    $("#header_cur_rgb").text("#" + rgb_str);
    $(".toolbar_img_delall-mousecolor").css("background-color", "#" + rgb_str);

    mouse_move_xyc = { x: current_pos.x, y: current_pos.y, c: rgb_str };


    //处理拖动鼠标选择范围的逻辑
    if (!is_mouse_downed) { //如果鼠标不是按下状态，直接退出
        return false;
    }
    if (!is_show_box) {
        is_show_box = true;
    }
    var pos = mouseParentPos(e);
    var x_current = pos.x;
    var y_current = pos.y;
    var width = x_current - x_mouse_down;
    var height = y_current - y_mouse_down;
    part_box.css("width", width + "px");
    part_box.css("height", height + "px");
    if (width > 0 & height > 0) {
        part_box.css("display", "block");
        // p2.val(current_pos.x + "," + current_pos.y);
        // alert(1)
        // $(".pb_con_empty").hide()
        // $(".pb_con").show()
        scope_pos[1] = current_pos;
        // part_control_i[0].text(pos_mouse_down.x)
        // part_control_i[1].text(pos_mouse_down.y)
        // part_control_i[2].text(current_pos.x)
        // part_control_i[3].text(current_pos.y)
        // $(".image_input_rect").val(pos_mouse_down.x + "," + pos_mouse_down.y + "," + current_pos.x + "," + current_pos.y);
        
    } else {
        // $(".badge .badge").text("0")
        $(".pb_con").hide()
    }

    scope_pos[0] = pos_mouse_down;

    // generate_code();
    return false;
}

function img_onmouseout(e) {
    // $(".zoomWindow").fadeOut(200,function(e){
    is_image_mouseover = false;
    // });
    $(".zoomContainer").hide();
}


function img_mousedown(e) {
    // alert(conimg.scrollTop())

    if(!hasFocus){
        return true;
    }

    var currentTrigger = $("#img_preview").data('contextMenuActive', true)
    var opt = currentTrigger.data('contextMenu') || {};
    if (opt.$menu !== null && typeof opt.$menu !== 'undefined') {
        opt.$menu.trigger('contextmenu:hide');
    }

    scope_pos = [null, null];
    $(".image_input_rect").val("")
    // if(findimage_capture){
    //     scope_pos_findimg  = [null, null];
    // }
    // $("#header_rect").val("");
    // $(".pb_con_empty").show()
    // $(".pb_con").hide()
    is_mouse_downed = true;
    var pos = mouseParentPos(e);
    x_mouse_down = pos.x;
    y_mouse_down = pos.y;
    $("#part_box").removeClass("shadow-lg");
    part_box.css("left", x_mouse_down + "px");
    part_box.css("top", y_mouse_down + "px");
    part_box.css("width", "0px");
    part_box.css("height", "0px");
    part_box.css("display", "none");
    pos_mouse_down = getPointOfImage();
    is_show_box = false;

    return false;


}

function hide_rect() {
    $("#part_box").removeClass("shadow-lg");
    part_box.css("left", 0 + "px");
    part_box.css("top", 0 + "px");
    part_box.css("width", "0px");
    part_box.css("height", "0px");
    part_box.css("display", "none");
}

function img_mouseup(e) {

    if(!hasFocus){
        // hasFocus = true
        return false;
    }

    is_mouse_downed = false;

    $(".part_box_control").show()

    change_part_rect(true)

    copyToClipboard(scope_pos[0].x + "," + scope_pos[0].y + "," + scope_pos[1].x + "," + scope_pos[1].y, "  此选中范围,已复制区域坐标到剪贴板!");

    return false;

}

function change_part_rect(noti_frame) {

    changeBoxRect();

    changeImageMarkSize();

}


//获取鼠标针对于父元素的位置
function mouseParentPos(e) {
    var x, y;
    conimg = $("#container_img");
    return {
        x: e.clientX - conimg.offset().left + conimg.scrollLeft(),
        y: e.clientY - conimg.offset().top + conimg.scrollTop()
    };
};

function changeBoxRect() {

    // alert(conimg.scrollLeft())
    var boxp = part_box.position();
    var boxwidth = part_box.width();
    var boxheight = part_box.height();
    var maxWidth = conimg.width() - 20;
    var maxHeight = conimg.height();

    var relwidth = maxWidth / (boxwidth / image.width);
    var relHeight = relwidth / (image.width / image.height);
    var relBoxWidth = (boxwidth / image.width) * relwidth;
    var relBoxHight = (boxheight / image.height) * relHeight;
    if (relBoxHight > maxHeight) {
        relHeight = maxHeight / (boxheight / image.height);
        relwidth = relHeight / (image.height / image.width);
        relBoxWidth = (boxwidth / image.width) * relwidth;
        relBoxHight = (boxheight / image.height) * relHeight;
    }



    var relBoxLeft = ((boxp.left + conimg.scrollLeft()) / image.width) * relwidth;
    var relBoxTop = ((boxp.top + conimg.scrollTop()) / image.height) * relHeight;



    if (boxwidth > 1 && boxheight > 1) {
        // alert(relwidth+"?"+relHeight)
        $(image).css("width", relwidth + "px");
        $(image).css("height", "auto");

        $("#part_box").addClass("shadow-lg")
        part_box.css("left", relBoxLeft + "px");
        part_box.css("top", relBoxTop + "px");
        part_box.css("width", relBoxWidth + "px");
        part_box.css("height", relBoxHight + "px");

        conimg.scrollLeft(relBoxLeft - 10)
        conimg.scrollTop(relBoxTop)

        // $("#img_contain").scrollLeft(relBoxLeft)
        // $("#img_contain").scrollLeft(relBoxTop)

        // alert(maxwidth)
        // alert(1)
    }

   

}

function changeImageMarkSize() {

    try {
        var rimgw = image_data_object.width;
        var rimgh = image_data_object.height;

        var cimgw = image.width;
        var cimgh = image.height;

         //---change box
        if (scope_pos[0] != null && scope_pos[1] != null) {
            var rboxw = scope_pos[1].x - scope_pos[0].x;
            var rboxh = scope_pos[1].y - scope_pos[0].y;
            //计算目标box 的 宽度和高度
            var tboxw = rboxw / (rimgw / cimgw);
            var tboxh = rboxh / (rimgh / cimgh);
            //计算目标box 的 left 和top值
            var tboxleft = scope_pos[0].x / (rimgw / cimgw);
            var tboxtop = scope_pos[0].y / (rimgw / cimgw);

            part_box.css("left", tboxleft + "px");
            part_box.css("top", tboxtop + "px");
            part_box.css("width", tboxw + "px");
            part_box.css("height", tboxh + "px");

            if (tboxw > 0 & tboxh > 0) {
                part_box.css("display", "block");
                $(part_box).addClass("shadow-lg");
            }
        }
        

        // alert(scope_pos[0])


        gpapi.marks.point.daos.forEach((p, index, arr) => {
            // alert("1")
            // var p = findColorMarks[index];
            var markx = p.x / (rimgw / cimgw);
            var marky = p.y / (rimgw / cimgw);
            // alert(markx+","+marky)
            $('.mark-points').children().eq(index).css({ 'left': markx + "px", 'top': marky + "px" });
        });

        gpapi.marks.rect.daos.forEach((p, index, arr) => {
            // alert("1")
            // var p = findColorMarks[index];
            var markx = p.rect[0] / (rimgw / cimgw);
            var marky = p.rect[1] / (rimgw / cimgw);
            var w = (p.rect[2] - p.rect[0]) / (rimgw / cimgw);
            var h = (p.rect[3] - p.rect[1]) / (rimgw / cimgw);
            // alert(markx+","+marky)
            $('.mark-rects').children().eq(index).css({ 'left': markx + "px", 'top': marky + "px", 'width': w + "px", 'height': h + "px" });
        });


    } catch (error) {
        alert(error)
    }
}


function showZoomCon(e) {
    // alert($(image).position().left)
    // $(image).posation().x;
    // $(".zoomContainer").fadeIn(200,function(e){
    //     // $(".zoomWindow").show();
    // });

    $(".zoomContainer").show();

    var pos = mousePos()

    // var left = image.width+ $(image).position().left +$(".screen-img-container").position().left;
    var left = pos.x + 30
    var conwidth = $("#container_img").width();
    // var top = $("#container_img").position().top;
    var top = pos.y
    // alert(conwidth)
    // if (left > conwidth) {
    //     left = conwidth;
    // }

    var maxHeight = $(window).height() - $(".zoomWindowContainer").height();

    if(top>maxHeight){
        top = maxHeight
    }

    // alert(maxHeight)

    $(".zoomContainer").css('left', left);
    $(".zoomContainer").css('top', top);

    

    var zoomwindow = $(".zoomWindow");

    var leftoff = e.x - (zoomwindow.width() / 2);
    leftoff = leftoff * -1;
    // alert(leftoff)
    var topoff = e.y - (zoomwindow.height() / 2);
    topoff = topoff * -1;

    zoomwindow.css('background-position', `${leftoff}px ${topoff}px`);

}



function init_Image_Mouse() {
    $("#img_preview").mouseup(img_mouseup);
    $("#img_preview").mousedown(img_mousedown);
    $("#img_preview").mousemove(img_mousemove);
    $("#img_preview").mouseout(img_onmouseout);


    part_control_c.forEach((element, index) => {
        element.click(function () {
            var dom = part_control_i[index]
            dom.text(Number(dom.text()) - 1)
            var rect = []
            part_control_i.forEach((e, i) => {
                rect.push(Number(e.text()))
            });
            gpapi.image.set_rect(rect,true)
        })
    });

    part_control_a.forEach((element, index) => {
        element.click(function () {
            var dom = part_control_i[index]
            dom.text(Number(dom.text()) + 1)
            var rect = []
            part_control_i.forEach((e, i) => {
                rect.push(Number(e.text()))
            });
            gpapi.image.set_rect(rect,true)
        })
    });

    $(".p_b_copy").click(function () {
        var rect = []
        part_control_i.forEach((e, i) => {
            rect.push(Number(e.text()))
        });

        gpapi.sys.copy(rect.join(","))
    })
}

