// const baseUrl = 'http://' + window.location.host
// const baseUrl = 'http://192.168.31.59:9096'
let zNodes = null // 树结构信息
let zNodes_cache = null

let selectorSteps = [
  { id: 'root', method: 'Selector', isRoot: true }
];

let currentFindMode = 'find'; // 默认为 find()

var $img = $('#cellphoneScreen')[0]
// 在 forEachNodes 函数外部或上方定义一个变量，用于存储计时器
let scrollTimer = null;
let currentHoverId = null; // 记录当前真正悬停的 ID


// //------------filter
// var node_f_visible = $("#v_f_visible").is(':checked')
// var node_f_text = $("#v_f_text").is(':checked')




$(document).ready(function () { // 初始化

  syncWithBrowserTheme();
  bind_execboard_drag();

  window.hwnd = getQueryString("hwnd");

  refreshWindows();

});


// 1. 刷新窗口列表的函数
async function refreshWindows() {
  // --- [1] 开始动画 ---
  const $icon = $('#refreshIcon');
  $icon.addClass('spin-animation');
  $('#refreshWinBtn').prop('disabled', true);

  console.log("正在请求窗口列表...");

  // --- [你的原始逻辑：不做任何改动] ---
  let response = await eel.get_online_windows()();

  if (response.status === "success") {
    const $menu = $('#windowList');
    const $selectorBtn = $('#windowSelector');
    $menu.empty();
    $menu.append('<li><h6 class="dropdown-header">运行中的应用</h6></li>');

    response.data.forEach(win => {
      let isMatched = (window.hwnd && String(win.hwnd) === String(window.hwnd));
      let item = `<li><a class="dropdown-item ${isMatched ? 'active' : ''}"
                               href="javascript:void(0)"
                               onclick="selectWindow('${win.display}', ${win.hwnd}, '${win.title}')">
                               ${win.display}
                            </a></li>`;
      $menu.append(item);

      if (isMatched) {
        $selectorBtn.text(win.display);
        $selectorBtn.attr('data-current-hwnd', win.hwnd);
        selectWindow(win.display, win.hwnd, win.title);
      }
    });
  }

  // --- [2] 停止动画 ---
  // 延迟 400ms 停止，防止闪烁过快
  setTimeout(() => {
    $icon.removeClass('spin-animation');
    $('#refreshWinBtn').prop('disabled', false);
  }, 400);
}



/**
 * 自动同步浏览器（系统）的主题色给 Bootstrap
 */
function syncWithBrowserTheme() {
  // 1. 定义修改主题的函数
  const setTheme = theme => {
    // 如果系统是 dark，就给 body 设置 data-bs-theme="dark"
    document.documentElement.setAttribute('data-bs-theme', theme);

    // 针对你的一体化代码框做细微调整
    const textarea = document.getElementById('p_i_xml');
    if (textarea) {
      // 深色模式下用深背景，浅色模式下用浅背景
      textarea.style.backgroundColor = (theme === 'dark') ? '#2d2d2d' : '#f8f9fa';
      textarea.style.color = (theme === 'dark') ? '#f8f8f2' : '#212529';
    }
  };

  // 2. 初始检查：获取当前系统/浏览器的主题
  const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  setTheme(preferredTheme);

  // 3. 实时监听：如果用户在 PyCharm/系统中途切换了主题，网页自动跟着变
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    setTheme(e.matches ? 'dark' : 'light');
  });
}

function handleAnalyzeClick() {
  // 从你之前的选择器和输入框取值
  const hwnd = $('#windowSelector').attr('data-current-hwnd');
  const depth = $('#depthInput').val() || 0;

  // 执行抽取的函数
  startAnalyze(hwnd, depth);
}


// 2. 选择窗口后的处理
function selectWindow(displayText, hwnd, window_title) {

  // 1. 更新顶部主按钮
  $('#windowSelector').text(displayText).attr('data-current-hwnd', hwnd);
  $("#node_package").text(displayText);
  window.hwnd = hwnd; // 同步全局变量
  window.window_title = window_title;

  // 2. 关键：更新列表中的选中样式
  // 先移除所有项的 active 类
  $('#windowList .dropdown-item').removeClass('active');

  // 找到当前点击或匹配的那一项，加上 active 类
  // 我们通过之前设置的 data-hwnd 来查找，这是最准的
  $(`#windowList .dropdown-item[data-hwnd="${hwnd}"]`).addClass('active');

  // 3. 联动执行：获取截图
  refreshScreenshot(hwnd);

  handleAnalyzeClick()
}

/**
 * 执行探测的核心函数
 * @param {number|string} hwnd - 目标窗口的句柄
 */
async function startAnalyze(hwnd) {

  // 隐藏 搜索结果框
  $('#nt_box').hide();
  hideAttrView();

  // 1. 确定 hwnd：如果没传参，就从按钮属性拿
  const targetHwnd = hwnd || $('#windowSelector').attr('data-current-hwnd');
  // 2. 内部获取 depth
  const depth = $('#depthInput').val() || 0;

  if (!targetHwnd) {
    alert("请先选择窗口！");
    return;
  }

  // 更新按钮状态（UI反馈）
  const $btn = $('.btn-primary').first();
  $btn.prop('disabled', true).text("正在探测...");



  try {
    // 3. 【核心衔接点】：调用 Python 获取数据
    // 注意：eel 调用返回的是 Promise，必须加 await
    let response = await eel.get_ui_tree_data(parseInt(targetHwnd), parseInt(depth))();



    if (response.status === "success") {
      console.log("数据获取成功，准备填充树...");

      // 4. 【关键步骤】：直接将返回的 data 传给你的 fill_tree_ui 函数
      window.zNodes_cache = response.data;
      fill_tree_ui(response.data);


    } else {
      alert("获取失败: " + response.message);
    }
  } catch (err) {
    console.error("通信失败:", err);
    showToast("通信失败，请检查后端服务是否正常运行", "danger");
  } finally {
    $btn.prop('disabled', false).text("开始探测");
  }
}

