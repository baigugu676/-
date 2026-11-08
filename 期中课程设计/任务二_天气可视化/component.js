/* 天气计算、折线图和日历组件。数据无效时保留缺测含义，不以 0 替代。 */
(function(global){
  'use strict';
  const colors={chengdu:'#258476',chongqing:'#d69551',kunming:'#618bd2',guiyang:'#9c78bc'};
  const isValid=(v)=>typeof v==='number'&&Number.isFinite(v);
  function filterDays(days,month){return month==='all'?days:days.filter(d=>Number(d.date.slice(5,7))===Number(month));}
  function summarize(days){
    const validTemp=days.filter(d=>isValid(d.temp)), validRain=days.filter(d=>isValid(d.rain)&&d.rain>=0);
    return {count:days.length,temp:validTemp.length?validTemp.reduce((s,d)=>s+d.temp,0)/validTemp.length:null,rain:validRain.length?validRain.reduce((s,d)=>s+d.rain,0):null,wet:validRain.filter(d=>d.rain>=0.1).length,max:days.some(d=>isValid(d.max))?Math.max(...days.filter(d=>isValid(d.max)).map(d=>d.max)):null,tempCount:validTemp.length,rainCount:validRain.length};
  }
  function svgEl(tag,attrs={},text){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n;}
  function colorFor(value,metric){
    if(!isValid(value))return '#e3e7eb';
    if(metric==='rain')return value<.1?'#edf3f0':value<2?'#d0e7dc':value<10?'#89c4ae':value<25?'#368e78':'#155b50';
    return value<5?'#7196b9':value<15?'#b7d4d9':value<22?'#e8e4bb':value<28?'#e8b47d':'#cc805e';
  }
  class TrendChart{
    constructor(container){this.container=container;}
    render(cities,{primary,month='all',metric='temp',selectedDate,onSelect=()=>{},threshold=10}={}){
      const series=cities.map(c=>({...c,rows:filterDays(c.days,month)}));
      const current=series.find(c=>c.id===primary)||series[0];
      const svg=svgEl('svg',{viewBox:'0 0 1000 315',role:'img','aria-label':`${metric==='temp'?'日均气温':'日降水量'}时间序列`});
      const L=50,T=24,W=924,H=229, dates=current?current.rows.map(d=>d.date):[];
      const values=series.flatMap(c=>c.rows.flatMap(d=>metric==='temp'&&c.id===primary?[d.temp,d.min,d.max]:[d[metric]])).filter(isValid);
      let min=metric==='rain'?0:Math.floor(Math.min(...values,0)/5)*5,max=metric==='rain'?Math.ceil(Math.max(5,...values,threshold)/10)*10:Math.ceil(Math.max(...values,5)/5)*5;
      if(max===min)max=min+5;
      const X=i=>L+i/Math.max(1,dates.length-1)*W,Y=v=>T+H-(v-min)/(max-min)*H;
      for(let i=0;i<=5;i++){const v=min+(max-min)*i/5,y=Y(v);svg.append(svgEl('line',{x1:L,x2:L+W,y1:y,y2:y,stroke:'#e9eef1'}));svg.append(svgEl('text',{x:L-10,y:y+4,'text-anchor':'end',fill:'#8794a2','font-size':11},v.toFixed(0)));}
      svg.append(svgEl('text',{x:L,y:12,fill:'#8794a2','font-size':10},metric==='temp'?'气温 / °C':'日降水 / mm'));
      const ticks=month==='all'?dates.map((d,i)=>d.endsWith('-01')?i:-1).filter(i=>i>=0):dates.map((d,i)=>(i%5===0||i===dates.length-1)?i:-1).filter(i=>i>=0);
      ticks.forEach(i=>svg.append(svgEl('text',{x:X(i),y:T+H+24,'text-anchor':'middle',fill:'#8794a2','font-size':11},month==='all'?`${Number(dates[i].slice(5,7))}月`:dates[i].slice(5))));
      if(current&&metric==='temp'){
        // 以连续有效片段绘制最高/最低气温带，避免跨缺测拼接。
        let group=[];const drawBand=()=>{if(!group.length)return;const path='M'+group.map(i=>`${X(i)},${Y(current.rows[i].max)}`).join(' L')+' L'+[...group].reverse().map(i=>`${X(i)},${Y(current.rows[i].min)}`).join(' L')+' Z';svg.append(svgEl('path',{d:path,fill:colors[primary],'fill-opacity':'.09'}));group=[];};
        current.rows.forEach((d,i)=>{if(isValid(d.min)&&isValid(d.max))group.push(i);else drawBand();});drawBand();
      }
      if(metric==='rain'){
        svg.append(svgEl('line',{x1:L,x2:L+W,y1:Y(threshold),y2:Y(threshold),stroke:'#ca9a59','stroke-dasharray':'5 5'}));
        svg.append(svgEl('text',{x:L+W,y:Y(threshold)-6,'text-anchor':'end',fill:'#b28850','font-size':10},`关注阈值 ${threshold} mm`));
      }
      series.forEach(c=>{
        let path='',connected=false;
        c.rows.forEach((d,i)=>{if(!isValid(d[metric])){connected=false;return;}path+=`${connected?' L':' M'}${X(i)},${Y(d[metric])}`;connected=true;});
        svg.append(svgEl('path',{d:path,fill:'none',stroke:colors[c.id],'stroke-width':c.id===primary?2.2:1.4,opacity:c.id===primary?1:.6,'data-series':c.id}));
        if(c.id===primary&&metric==='rain')c.rows.forEach((d,i)=>{if(isValid(d.rain))svg.append(svgEl('rect',{x:X(i)-1.5,y:Y(d.rain),width:3,height:Math.max(0,Y(0)-Y(d.rain)),fill:colors[c.id],opacity:.18}));});
      });
      if(current)current.rows.forEach((d,i)=>{
        if(!isValid(d[metric]))return;
        const point=svgEl('circle',{cx:X(i),cy:Y(d[metric]),r:d.date===selectedDate?5:3.5,fill:colors[current.id],opacity:d.date===selectedDate?1:0,tabindex:0,role:'button','aria-label':`${d.date}，${d[metric]} ${metric==='temp'?'摄氏度':'毫米'}`,'data-date':d.date});
        point.append(svgEl('title',{},point.getAttribute('aria-label')));
        point.addEventListener('mouseenter',()=>point.setAttribute('opacity','1'));
        point.addEventListener('mouseleave',()=>point.setAttribute('opacity',d.date===selectedDate?'1':'0'));
        point.addEventListener('focus',()=>point.setAttribute('opacity','1'));
        point.addEventListener('blur',()=>point.setAttribute('opacity',d.date===selectedDate?'1':'0'));
        point.addEventListener('click',()=>onSelect(d.date));
        point.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(d.date);}});svg.append(point);
      });
      if(!values.length)svg.append(svgEl('text',{x:500,y:150,'text-anchor':'middle',fill:'#8794a2'},'当前没有有效数据'));
      this.container.replaceChildren(svg);return svg;
    }
  }
  class WeatherCalendar{
    constructor(container){this.container=container;}
    render(city,{metric='rain',selectedDate,month='all',threshold=10,onSelect=()=>{}}={}){
      const svg=svgEl('svg',{viewBox:'0 0 1000 205',role:'img','aria-label':`${city.name}2024年天气日历，${metric==='rain'?'降水':'气温'}色阶`});
      const first=Date.UTC(2024,0,1),cell=15,gap=3,L=45,T=30,step=cell+gap;
      // 2024-01-01 是星期一，以周一为每周起点。
      ['一','二','三','四','五','六','日'].forEach((d,i)=>svg.append(svgEl('text',{x:27,y:T+i*step+11,'font-size':10,fill:'#8a98a5','text-anchor':'end'},d)));
      city.days.forEach(d=>{
        const offset=Math.round((Date.parse(d.date+'T00:00:00Z')-first)/86400000),col=Math.floor(offset/7),row=offset%7,m=Number(d.date.slice(5,7));
        if(d.date.endsWith('-01'))svg.append(svgEl('text',{x:L+col*step,y:18,fill:'#7a8c9b','font-size':10},`${m}月`));
        const rect=svgEl('rect',{x:L+col*step,y:T+row*step,width:cell,height:cell,rx:3,fill:colorFor(d[metric],metric),opacity:month==='all'||m===Number(month)?1:.3,stroke:d.date===selectedDate?'#d89444':metric==='rain'&&isValid(d.rain)&&d.rain>=threshold?'#346b5e':'none','stroke-width':d.date===selectedDate?2:1,tabindex:0,role:'button','data-date':d.date,'aria-label':`${d.date}，${isValid(d[metric])?d[metric]:'缺测'} ${metric==='rain'?'毫米':'摄氏度'}`});
        rect.append(svgEl('title',{},rect.getAttribute('aria-label')));
        rect.addEventListener('click',()=>onSelect(d.date));rect.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(d.date);}});svg.append(rect);
      });
      const labels=metric==='rain'?['<0.1','0.1–<2','2–<10','10–<25','≥25']:['<5','5–<15','15–<22','22–<28','≥28'];
      const examples=metric==='rain'?[0,1,5,15,30]:[0,10,18,25,30];
      labels.forEach((t,i)=>{svg.append(svgEl('rect',{x:L+i*150,y:178,width:12,height:12,rx:2,fill:colorFor(examples[i],metric)}));svg.append(svgEl('text',{x:L+18+i*150,y:188,fill:'#7a8c9b','font-size':11},t+(metric==='rain'?' mm':' °C')));});
      this.container.replaceChildren(svg);return svg;
    }
  }
  global.WeatherViz={colors,isValid,filterDays,summarize,svgEl,colorFor,TrendChart,WeatherCalendar};
})(window);
