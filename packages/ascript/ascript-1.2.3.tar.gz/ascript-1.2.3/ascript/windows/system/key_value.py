import json
import os
import pathlib
import threading

class KeyValueMeta(type):
    """元类：支持 KeyValue["key"] 这种类级别的索引操作"""

    def __getitem__(cls, key):
        return cls.get(key)

    def __setitem__(cls, key, value):
        cls.save(key, value)

    def __delitem__(cls, key):
        cls.remove(key)


class KeyValue(metaclass=KeyValueMeta):
    _data = None
    _file_path = None
    _lock = threading.Lock()  # 线程锁，防止并发写入冲突
    FILENAME = "config.json"

    @classmethod
    def _initialize(cls):
        with cls._lock:
            if cls._data is None:
                cls._file_path = cls._determine_path()
                cls._data = cls._load_data()

    @classmethod
    def _determine_path(cls):
        # 1. 尝试根目录
        root_path = pathlib.Path(os.getcwd())
        if os.access(root_path, os.W_OK):
            return root_path / cls.FILENAME

        # 2. 回退到用户家目录 (隐藏文件夹)
        home_dir = pathlib.Path.home() / ".app_data"
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir / cls.FILENAME

    @classmethod
    def _load_data(cls):
        if cls._file_path.exists():
            try:
                return json.loads(cls._file_path.read_text(encoding='utf-8'))
            except:
                return {}
        return {}

    @classmethod
    def _commit(cls):
        """确保写入过程是线程安全的"""
        with cls._lock:
            cls._file_path.write_text(
                json.dumps(cls._data, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )

    @classmethod
    def save(cls, key, value):
        cls._initialize()
        cls._data[key] = value
        cls._commit()

    @classmethod
    def get(cls, key, default=None):
        cls._initialize()
        return cls._data.get(key, default)

    @classmethod
    def remove(cls, key):
        cls._initialize()
        if key in cls._data:
            del cls._data[key]
            cls._commit()