/**
 * 刷新窗口截图
 * @param {number|string} hwnd
 */
async function refreshScreenshot(hwnd) {
  if (!hwnd) return;

  console.log("正在请求窗口截图...");
  const response = await eel.get_screenshot(hwnd)();

  if (response.status === "success") {
    // 假设你页面上有一个 id 为 targetImg 的图片标签
    $('#cellphoneScreen').attr('src', response.data);
  } else {
    console.error("截图失败:", response.message);
  }
}


function submit_config() {

  var attrs = []

  for (let i = 0; i < dump_attr.length; i++) {
    if ($(`#cb_${i + 1}`).is(':checked')) {

    } else {
      attrs.push(dump_attr[i])
    }
  }

  // alert(attrs.join(','))

  let param_data = {}
  param_data["ex_attrs"] = attrs.join(',')

  var cb_other_attr = $("#cb_other").is(':checked')
  if (cb_other_attr) {
    cb_other_attr = 1
  } else {
    cb_other_attr = 2
  }

  param_data["other_filter"] = cb_other_attr

  var timeout = $("#v_f_timeout").val()

  if (timeout.length > 0) {
    param_data["timeout"] = timeout
  }

  // alert(JSON.stringify(param_data,0,2))

  $.ajax({
    url: `${baseUrl}/api/node/dumpconfig`,
    type: 'post',
    data: param_data,
    async: true,
    success: function (res) {
      // alert(res)

    },
    error: function (err) {
      // console.log('err', err)
      alert(JSON.parse(err, 2, 0))

    }
  })

}

function getQueryString(name) {
  var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
  var r = window.location.search.substr(1).match(reg);
  if (r != null) {
    return unescape(r[2]);
  }
  return null;
}


//function getactivity() {
//  var strm = getQueryString("activity");
//  if (strm == undefined || strm.length < 0 || strm == "0") {
//    return 0;
//  } else {
//    return strm;
//  }
//
//}

var zTreeObj;
// zTree 的参数配置，深入使用请参考 API 文档（setting 配置详解）
var setting = {
  data: {
    key: {
      name: "name",
      children: "children"
    }
  },
  view: {
    addDiyDom: addDiyDom,
    showIcon: false,
    showLine: true,       // 你之前的配置里开启了线
    selectedMulti: false,
    txtSelectedEnable: false,
    dbClickExpand: false,
    showTitle: false
  },
  callback: {
    // 【核心改动 1】：点击时不让 zTree 把它设为“选中状态”
    // 这样就不会出现那个 curSelectedNode 类名，也就没有黄色背景了
    beforeClick: function (treeId, treeNode) {
      return false;
    }
  }
};


function fill_tree_ui(zNodes) {
  // 1. 确保数据是数组格式
  if (!Array.isArray(zNodes)) {
    zNodes = [zNodes];
  }

  window.zNodes = zNodes;

  const nodeCount = countNodes(zNodes);
  $("#header_total_number").text(` 共找到控件 ${nodeCount} 个`);

  // 2. 递归函数：修改显示条目为 [类型] 名字
  function formatNodeName(node) {
    // 如果 children 是空数组，直接删除该属性
    if (node.children && node.children.length === 0) {
      delete node.children;
      node.isParent = false; // 明确标记为叶子节点
    } else if (node.children) {
      node.children.forEach(formatNodeName);
    }
  }

  // 执行预处理
  zNodes.forEach(formatNodeName);

  // 4. 初始化
  $(".phone-box").remove();
  var zTreeObj = $.fn.zTree.init($("#treeDemo"), setting, zNodes);
  zTreeObj.expandAll(true);

  setCellphoneScreenImg();
}

// 辅助函数：统计总节点数
function countNodes(nodes) {
  let count = 0;
  for (let i = 0; i < nodes.length; i++) {
    count++; // 计入当前节点
    if (nodes[i].children && nodes[i].children.length > 0) {
      count += countNodes(nodes[i].children); // 递归计入子节点
    }
  }
  return count;
}

function screen_size() {
  $.ajax({
    url: `${baseUrl}/api/screen/size`,
    type: 'get',
    data: { device_id: getQueryString("device_id") },
    async: false,
    success: function (res) {
      // alert(JSON.stringify(res,0,2))
      // // alert(JSON.stringify(res,0,2));
      // alert(JSON.stringify(res.data.width))
      modelConfig.noncompatHeightPixels = res.data.height;
      modelConfig.noncompatWidthPixels = res.data.width;
    }
  });
}

function node_package() {
  $.ajax({
    url: `${baseUrl}/api/node/package`,
    type: 'get',
    async: true,
    success: function (res) {
      // alert(res.data.bundle_id)
      node_package_cache = res.data.bundle_id
      $("#node_package").text(res.data.bundle_id)
    }
  });
}

function setInfoData() {
  // alert('1')
  $('#header_pixels').text(`${modelConfig.widthPixels} * ${modelConfig.heightPixels}`)
}

