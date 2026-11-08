/* 运行：npm install playwright && node 工具/browser_check.cjs
 * 可设 PLAYWRIGHT_MODULE 指向已安装的 Playwright 模块。 */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),shots=path.join(root,'验证截图');
fs.mkdirSync(shots,{recursive:true});
const results=[],errors=[];
async function check(name,fn){try{await fn();results.push({name,pass:true});console.log('PASS '+name);}catch(e){results.push({name,pass:false,error:e.stack});console.log('FAIL '+name+': '+e.message);}}
const url=(folder,file='index.html')=>pathToFileURL(path.join(root,folder,file)).href;
const task1='任务一_堆叠柱状图',task2='任务二_天气可视化';
(async()=>{
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1080},acceptDownloads:true});
  // 所有交付页面验证时屏蔽联网请求，确认离线可用。
  await context.route(/^https?:\/\//,route=>route.abort());
  const page=await context.newPage();page.setDefaultTimeout(7000);page.on('pageerror',e=>errors.push(e.message));
  for(const [folder,label] of [[task1,'task1'],[task2,'task2']]){
    await check(`${label} 浏览器内组件测试全部通过`,async()=>{await page.goto(url(folder,'tests.html'));const r=await page.evaluate(()=>window.TEST_RESULTS);assert(r&&r.length>10);assert.deepEqual(r.filter(x=>!x.pass),[]);results.push({name:`${label} 组件断言明细`,pass:true,cases:r});await page.screenshot({path:path.join(shots,label+'_tests.png'),fullPage:true});});
  }
  await page.goto(url(task1));
  await check('任务一 默认展示 12 个月',async()=>assert.equal(await page.locator('#chart rect[data-month]').evaluateAll(nodes=>new Set(nodes.map(n=>n.dataset.month)).size),12));
  await check('任务一 城市切换更新明细',async()=>{await page.selectOption('#city','kunming');assert.match(await page.locator('#detailTitle').textContent(),/昆明/);});
  await check('任务一 百分比与分组开关',async()=>{await page.selectOption('#mode','percent');assert.match(await page.locator('#chart svg').getAttribute('aria-label'),/百分比/);await page.locator('#legend button').first().click();assert.equal(await page.locator('#chart [data-category="dry"]').count(),0);});
  await check('任务一 全隐藏后空态提示',async()=>{while(await page.locator('#legend button[aria-pressed="true"]').count())await page.locator('#legend button[aria-pressed="true"]').first().click();assert.match(await page.locator('#chart').textContent(),/请至少启用/);});
  await page.click('#reset');
  await check('任务一 键盘选择月份更新明细',async()=>{await page.locator('#chart rect[data-month="2"]').first().focus();await page.keyboard.press('Enter');assert.match(await page.locator('#detailTitle').textContent(),/2月/);});
  await check('任务一 按降水日数排序为降序',async()=>{await page.selectOption('#sort','wet');const ordered=await page.locator('#chart text[aria-label^="查看"]').evaluateAll(nodes=>nodes.map(n=>parseInt(n.textContent)));const wet=await page.evaluate(()=>WeatherStack.aggregate(WEATHER_DATA.cities[0].days).map(r=>r.valid-r.dry));for(let i=1;i<ordered.length;i++)assert(wet[ordered[i-1]-1]>=wet[ordered[i]-1]);});
  await check('任务一 CSV 为 12 个月且带中文表头',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.click('#csv')]);const contents=fs.readFileSync(await download.path(),'utf8');assert.equal(contents.trim().split(/\r?\n/).length,13);assert.match(contents,/累计降水mm/);});
  await check('任务一 SVG 下载为有效图表',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.click('#svg')]);const contents=fs.readFileSync(await download.path(),'utf8');assert.match(contents,/<svg/);assert(!contents.includes('NaN'));});
  await page.click('#reset');await page.screenshot({path:path.join(shots,'task1_desktop.png'),fullPage:true});await page.locator('#chart').screenshot({path:path.join(shots,'task1_chart.png')});
  await page.goto(url(task2));
  await check('任务二 默认全年日历 366 天',async()=>assert.equal(await page.locator('#calendar rect[data-date]').count(),366));
  await check('任务二 日历点击联动月份、明细、表格',async()=>{await page.locator('#calendar [data-date="2024-02-29"]').click();assert.equal(await page.inputValue('#month'),'2');assert.match(await page.locator('#dayTitle').textContent(),/2024-02-29/);assert.equal(await page.locator('#dailyRows tr').count(),29);});
  await check('任务二 城市切换更新图表且保留所选日期',async()=>{await page.selectOption('#city','guiyang');assert.match(await page.locator('#trendTitle').textContent(),/贵阳/);assert.match(await page.locator('#dayTitle').textContent(),/2024-02-29/);});
  await check('任务二 切换到降水并调整阈值',async()=>{await page.selectOption('#metric','rain');await page.locator('#threshold').fill('23');assert.match(await page.locator('#trend').textContent(),/23 mm/);assert.match(await page.locator('#stats').textContent(),/≥23 mm/);});
  await check('任务二 关闭对比城市移除对应曲线',async()=>{const before=await page.locator('#trend path[data-series]').count();await page.locator('#compareControls input[value="kunming"]').uncheck();assert.equal(await page.locator('#trend path[data-series]').count(),before-1);});
  await check('任务二 曲线键盘交互更新日期明细',async()=>{await page.locator('#trend circle[data-date="2024-02-10"]').focus();await page.keyboard.press('Enter');assert.match(await page.locator('#dayTitle').textContent(),/2024-02-10/);});
  await check('任务二 导出恰好 29 天二月数据',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.click('#export')]);const contents=fs.readFileSync(await download.path(),'utf8');assert.equal(contents.trim().split(/\r?\n/).length,30);assert.match(contents,/2024-02-29/);assert(!contents.includes('2024-03-01'));});
  await check('任务二 SVG 下载包含降水阈值',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.click('#exportSvg')]);const contents=fs.readFileSync(await download.path(),'utf8');assert.match(contents,/23 mm/);assert(!contents.includes('NaN'));});
  await check('任务二 重置恢复全部默认设置',async()=>{await page.click('#reset');assert.equal(await page.inputValue('#month'),'all');assert.equal(await page.inputValue('#city'),'chengdu');assert.equal(await page.inputValue('#metric'),'temp');assert.equal(await page.inputValue('#threshold'),'10');assert.equal(await page.locator('#dailyRows tr').count(),366);});
  await page.screenshot({path:path.join(shots,'task2_desktop.png'),fullPage:true});await page.screenshot({path:path.join(shots,'task2_overview.png'),fullPage:false});await page.locator('#calendar').screenshot({path:path.join(shots,'task2_calendar.png')});
  await page.selectOption('#metric','rain');await page.selectOption('#month','7');await page.screenshot({path:path.join(shots,'task2_rain.png'),fullPage:true});
  await page.click('#reset');
  for(const [folder,label] of [[task1,'task1'],[task2,'task2']]){
    await check(`${label} 390px 移动端无页面横向溢出`,async()=>{await page.setViewportSize({width:390,height:844});await page.goto(url(folder));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));await page.screenshot({path:path.join(shots,label+'_mobile.png'),fullPage:true});});
  }
  await check('离线模式运行全程无 JavaScript 异常',async()=>assert.deepEqual(errors,[]));
  await browser.close();
  const report={checked_at:new Date().toISOString(),browser:'Playwright Chromium',offline_http_blocked:true,results,errors};
  fs.writeFileSync(path.join(root,'浏览器验证结果.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({passed:results.filter(r=>r.pass).length,total:results.length,failed:results.filter(r=>!r.pass)},null,2));
  if(results.some(r=>!r.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
