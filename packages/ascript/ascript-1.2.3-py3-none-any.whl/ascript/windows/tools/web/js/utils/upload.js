

function uploadFile(dom,upDir,callback,zipDir) {
    $(dom).trigger('click');
    if (!$(dom).data('hasChangeEvent')) { 
        $(dom).change(function (e) {
            // alert($('#fileupload')[0].files.length)
            if ($(dom)[0].files.length >= 1) {
                var formData = new FormData();
                var fName = $(dom)[0].files[0].name;
                // var fName = new Date().getTime()+".png"
                formData.append("data", e.target.files[0]);
                // formData.append("path", uploadDir+fName);

                if(upDir.endsWith('/')){

                }else{
                    upDir = upDir+"/";
                }

                zipDirStr = "";

                if(zipDir!=undefined && zipDir.length>0){
                    zipDirStr = "&zip="+zipDir+fName.split('.')[0];
                }
                
                $.ajax({
                    url: baseUrl+'/api/file/upload?path='+(upDir+fName)+zipDirStr,
                    type: 'POST',
                    cache: false,
                    data: formData,
                    processData: false,
                    contentType: false
                }).done(function (res) {
                    // $("#upload_pic").text("导入图片");
                    // addPicCacheListItem(fName,false)
                    if(callback){
                        callback();
                    }
                    
                }).fail(function (res) {
                    // getFilesList();
                    // $("#upload_pic").text("导入图片");
                    alert("上传失败")
                });
            }else{
                $("#upload_pic").text("导入图片");
            }

        });
        $(dom).data('hasChangeEvent', true);
    }
}

function upload_zip(dom,upDir,callback,zipDir) {
    $(dom).trigger('click');
    if (!$(dom).data('hasChangeEvent')) { 
        $(dom).change(function (e) {
            // alert($('#fileupload')[0].files.length)
            if ($(dom)[0].files.length >= 1) {
                var formData = new FormData();
                var fName = $(dom)[0].files[0].name;
                // var fName = new Date().getTime()+".png"
                formData.append("data", e.target.files[0]);
                // formData.append("path", uploadDir+fName);

                if(upDir.endsWith('/')){

                }else{
                    upDir = upDir+"/";
                }

                zipDirStr = "";

                if(zipDir!=undefined && zipDir.length>0){
                    zipDirStr = "&zip="+zipDir+fName.split('.')[0];
                }
                
                $.ajax({
                    url: baseUrl+'/api/file/upload?path='+(upDir)+"&zipfile=true",
                    type: 'POST',
                    cache: false,
                    data: formData,
                    processData: false,
                    contentType: false
                }).done(function (res) {
                    // $("#upload_pic").text("导入图片");
                    // addPicCacheListItem(fName,false)
                    if(callback){
                        callback();
                    }
                    
                }).fail(function (res) {
                    // getFilesList();
                    // $("#upload_pic").text("导入图片");
                    alert("上传失败")
                });
            }else{
                $("#upload_pic").text("导入图片");
            }

        });
        $(dom).data('hasChangeEvent', true);
    }
}

function uploadUiFile(dom,upDir,callback,zipDir) {
    $(dom).trigger('click');
    if (!$(dom).data('hasChangeEvent')) { 
        $(dom).change(function (e) {
            // alert($('#fileupload')[0].files.length)
            if ($(dom)[0].files.length >= 1) {
                var formData = new FormData();
                var fName = $(dom)[0].files[0].name;
                // var fName = new Date().getTime()+".png"
                formData.append("data", e.target.files[0]);
                // formData.append("path", uploadDir+fName);

                if(upDir.endsWith('/')){

                }else{
                    upDir = upDir+"/";
                }

                zipDirStr = "";

                if(zipDir!=undefined && zipDir.length>0){
                    zipDirStr = "&zip="+zipDir;
                }
                
                $.ajax({
                    url: baseUrl+'/api/file/upload?path='+(upDir+fName)+zipDirStr,
                    type: 'POST',
                    cache: false,
                    data: formData,
                    processData: false,
                    contentType: false
                }).done(function (res) {
                    // $("#upload_pic").text("导入图片");
                    // addPicCacheListItem(fName,false)
                    if(callback){
                        callback();
                    }
                    
                }).fail(function (res) {
                    // getFilesList();
                    // $("#upload_pic").text("导入图片");
                    alert("上传失败")
                });
            }else{
                $("#upload_pic").text("导入图片");
            }

        });
        $(dom).data('hasChangeEvent', true);
    }
}