function addDiyDom(treeId, treeNode) {
  var $spanObj = $("#" + treeNode.tId + "_span");
  $spanObj.empty();

  // 1. 构建内容
  let typeStr = treeNode.type || "";
  let nameStr = treeNode.name || "";
  let valStr = treeNode.value || "";
  let fullHtml = `
        <span class="node-type" style="color: var(--bs-secondary-color); margin-right: 2px;">${typeStr}</span>
        <span class="node-name" style="color: var(--bs-body-color);">${nameStr}</span>
        ${valStr ? `<span class="node-val" style="margin-left: 10px; font-style: italic;">"${valStr}"</span>` : ""}
    `;

  // 2. 【关键】统一包装容器：无论是否 clickable，都用这个 div
  // 这样红框覆盖寻找的 .tree-node-xxx 永远是这个 div，样式才可能统一
  let $wrapper = $(`
        <div class="attr-target tree-node-${treeNode.memory_id}" 
             style="display: inline-block; cursor: pointer; padding: 0px 4px; border-radius: 4px; border: 1px solid transparent; transition: all 0.1s;">
        </div>
    `);

  // 3. 区分可点击样式（只改背景边框，不改结构）
  if (treeNode.clickable) {
    $wrapper.css({
      "background-color": "var(--bs-secondary-bg)",
      "border-color": "var(--bs-border-color)"
    }).attr("id", "treenode_" + treeNode.nodeId);
  }

  $wrapper.append(fullHtml);
  $spanObj.append($wrapper);

  const container = $wrapper[0];

  // 4. 事件绑定：统一使用 .tree-node-highlight 类
  container.onmouseover = function (e) {
    // 先清理全局，避免多处高亮
    $('.tree-node-highlight').removeClass("tree-node-highlight");
    $(this).addClass("tree-node-highlight");

    if (typeof handleMouseoverTree === "function") handleMouseoverTree(treeNode);

    // $('.tree-node-locked').removeClass('tree-node-locked');
    e.stopPropagation();
  };

  container.onmouseout = function (e) {
    $(this).removeClass("tree-node-highlight");
    if (typeof handleMouseoutTree === "function") handleMouseoutTree(treeNode);
    e.stopPropagation();
  };

  container.onclick = function (e) {
    if (typeof clickTreeNode === "function") clickTreeNode(treeNode);
    showAttrView();
    e.stopPropagation();
  };
}

function formatZnodes(list) {
  function deleteEmptyArray(children) {
    children.forEach(item => {
      item.nodeId = nodeIdCount
      nodeIdCount++
      if (item.childs.length === 0) {
        delete item.childs
      } else {
        formatZnodes(item.childs)
      }
    })
  }
  deleteEmptyArray(list)
  return list
}

function formatNodeAsString(dom) {
  let attributes = [];
  // 遍历并收集所有属性  
  for (let i = 0; i < dom.attributes.length; i++) {
    const attr = dom.attributes[i];
    attributes.push(`${attr.name}="${attr.value.replace(/"/g, '&quot;')}"`); // 转义属性值中的双引号  
  }
  // 构建包含标签和属性的字符串  
  let stringRepresentation = `<${dom.nodeName} ${attributes.join(' ')}>`;
  // 如果需要闭合标签（对于非自闭合元素）  
  if (!dom.isSelfClosing) { // 注意：isSelfClosing不是标准属性，这里只是示意  
    stringRepresentation += `</${dom.nodeName}>`;
  }
  return stringRepresentation;
}


function formatZnodesXml(dom, de_path) {
  var item = {}
  item.tag = dom.nodeName
  item.type = dom.nodeName
  item.nodeId = nodeIdCount
  item.name = dom.getAttribute("name")
  item.value = dom.getAttribute("value")
  item.label = dom.getAttribute("label")
  item.enabled = dom.getAttribute("enabled") === "true"
  item.visible = dom.getAttribute("visible") === "true"
  item.accessible = dom.getAttribute("accessible") === "true"
  item.x = Number(dom.getAttribute("x"))
  item.y = Number(dom.getAttribute("y"))
  item.width = Number(dom.getAttribute("width"))
  item.height = Number(dom.getAttribute("height"))
  item.index = Number(dom.getAttribute("index"))
  // item.scale = Number(dom.getAttribute("scale"))
  item.xpath = `${de_path}/${item.type}[${item.index + 1}]`
  item.source = formatNodeAsString(dom)

  if (node_f_visible && !item.visible) {
    return undefined
  }

  // if(node_f_text){
  //   if(item.label==null && item.name==null && item.value==null){
  //     return undefined
  //   }
  // }else{
  //   doms.push(dom)
  // }



  // alert(JSON.stringify(item,0,2))

  nodeIdCount++
  var nodes = dom.childNodes
  if (nodes.length > 0) {
    item.children = []
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].nodeType === 1) {
        var cn = formatZnodesXml(nodes[i], item.xpath)
        if (cn != undefined) {
          item.children.push(cn)
        }
      }
    }
  }

  // item.xmldom = dom

  return item
}



