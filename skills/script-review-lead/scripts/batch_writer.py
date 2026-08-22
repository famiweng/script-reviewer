# -*- coding: utf-8 -*-
"""
影视剧本审稿批次写盘与台账快照引擎 (Batch Writer & Snapshot Engine)
纯本地物理执行，提供跨平台 UTF-8 安全落盘、自动目录创建与长剧集分卷快照备份。
"""

import sys
import io
import shutil
import argparse
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


def read_content_or_file(val: str) -> str:
    if not val:
        return ""
    # 若传入的是存在的文件路径，则以 UTF-8 读取其内容
    p = Path(val)
    if p.is_file() and p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            for enc in ["gb18030", "gbk", "utf-16"]:
                try:
                    return p.read_text(encoding=enc)
                except Exception:
                    continue
    return val


def write_whitepaper(
    workspace_dir: Path,
    whitepaper_content: str
):
    workspace_dir.mkdir(parents=True, exist_ok=True)
    whitepaper_file = workspace_dir / "final_whitepaper.md"
    whitepaper_file.write_text(whitepaper_content, encoding="utf-8")
    print(f"✅ 全剧终极白皮书已安全落盘至工作区根目录: {whitepaper_file}")


def write_batch(
    workspace_dir: Path,
    batch_id: str,
    report_content: str,
    changelog_content: str,
    ledger_content: str,
    end_ep: int = 0
):
    reports_dir = workspace_dir / "reports"
    ledgers_dir = workspace_dir / "ledgers"
    snapshots_dir = ledgers_dir / "snapshots"

    reports_dir.mkdir(parents=True, exist_ok=True)
    ledgers_dir.mkdir(parents=True, exist_ok=True)

    # 1. 写入分集/批次审查报告
    if report_content:
        report_file = reports_dir / f"report_{batch_id}.md"
        report_file.write_text(report_content, encoding="utf-8")
        print(f"✅ 审查报告已落盘: {report_file}")

    # 2. 写入本批增量变更日志
    if changelog_content:
        changelog_file = ledgers_dir / f"changelog_{batch_id}.md"
        changelog_file.write_text(changelog_content, encoding="utf-8")
        print(f"✅ 增量变更日志已落盘: {changelog_file}")

    # 3. 原地更新全剧总台账
    if ledger_content:
        global_ledger_file = ledgers_dir / "global_ledgers.md"
        global_ledger_file.write_text(ledger_content, encoding="utf-8")
        print(f"✅ 全剧总台账已演进: {global_ledger_file}")

        # 4. 长剧集分卷快照备份 (智能跨越满 10 集里程碑自动备份，兼容任意批次步长)
        if end_ep >= 10:
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            max_milestone = (end_ep // 10) * 10
            for milestone in range(10, max_milestone + 1, 10):
                snapshot_file = snapshots_dir / f"global_ledgers_ep_{milestone:03d}.md"
                if not snapshot_file.exists():
                    shutil.copy2(global_ledger_file, snapshot_file)
                    print(f"📸 [快照备份] 跨越第 {milestone} 集里程碑，台账快照已自动归档: {snapshot_file}")


def main():
    parser = argparse.ArgumentParser(description="剧本审查批次写盘与快照引擎 (Batch Writer)")
    parser.add_argument("--workspace", "-w", required=True, help="剧本工作区路径 (如 .script_review_workspace/<剧本名>)")
    parser.add_argument("--batch-id", "-b", default="", help="批次标识 (如 ep_001_003 或 ep_001)")
    parser.add_argument("--end-ep", "-e", type=int, default=0, help="当前批次结束集数序号 (用于自动判断是否触发满10集快照备份)")
    parser.add_argument("--report", "-r", default="", help="审查报告文本或输入文件路径")
    parser.add_argument("--changelog", "-c", default="", help="增量日志文本或输入文件路径")
    parser.add_argument("--ledger", "-l", default="", help="演进后的全局总台账文本或输入文件路径")
    parser.add_argument("--whitepaper", "--wp", default="", help="全剧终极白皮书文本或输入文件路径 (直接落盘至工作区根目录 final_whitepaper.md)")

    args = parser.parse_args()
    ws_path = Path(args.workspace)

    # 若传入了白皮书内容，直接执行终极白皮书落盘至工作区根目录
    if args.whitepaper:
        wp_text = read_content_or_file(args.whitepaper)
        write_whitepaper(workspace_dir=ws_path, whitepaper_content=wp_text)

    # 若传入了批次审查内容，执行分集与台账批次落盘
    if args.batch_id or args.report or args.changelog or args.ledger:
        report_text = read_content_or_file(args.report)
        changelog_text = read_content_or_file(args.changelog)
        ledger_text = read_content_or_file(args.ledger)

        write_batch(
            workspace_dir=ws_path,
            batch_id=args.batch_id or "latest",
            report_content=report_text,
            changelog_content=changelog_text,
            ledger_content=ledger_text,
            end_ep=args.end_ep
        )


if __name__ == "__main__":
    main()
