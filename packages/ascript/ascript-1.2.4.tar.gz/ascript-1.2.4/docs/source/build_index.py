import json
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, STORED
from whoosh.qparser import MultifieldParser
import os


def build_search_index(data_path, index_dir):
    # 定义索引结构
    schema = Schema(
        name=TEXT(stored=True),
        module=STORED,
        signature=STORED,
        doc=TEXT,
        params=STORED,
        returns=STORED,
        examples=STORED,
        notes=STORED,
        warnings=STORED,
        file=STORED,
        line=STORED,
        keywords=KEYWORD
    )

    # 创建索引目录
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    # 创建索引
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    # 加载数据
    with open(data_path, 'r', encoding='utf-8') as f:
        functions = json.load(f)

    # 添加到索引
    for func in functions:
        # 创建关键词列表
        keywords = [
            func['name'],
            func['module'].split('.')[-1],
            *func['params'].keys()
        ]

        # 添加文档到索引
        writer.add_document(
            name=func['name'],
            module=func['module'],
            signature=func['signature'],
            doc=func['doc'],
            params=json.dumps(func['params']),
            returns=func['returns'],
            examples="\n".join(func['examples']),
            notes="\n".join(func['notes']),
            warnings="\n".join(func['warnings']),
            file=func['file'],
            line=func['line'],
            keywords=",".join(keywords)
        )

    writer.commit()


if __name__ == "__main__":
    build_search_index(
        data_path="build/html/api_data.json",
        index_dir="search_index"
    )