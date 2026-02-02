import eel
from ascript.windows.tools.gpplug.plug import GpPlug

class FindImagesPlug(GpPlug):
    name = "找图"
    description = "快速找到小图在大图中的位置"
    entry_html = "plugs/find_images.html"
    icon = "img/svg/find_images.svg"


class FindColorsPlug(GpPlug):
    name = "找色"
    description = "通过颜色特征,找到图像中的点位"
    entry_html = "plugs/find_colors.html"
    icon = "img/svg/find_colors.svg"


class RapidOCRPlug(GpPlug):
    name = "Rapid文字识别"
    description = "传入图像,识别途中文字"
    entry_html = "plugs/rapidocr.html"
    icon = "img/svg/ocr.svg"


@eel.expose
def ascript_plug_list():
    plugs = [FindImagesPlug(), FindColorsPlug(), RapidOCRPlug()]
    return [el.to_dict() for el in plugs]