async function setCellphoneScreenImg() {
  // 1. 必须重新定义 $img 变量，否则 onload 内部无法识别
  var $img = $('#cellphoneScreen')[0];
  if (!window.hwnd || !$img) return;

  // 2. 获取数据
  const response = await eel.get_screenshot(window.hwnd)();

  if (response.status === "success") {
    const base64Data = response.data;

    // 3. 【关键修改】：先绑定 onload 事件，再给 src 赋值
    $img.onload = function () {
      // 获取图片原始物理尺寸
      var realW = $img.naturalWidth;
      var realH = $img.naturalHeight;

      // console.log(`检测到截图分辨率: ${realW}x${realH}`);

      // 获取容器限制（确保 image_container 在 CSS 中有高度，如 height: 80vh）
      var maxHeight = $("#image_container").height() - 25;
      var maxWidth = ($("#image_container").width() > 1) ?
        $("#image_container").width() - 20 : $("body").width() * 0.3;

      // 防止容器高度为 0 导致计算错误
      if (maxHeight <= 0) maxHeight = 600;

      // 计算缩放比例
      var bl = (realH > realW) ? realH / maxHeight : realW / maxWidth;

      // 计算显示尺寸
      let viewW = Math.round(realW / bl);
      let viewH = Math.round(realH / bl);

      // 更新 UI 样式
      // 同时更新图片和父容器 phoneimgView 的宽高
      $('#phoneimgView').css({ width: viewW + 'px', height: viewH + 'px' });
      $('#cellphoneScreen').css({ width: viewW + 'px', height: viewH + 'px' });
      $('#image_container').css({ width: (viewW + 20) + 'px' });

      // 计算坐标转换比例
      xDpi = realW / viewW;
      yDpi = realH / viewH;

      // 清除旧红框并重新绘制
      $(".phone-box").remove();

      // 确保 window.zNodes 已经在 fill_tree_ui 中赋值
      if (window.zNodes) {
        forEachNodes(window.zNodes);
      }

      // 恢复排序和拖拽功能
      if (typeof phoneBoxSort === "function") phoneBoxSort();
      // if (typeof bind_execboard_drag === "function") bind_execboard_drag();
    };

    // 4. 最后触发加载
    $img.src = base64Data;

  } else {
    console.error("截图失败:", response.message);
  }
}

function func(item, item1) {
  // let awidth = ((item.rect.right - item.rect.left) / xDpi)
  // let aheight = ((item.rect.bottom - item.rect.top) / yDpi)

  // let awidth1 = ((item1.rect.right - item1.rect.left) / xDpi)
  // let aheight1 = ((item1.rect.bottom - item1.rect.top) / yDpi)
  return ($(item).width() * $(item).height()) - ($(item1).width() * $(item1).height());
}

function phoneBoxSort() {
  // 1. 获取所有红框并转为纯数组进行排序（数组操作比 jQuery 对象快得多）
  var bs = $(".phone-box").get();

  // 2. 排序逻辑
  bs.sort(function (a, b) {
    // 计算面积：长 * 宽
    var areaA = a.offsetWidth * a.offsetHeight;
    var areaB = b.offsetWidth * b.offsetHeight;
    // 目标：面积大的排前面（z-index小），面积小的排后面（z-index大）
    return areaB - areaA;
  });

  // 3. 批量应用 z-index
  // 注意：10000次 DOM 操作会卡顿，所以我们尽量减少操作
  for (var i = 0; i < bs.length; i++) {
    bs[i].style.zIndex = i + 10; // 面积最大的 z-index 为 10，之后递增
  }

  console.log(`已完成 ${bs.length} 个红框的层级排序`);
}
//--变大缩小
// 1. 事件只绑定一次，不要放在 setCellphoneScreenImg 里面
$(document).ready(function () {
  bind_execboard_drag();
});

function bind_execboard_drag() {
  var src_posi_X = 0, is_mouse_down = false, initialWidth = 0;

  $(".right_bar").mousedown(function (e) {
    is_mouse_down = true;
    src_posi_X = e.pageX;
    initialWidth = $("#image_container").width();
    e.preventDefault();
  });

  $(document).on("mouseup", function () {
    if (is_mouse_down) {
      is_mouse_down = false;
      // 只有在松开鼠标时，才更新红框坐标系，不需要重新请求图片
      updateImageScaleOnly();
    }
  });

  $(document).mousemove(function (e) {
    if (is_mouse_down) {
      let move_X = e.pageX - src_posi_X;
      let newWidth = initialWidth + move_X;
      if (newWidth > 100) {
        $("#image_container").width(newWidth + "px");
        // 实时调整图片高度以维持比例（可选）
      }
    }
  });
}

function forEachNodes(list, containerFragment = null) {
  if (!list || list.length === 0) return;

  // 如果是递归的第一层，创建一个文档片段（DocumentFragment）来提升性能
  const isRoot = containerFragment === null;
  const fragment = containerFragment || document.createDocumentFragment();

  list.forEach(item => {
    const uniqueId = item.memory_id;

    // 1. 物理坐标转换为当前视图坐标
    const viewX = item.rect.left / xDpi;
    const viewY = item.rect.top / yDpi;
    const viewW = (item.rect.right - item.rect.left) / xDpi;
    const viewH = (item.rect.bottom - item.rect.top) / yDpi;

    // 2. 核心：计算 z-index 解决覆盖问题
    // 面积越小，层级越高。基数 1000000 足够涵盖大多数屏幕分辨率
    const area = Math.round(viewW * viewH);
    const zIndex = 1000000 - area;

    const boxDom = document.createElement("div");
    boxDom.className = 'phone-box';
    boxDom.id = 'imgnode_' + uniqueId;

    // 应用样式
    Object.assign(boxDom.style, {
      left: viewX + 'px',
      top: viewY + 'px',
      width: viewW + 'px',
      height: viewH + 'px',
      zIndex: zIndex,
      position: 'absolute' // 确保定位生效
    });

    // 3. 事件绑定：MouseOver
    // 3. 事件绑定：MouseOver
    boxDom.onmouseover = function () {
      currentHoverId = uniqueId;

      // 清空临时的 Highlight，但不清空 Locked
      $('.tree-node-highlight').removeClass("tree-node-highlight");

      const $this = $(this);
      $this.addClass('actived-imgnode shadow-lg');

      const $treeNode = $('.tree-node-' + uniqueId);
      $treeNode.addClass("tree-node-highlight");

      // 更新工具栏坐标
      const realCenterX = Math.round(item.rect.left + (item.rect.right - item.rect.left) / 2);
      const realCenterY = Math.round(item.rect.top + (item.rect.bottom - item.rect.top) / 2);
      $('#header_viewcenter').text(`${realCenterX}, ${realCenterY}`);

      if (scrollTimer) clearTimeout(scrollTimer);

      scrollTimer = setTimeout(() => {
        if (currentHoverId !== uniqueId) return;

        if ($treeNode.length > 0) {
          // --- 新增：施加特殊锁定样式 ---
          clearLockedStatus(); // 触发前先清空旧的锁定
          $treeNode.addClass('tree-node-locked');

          // --- 优化：调整滚动位置为 center ---
          $treeNode[0].scrollIntoView({
            behavior: 'smooth',
            block: 'center' // 改为 center，确保节点出现在列表正中
          });
        }
      }, 500);
    };

    // 4. 事件绑定：MouseOut
    boxDom.onmouseout = function () {
      if (currentHoverId === uniqueId) currentHoverId = null;
      if (scrollTimer) {
        clearTimeout(scrollTimer);
        scrollTimer = null;
      }
      $(this).removeClass('actived-imgnode shadow-lg');
      $('.tree-node-' + uniqueId).removeClass("tree-node-highlight");
    };

    // 5. 事件绑定：Click
    boxDom.onclick = function (e) {
      e.stopPropagation();
      if (typeof clickTreeNode === "function") {
        clickTreeNode(item);
      } else if (typeof clickNode === "function") {
        clickNode(item);
      }
      if (window.showAttrView) showAttrView();
    };

    // 将生成的节点放入片段中
    fragment.appendChild(boxDom);

    // 递归处理子节点，共用同一个 fragment
    if (item.children && item.children.length > 0) {
      forEachNodes(item.children, fragment);
    }
  });

  // 递归完成后，如果是最顶层，一次性将 10,000 个节点注入 DOM
  if (isRoot) {
    const container = document.getElementById('phoneimgView');
    if (container) {
      container.appendChild(fragment);
    }
  }
}

