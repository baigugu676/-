/* 可复用的原生 SVG 堆叠柱状图。无网络依赖。 */
(function (global) {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const CATEGORIES = [
    {id:'dry', name:'少于 0.1 mm', color:'#c8d5df'},
    {id:'light', name:'0.1–<10 mm', color:'#55b6a2'},
    {id:'medium', name:'10–<25 mm', color:'#447bd4'},
    {id:'heavy', name:'≥25 mm', color:'#8661bd'}
  ];
  function classify(rain) {
    if (!Number.isFinite(rain) || rain < 0) return null;
    return rain < 0.1 ? 'dry' : rain < 10 ? 'light' : rain < 25 ? 'medium' : 'heavy';
  }
  function aggregate(days) {
    const months = Array.from({length:12}, (_,i) => ({month:i+1,dry:0,light:0,medium:0,heavy:0,valid:0,missing:0,rain:0}));
    for (const d of days) {
      const m = Number(d.date.slice(5,7));
      if (m < 1 || m > 12) continue;
      const row = months[m-1], category = classify(d.rain);
      if (category === null) { row.missing++; continue; }
      row[category]++; row.valid++; row.rain += d.rain;
    }
    return months;
  }
  function el(tag, attrs={}, text) {
    const node=document.createElementNS(NS,tag);
    Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,v));
    if (text !== undefined) node.textContent=text;
    return node;
  }
  class StackedBarChart {
    constructor(container, options={}) { this.container=container; this.options=options; this.render([]); }
    render(rows, options={}) {
      this.options={...this.options,...options};
      const {mode='count',active=CATEGORIES.map(c=>c.id),selectedMonth=1,onSelect=()=>{}}=this.options;
      const svg=el('svg',{viewBox:'0 0 1000 390',role:'img','aria-label':`月度降水分组堆叠柱状图，${mode==='percent'?'百分比':'天数'}模式`});
      const left=58, top=30, width=915, height=292;
      const maximum=mode==='percent'?100:Math.max(5,...rows.map(r=>active.reduce((s,k)=>s+r[k],0)));
      const max=mode==='percent'?100:Math.ceil(maximum/5)*5;
      for(let i=0;i<=5;i++) {
        const y=top+height-height*i/5;
        svg.append(el('line',{x1:left,y1:y,x2:left+width,y2:y,stroke:'#e8edf1'}));
        svg.append(el('text',{x:left-12,y:y+4,'text-anchor':'end',fill:'#68798d','font-size':12},`${(max*i/5).toFixed(0)}${mode==='percent'?'%':''}`));
      }
      svg.append(el('text',{x:left,y:15,fill:'#68798d','font-size':12},mode==='percent'?'占当月有效观测日的比例':'有效天数 / 天'));
      const step=width/Math.max(1,rows.length), barWidth=Math.min(48,step*0.63);
      rows.forEach((r,i)=>{
        const x=left+step*(i+0.5), total=active.reduce((s,k)=>s+r[k],0);
        if(r.month===selectedMonth) svg.append(el('rect',{x:x-step*.44,y:top-6,width:step*.88,height:height+42,rx:9,fill:'#eef5f3'}));
        let stack=0;
        CATEGORIES.filter(c=>active.includes(c.id)).forEach(c=>{
          const value=mode==='percent'?(r.valid?r[c.id]/r.valid*100:0):r[c.id];
          const h=value/max*height;
          if(h>0) {
            const rect=el('rect',{x:x-barWidth/2,y:top+height-(stack+value)/max*height,width:barWidth,height:h,fill:c.color,tabindex:0,role:'button','aria-label':`${r.month}月，${c.name}，${r[c.id]}天，${r.valid?(r[c.id]/r.valid*100).toFixed(1):0}%`,'data-month':r.month,'data-category':c.id});
            rect.append(el('title',{},rect.getAttribute('aria-label')));
            rect.addEventListener('click',()=>onSelect(r.month));
            rect.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(r.month);}});
            svg.append(rect);
            if(h>24) svg.append(el('text',{x,y:top+height-(stack+value/2)/max*height+4,'text-anchor':'middle',fill:c.id==='dry'?'#33475b':'white','font-size':12,'pointer-events':'none'},mode==='percent'?`${value.toFixed(0)}%`:r[c.id]));
          }
          stack+=value;
        });
        const label=el('text',{x,y:top+height+25,'text-anchor':'middle',fill:'#53677c','font-size':13,tabindex:0,role:'button','aria-label':`查看${r.month}月详情`},`${r.month}月`);
        label.addEventListener('click',()=>onSelect(r.month));
        label.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(r.month);}});
        svg.append(label);
        if(active.length && r.valid) svg.append(el('text',{x,y:top+height-stack/max*height-8,'text-anchor':'middle',fill:'#42556a','font-size':12},mode==='percent'?`${(total/r.valid*100).toFixed(0)}%`:total));
      });
      if(!rows.length||!active.length||!rows.some(r=>r.valid)) svg.append(el('text',{x:510,y:165,'text-anchor':'middle',fill:'#64748b','font-size':18},!active.length?'请至少启用一个降水分组':'当前没有有效降水数据'));
      this.container.replaceChildren(svg);
      return svg;
    }
    exportSVG() { return new XMLSerializer().serializeToString(this.container.querySelector('svg')); }
    destroy() { this.container.replaceChildren(); }
  }
  global.WeatherStack={CATEGORIES,classify,aggregate,StackedBarChart};
})(window);
