  function setIframeHeight(iframe) {
    if (iframe) {
    var iframeWin = iframe.contentWindow || iframe.contentDocument.parentWindow;
    if (iframeWin.document.body) {
    iframe.height = iframeWin.document.documentElement.scrollHeight || iframeWin.document.body.scrollHeight;
    }
    }
    };

    window.onload = function () {
    setIframeHeight(document.getElementById('external-frame'));
    };

    function skip(i){
                if(i==1){
                    top.location.href= "http://"+location.host;
                }
                if(i==2){
                    top.location.href= "http://"+location.host+"/create";
                }
                if(i==3){
                    top.location.href= "http://"+location.host+"/dump";
                }
                if(i==4){
                    top.location.href= "http://"+location.host+"/colortool";
                }
            }