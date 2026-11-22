"""Single-turn text evaluation. Python 3.10+, standard library."""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def export_records():
    records = []
    for file in sorted((ROOT / "runs").glob("*/*/*.json")):
        record = json.loads(file.read_text(encoding="utf-8"))
        records.append([record.get(k, "") for k in ("id", "attempt", "timestamp", "model", "status")] + [str(file.relative_to(ROOT))])
    directory = ROOT / "exports"
    directory.mkdir(exist_ok=True)
    with (directory / "index.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["编号", "尝试", "UTC时间", "模型", "状态", "原始记录"])
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["pilot", "formal", "export"])
    parser.add_argument("--id")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    if args.stage == "export":
        return export_records()
    protocol = load("protocol.json")
    ids = protocol[args.stage]
    if args.id and args.id not in ids:
        parser.error("编号与阶段不符")
    if not args.send:
        for rid in ([args.id] if args.id else ids):
            print(rid, protocol["prompts"][rid.removeprefix("P-").rsplit("-", 1)[0]])
        return
    if not args.id:
        parser.error("每次发送须给出一个 --id")
    cfg = load("config.json")
    if not cfg["model"] or cfg["protocol_version"] != protocol["version"]:
        parser.error("填写模型与一致的提示版本")
    if args.stage == "formal" and not cfg["formal_frozen"]:
        parser.error("正式阶段需先记录冻结决定")
    if not re.fullmatch(r"[A-Za-z0-9_-]+",cfg["model_code"]):
        parser.error("模型管理编号无效")
    if set(cfg["parameters"]) - {"temperature","top_p","max_tokens","seed"}:
        parser.error("配置仅允许采样参数与输出上限")
    if not cfg["endpoint"].startswith("https://"):
        parser.error("请使用官方 HTTPS 地址")
    token = os.environ["MODEL_API_KEY"]
    prompt = protocol["prompts"][args.id.removeprefix("P-").rsplit("-",1)[0]]
    payload = dict(model=cfg["model"],messages=[dict(role="user", content=prompt)],**cfg["parameters"])
    directory = ROOT / "runs" / cfg["model_code"] / args.id
    directory.mkdir(parents=True,exist_ok=True)
    previous = sorted(directory.glob("a*.json"))
    if previous and not args.retry:
        parser.error("已有尝试，检查记录后用 --retry 明确重试")
    number = max((int(p.stem[1:]) for p in previous),default=0)+1
    file = directory / f"a{number:03}.json"
    record = dict(id=args.id,attempt=number,timestamp=datetime.now(timezone.utc).isoformat(),
                  endpoint=cfg["endpoint"],model=cfg["model"],version=protocol["version"],request=payload,status="pending")
    with file.open("x",encoding="utf-8") as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2)
    try:
        request=Request(cfg["endpoint"],json.dumps(payload).encode(),{"Authorization":"Bearer "+token,"Content-Type":"application/json"})
        with urlopen(request,timeout=120) as response:
            record["response"]=json.load(response)
        answer=record["response"]["choices"][0]
        record["status"]="received" if answer["message"].get("content") else "empty"
    except Exception as exc:
        record.update(status="error",error=str(exc))
    tmp=file.with_suffix(".tmp")
    tmp.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(file)
    print(file,record["status"])
    return int(record["status"]!="received")


if __name__ == "__main__":
    sys.exit(main())
