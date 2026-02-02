// var gp_job = [];

// ----
const strackDir = "~/data/gp/"
var temp_gp_dataname = "data.gp"
var workspace;
api_get_workspace();

var gpapi = {
    file: {
        file_url:api_file_url,
        url: api_file_url,
        img_url:api_file_url,
        path: {
            workspace: '~',
            model: "~/modules/",
            screen: "~/data/screenshot/",
            concat: api_file_path_concat
        },
        read:api_file_read,
        copy: api_file_copy,
        dir:api_file_dir,
        rname:api_file_rname,
        delete: api_file_delect,
        write: api_file_write,
    },
    marks: {
        point: {
            daos: [],
            add: api_marks_point_add,
            clear: api_marks_point_clear
        },
        rect: {
            daos: [],
            add: api_marks_rect_add,
            clear: api_marks_rect_clear
        },
    },
    image: {
        show:api_image_show,
        get_rect: api_get_rect,
        set_rect: api_set_rect,
        get_color: {},
        crop: api_image_crop
    },
    module: {
        current: undefined,
        all: undefined,
        get_all: api_module_getlist
    },
    sys:{
        copy:api_sys_copy,
        alert:api_sys_tip
    }
}

gpapi.stack = gpapi.strack

function api_image_show(path){
    gp_path = path;
    showImg(gp_path)
}

function api_get_workspace(){
//    $.ajax({
//        url: "http://127.0.0.1:9097/env",
//        type: 'GET',
//        async:false,
//        dataType: 'json',
//        success: function(data) {
//            workspace = data.data.home;
//        },
//        error: function(xhr, status, error) {
//            return null;
//        }
//    });
}

function api_getimage() {
    alert("img")
}

function api_get_rect() {
    // var rect = scope_pos[0].x
    if (scope_pos != null && scope_pos.length == 2) {
        if (scope_pos[0] != null && scope_pos[1] != null) {
            return [scope_pos[0].x, scope_pos[0].y, scope_pos[1].x, scope_pos[1].y]
        }
    }
    return []
}

function api_set_rect(rect,noti_iframe) {

    if (rect == undefined) {
        scope_pos = [null, null];

        // change_part_rect(false)
        return
    }

    // alert(rect)
    var down = { x: rect[0], y: rect[1], color: null }
    var up = { x: rect[2], y: rect[3], color: null }
    scope_pos = [down, up]

    var rimgw = image_data_object.width;
        var rimgh = image_data_object.height;

        var cimgw = image.width;
        var cimgh = image.height;

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

    // part_box.css("width", 2 + "px");
    // part_box.css("height", 2 + "px");

    // alert(scope_pos[0].x)

    // part_box.css("left", down.x + "px");
    // part_box.css("top", down.x.y + "px");
    // part_box.css("width", (up.x-down.x)+"px");
    // part_box.css("height", (up.y-down.y)+"px");
    // part_box.css("display", "block");

    if(noti_iframe==undefined){
        noti_iframe = false;
    }

    change_part_rect(noti_iframe)

    // changeImageMarkSize()

    // changeBoxRect()

}

function api_get_xycolor() {

}

function api_strack_load() {
    // alert("load")
    var gp_file = getQueryString("gp", window.location.href);
    if (gp_file) {
        var file_name = gp_file.split('/').pop();
        var gp_target_name = "as_gp_"+file_name.split(".")[0]
        $.ajax({
            url: `${baseUrl}/api/gp/strack/load`,
            type: 'post',
            data: { file: gp_file,name:gp_target_name },
            async: false,
            success: function (res) {
                if (res.code == 1) {
                    // alert(res.data)
                    var daos = JSON.parse(res.data)
                    gpapi.strack.info.gpname = file_name.split(".")[0]
                    gpapi.strack.info.name = gp_target_name
                    gpapi.strack.info.path = strackDir + gp_target_name
                    gpapi.strack.info.data_path = gpapi.strack.info.path + "/" + temp_gp_dataname

                    gpapi.strack.daos = daos;
                    fill_gp_job(gpapi.strack.daos)

                }
            },
            error: function (err) {
                // alert(err)
            }
        })
    } else {
        // 创建临时GP文件夹以及数据文件
        var temp_gpname = "temp"
        var temp_gpdir = strackDir +"/"+temp_gpname

        // $.ajax({
        //     url: `${baseUrl}/api/file/remove`,
        //     type: 'post',
        //     data: {path: "~/data/cache/" },
        //     async: false,
        //     success: function (res) {
        //         // alert(res)
        //         // alert(JSON.stringify(res))
        //     },
        //     error: function (err) {
        //         alert(JSON.stringify(err))
        //     }
        // })

        $.ajax({
            url: `${baseUrl}/api/file/create`,
            type: 'post',
            data: {path: temp_gpdir, name: temp_gp_dataname, type: "file" },
            async: false,
            success: function (res) {
                // alert(JSON.stringify(res))
            },
            error: function (err) {
                alert(JSON.stringify(err))
            }
        })



        gpapi.strack.info.gpname = temp_gpname
        gpapi.strack.info.name = temp_gpname
        gpapi.strack.info.path = temp_gpdir
        gpapi.strack.info.data_path = temp_gpdir + "/" + temp_gp_dataname
        gpapi.strack.info.id = temp_gpname

        // alert(gpapi.strack.info.data_path)
    }
}

