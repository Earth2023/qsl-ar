#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QSO 卡片批量生成器（适配新版 sample.html）
用法：将 sample.html 放在同目录，准备 qso_data.csv，运行脚本。
依赖：beautifulsoup4, lxml
"""

import csv
import os
from pathlib import Path
from bs4 import BeautifulSoup

# ---------- 配置 ----------
TEMPLATE_FILE = "sample.html"
OUTPUT_DIR = "qso"
DATA_FILE = "qso_data.csv"      # 或 .json
# -------------------------

def load_soup(path):
    with open(path, "r", encoding="utf-8") as f:
        return BeautifulSoup(f, "html.parser")

def update_element_by_id(soup, id_name, new_value):
    """
    通用更新：对于大多数普通 id，直接设置 .string。
    对于网格相关的特殊 id（wkd-grid, my-grid），调用专门函数处理。
    """
    # 特殊处理网格字段（因为有两处且结构不同）
    if id_name in ("wkd-grid", "my-grid"):
        update_grid_both_places(soup, id_name, new_value)
        return

    # 其他 id 直接查找并替换
    elem = soup.find(id=id_name)
    if elem:
        elem.string = str(new_value)
    else:
        print(f"   ⚠️ 未找到 id='{id_name}'")

def update_grid_both_places(soup, grid_id, grid_value):
    """同时更新顶部 country-tag 区域和中间 grid-badge 区域的网格值"""
    # 1. 更新中间的 grid-badge (span 元素)
    badge_span = soup.find("span", class_="grid-badge", id=grid_id)
    if badge_span:
        badge_span.string = str(grid_value)
    else:
        print(f"   ⚠️ 未找到中间网格徽章 id='{grid_id}'")

    # 2. 更新顶部的 country-tag 区域网格显示
    # 根据 grid_id 区分是对方网格 (wkd-grid) 还是我方网格 (my-grid)
    if grid_id == "wkd-grid":
        # 找到第一个 station (对方电台) 内的 <i id="wkd-grid">
        icon_tag = soup.select_one(".station:first-of-type i[id='wkd-grid']")
        if icon_tag:
            # 替换或添加紧随其后的文本节点
            set_text_after_icon(icon_tag, grid_value)
    elif grid_id == "my-grid":
        # 找到第二个 station (我方电台) 内的 <i id="my-grid">
        icon_tag = soup.select_one(".station:last-of-type i[id='my-grid']")
        if icon_tag:
            set_text_after_icon(icon_tag, grid_value)

def set_text_after_icon(icon_tag, text):
    """在 <i> 标签后面设置文本节点（替换已存在的文本节点）"""
    # 获取父节点 .country-tag
    parent = icon_tag.parent
    # 找到 icon_tag 在 parent.contents 中的索引
    for i, child in enumerate(parent.contents):
        if child == icon_tag:
            # 检查下一个兄弟节点是否是文本节点
            next_sib = parent.contents[i+1] if i+1 < len(parent.contents) else None
            if next_sib and isinstance(next_sib, str):
                # 已有文本节点，直接替换内容
                parent.contents[i+1].replace_with(f" {text}")
            else:
                # 没有文本节点，插入一个新的
                icon_tag.insert_after(f" {text}")
            break

def generate_html_files(template_path, records, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for idx, record in enumerate(records, start=1):
        soup = load_soup(template_path)

        # 遍历记录中的每个字段，调用更新函数
        for field_id, value in record.items():
            if value is None or value == "":
                continue
            update_element_by_id(soup, field_id, value)

        # 生成文件名：优先使用 card-id，否则用序号
        card_id = record.get("card-id", f"QSO_{idx:03d}").replace("#", "").replace("/", "-")
        # card id version if
        filename = ""
        if card_id[0] == 'A':
            Path("".join([output_dir, '/', card_id[1:9]])).mkdir(parents=True, exist_ok=True)
            filename = f"{card_id[1:9]}/{card_id[9:12]}.html"
        else:
            filename = f"{card_id}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"✅ 已生成: {filepath}")

def load_data_from_csv(csv_path):
    records = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 清理键值
            clean_row = {k.strip(): v.strip() for k, v in row.items() if v is not None}
            records.append(clean_row)
    return records

def load_data_from_json(json_path):
    import json
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    if not os.path.exists(TEMPLATE_FILE):
        print(f"❌ 模板文件 {TEMPLATE_FILE} 不存在")
        return

    if DATA_FILE.endswith(".csv"):
        records = load_data_from_csv(DATA_FILE)
    elif DATA_FILE.endswith(".json"):
        records = load_data_from_json(DATA_FILE)
    else:
        print("❌ 数据文件必须是 .csv 或 .json")
        return

    if not records:
        print("⚠️ 没有数据，无文件生成")
        return

    print(f"📋 共 {len(records)} 条记录，开始生成...")
    generate_html_files(TEMPLATE_FILE, records, OUTPUT_DIR)
    print("🎉 完成！")

if __name__ == "__main__":
    main()