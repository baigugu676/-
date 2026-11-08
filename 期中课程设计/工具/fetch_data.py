"""下载 NASA POWER 历史逐日数据；优先使用本地缓存，--refresh 强制刷新。"""
import argparse, concurrent.futures, csv, hashlib, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
CITIES = [("chengdu", "成都", 30.67, 104.06), ("chongqing", "重庆", 29.56, 106.55), ("kunming", "昆明", 25.04, 102.72), ("guiyang", "贵阳", 26.65, 106.63)]
FIELDS = {"temp":"T2M", "max":"T2M_MAX", "min":"T2M_MIN", "rain":"PRECTOTCORR", "humidity":"RH2M", "wind":"WS2M"}
def download(city, refresh):
    key,name,lat,lon=city
    query=urllib.parse.urlencode(dict(parameters=",".join(FIELDS.values()),community="AG",latitude=lat,longitude=lon,start="20240101",end="20241231",format="JSON",**{"time-standard":"LST"}))
    url="https://power.larc.nasa.gov/api/temporal/daily/point?"+query
    target=ROOT/"数据"/"raw"/(key+"_2024.json")
    if refresh or not target.exists():
        request=urllib.request.Request(url,headers={"User-Agent":"CourseVisualization/1.0"})
        with urllib.request.urlopen(request,timeout=120) as response: raw=response.read()
        payload=json.loads(raw)
        if "properties" not in payload: raise ValueError(payload)
        target.write_bytes(raw)
    payload=json.loads(target.read_text())
    params=payload["properties"]["parameter"]
    fill=payload.get("header",{}).get("fill_value",-999)
    rows=[]
    for date in sorted(params["T2M"]):
        row={"date":date[:4]+"-"+date[4:6]+"-"+date[6:]}
        for field,param in FIELDS.items():
            val=params[param].get(date,fill)
            row[field]=None if val==fill else val
        rows.append(row)
    print(name, len(rows), "days", flush=True)
    return dict(id=key,name=name,lat=lat,lon=lon,days=rows,source_url=url,raw_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),parameters=payload.get("parameters"),header=payload.get("header"))
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--refresh",action="store_true");args=parser.parse_args()
    (ROOT/"数据"/"raw").mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: cities=list(pool.map(lambda c:download(c,args.refresh),CITIES))
    result={"year":2024,"source":"NASA POWER Daily API","time_standard":"LST (Local Solar Time)","downloaded_at_utc":datetime.now(timezone.utc).isoformat(),"cities":cities}
    (ROOT/"数据"/"weather_2024.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    for folder in ["任务一_堆叠柱状图","任务二_天气可视化"]:
        (ROOT/folder/"data.js").write_text("window.WEATHER_DATA="+json.dumps(result,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
    with (ROOT/"数据"/"weather_2024.csv").open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=["city","lat","lon","date",*FIELDS]);writer.writeheader()
        for c in cities:
            for d in c["days"]:writer.writerow(dict(city=c["name"],lat=c["lat"],lon=c["lon"],**d))
if __name__=="__main__":main()