function api_strack_export(path, name) {
    // 保存数据文件

    // var gp = {
    //     id:gpapi.strack.info.id,
    //     data:gpapi.strack.daos
    // }

    var gp = gpapi.strack.daos;

    // alert(gpapi.strack.info.data_path)

    var data = JSON.stringify(gp)

    

    $.ajax({
        url: `${baseUrl}/api/file/save`,
        type: 'post',
        data: { path: gpapi.strack.info.data_path, content: data },
        async: false,
        success: function (res) {
            // alert("亨功")
        },
        error: function (err) {
            // alert(err)
        }
    })

    // alert(data)

    // 打包gp文件,

    var source_path = gpapi.strack.info.path

    // alert(source_path)

    var target_path = path + "/res/gp/" + name + ".gp"
    // alert(target_path)
    $.ajax({
        url: `${baseUrl}/api/gp/strack/export`,
        type: 'post',
        data: { source: source_path, target: target_path },
        async: false,
        success: function (res) {
            // alert(res)
            // $("#gp_export_submitf").text("已保存")
        },
        error: function (err) {
            alert(err)
        }
    })
}

function api_strack_res_get_path(file) {
    var path = gpapi.file.path.concat([gpapi.strack.info.path, file])
    return path
}

function api_strack_file(file){
    var path = gpapi.file.path.concat([gpapi.strack.info.path, file])
    var url =  `${baseUrl}/api/file/get?path=${path}`;
    return {path:path,url:url}
}

function api_strack_daos_exist(nid) {
    if (nid) {
        var exist = false
        gpapi.strack.daos.forEach(dao => {
            if (dao.nid == nid) {
                exist = true
                return
            }
        });

        return exist
    } else {
        return false
    }
}

function api_strack_insert(data) {
    gpframe = document.getElementById("gpiframe")
    if (gpframe && gpframe.contentWindow.gp) {
        if (api_strack_daos_exist(gpframe.contentWindow.gp.nid)) {
            //更新
            gpframe.contentWindow.gp["data"] = data
            fill_gp_job(gpapi.strack.daos)
        } else {
            //添加
            var gp = JSON.parse(JSON.stringify(gpframe.contentWindow.gp));
            gp["nid"] = Date.now()
            if (data) {
                gp["data"] = data
            }
            gpapi.strack.daos.push(gp)
            gpframe.contentWindow.gp = gp
            // gp_job.push(gp)
            fill_gp_job(gpapi.strack.daos)
        }
        gpapi.strack.run(on_strack_run_result)
        // excute_gpjob()
    } else {
        alert("Error 没有找到GP对象")
    }
}

function api_strack_update(data) {
    gpframe = document.getElementById("gpiframe")
    if (gpframe && gpframe.contentWindow.gp) {
        if (data) {
            gpframe.contentWindow.gp["data"] = data
        }

        fill_gp_job(gpapi.strack.daos)
        // excute_gpjob()
        gpapi.strack.run(on_strack_run_result)
    } else {
        alert("Error 没有找到GP对象")
    }
}

function api_strack_delect(nid) {
    var niddom = undefined;
    // alert(gpapi.strack.daos.length)
    gpapi.strack.daos.forEach((gp, index) => {
        if (gp.nid == nid) {
            niddom = index
        }
    });

    if (niddom != undefined) {
        gpapi.strack.daos.splice(niddom, 1)
        fill_gp_job(gpapi.strack.daos)
        gpapi.strack.run(on_strack_run_result)
    }

    // alert(gpapi.strack.daos.length)

}

function api_strack_clear() {
    var niddom = undefined;
    // alert(gpapi.strack.daos.length)
    gpapi.strack.daos = [];

    fill_gp_job(gpapi.strack.daos)



    // alert(gpapi.strack.daos.length)

}