function clearLockedStatus() {
    $('.tree-node-locked').removeClass('tree-node-locked');
}


function handleNodeDialog(treeNode) {
  // url: `${baseUrl}/cmd?a=click&rule={id=${treeNode.id}}`,

  if (treeNode.id == undefined) {
    alert("ID 为空，请尝试用代码点击，或 坐标点击");
    return;
  }


  $.ajax({
    url: `${baseUrl}/cmd?a=click&rule={\"id\":\"${treeNode.id}\"}`,
    type: 'get',
    async: false,
    success: function (res) {
      console.log('res')
    },
    error: function (err) {
      console.log('err', err)
      alert('err', err)
    }
  })
}

function handleMouseoverTree(node) {
  // 使用 memory_id 寻找对应的红框
  const $imgNode = $('#imgnode_' + node.memory_id);

  if ($imgNode.length > 0) {
    // 增加高亮类，保留基础类
    $imgNode.addClass('actived-imgnode shadow-lg');
  }

  // 更新中心坐标显示
  if (node.rect) {
    const x = Math.round(node.rect.left + (node.rect.right - node.rect.left) / 2);
    const y = Math.round(node.rect.top + (node.rect.bottom - node.rect.top) / 2);
    $('#header_viewcenter').text(`${x}, ${y}`);
  }
}

function handleMouseoutTree(node) {
  const $imgNode = $('#imgnode_' + node.memory_id);
  if ($imgNode.length > 0) {
    $imgNode.removeClass('actived-imgnode shadow-lg');
  }
}

function postclick(id) {
  var xhr = window.XMLHttpRequest ? new XMLHttpRequest : new ActiveXObject('Microsoft.XMLHTTP');
  var url = 'http://' + window.location.host + '/cmd?a=click&rule={"id":"123"}';
  xhr.open('GET', url, true);
  xhr.send(null);
}

function scrool(t, id) {
  var xhr = window.XMLHttpRequest ? new XMLHttpRequest : new ActiveXObject('Microsoft.XMLHTTP');
  var url = 'http://' + window.location.host + '/cmd?a=click&rule={id:"' + id + '"}';
  xhr.open('GET', url, true);
  xhr.send(null);
}

function changeAttrNodeModeAndFillData(msg, id_i, id_c) {
  const inputEl = document.getElementById(id_i);
  const btnEl = id_c ? document.getElementById(id_c) : null;

  // 核心修复：如果输入框 ID 不存在，直接跳过，不报错
  if (!inputEl) {
    console.warn(`未找到输入框 ID: ${id_i}，跳过该属性填充。`);
    return;
  }

  if (msg !== null && msg !== undefined && msg !== "") {
    // 规范化显示布尔值
    if (msg === true) msg = "True";
    if (msg === false) msg = "False";

    inputEl.value = msg;
    inputEl.disabled = false;

    // 如果按钮存在，则启用
    if (btnEl) {
      btnEl.disabled = false;
    }
  } else {
    inputEl.value = "";
    // 如果没有值，建议不要 disabled，方便用户手动输入检索
    // inputEl.disabled = true;
    if (btnEl) {
      btnEl.disabled = true; // 没数据时，点击“+”没意义，可以禁用
    }
  }
}

function updateCodePreview() {
  let finalCode = selectorChain.join("") + ".find_first()";
  $("#p_i_xml").val(finalCode);
}

function get_attr_with_id(nid) {
  $(".node_attr_loading").show()
  let param_data = { device_id: getQueryString("device_id"), node_id: nid }
  $.ajax({
    url: `${baseUrl}/api/node/attr`,
    type: 'get',
    data: param_data,
    async: true,
    success: function (res) {
      $(".node_attr_loading").hide()
      res.data.id = null
      clickTreeNode(res.data)


      zNodes.forEach(function (data, index) {
        if (data.id == nid) {
          zNodes[index] = res.data
          zNodes[index].id = nid
        }
      });

      fill_tree_ui(zNodes)



    },
    error: function (err) {
      // console.log('err', err)
      alert(err)
      $(".node_loading_attr").hide()
    }
  })
}

