/* 页面装配与组件分离；所有数值从随包数据计算。 */
'use strict';
const $=s=>document.querySelector(s);
const {CATEGORIES,aggregate,StackedBarChart}=WeatherStack;
const state={city:'chengdu',mode:'count',sort:'month',active:CATEGORIES.map(c=>c.id),month:7};
const chart=new StackedBarChart($('#chart'));
WEATHER_DATA.cities.forEach(c=>$('#city').add(new Option(c.name,c.id)));
function download(content,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function render(){
  const city=WEATHER_DATA.cities.find(c=>c.id===state.city), rows=aggregate(city.days);
  const wet=rows.reduce((s,r)=>s+r.light+r.medium+r.heavy,0),valid=rows.reduce((s,r)=>s+r.valid,0),total=rows.reduce((s,r)=>s+r.rain,0);
  const peak=[...rows].sort((a,b)=>b.rain-a.rain)[0];
  $('#stats').innerHTML=[['有效降水观测',valid,'天 / 366'],['降水日 ≥0.1 mm',wet,`天 · ${(wet/valid*100).toFixed(1)}%`],['全年累计降水',total.toFixed(1),'mm'],['降水量最高月份',`${peak.month}月`,`${peak.rain.toFixed(1)} mm`]].map(([k,v,u])=>`<article><p>${k}</p><strong>${v}</strong><span>${u}</span></article>`).join('');
  $('#legend').replaceChildren();
  CATEGORIES.forEach(c=>{const b=document.createElement('button');b.className='legend-btn';b.setAttribute('aria-pressed',state.active.includes(c.id));b.innerHTML=`<i style="background:${c.color}"></i>${c.name}`;b.onclick=()=>{state.active=state.active.includes(c.id)?state.active.filter(x=>x!==c.id):[...state.active,c.id];render();};$('#legend').append(b);});
  const sorted=state.sort==='wet'?[...rows].sort((a,b)=>(b.valid-b.dry)-(a.valid-a.dry)||a.month-b.month):rows;
  chart.render(sorted,{...state,selectedMonth:state.month,onSelect:m=>{state.month=m;render();}});
  const row=rows[state.month-1];
  $('#detailTitle').textContent=`${city.name} · ${state.month}月`;
  $('#detail').innerHTML=`<table><thead><tr><th>降水区间</th><th>天数</th><th>占有效日</th></tr></thead><tbody>${CATEGORIES.map(c=>`<tr><td><i class="dot" style="background:${c.color}"></i>${c.name}</td><td>${row[c.id]}</td><td>${row.valid?(row[c.id]/row.valid*100).toFixed(1):'—'}%</td></tr>`).join('')}</tbody></table><p class="note">有效 ${row.valid} 天；缺测 ${row.missing} 天；累计 ${row.rain.toFixed(1)} mm。</p>`;
  $('#insight').textContent=`${city.name}的 ${peak.month} 月累计降水量最高，为 ${peak.rain.toFixed(1)} mm，占全年 ${(peak.rain/total*100).toFixed(1)}%。降水日数与累计降水量反映不同维度，应结合阅读。`;
  ['city','mode','sort'].forEach(k=>$('#'+k).value=state[k]);
}
['city','mode','sort'].forEach(k=>$('#'+k).addEventListener('change',e=>{state[k]=e.target.value;render();}));
$('#reset').onclick=()=>{Object.assign(state,{city:'chengdu',mode:'count',sort:'month',active:CATEGORIES.map(c=>c.id),month:7});render();};
$('#svg').onclick=()=>download(chart.exportSVG(),`${state.city}_降水日结构.svg`,'image/svg+xml;charset=utf-8');
$('#csv').onclick=()=>{const city=WEATHER_DATA.cities.find(c=>c.id===state.city);const rows=aggregate(city.days);download('\ufeff城市,月份,少于0.1mm天数,0.1至小于10mm天数,10至小于25mm天数,大于等于25mm天数,有效天数,缺测天数,累计降水mm\r\n'+rows.map(r=>[city.name,r.month,r.dry,r.light,r.medium,r.heavy,r.valid,r.missing,r.rain.toFixed(2)].join(',')).join('\r\n'),`${city.id}_月度降水.csv`,'text/csv;charset=utf-8');};
render();