function api_strack_test(data, listener) {

    var gp = JSON.parse(JSON.stringify(gpframe.contentWindow.gp));
    // gpapi.strack.daos.push(gp)

    var param_gpjob = gpapi.strack.daos.slice();

    if (!gp.nid) {
        gp["nid"] = Date.now()
        if (data) {
            gp["data"] = data
        }
        param_gpjob.push(gp)
    } else {
        param_gpjob.forEach(item => {
            if (item.nid == gp.nid) {
                item.data = data
            }
        });
    }

    $.ajax({
        url: `${baseUrl}/api/screen/gp`,
        type: 'post',
        data: {device_id:device_id, strack: JSON.stringify(param_gpjob), image: source_path, gp: gpapi.strack.info.name },
        async: true,
        success: function (res) {
            if (res.code == 1) {
                res.data = JSON.parse(res.data)
                // fill_excute_res(data,param_gpjob[param_gpjob.length-1])
            }
            listener(res)

        },
        error: function (err) {
            listener(0, err)
        }
    })
}

function api_strack_run(listener, pos) {

    $("#imagelist_loading").show();

    var currentGP = undefined;

    if (gpapi.strack.daos == null || gpapi.strack.daos.length < 1 || pos == -1) {
        // $("#imagelist_loading").show();
        // showImg(source_path)

        var res = {
            code: 1,
            data: {
                image: source_path, data: ""
            }
        }

        listener(res)
        return;
    }

    var param_gpjob = gpapi.strack.daos;

    if (pos != undefined) {
        param_gpjob = gpapi.strack.daos.slice(0, pos + 1);
    }

    currentGP = param_gpjob[param_gpjob.length - 1]

    $("#coder-board-loading").show();
    $.ajax({
        url: `${baseUrl}/api/screen/gp`,
        type: 'post',
        data: { device_id:device_id,strack: JSON.stringify(param_gpjob), image: source_path, gp: gpapi.strack.info.name },
        async: true,
        success: function (res) {
            // alert(res)
            $("#coder-board-loading").hide();
            if (res.code == 1) {
                var data = JSON.parse(res.data)
                res.data = data
                // listener(res.code, data, currentGP)
                gpapi.strack.result = res
                listener(res, currentGP)
                // fill_excute_res(data,param_gpjob[param_gpjob.length-1])
            } else {
                listener(res)
            }
        },
        error: function (err) {
            alert(err)
            $("#coder-board-loading").hide();
        }
    })
}


function api_marks_point_add(id, xy) {
    var dom = $("#mark-point-item").clone()
    gpapi.marks.point.daos.push({ id: id, x: xy[0], y: xy[1] })
    dom.appendTo(".mark-points")
    dom.attr("id", null)
    dom.find(".mark-points-number").text(id + "")
    dom.find(".mark-points-xy").text(xy[0] + "," + xy[1])

    $("#toolbar_mask_clear").addClass("toolbar_mask_active")

    changeImageMarkSize()

}

function api_marks_point_clear() {
    gpapi.marks.point.daos = []

    $(".mark-points").empty()
    $("#toolbar_mask_clear").removeClass("toolbar_mask_active")

    // changeImageMarkSize()

}

function api_marks_rect_add(id, rect) {
    var dom = $("#mark-rect-item").clone()
    gpapi.marks.rect.daos.push({ id: id, rect: rect })
    dom.appendTo(".mark-rects")
    dom.attr("id", null)
    dom.find(".mark-rect-number").text(id + "")

    $("#toolbar_mask_clear").addClass("toolbar_mask_active")

    changeImageMarkSize()

}

function api_marks_rect_clear() {
    gpapi.marks.rect.daos = []
    $(".mark-rects").empty()
    $("#toolbar_mask_clear").removeClass("toolbar_mask_active")

    // changeImageMarkSize()

}

// function api_marks_rect_add(id,rect){
//     var dom = $("#mark-point-item").clone()
//     gpapi.marks.point.daos.push({id:id,x:xy[0],y:xy[1]})
//     dom.appendTo(".mark-points")
//     dom.attr("id",null)
//     dom.find(".mark-points-number").text(id+"")
//     dom.find(".mark-points-xy").text(xy[0]+","+xy[1])

//     changeImageMarkSize()

// }

function api_image_crop(listener, p_rect, target_path) {
    if (p_rect) {
        $.ajax({
            url: `${baseUrl}/api/file/image/crop`,
            type: 'post',
            data: { image: gp_path, rect: JSON.stringify(p_rect), target: target_path },
            async: true,
            success: function (res) {
                if (res.code == 1) {
                    listener(res.data)
                    // fill_excute_res(data,param_gpjob[param_gpjob.length-1])
                } else {
                    alert(res.msg)
                }
            },
            error: function (err) {
                alert(res.msg)
            }
        })
    } else {
        return source_path
    }
}

