#!/usr/bin/env python3
"""扬州英语考题周报 - 每周自动生成脚本"""

import json, random, re, os
from datetime import datetime, timedelta

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_FILE = os.path.join(REPO_DIR, "questions_bank.json")
USED_FILE = os.path.join(REPO_DIR, "used_questions.json")
INDEX_FILE = os.path.join(REPO_DIR, "index.html")

def load_bank():
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used(ids):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False)

def pick_questions(bank, used_ids):
    """随机选题，避免重复"""
    by_type_year = {}
    for i, q in enumerate(bank):
        key = (q["type"], q["year"])
        if key not in by_type_year:
            by_type_year[key] = []
        by_type_year[key].append((i, q))
    
    selected_indices = []
    used_set = set(used_ids)
    available = [i for i in range(len(bank)) if i not in used_set]
    
    # 按题型选
    picks = {"单项选择": 5, "词汇运用": 5, "句子翻译": 5, "书面表达": 1}
    
    for qtype, count in picks.items():
        # 从该类型可用题目中选
        type_available = [i for i in available if bank[i]["type"] == qtype]
        if len(type_available) < count:
            # 不够就全部用上（包括已用过的）
            all_type = [i for i in range(len(bank)) if bank[i]["type"] == qtype]
            chosen = random.sample(all_type, min(count, len(all_type)))
        else:
            chosen = random.sample(type_available, count)
        selected_indices.extend(chosen)
    
    return [bank[i] for i in selected_indices], selected_indices

def clean_text(s):
    """清理文本中的多余空白和换行"""
    s = re.sub(r'\n+', ' ', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()

def generate_card(q, idx):
    """生成题目卡片 HTML"""
    qtype = q["type"]
    year = q["year"]
    source = q.get("source", f"{year}年扬州中考真题")
    question = clean_text(q["question"])
    answer = clean_text(q.get("answer", ""))
    explanation = clean_text(q.get("explanation", ""))
    
    if qtype == "单项选择":
        options = q.get("options", "")
        q_body = f'<div class="card-header"><span class="q-number">Q{idx}</span><span class="q-text">{question}</span></div>'
        q_body += f'<div style="font-size:15px;color:var(--text-muted);margin:8px 0 0 36px;line-height:2.2;">{options}</div>'
    else:
        q_body = f'<div class="card-header"><span class="q-number">Q{idx}</span><span class="q-text">{question}</span></div>'
    
    meta = f'<div class="card-meta"><span class="meta-tag">{year}年</span><span class="meta-tag type-tag">{qtype}</span><span class="meta-tag source">来源：{source}</span></div>'
    hint = '<div class="expand-hint">💡 点击查看答案与解析</div>'
    
    answer_label = "✅ 答案" if qtype != "书面表达" else "✅ 参考范文"
    answer_section = f'<div class="answer-section"><div class="answer-box"><div class="answer-label">{answer_label}</div><div class="answer-content">{answer}</div></div>'
    exp_section = f'<div class="explanation-box"><div class="explanation-label">📖 解析</div><div class="explanation-content">{explanation}</div></div></div>'
    
    return f'<div class="question-card" data-type="{qtype}" data-year="{year}">{q_body}{meta}{hint}{answer_section}{exp_section}</div>'

def generate_week_section(questions, week_num):
    """生成一周的 HTML"""
    # 分组
    groups = {"单项选择": [], "词汇运用": [], "句子翻译": [], "书面表达": []}
    for q in questions:
        groups[q["type"]].append(q)
    
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    date_range = f"{week_start.strftime('%Y.%m.%d')} - {week_end.strftime('%Y.%m.%d')}"
    
    html = f'  <div class="week-section" data-week="week-{week_num}">\n'
    html += '    <div class="week-header">\n'
    html += '      <span class="week-dot"></span>\n'
    html += f'      <h2>第{week_num}周考题精选</h2>\n'
    html += f'      <span class="week-badge">{date_range}</span>\n'
    html += '    </div>\n'
    html += f'    <div class="grade-section" data-grade="grade9">\n'
    html += f'      <div class="grade-label g9">📕 扬州中考英语真题 · 第{week_num}期</div>\n'
    
    type_labels = {
        "单项选择": "单项选择（5题）· 2022-2025随机选题",
        "词汇运用": "词汇运用（5题）· 2022-2025随机选题",
        "句子翻译": "句子翻译（5题）· 2022-2025随机选题",
        "书面表达": "书面表达（1题）· 2022-2025随机选题",
    }
    
    q_idx = 0
    for qtype in ["单项选择", "词汇运用", "句子翻译", "书面表达"]:
        items = groups.get(qtype, [])
        if not items:
            continue
        html += f'      <div class="type-group" data-type="{qtype}">\n'
        html += f'        <div class="type-label">{type_labels[qtype]}</div>\n'
        html += '        <div class="questions-grid">\n'
        for q in items:
            q_idx += 1
            html += f'          {generate_card(q, q_idx)}\n'
        html += '        </div>\n'
        html += '      </div>\n'
    
    html += '    </div>\n'
    html += '  </div>\n'
    
    return html

def update_index_html(week_html, week_num):
    """更新 index.html"""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 插入新周报内容（在 WEEKLY_CONTENT_END 之前）
    marker = "<!-- WEEKLY_CONTENT_END -->"
    insert_pos = content.find(marker)
    if insert_pos < 0:
        print("ERROR: Cannot find WEEKLY_CONTENT_END marker")
        return False
    
    new_content = content[:insert_pos] + week_html + content[insert_pos:]
    
    # 更新周次筛选器 - 添加新周的 chip
    new_content = re.sub(
        r'(<span class="filter-chip active" data-filter="week" data-value="all">全部</span>)',
        r'\1\n    <span class="filter-chip" data-filter="week" data-value="week-' + str(week_num) + r'">第' + str(week_num) + r'周</span>',
        new_content
    )
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return True

def main():
    print("=== 扬州英语考题周报生成器 ===")
    
    # 加载题库
    bank = load_bank()
    print(f"题库: {len(bank)} 题")
    
    # 加载已用题目
    used_ids = load_used()
    
    # 确定周次
    week_num = len(used_ids) // 16 + 1 if used_ids else 1
    # 从 index.html 中读取当前最大周次
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    existing_weeks = re.findall(r'week-(\d+)', html)
    if existing_weeks:
        max_week = max(int(w) for w in existing_weeks)
        week_num = max_week + 1
    
    print(f"生成第 {week_num} 周")
    
    # 随机选题
    questions, selected_indices = pick_questions(bank, used_ids)
    
    # 更新已用列表
    new_used = used_ids + selected_indices
    if len(new_used) > len(bank) * 0.9:
        print("题库快用完了，重置已用列表")
        save_used(selected_indices)  # 只保留本周的
    else:
        save_used(new_used)
    
    # 生成 HTML
    week_html = generate_week_section(questions, week_num)
    
    # 更新 index.html
    if update_index_html(week_html, week_num):
        print(f"✅ index.html 已更新")
    else:
        print("❌ 更新失败")
        return 1
    
    # 统计
    types = {}
    for q in questions:
        types[q["type"]] = types.get(q["type"], 0) + 1
    print(f"选题: {types}")
    
    return 0

if __name__ == "__main__":
    exit(main())