function clickTreeNode(treeNode) {
  const $container = $("#property");
  $container.empty();

  // 1. zTree 注入的内部属性黑名单（这些绝对不要显示）
  const zTreeBlackList = [
    'isParent', 'isFirstNode', 'isLastNode', 'isAjaxing',
    'checked', 'checkedOld', 'nocheck', 'chkDisabled',
    'halfCheck', 'check_Child_State', 'check_Focus',
    'isHover', 'editNameFlag', 'tId', 'parentTId',
    'zAsync', 'level', 'order', 'source', 'children', 'rect',"memory_id","open"
  ];

  // 2. 初始化预览代码
  currentSelector = "Selector()";
  //    updateCodeArea();

  // 3. 遍历 treeNode
  Object.keys(treeNode).forEach(key => {
    const val = treeNode[key];

    // --- 过滤逻辑 ---
    if (typeof val === 'function') return; // 过滤掉 getParentNode 等方法
    if (zTreeBlackList.includes(key)) return; // 过滤掉 zTree 注入的属性
    if (key.startsWith('__')) return; // 过滤掉可能的双下划线私有变量

    // 4. 调用我们规范化的一体化模板渲染
    // 这里 key 就是 Python 传来的字段，直接作为 Selector 的 method
    $container.append(renderPropertyRow(key, key, key, val));
  });

  // 5. 特殊处理：将 nodeId 显示为 id 并使用 .id() 方法
  if (treeNode.nodeId) {
    $container.prepend(renderPropertyRow("nodeId", "id", "id", treeNode.nodeId));
  }

  //    // 6. 坐标展示（只读）
  //    if (treeNode.rect) {
  //        renderRectRow(treeNode.rect, $container);
  //    }


  showAttrView();
}

function renderPropertyRow(key, label, method, value) {
  const inputId = `p_i_${key}`;
  const displayVal = (value === true) ? "True" : (value === false ? "False" : (value || ""));

  // 核心逻辑：判断当前原始值的类型
  let valueType = "string";
  if (typeof value === "number") valueType = "number";
  if (typeof value === "boolean") valueType = "boolean";

  return `
    <div class="input-group input-group-sm mb-2 shadow-sm">
        <span class="input-group-text bg-body-secondary border-secondary-subtle text-secondary"
              style="width: 85px; justify-content: center;">
            ${label}
        </span>
        <input class="form-control border-secondary-subtle bg-body"
               id="${inputId}"
               type="text"
               value="${displayVal}">
        <button class="btn btn-outline-primary border-secondary-subtle"
                type="button"
                style="width: 35px;"
                data-type="${valueType}" 
                onclick="addSelectorStep('${method}', '${inputId}', this)">
            <i class="bi bi-plus-lg"></i>
        </button>
    </div>`;
}

/**
 * 修改后的添加步骤方法
 */
function addSelectorStep(method, inputId, btnEl) {
  const inputEl = document.getElementById(inputId);
  const val = inputEl ? inputEl.value : "";
  // if (val === "" && method !== 'find_first') return;

  // 从按钮读取预设的类型标记
  const paramType = btnEl ? btnEl.getAttribute('data-type') : 'string';

  selectorSteps.push({
    id: Date.now(),
    method: method,
    param: val,
    paramType: paramType // 显式保存类型
  });

  renderSelectorChain();
}

/**
 * 渲染链条：包含动态属性和最终的 find 模式
 */
function renderSelectorChain() {
  const container = document.getElementById('p_i_xml_container');
  if (!container) return;
  container.innerHTML = '';

  // 1. 遍历中间的属性步骤 (name, id, depth 等)
  selectorSteps.forEach((step) => {
    const span = document.createElement('span');
    span.className = 'code-step px-1 rounded cursor-pointer';

    let displayText = "";
    if (step.isRoot) {
      displayText = "Selector(...)";
    } else {
      // 参数格式化逻辑
      let finalParam = step.paramType === 'string' ? `"${step.param}"` : step.param;
      displayText = `.${step.method}(${finalParam})`;
    }

    span.innerText = displayText;

    // 绑定编辑弹窗 (Root 不绑定)
    if (!step.isRoot) {
      span.style.color = "var(--bs-primary-text-emphasis)";
      span.style.fontWeight = "bold";
      span.onclick = (e) => showEditPopover(e, step.id);
    }

    container.appendChild(span);
  });

  // 2. 追加最终的 find 动作
  const findSpan = document.createElement('span');
  findSpan.className = 'px-1 fw-bold';
  findSpan.style.color = "var(--bs-warning-text-emphasis)"; // 给 find() 一个不同的颜色（如黄色/橙色）
  findSpan.innerText = `.${currentFindMode}()`;

  container.appendChild(findSpan);
}

/**
 * 弹出悬浮修改窗
 */
// 记录当前打开的 Popover 实例
let currentPopover = null;

/**
 * 弹出悬浮修改窗
 */
