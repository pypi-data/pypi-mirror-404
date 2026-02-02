from abc import ABC, abstractmethod
class GpPlug(ABC):

    @property
    @abstractmethod
    def name(self):
        """插件显示名称"""
        pass

    @property
    @abstractmethod
    def description(self):
        """插件显示名称"""
        pass

    @property
    @abstractmethod
    def entry_html(self):
        """入口 HTML 文件名"""
        pass

    @property
    @abstractmethod
    def icon(self):
        """入口 HTML 文件名"""
        pass

    @property
    def class_name(self):
        """自动获取当前类的类名 (例如: 'ColorPicker')"""
        return self.__class__.__name__

    def to_dict(self):
        """将所有约定的属性转换为字典，方便后续转 JSON"""
        return {
            "name": self.name,
            "class_name": self.class_name,
            "description": self.description,
            "entry_html": self.entry_html,
            "icon": self.icon
        }