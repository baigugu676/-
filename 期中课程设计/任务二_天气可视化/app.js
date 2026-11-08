'use strict';
const $=s=>document.querySelector(s);
const {colors,isValid,filterDays,summarize,TrendChart,WeatherCalendar}=WeatherViz;
const state={city:'chengdu',month:'all',metric:'temp',threshold:10,date:'2024-07-15',compare:new Set(['chongqing','kunming'])};
const trend=new TrendChart($('#trend')),calendar=new WeatherCalendar($('#calendar'));
const fmt=(v,n=1)=>isValid(v)?v.toFixed(n):'—';
WEATHER_DATA.cities.forEach(c=>$('#city').add(new Option(c.name,c.id)));
for(let i=1;i<=12;i++)$('#month').add(new Option(`${i}月`,String(i)));
function getCity(id){return WEATHER_DATA.cities.find(c=>c.id===id);}
function chooseDate(date,fromCalendar=false){state.date=date;if(fromCalendar)state.month=String(Number(date.slice(5,7)));render();}
function render(){
  const city=getCity(state.city),days=filterDays(city.days,state.month),summary=summarize(days),period=state.month==='all'?'全年':`${state.month}月`;
  if(!days.some(d=>d.date===state.date))state.date=days[0]?.date;
  const thresholdDays=days.filter(d=>isValid(d.rain)&&d.rain>=state.threshold).length;
  $('#stats').innerHTML=[['平均气温',fmt(summary.temp),'°C · 有效日均值'],['累计降水',fmt(summary.rain),'mm · 当前时段'],['最高日最高气温',fmt(summary.max),'°C'],[`降水 ≥${state.threshold} mm`,thresholdDays,`天 / ${summary.rainCount} 有效日`]].map(([k,v,u])=>`<article><p>${k}</p><strong>${v}</strong><span>${u}</span></article>`).join('');
  $('#compareControls').replaceChildren();
  WEATHER_DATA.cities.forEach(c=>{
    const label=document.createElement('label');label.className='compare-check';
    const input=document.createElement('input');input.type='checkbox';input.value=c.id;input.checked=c.id===state.city||state.compare.has(c.id);input.disabled=c.id===state.city;
    input.onchange=()=>{if(input.checked)state.compare.add(c.id);else state.compare.delete(c.id);render();};
    const dot=document.createElement('i');dot.className='dot';dot.style.background=colors[c.id];
    label.append(input,dot,document.createTextNode(c.name+(c.id===state.city?' · 主城市':'')));$('#compareControls').append(label);
  });
  const cities=WEATHER_DATA.cities.filter(c=>c.id===state.city||state.compare.has(c.id));
  trend.render(cities,{primary:state.city,month:state.month,metric:state.metric,threshold:state.threshold,selectedDate:state.date,onSelect:date=>chooseDate(date)});
  calendar.render(city,{metric:state.metric,month:state.month,threshold:state.threshold,selectedDate:state.date,onSelect:date=>chooseDate(date,true)});
  $('#trendTitle').textContent=`${city.name} · ${period}${state.metric==='temp'?'每日气温':'逐日降水'}`;
  $('#trendNote').textContent=state.metric==='temp'?'实线表示日均气温；主城市浅色带表示逐日最低至最高气温范围。':'实线表示日降水量；主城市同时显示浅色细柱，虚线表示可调的降水关注阈值。';
  $('#calendarTitle').textContent=`${city.name} · 全年${state.metric==='temp'?'气温':'降水'}日历`;
  $('#calendarNote').textContent=state.metric==='rain'?`绿色细边框标记降水量 ≥${state.threshold} mm 的日期。各城市共用固定色阶，缺测为灰色。`:'各城市共用固定气温色阶，缺测为灰色；选择日期后，可在下方比较四座城市。';
  const compared=WEATHER_DATA.cities.map(c=>({city:c,summary:summarize(filterDays(c.days,state.month))}));
  const key=state.metric==='temp'?'temp':'rain';compared.sort((a,b)=>(b.summary[key]??-Infinity)-(a.summary[key]??-Infinity));
  const max=Math.max(1,...compared.map(r=>Math.abs(r.summary[key]||0)));
  $('#comparisonTitle').textContent=`${period} · 四城${key==='temp'?'平均气温':'累计降水'}对比`;
  $('#comparison').innerHTML=compared.map(({city:c,summary:s})=>`<div class="comparison-row"><span>${c.name}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.abs(s[key]||0)/max*100}%;background:${colors[c.id]}"></div></div><strong>${fmt(s[key])}<small> ${key==='temp'?'°C':'mm'}</small></strong></div>`).join('');
  $('#dayTitle').textContent=`${state.date} · 四城明细`;
  $('#dayDetail').innerHTML=`<table><thead><tr><th>城市</th><th>均温 °C</th><th>降水 mm</th><th>湿度 %</th></tr></thead><tbody>${WEATHER_DATA.cities.map(c=>{const d=c.days.find(d=>d.date===state.date)||{};return `<tr class="${c.id===state.city?'highlight':''}"><td><i class="dot" style="background:${colors[c.id]}"></i>${c.name}</td><td>${fmt(d.temp)}</td><td>${fmt(d.rain,2)}</td><td>${fmt(d.humidity)}</td></tr>`;}).join('')}</tbody></table>`;
  $('#tableTitle').textContent=`${city.name} · ${period}逐日数据`;
  $('#rowCount').textContent=`${days.length} 条记录`;
  $('#dailyRows').innerHTML=days.map(d=>`<tr class="${d.date===state.date?'highlight':''}"><td>${d.date}</td>${['temp','min','max','rain','humidity','wind'].map(k=>`<td>${fmt(d[k],k==='rain'?2:1)}</td>`).join('')}</tr>`).join('');
  ['city','month','metric','threshold'].forEach(k=>$('#'+k).value=state[k]);$('#thresholdValue').value=`${state.threshold} mm`;
}
['city','month','metric'].forEach(k=>$('#'+k).onchange=e=>{state[k]=e.target.value;render();});
$('#threshold').oninput=e=>{state.threshold=Number(e.target.value);render();};
$('#reset').onclick=()=>{Object.assign(state,{city:'chengdu',month:'all',metric:'temp',threshold:10,date:'2024-07-15',compare:new Set(['chongqing','kunming'])});render();};
function download(content,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('#export').onclick=()=>{const c=getCity(state.city),rows=filterDays(c.days,state.month);download('\ufeff城市,日期,日均温C,最低温C,最高温C,降水mm,湿度percent,风速m_s\r\n'+rows.map(d=>[c.name,d.date,...['temp','min','max','rain','humidity','wind'].map(k=>d[k]??'')].join(',')).join('\r\n'),`${c.id}_2024_${state.month}.csv`,'text/csv;charset=utf-8');};
$('#exportSvg').onclick=()=>download(new XMLSerializer().serializeToString($('#trend svg')),`${state.city}_${state.metric}_${state.month}.svg`,'image/svg+xml;charset=utf-8');
render();