function showEditPopover(event, stepId) {
  event.stopPropagation();
  const target = event.currentTarget;
  const step = selectorSteps.find(s => s.id === stepId);

  hideActivePopover();

  currentPopover = new bootstrap.Popover(target, {
    html: true,
    title: `修改参数`,
    container: 'body',
    content: () => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = `
                <div class="d-flex flex-column gap-2">
                    <div class="input-group input-group-sm" style="width: 240px;">
                        <input type="text" id="pop-input-${stepId}" 
                               class="form-control bg-dark text-white border-secondary" 
                               value='${step.param}'>
                        <button class="btn btn-primary btn-sm" onclick="saveStepEdit(${stepId})">确定</button>
                    </div>
                    <button class="btn btn-sm btn-outline-danger w-100" onclick="deleteSelectorStep(${stepId})">
                        <i class="bi bi-trash"></i> 删除该属性
                    </button>
                </div>`;
      return wrapper;
    },
    placement: 'top',
    trigger: 'manual'
  });

  currentPopover.show();
  target.classList.add('active-edit');

  setTimeout(() => {
    const input = document.getElementById(`pop-input-${stepId}`);
    if (input) {
      input.focus();
      input.select();

      if (step.paramType === 'number') {
        input.onkeypress = (e) => {
          if (!/[0-9.\-]/.test(e.key)) e.preventDefault();
        };
      }
      input.onkeyup = (e) => { if (e.key === 'Enter') saveStepEdit(stepId); };
    }
  }, 100);
}

/**
 * 删除指定的属性步骤
 */
window.deleteSelectorStep = function (stepId) {
  // 过滤掉当前点击的这个 step
  selectorSteps = selectorSteps.filter(step => step.id !== stepId);

  // 关闭弹窗
  hideActivePopover();

  // 重新渲染链条
  renderSelectorChain();

  console.log(`Step ${stepId} deleted.`);
};

/**
 * 保存修改
 */
window.saveStepEdit = function (stepId) {
  const input = document.getElementById(`pop-input-${stepId}`);
  if (!input) return;

  const step = selectorSteps.find(s => s.id === stepId);
  let newVal = input.value.trim();

  // --- 核心校验逻辑 ---
  if (step.paramType === 'number') {
    // 如果不是纯数字（允许负数或小数点），则弹出提示
    if (newVal !== "" && isNaN(newVal)) {
      input.classList.add('is-invalid'); // 触发 Bootstrap 的错误样式
      alert("该字段仅支持输入数字！");
      return;
    }
  }
  else if (step.paramType === 'boolean') {
    // 强制只能输入 True 或 False (Python 风格)
    const boolMap = { "true": "True", "false": "False", "t": "True", "f": "False" };
    let lowerVal = newVal.toLowerCase();
    if (boolMap[lowerVal]) {
      newVal = boolMap[lowerVal];
    } else {
      alert("该字段仅支持输入 True 或 False！");
      return;
    }
  }

  step.param = newVal;
  hideActivePopover();
  renderSelectorChain();
};

/**
 * 隐藏并清理
 */
function hideActivePopover() {
  if (currentPopover) {
    currentPopover.dispose();
    currentPopover = null;
  }
  // 移除所有高亮状态
  document.querySelectorAll('.code-step').forEach(el => el.classList.remove('active-edit'));
}

/**
 * 全局点击监听：点击弹窗以外区域自动关闭
 */
document.addEventListener('mousedown', function (e) {
  const popoverEl = document.querySelector('.popover');
  // 如果点击的既不是弹窗本身，也不是正在编辑的代码块，就关闭
  if (popoverEl && !popoverEl.contains(e.target) && !e.target.classList.contains('code-step')) {
    hideActivePopover();
  }



});


/**
 * 设置查找模式并重新生成预览
 */
function setFindMode(mode) {
  currentFindMode = mode;

  // 更新按钮显示的文字
  const btn = document.getElementById('find_mode_btn');
  if (btn) {
    btn.innerText = mode + '()';
  }

  // 触发重新渲染预览区
  renderSelectorChain();
}


function getFullSelectorString() {
  let base = "";
  selectorSteps.forEach(step => {
    if (step.isRoot) {
      base += `Selector(title="${window.window_title}")`;
    } else {
      let param = step.paramType === 'string' ? `"${step.param}"` : step.param;
      base += `.${step.method}(${param})`;
    }
  });
  return base + `.${currentFindMode}()`;
}

// 修改原有的 copySelector
function copySelector() {
  const fullCode = getFullSelectorString();
  navigator.clipboard.writeText(fullCode).then(() => {
    showToast("代码已复制到剪贴板\n" + fullCode, "success");
  }).catch(() => {
    showToast("复制失败，请手动选择", "danger");
  });
}

async function testSelector() {
  const fullCode = getFullSelectorString();

  // 1. 发起搜索前，如果当前不是搜索结果状态，记录下原始数据
  // 假设你的全量数据存储在 globalZNodes 变量中，或者从 zTree 对象获取
  const treeObj = $.fn.zTree.getZTreeObj("treeDemo");
  if (!document.getElementById('nt_box').style.display || document.getElementById('nt_box').style.display === 'none') {
    lastZNodes = treeObj.getNodes();
  }

  // 调用 Python
  const response = await eel.test_selector(fullCode)();

  if (response.status === "success") {
    // 2. 显示通知栏
    const ntBox = document.getElementById('nt_box');
    const ntMsg = document.getElementById('nt_msg');
    ntBox.style.display = 'flex';
    ntMsg.innerText = `当前为搜索结果，共找到 ${response.data.length} 个控件`;

    // 3. 渲染搜索结果
    // 注意：这里需要根据你的 zTree 初始化逻辑，传入搜索到的结果数据
    // $.fn.zTree.init($("#treeDemo"), setting, response.data);
    fill_tree_ui(response.data);

    // 绑定复制功能
    document.getElementById('copy_nt_code').onclick = () => {
      copySelector();
    };

    // 绑定关闭/还原功能
    document.getElementById('close_nt').onclick = () => {
      restoreOriginalTree();
    };

  } else {
    alert("执行错误: " + response.message);
  }
}

/**
 * 重置选择器链条：直接清除，不弹窗
 */
