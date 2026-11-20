import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from editorial import Store, display_time, render_card


ROOT = Path(__file__).resolve().parent
STATUS = {"pending": "待审", "research": "继续调查", "approved": "已批准", "rejected": "已放弃"}


def positive(value):
    integer = int(value)
    if integer < 1:
        raise argparse.ArgumentTypeError("需要正整数")
    return integer


def arguments():
    parser = argparse.ArgumentParser(description="AI 情报监测与公众号选题工作流")
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "editorial.sqlite",
                        help="SQLite 文件，默认 data/editorial.sqlite")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="采集、回查一手来源并生成本地提醒")
    run.add_argument("--sources", type=Path, default=ROOT / "sources.json", help="信源配置")
    run.add_argument("--days", type=positive, default=21, help="采集窗口，默认 21 天")
    run.add_argument("--limit", type=positive, default=7, help="每个源最多保留 7 条，可调整")
    run.add_argument("--report-dir", type=Path, default=ROOT / "data" / "reports", help="提醒文件目录")
    listing = commands.add_parser("list", help="查看选题。默认显示 A/B，按等级和分数排列")
    listing.add_argument("--grade", choices=("A", "B", "C", "D", "AB", "all"), default="AB")
    listing.add_argument("--status", choices=STATUS)
    listing.add_argument("--region", choices=("海外", "国内"))
    listing.add_argument("--limit", type=positive, default=30)
    card = commands.add_parser("card", help="查看详细选题卡和原始链接")
    card.add_argument("id", type=positive)
    card.add_argument("--out", type=Path, help="另存为 Markdown 选题卡")
    review = commands.add_parser("review", help="记录人工审核决策")
    review.add_argument("id", type=positive)
    review.add_argument("status", choices=STATUS)
    review.add_argument("--note", default="", help="核查结论和编辑备注")
    export = commands.add_parser("export", help="导出已批准的选题和公众号写作底稿")
    export.add_argument("id", type=positive)
    export.add_argument("--out", type=Path, default=ROOT / "exports", help="导出根目录")
    commands.add_parser("status", help="查看最近采集的信源健康和处理结果")
    return parser.parse_args()


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def print_metrics(metrics):
    counts = "  ".join(f"{grade} {count}" for grade, count in metrics["counts"].items())
    print(f"批次 {metrics['run_id']}　新条目 {metrics['new_items']}　重复抓取 {metrics['repeated']}"
          f"　合并报道 {metrics['merged']}　新事件 {metrics['new_events']}　新提醒 {len(metrics['alert_ids'])}")
    print("本批次事件　" + counts)


def run_collection(db, args):
    from sources import collect

    now = datetime.now(timezone.utc)
    batch, outcomes = collect(args.sources, now, args.days, args.limit)
    metrics = db.save_run(now, batch, outcomes)
    cards = sorted((db.get(id_) for id_ in metrics["alert_ids"]),
                   key=lambda card: (card["grade"], -card["score"], card["region"] != "海外"))
    base = f"# AI 选题提醒 · 批次 {metrics['run_id']}\n\n{display_time(now.isoformat())}\n\n"
    entries = [render_card(card) for card in cards]
    report = args.report_dir / f"run-{metrics['run_id']:05d}.md"
    write_text(report, base + ("\n---\n\n".join(entries) if entries else "本批次没有新的 A/B 级提醒。\n"))
    print_metrics(metrics)
    print(f"信源 {len(outcomes)} 个。用 status 查看详情。\n提醒文件 {report.resolve()}")
    if outcomes and all(row.get("status") in {"error", "failed"} for row in outcomes):
        return 2
    return 0


def main():
    args = arguments()
    try:
        with Store(args.db) as db:
            if args.command == "run":
                return run_collection(db, args)
            if args.command == "list":
                cards = [card for card in db.list()
                         if (args.grade == "all" or card["grade"] in args.grade)
                         and (not args.status or card["status"] == args.status)
                         and (not args.region or card["region"] == args.region)]
                for card in cards[:args.limit]:
                    print(f"{card['id']:>4}  {card['grade']} {card['score']:>2}/30  {STATUS[card['status']]}  "
                          f"{card['region']}  {card['title']}")
                if not cards:
                    print("没有符合条件的选题。")
            if args.command == "card":
                text = render_card(db.get(args.id))
                if args.out:
                    write_text(args.out, text)
                    print(args.out.resolve())
                else:
                    print(text, end="")
            if args.command == "review":
                db.review(args.id, args.status, args.note)
                print(f"选题 {args.id} 已设为{STATUS[args.status]}。")
            if args.command == "export":
                print(db.export(args.id, args.out).resolve())
            if args.command == "status":
                run = db.latest_run()
                print(json.dumps(run, ensure_ascii=False, indent=2) if run else "还没有采集批次。")
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f"操作失败　{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    if os.name == "nt":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
