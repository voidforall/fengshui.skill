"""礼貌地批量抓取维基文库原文（wikitext）。

用法：python3 -I fetch_wikisource.py <输出目录> <任务文件>
任务文件每行一条：`raw 标题`（取该页 wikitext）或 `search 关键词`（标题搜索）。
每次请求间隔 45 秒；遇限流（429）等待 90 秒重试，最多 3 次；404 视为无此页。
注意：ctext.org 禁止自动下载，不要用本脚本或其他自动工具抓取。
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request, os
OUT = sys.argv[1]
UA = {"User-Agent": "fengshui-skill-research/1.0 (verifying classical citations)"}
BASE = "https://zh.wikisource.org/w/"

def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                body = r.read().decode("utf-8", "replace")
            if "too many requests" in body.lower() or "Wikimedia Error" in body[:500]:
                raise RuntimeError("rate limited")
            return body
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            print("  retry", url[:80], e, flush=True)
            time.sleep(90)
            continue
        except Exception as e:
            print("  retry", url[:80], e, flush=True)
            time.sleep(90)
    return ""

def raw(title):
    return get(BASE + "index.php?title=" + urllib.parse.quote(title) + "&action=raw")

def search(q):
    body = get(BASE + "api.php?action=opensearch&limit=30&format=json&search=" + urllib.parse.quote(q))
    try:
        return json.loads(body)[1]
    except Exception:
        return []

jobs = [l.strip() for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
for job in jobs:
    kind, arg = job.split(" ", 1)
    if kind == "raw":
        txt = raw(arg)
        fn = os.path.join(OUT, arg.replace("/", "_") + ".wiki")
        open(fn, "w", encoding="utf-8").write(txt)
        print(f"raw {arg}: {len(txt)} chars", flush=True)
    else:
        print(f"search {arg}: {search(arg)}", flush=True)
    time.sleep(45)
print("DONE", flush=True)