function resetSelectorChain() {
  // 1. 记录当前的窗口名，防止重置后还要重新输入窗口
  const currentWin = (selectorSteps.length > 0) ? selectorSteps[0].windowTitle : "当前窗口";

  // 2. 彻底重置数组，只保留根节点和当前的窗口名
  selectorSteps = [
    {
      id: 'root',
      method: 'Selector',
      windowTitle: currentWin,
      isRoot: true
    }
  ];

  // 3. 必须清理掉可能存在的编辑弹窗，否则弹窗会残留
  hideActivePopover();

  // 4. 重新刷新界面
  renderSelectorChain();
}

/**
 * 撤销上一步：同样建议直接撤销，不设阻碍
 */
function undoSelectorStep() {
  if (selectorSteps.length > 1) {
    selectorSteps.pop();
    hideActivePopover();
    renderSelectorChain();
  }
}

/**
 * 抽取通用的气泡弹窗方法
 * @param {string} message 提示内容
 * @param {string} type 颜色类型 (success, danger, warning)
 */
function showToast(message, type = 'success') {
  // 1. 创建 Toast 容器（如果不存在）
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            pointer-events: none;
        `;
    document.body.appendChild(container);
  }

  // 2. 创建单个 Toast 元素
  const toast = document.createElement('div');
  const bgClass = type === 'success' ? '#28a745' : (type === 'danger' ? '#dc3545' : '#ffc107');

  toast.style.cssText = `
        background-color: ${bgClass};
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        white-space: nowrap;
        pointer-events: auto;
    `;
  toast.innerText = message;

  container.appendChild(toast);

  // 3. 触发动画：淡入并向上浮动
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  }, 10);

  // 4. 定时销毁：2.5秒后淡出，3秒后完全移除
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-20px)';
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}



/**
 * 1. 显示属性面板 (优化：已显示不重复动画)
 */
function showAttrView() {
  const $panel = $('#attrView');
  // 如果已经打开，直接返回，避免动画闪烁
  if ($panel.hasClass('is-open') && $panel.is(':visible')) {
    return;
  }

  $panel.stop(true, true).fadeIn(150, function () {
    // jQuery fadeIn 默认转 block，这里强行恢复 flex 确保布局对齐
    $(this).css('display', 'flex');
  }).addClass('is-open');
}

/**
 * 2. 隐藏属性面板
 */
function hideAttrView() {
  const $panel = $('#attrView');
  if (!$panel.hasClass('is-open')) return;

  $panel.stop(true, true).fadeOut(150).removeClass('is-open');

  // 如果有正在编辑的 Popover 气泡，顺便关掉
  if (window.hideActivePopover) window.hideActivePopover();
}

/**
 * 3. 全局点击监听 (处理“点击其他区域隐藏”)
 */
$(document).on('mousedown', function (e) {
  const $panel = $('#attrView');

  // 面板未打开时，不浪费性能
  if (!$panel.hasClass('is-open')) return;

  // --- 判定判定区 ---
  const isInsidePanel = $panel.is(e.target) || $panel.has(e.target).length > 0;
  const isPopover = $(e.target).closest('.popover').length > 0;
  const isCodeStep = $(e.target).closest('.code-step').length > 0;

  // --- 精确豁免区：点击这些元素不会导致面板隐藏 ---
  // .phone-box: 左侧红框
  // .attr-target: 右侧 zTree 的自定义条目容器
  const isRedBox = $(e.target).closest('.phone-box').length > 0;
  const isDiyItem = $(e.target).closest('.attr-target').length > 0;

  // 只有当以上都不是时，才隐藏面板
  if (!isInsidePanel && !isPopover && !isCodeStep && !isRedBox && !isDiyItem) {
    hideAttrView();
  }
});

/**
 * 4. 监听 Esc 按键隐藏
 */
$(document).on('keydown', function (e) {
  if (e.key === 'Escape') {
    hideAttrView();
  }
});

function updateImageScaleOnly() {
  var $img = $('#cellphoneScreen')[0];
  if (!$img || !$img.src || $img.naturalWidth === 0) return;

  var realW = $img.naturalWidth;
  var realH = $img.naturalHeight;

  // 1. 获取容器宽度
  var containerW = $("#image_container").width();

  // 2. 【核心修复】：动态获取窗口高度，减去工具栏等占用的高度
  // 不要直接信任容器的 .height()，因为它可能被 CSS 限制死了
  var vh = window.innerHeight || document.documentElement.clientHeight;
  var containerH = vh - $("#con_tools_bar").height() - 40; // 减去底部工具栏和间距

  var paddingX = 20;
  var maxWidth = Math.max(containerW - paddingX, 50);
  var maxHeight = Math.max(containerH, 50);

  // 3. 计算缩放比
  var blW = realW / maxWidth;
  var blH = realH / maxHeight;

  // 如果你希望拖动宽度时图片有反应，这里可以加一个权重判断
  // 或者干脆采用“适应宽度”模式
  var bl = Math.max(blW, blH);

  let viewW = Math.round(realW / bl);
  let viewH = Math.round(realH / bl);

  $('#phoneimgView, #cellphoneScreen').css({
    width: viewW + 'px',
    height: viewH + 'px'
  });

  window.xDpi = realW / viewW;
  window.yDpi = realH / viewH;

  $(".phone-box").remove();
  if (window.zNodes) forEachNodes(window.zNodes);
}



function restoreOriginalTree() {
  if (window.zNodes_cache) {
    fill_tree_ui(window.zNodes_cache);
  }

  $('#nt_box').hide();
  // window.zNodes_cache = null;
}




function hideparams() {
  tipClose();
}

function back() {
  window.location.href = 'http://' + window.location.host;
}

function refesh() {
  window.location.reload();
}


