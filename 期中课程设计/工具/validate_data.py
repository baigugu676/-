"""独立于前端实现的数据质量与统计校验；仅使用 Python 标准库。"""
import calendar, csv, datetime, hashlib, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main():
    dataset=json.loads((ROOT/'数据/weather_2024.json').read_text(encoding='utf-8'))
    issues=[];stats=[]
    expected=[(datetime.date(2024,1,1)+datetime.timedelta(days=i)).isoformat() for i in range(366)]
    missing=0
    for city in dataset['cities']:
        days=city['days']
        if [d['date'] for d in days]!=expected:issues.append(city['name']+'日期不连续/重复')
        for day in days:
            missing+=sum(day[k] is None for k in ['temp','min','max','rain','humidity','wind'])
            if not all(isinstance(day[k],(int,float)) and math.isfinite(day[k]) for k in ['temp','min','max','rain','humidity','wind']):
                issues.append(city['name']+day['date']+'含非数值');continue
            if not(day['min']<=day['temp']<=day['max'] and day['rain']>=0 and 0<=day['humidity']<=100 and day['wind']>=0):issues.append(city['name']+day['date']+'范围异常')
        if hashlib.sha256((ROOT/'数据/raw'/(city['id']+'_2024.json')).read_bytes()).hexdigest()!=city['raw_sha256']:issues.append(city['name']+'原始数据哈希不一致')
        months=[]
        for m in range(1,13):
            rows=[d for d in days if int(d['date'][5:7])==m]
            if len(rows)!=calendar.monthrange(2024,m)[1]:issues.append(city['name']+f'{m}月条数错误')
            bins=[sum(0<=d['rain']<.1 for d in rows),sum(.1<=d['rain']<10 for d in rows),sum(10<=d['rain']<25 for d in rows),sum(d['rain']>=25 for d in rows)]
            if sum(bins)!=len(rows):issues.append(city['name']+f'{m}月分组不守恒')
            months.append(dict(month=m,days=len(rows),bins=bins,temp=sum(d['temp'] for d in rows)/len(rows),rain=sum(d['rain'] for d in rows),wet=sum(d['rain']>=.1 for d in rows)))
        stats.append(dict(id=city['id'],city=city['name'],temp=sum(d['temp'] for d in days)/len(days),rain=sum(d['rain'] for d in days),wet=sum(d['rain']>=.1 for d in days),max=max(d['max'] for d in days),months=months))
    with (ROOT/'数据/weather_2024.csv').open(encoding='utf-8-sig') as f:
        if len(list(csv.DictReader(f)))!=1464:issues.append('CSV行数错误')
    report=dict(records=sum(len(c['days']) for c in dataset['cities']),cities=4,days_per_city=366,numeric_fields=6,missing_values=missing,issues=issues,checks=['完整闰年日期与唯一性','每月天数一致','温度顺序、湿度、风速、降水范围','原始文件SHA-256一致','月度分组计数守恒','CSV记录数一致'],statistics=stats)
    (ROOT/'数据/数据质量验证.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"数据校验：{report['records']} 条，缺测值 {missing}，异常 {len(issues)}")
    if issues:raise SystemExit('\n'.join(issues))
if __name__=='__main__':main()
