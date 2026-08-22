# -*- coding: utf-8 -*-
"""
影视剧本智能分章与工作区初始化引擎 (Script Splitter & Workspace Initializer)
纯本地物理执行，无需任何 API Key，实现毫秒级剧本解析、分章切片与工作区目录树建立。
"""

import os
import re
import sys
import io
import argparse
from pathlib import Path
from typing import List, Dict

if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

LEAD_SKILL_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = LEAD_SKILL_DIR.parent
PLUGIN_ROOT = SKILLS_DIR.parent
TEMPLATE_PATH = LEAD_SKILL_DIR / "references" / "ledgers_template.md"


class ScriptSplitter:
    EPISODE_PATTERNS = [
        r"(?m)^[\s#*=-]*(?:[^\n：:\s]{1,15}[:：\s]+)?第\s*([0-9一二三四五六七八九十百]+)\s*[集话回].*$",
        r"(?m)^[\s#*=-]*(?:EPISODE|Episode|EP|Ep)\s*\.?\s*([0-9]+).*$",
        r"(?m)^[\s#*=-]*【第\s*([0-9一二三四五六七八九十百]+)\s*[集话回]】.*$",
        r"(?m)^[\s#*=-]*(?:[^\n：:\s]{1,15}[:：\s]+)?第\s*([0-9一二三四五六七八九十百]+)\s*幕.*$",
        r"(?m)^[\s#*=-]*(?:ACT|Act)\s*\.?\s*([IVXLCDM0-9]+).*$",
        r"(?m)^[\s#*=-]*(?:Sequence|SEQUENCE)\s*\.?\s*([0-9]+).*$",
    ]

    SCENE_PATTERNS = [
        r"(?m)^[\s#*=-]*第\s*([0-9]+)\s*场.*$",
        r"(?m)^[\s#*=-]*(?:SCENE|Scene|Sc)\s*\.?\s*([0-9]+).*$",
        r"(?m)^[\s#*=-]*([0-9]+)[-–.]([0-9]+)\s+(?:内景|外景|INT\.|EXT\.|日|夜).*$",
        r"(?m)^[\s#*=-]*(?:内景|外景|INT\.|EXT\.)\s+.*$",
    ]

    @classmethod
    def read_text(cls, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"剧本文件未找到: {file_path}")

        if file_path.suffix.lower() in [".txt", ".md"]:
            for encoding in ["utf-8", "gb18030", "gbk", "utf-16"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"无法使用常见编码读取文件: {file_path}")
        elif file_path.suffix.lower() == ".docx":
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                raise ImportError("读取 .docx 文件需要安装 python-docx 库: pip install python-docx")
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

    @classmethod
    def split(cls, text: str, project_type: str = "series") -> List[Dict[str, str]]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 1. 优先尝试集数/幕次正则匹配
        matches = []
        for pattern in cls.EPISODE_PATTERNS:
            for match in re.finditer(pattern, text):
                matches.append((match.start(), match.group(0).strip()))

        matches = sorted(list({m[0]: m for m in matches}.values()), key=lambda x: x[0])

        chapters = []
        if len(matches) >= 2:
            for i in range(len(matches)):
                start_idx = matches[i][0]
                end_idx = matches[i+1][0] if i + 1 < len(matches) else len(text)
                title = matches[i][1]
                content = text[start_idx:end_idx].strip()
                chapters.append({
                    "index": i + 1,
                    "title": title,
                    "content": content
                })
            return chapters

        # 2. 次选尝试场次正则匹配 (全类型自适应智能分块)
        scene_matches = []
        for pattern in cls.SCENE_PATTERNS:
            for match in re.finditer(pattern, text):
                scene_matches.append((match.start(), match.group(0).strip()))

        scene_matches = sorted(list({m[0]: m for m in scene_matches}.values()), key=lambda x: x[0])

        if len(scene_matches) >= 5:
            # 短剧按 10 场一组，电影/长剧按 15 场一组
            chunk_size = 10 if project_type == "short_drama" else 15
            for i in range(0, len(scene_matches), chunk_size):
                start_idx = scene_matches[i][0]
                next_chunk_idx = i + chunk_size
                end_idx = scene_matches[next_chunk_idx][0] if next_chunk_idx < len(scene_matches) else len(text)
                chunk_num = (i // chunk_size) + 1
                title = f"第 {chunk_num} 分段 (第 {i+1} ~ {min(next_chunk_idx, len(scene_matches))} 场)"
                content = text[start_idx:end_idx].strip()
                chapters.append({
                    "index": chunk_num,
                    "title": title,
                    "content": content
                })
            return chapters

        # 3. 兜底逻辑：若文本超长 (> 3500 字符) 且无任何集/场标记，按语义段落/字数切分，防止单章注意力衰减
        if len(text) > 3500:
            target_chunk_size = 3000
            paragraphs = text.split("\n\n")
            current_chunk = []
            current_len = 0
            chunk_num = 1

            for p in paragraphs:
                current_chunk.append(p)
                current_len += len(p)
                if current_len >= target_chunk_size:
                    chapters.append({
                        "index": chunk_num,
                        "title": f"第 {chunk_num} 分段 (篇幅约 {current_len} 字)",
                        "content": "\n\n".join(current_chunk).strip()
                    })
                    chunk_num += 1
                    current_chunk = []
                    current_len = 0

            if current_chunk:
                chapters.append({
                    "index": chunk_num,
                    "title": f"第 {chunk_num} 分段 (篇幅约 {current_len} 字)",
                    "content": "\n\n".join(current_chunk).strip()
                })
            return chapters

        # 4. 单章/短篇剧本
        return [{
            "index": 1,
            "title": "全剧 (完整送审稿)",
            "content": text.strip()
        }]


def init_workspace(workspace_dir: Path, chapters: List[Dict[str, str]], clean: bool = True):
    import shutil
    episodes_dir = workspace_dir / "episodes"
    ledgers_dir = workspace_dir / "ledgers"
    reports_dir = workspace_dir / "reports"
    global_ledger_file = ledgers_dir / "global_ledgers.md"

    # 清理旧残留数据，确保全新审查不受历史脏数据污染
    if clean:
        if reports_dir.exists():
            shutil.rmtree(reports_dir)
        if ledgers_dir.exists():
            shutil.rmtree(ledgers_dir)
        if episodes_dir.exists():
            shutil.rmtree(episodes_dir)

    episodes_dir.mkdir(parents=True, exist_ok=True)
    ledgers_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 强制写入干净的初始台账模板
    if TEMPLATE_PATH.exists():
        global_ledger_file.write_text(TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        global_ledger_file.write_text("# 📊 四大核心资产追踪总台账\n\n*(初始空白台账)*\n", encoding="utf-8")

    for ch in chapters:
        ch_path = episodes_dir / f"ep_{ch['index']:03d}.md"
        ch_path.write_text(f"# {ch['title']}\n\n{ch['content']}", encoding="utf-8")

    print(f"✅ 工作区初始化完成！已成功拆分 {len(chapters)} 个独立章节至 {episodes_dir}")
    print(f"📊 纯 Markdown 资产台账已重置并就绪: {global_ledger_file}")


def main():
    parser = argparse.ArgumentParser(description="影视剧本分章落盘与工作区初始化引擎 (Script Splitter)")
    parser.add_argument("--input", "-i", required=True, help="原始剧本文件路径 (.txt / .md / .docx)")
    parser.add_argument("--output", "-o", default=".script_review_workspace", help="工作区输出目录路径")
    parser.add_argument("--type", "-t", default="series", choices=["series", "movie", "short_drama"], help="作品载体类型")
    parser.add_argument("--clean", action="store_true", default=True, help="是否重置并清理工作区历史残留报告与台账 (默认: True)")
    parser.add_argument("--keep-history", action="store_false", dest="clean", help="保留工作区已有历史报告与台账")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 错误: 输入剧本文件不存在: {input_path}")
        sys.exit(1)

    workspace_path = Path(args.output)
    # 清洗项目名称，过滤文件系统非法字符并去除首尾冗余空格
    clean_stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', input_path.stem).strip()
    project_name = clean_stem or "unnamed_project"
    # 自动命名空间隔离：如果输出路径为默认根目录且未包含项目名，则自动按剧本名创建独立子工作区
    if workspace_path.name == ".script_review_workspace":
        workspace_path = workspace_path / project_name

    raw_text = ScriptSplitter.read_text(input_path)
    chapters = ScriptSplitter.split(raw_text, project_type=args.type)
    init_workspace(workspace_path, chapters, clean=args.clean)


if __name__ == "__main__":
    main()