function api_file_url(file_path) {
    return `${baseUrl}/api/file/get?path=${file_path}`;
}

function api_file_path_concat(paths) {
    var real_path = ""
    paths.forEach(path => {
        var spc = ""
        if(!path.startsWith("/")){
            spc = "/"
        }
        real_path = real_path +spc+ path;
    });
    real_path = real_path.replace(/\/\//g, '/')
    return real_path;
}

function api_file_read(source_file,listener){
    $.ajax({
        url: `${baseUrl}/api/file/get`,
        type: 'post',
        data: { path: source_file },
        async: false,
        success: function (res) {
            if (listener && res) {
                listener(res)
            }
        },
        error: function (err) {
            alert(err)
        }
    })
}

function api_file_copy(source_file, target_file, listener) {
    $.ajax({
        url: `${baseUrl}/api/file/copy`,
        type: 'post',
        data: { source: source_file, target: target_file },
        async: false,
        success: function (res) {
            if (res.code == 1) {
                if (listener) {
                    listener(res.data)
                }
                // fill_excute_res(data,param_gpjob[param_gpjob.length-1])
            } else {
                listener(res)
                // alert(res.msg)
            }
        },
        error: function (err) {
            alert(JSON.stringify(err))
        }
    })
}

function api_file_dir(dir_path,listener){
    $.ajax({
        url: `${baseUrl}/api/files`,
        type: 'post',
        data: { path: dir_path },
        async: false,
        success: function (res) {
            if (listener) {
                listener(res)
            }
        },
        error: function (err) {
            alert(res.msg)
        }
    })
}

function api_file_rname(path,rname,listener){
    $.ajax({
        url: `${baseUrl}/api/file/rename`,
        type: 'post',
        data: { path: path,name:rname },
        async: false,
        success: function (res) {
            if (listener) {
                listener(res)
            }
        },
        error: function (err) {
            alert(res.msg)
        }
    })
}

function api_file_delect(path,listener){
    $.ajax({
        url: `${baseUrl}/api/file/remove`,
        type: 'post',
        data: { path: path },
        async: false,
        success: function (res) {
            if (listener) {
                listener(res)
            }
        },
        error: function (err) {
            alert(res.msg)
        }
    })
}

function api_file_write(path,content){
    $.ajax({
        url: `${baseUrl}/api/file/save`,
        type: 'post',
        data: { path: path,content: content},
        async: false,
        success: function (res) {
            if (listener) {
                listener(res)
            }
        },
        error: function (err) {
            alert(res.msg)
        }
    })
}

function api_module_getlist(listener) {
    $.get(baseUrl + "/api/module/list ", {}, function (data, textStatus) {
        listener(data)
    }
    );
}

function api_strack_genor_code(name) {
    var header = []
    var body = []

    header.push("from ascript.android.screen import gp")
    header.push("from ascript.android.system import R")
    header.push("")

    body.push(`res = gp.run(R.res('gp/${name}.gp'))`)
    body.push(`if res:`)
    body.push(`   print(res.data)`)

    let all_codes = header.concat(body); 
    var f_code = all_codes.join("\n");
    $("#gp_export_code").val(f_code)
}

function api_strack_source_code(name) {
    var header = []
    var body = []

    header.push("from ascript.android.screen import gp")
    header.push("from ascript.android.system import R")
    header.push("")

    body.push(`res = gp.run(R.res('gp/${name}.gp'))`)
    body.push(`if res:`)
    body.push(`   print(res.data)`)

    let all_codes = header.concat(body); 
    var f_code = all_codes.join("\n");
    $("#gp_export_code").val(f_code)
}

function api_sys_copy(msg){
    // alert(msg)
    var createInput = document.createElement("input");
    createInput.value = msg;
    document.getElementById("container_img").appendChild(createInput);
    createInput.select();
    document.execCommand("Copy");
    createInput.className = 'createInput';
    createInput.style.display = "none";

    api_sys_tip("已复制:"+msg)

    // alert(createInput.value)
}

function api_sys_copy_form(msg,formid){
    // alert(msg)
    createInput = document.getElementById(formid)
    createInput.select();
    document.execCommand("Copy");

    api_sys_tip("已复制:"+msg)

    // alert(createInput.value)
}

async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      console.log('Text copied to clipboard');
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  }
  

function api_sys_tip(msg){

    if (msg.length > 30) {  
        msg = msg.slice(0, 30) + '...';  
      } 

    $("#as_toast_msg").text(msg)
    $('#liveToast').toast('show')
    
}
