"""从真实数据和浏览器验证结果生成课程设计报告与两份需求文档。"""
import json
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'数据/weather_2024.json').read_text(encoding='utf-8'))
QUALITY=json.loads((ROOT/'数据/数据质量验证.json').read_text(encoding='utf-8'))
CHECKS=json.loads((ROOT/'浏览器验证结果.json').read_text(encoding='utf-8'))
STATS=QUALITY['statistics']
PAGES=[]
def page(title,blocks):PAGES.append((title,blocks))
def text(s):return ('text',s)
def sub(s):return ('sub',s)
def table(head,rows):return ('table',head,rows)
def image(name,caption,width=16):return ('image',name,caption,width)
def code(s):return ('code',s)

page('1  设计总览与任务对应',[
 text('本设计围绕“西南天气观察”完成课程要求的两个独立任务。任务一在树形图、扇形图、堆叠柱状图中选择堆叠柱状图；任务二按第二项选择天气相关数据，开展气温与降水可视化研究。两项任务分别提供可运行组件、实际交互页面与测试页面。'),
 table(['作业要求','实现与文件'],[
 ['任务一① 需求文档','本报告第 3 章；任务一_需求文档.md'],['任务一② 组件代码','任务一_堆叠柱状图/component.js、app.js'],['任务一③ 交互测试页面','任务一_堆叠柱状图/index.html、tests.html'],['任务一④ 合作分工','本报告第 6 章（角色与姓名待实际确认）'],['任务二① 需求文档','本报告第 7 章；任务二_需求文档.md'],['任务二② 组件代码','任务二_天气可视化/component.js、app.js'],['任务二③ 交互测试页面','任务二_天气可视化/index.html、tests.html'],['任务二④ 合作分工','本报告第 11 章（含工作量、交付与验收）']]),
 sub('设计目标'),text('使用真实、可追溯的数据回答三个问题：不同月份的降水日结构有什么差异？相同时间内四座城市的气温与降水有何差别？全年概览中值得继续查看的日期和月份在哪里？'),
 sub('整体技术路线'),text('NASA POWER 原始 JSON → Python 标准库整理与独立校验 → 标准 JSON / CSV / 离线 data.js → 原生 JavaScript 计算 → SVG 图表 → 点击、筛选和键盘联动 → CSV / SVG 导出。'),
 sub('交付范围'),text('数据覆盖 2024 年完整闰年、四座城市、六项逐日指标，共 1,464 条记录。页面直接读取随包数据，不调用在线接口，不依赖 CDN、地图密钥或构建工具。入口文件为“入口.html”。')])

page('2  数据来源、字段与统计口径',[
 sub('2.1 数据集的选择与意义'),text('成都、重庆、昆明、贵阳位于西南地区，适合在相同年份、同一数据产品下比较天气变化。本项目选择完整的 2024 年，避免把尚未结束的年份与完整年度混合比较。城市名表示所选坐标附近的网格数据，不代表整个行政区的平均值。'),
 table(['城市','纬度 / °N','经度 / °E','记录数'],[[c['name'],str(c['lat']),str(c['lon']),str(len(c['days']))] for c in DATA['cities']]),
 sub('2.2 来源与下载参数'),text('来源：NASA POWER Daily API。接口为 https://power.larc.nasa.gov/api/temporal/daily/point 。参数：community=AG，start=20240101，end=20241231，format=JSON，time-standard=LST；parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M。城市坐标见上表。原始响应中的 header.sources 为 MERRA2、POWER，API 版本为 v2.10.2。'),
 table(['前端字段','NASA 参数','含义与单位'],[['date','日期键 YYYYMMDD','转换为 YYYY-MM-DD'],['temp','T2M','2 米日均气温 / °C'],['max / min','T2M_MAX / T2M_MIN','2 米日最高 / 日最低气温 / °C'],['rain','PRECTOTCORR','校正降水量 / mm/day，按日累计分析'],['humidity','RH2M','2 米相对湿度 / %'],['wind','WS2M','2 米风速 / m/s']]),
 text('原始数据使用 LST（本地太阳时），不等同于北京时间的日界线。fill_value=-999 转换为 null；缺测不当作零降水或零气温。原始 JSON、请求 URL、SHA-256、字段说明与标准化数据全部随包保留。')])

page('2.3  数据质量与计算定义',[
 text(f"独立数据校验结果：{QUALITY['records']} 条逐日记录，六项数值字段共 8,784 个值，缺测值 {QUALITY['missing_values']} 个；异常 {len(QUALITY['issues'])} 项。校验脚本为工具/validate_data.py，详细结果见数据/数据质量验证.json。"),
 table(['检查项','结果与处理规则'],[['日期完整性','每城 366 条，2024-01-01 至 2024-12-31 连续且无重复；含 2 月 29 日'],['取值范围','最低温 ≤ 日均温 ≤ 最高温；降水与风速非负；湿度在 0–100%'],['文件一致性','四个原始文件的 SHA-256 与标准化数据中的记录一致'],['分组守恒','每个月四个分组的天数总和等于有效降水观测日数'],['缺测处理','下载层把 -999 置为 null；统计层排除缺测，分母按各指标有效日数确定'],['导出复核','标准 CSV 共 1,464 条记录；浏览器实测月份导出条数与筛选一致']]),
 sub('关键公式'),code('月均温 = Σ(当月有效日均温) / 有效气温日数\n月累计降水 = Σ(当月有效日降水)\n降水日数 = count(rain ≥ 0.1 mm)\n分组占比 = 分组有效日数 / 当月全部有效降水日数 × 100%\n时段最高温 = max(时段内有效日最高气温)'),
 text('计算保留原始数值精度，仅显示时四舍五入。年度平均气温直接对有效逐日值求均值，避免把不同长度月份的月均温等权平均。'),
 sub('四城全年汇总（由独立 Python 脚本计算）'),
 table(['城市','年均温 °C','累计降水 mm','降水日 ≥0.1 mm','最高气温 °C'],[[c['city'],f"{c['temp']:.2f}",f"{c['rain']:.2f}",str(c['wet']),f"{c['max']:.2f}"] for c in STATS]),
 text('这些结果描述选定网格和选定年份。单一年份不能代表多年气候常态；低阈值降水日统计对网格微量降水较敏感，不宜直接等同于气象站“下雨天”的体感判断。')])

page('3  任务一：堆叠柱状图需求文档',[
 sub('3.1 背景与目标用户'),text('只看月累计降水，无法区分“多次少量”与“少次较强”的组成。面向课程展示者和一般数据阅读者，设计月度降水日结构组件，同时支持看数量、看比例和查看明细。'),
 sub('3.2 可视化介绍'),text('横轴为月份，纵轴为天数或百分比；每个月由四类日降水区间自下而上堆叠。区间分别为 [0,0.1)、[0.1,10)、[10,25)、[25,+∞) mm。它们是本项目的分析分组，未作为官方预警等级。固定颜色为浅灰、浅绿、蓝、紫。'),
 table(['编号','功能需求','可观察的验收标准'],[['F1','选择四座城市','切换城市后统计卡片、柱体、明细和结论同步变化'],['F2','天数 / 百分比切换','天数用整数；百分比用有效日为分母，全年不受月份长度差异影响'],['F3','图例控制显隐','逐项开关分组；全部关闭出现提示；隐藏后百分比分母保持不变'],['F4','排序与月份选择','按自然月份或降水日数降序；点击或 Enter / 空格后更新月份明细'],['F5','明细与解释','显示四组天数、占比、有效日、缺测日与累计降水'],['F6','导出与重置','导出当前城市全年完整月度 CSV 和当前视图 SVG；重置回成都 7 月'],['F7','异常与空态','无有效数据时明确提示，不输出 NaN，不把 null 分到无雨组']]),
 sub('3.3 亮点与非功能需求'),text('组件与页面分离，可传入其他符合格式的逐日数据；数量和组成双视角；明确隐藏图例后的比例含义；保留缺测；原生 SVG 可编辑导出；键盘可触发选择；适配手机，图表在容器内横向滚动。无需联网、安装依赖或启动服务器即可演示。')])

page('4  任务一：组件结构与接口',[
 table(['文件','职责'],[['data.js','完整离线数据，挂载为 window.WEATHER_DATA'],['component.js','分类、月度聚合、可复用 StackedBarChart 组件'],['app.js','页面状态、城市和图例筛选、统计解释、导出与重置'],['index.html / style.css','可运行交互页面及样式'],['tests.html / tests.js','独立组件测试页，自动断言并保留可交互实例']]),
 sub('4.1 接口约定'),code("const rows = WeatherStack.aggregate(city.days);\nconst chart = new WeatherStack.StackedBarChart(container);\nchart.render(rows, {\n  mode: 'percent',                 // count 或 percent\n  active: ['dry', 'light', 'medium', 'heavy'],\n  selectedMonth: 7,\n  onSelect: month => updateDetail(month)\n});\nconst xml = chart.exportSVG();     // 当前视图字符串\nchart.destroy();                 // 清理 DOM"),
 text('输入逐日记录至少包含 date 和 rain。aggregate 返回 12 项，每项含 month、dry、light、medium、heavy、valid、missing、rain。组件不直接读取页面控件，不绑定某一座城市；onSelect 只返回所选月份。'),
 sub('4.2 算法与状态'),text('一次遍历逐日数据，依据降水区间累计到对应月份；render 按传入顺序绘制各月。每段矩形的高度等于数值 / 纵轴上限 × 绘图区高度，纵向位置由前面可见分组的累计值决定。百分比以全部有效降水日为分母，隐藏分组只移除绘制，不改变统计。'),
 text('页面状态包含 city、mode、sort、active、month。城市或排序变化不把所选月份错误地解释为“第几个柱子”，而是以月份数字定位明细。柱段提供 title、aria-label 和键盘事件。'),
 sub('4.3 性能与边界'),text('聚合复杂度 O(n)，SVG 图形数上限为 12×4 个柱段，适合当前规模。空数组、空分组与无有效降水有明确提示。导出 CSV 始终包含全年全部四组，避免把图例隐藏误当作原始数据删除。')])

page('4.4  任务一实际运行效果',[
 image('task1_desktop.png','图 1  任务一默认状态：成都全年降水日结构、7 月明细与自动统计说明。',15.7),
 text('使用方法：切换城市 → 切换“百分比” → 点击图例隐藏分组 → 按降水日数排序 → 点击目标月份查看占比 → 导出 CSV 或 SVG。操作页面与自动测试页面分别独立提供。')])

chengdu=STATS[0];july=chengdu['months'][6]
page('4.5  任务一研究结果与图表解读',[
 sub('成都月度降水分组（天）'),
 table(['月','<0.1','0.1–<10','10–<25','≥25','累计 mm'],[[str(m['month']),*map(str,m['bins']),f"{m['rain']:.2f}"] for m in chengdu['months']]),
 text(f"发现一：成都 7 月累计降水 {july['rain']:.2f} mm，为全年最高，占全年 {july['rain']/chengdu['rain']*100:.1f}%。其 31 天中四组分别为 1、15、12、3 天；≥10 mm 的日期共 15 天，占当月有效日的 {15/31*100:.1f}%。"),
 text('发现二：6 月与 7 月的降水日数均为 30 天，但累计降水分别为 101.51 mm 与 378.95 mm，后者约为前者的 3.73 倍。天数相同不意味着降水量相近，堆叠组成与累计量明细需要一起阅读。'),
 text('发现三：8 月与 1 月的降水日数均为 19 天，但 8 月存在 10–<25 mm 与 ≥25 mm 的日期，累计量也明显不同。仅按降水日数排序不能替代按降水量比较。'),
 text('图表编码的限制：堆叠图最底层共享基线，其余分组的起点不同；比较单一分组时可隐藏其他分组，或读取明细表，不单靠视觉估计。所有研究结论均限定为本项目的历史网格样本。')])

case1=next(r['cases'] for r in CHECKS['results'] if r['name']=='task1 组件断言明细')
page('5  任务一：交互测试与验收',[
 text(f"测试入口：任务一_堆叠柱状图/tests.html。真实浏览器执行 {len(case1)} 条断言，全部通过。可点击“重新运行全部测试”，下方保留实际图表供人工交互。"),
 table(['序号','测试内容','结果'],[[str(i),r['name'],'通过' if r['pass'] else '失败'] for i,r in enumerate(case1,1)]),
 sub('页面流程验收'),text('另用浏览器验证城市切换、百分比与图例、全隐藏空态、键盘选月、按降水日数排序、CSV 表头与 12 个月数据、SVG 下载和移动端无页面溢出。下载测试读取真实下载文件内容，不仅检查按钮是否可点击。')])

page('6  任务一：合作分工详细安排',[
 text('本表为可执行的分工方案。A、B、C 是角色占位，实际成员姓名、真实工作量和贡献须按实际情况补全，不作为已发生多人合作的记录；独立完成时可由同一人承担全部角色。'),
 table(['工作包 / 建议日期','负责人','详细任务与交付','估时 / 验收'],[['需求与口径\n11/04–11/05','A（姓名待填）','整理任务、定义四个区间和百分比分母；交付需求说明与验收清单','2 h；B 复核每个区间边界'],['数据与校验\n11/04–11/06','A 主责、C 复核','保留原始响应，生成 JSON/CSV/data.js；完成缺测、日期、哈希校验','3 h；四城 1,464 条完整可追溯'],['SVG 组件\n11/06–11/08','B（姓名待填）','实现聚合、布局、显隐与选择事件、空态及导出接口','5 h；18 条组件断言通过'],['页面装配\n11/08–11/09','B 主责、A 支持','筛选器、明细、统计卡片、重置、移动端样式与数据说明','3 h；筛选和导出一致'],['测试与文档\n11/09–11/12','C（姓名待填）','测试页、真实点击/键盘/下载验证；整理截图和结果说明','3 h；结果 JSON 与截图可复查'],['集成与展示\n11/13–11/16','A/B/C 联合','跨浏览器人工复核、角色贡献确认、报告校对、5 分钟演示','2 h；11/17 前完成提交']]),
 sub('协作接口与交接'),text('A 向 B 提供 date/rain 字段和缺测定义；B 向 C 提供 render/onSelect/exportSVG 接口与默认配置；C 按需求编号反馈问题和复现步骤。接口字段或统计口径调整时，先同步需求文档，再更新组件、测试与报告。'),
 sub('贡献确认栏（据实填写）'),text('成员 A：________  实际完成内容：________________________\n成员 B：________  实际完成内容：________________________\n成员 C：________  实际完成内容：________________________')])

page('7  任务二：天气可视化需求文档',[
 sub('7.1 选题与背景'),text('选择题目第二项中的“天气等相关数据”，研究四座西南城市在 2024 年的气温和降水差异。面向需要从全年趋势定位到月份、再查看某一天的课程阅读场景，强调概览与细节相互联动。'),
 sub('7.2 可视化介绍与亮点'),text('采用多城市时间序列、全年日历热力图、四城排序条形比较和逐日明细表。曲线回答“何时变化”，日历回答“在全年哪里出现集中变化”，比较条形图回答“相同时段哪座城市更高”，日期表展示准确数值。主城市气温带显示每日最低至最高范围，不表示置信区间。'),
 table(['编号','功能需求','验收标准'],[['W1','主城市、月份与指标筛选','四城可选；全年/1–12 月；温度与降水切换；图表、卡片、表格同步'],['W2','城市对比曲线','主城市始终显示；其他城市开关只影响曲线，不删除四城统计'],['W3','日历联动','一格一天，含闰日；点击日期切换月份并更新日期明细'],['W4','可调降水阈值','1–50 mm；改变阈值线、关注日数及降水日历边框'],['W5','精确读数与键盘','主城市曲线点、日历色块支持点击/Enter/空格；明细显示四城同日值'],['W6','导出与重置','CSV 只含当前主城市、当前时段的全部字段；SVG 导出当前趋势图'],['W7','日历固定色阶与缺测','城市切换不改变分级边界；缺测为灰色，不作为零处理']]),
 sub('7.3 非功能要求'),text('离线运行；页面与组件分离；SVG 保持缩放；手机图表在容器内滚动，控件自动换行；真实来源、时间标准、单位和缺测口径始终可查。输出描述性研究结果，不根据一年数据做长期趋势或因果推断。')])

page('8  任务二：架构与交互实现',[
 table(['模块','作用'],[['filterDays / summarize','按月筛选；分别计算有效均温、累计降水、最高温与降水日数'],['TrendChart','多城市曲线、主城市温度带、降水细柱、阈值线与日期点交互'],['WeatherCalendar','366 个日历色块；固定色阶、阈值框与选中日期框'],['app.js','维护状态、统一渲染卡片/曲线/日历/对比/明细/数据表'],['tests.html / tests.js','21 条可重复运行的组件测试及实时交互实例']]),
 sub('8.1 复用接口'),code("const options = {\n  primary: 'chengdu', month: '7', metric: 'rain',\n  threshold: 10, selectedDate: '2024-07-15',\n  onSelect: date => updateDate(date)\n};\nnew WeatherViz.TrendChart(trendNode).render(cities, options);\nnew WeatherViz.WeatherCalendar(calendarNode)\n  .render(city, options);\nconst summary = WeatherViz.summarize(\n  WeatherViz.filterDays(city.days, '7'));"),
 sub('8.2 联动规则'),text('城市切换保留月份与合法的所选日期；手动月份切换时，若原日期不在该月则选择该月首日。日历点击把月份切换到点击日期所属月。曲线点只更新日期明细。主要城市与其他曲线城市使用独立状态，避免关闭开关后主城市消失。'),
 sub('8.3 图形计算与缺测'),text('日期以 UTC 毫秒差计算布局，避免浏览器本地时区影响日历列位置；2024 年 1 月 1 日为周一。缺测点断开折线，温度带按连续有效片段绘制。统计不足时显示“—”；无有效曲线数据时显示空态。降水单位在逐日图为 mm，在时段对比中对有效日量求和。')])

page('8.4  任务二实际运行效果',[
 image('task2_overview.png','图 2  任务二桌面概览：筛选、统计卡片、多城市气温曲线与主城市日温度范围。',16),
 image('task2_calendar.png','图 3  全年日历：固定色阶、按周布局、每天均可点击选择。',16),
 text('主城市默认成都，时间默认全年，默认显示成都、重庆、昆明三条曲线。页面下半部提供四城同周期排序、所选日期明细和完整的可滚动逐日数据表。')])

page('9  任务二：研究结果与解释',[
 table(['城市','最暖月 / 月均温','最冷月 / 月均温','降水量最高月'],[[c['city'],f"{max(c['months'],key=lambda m:m['temp'])['month']} 月 / {max(c['months'],key=lambda m:m['temp'])['temp']:.2f} °C",f"{min(c['months'],key=lambda m:m['temp'])['month']} 月 / {min(c['months'],key=lambda m:m['temp'])['temp']:.2f} °C",f"{max(c['months'],key=lambda m:m['rain'])['month']} 月 / {max(c['months'],key=lambda m:m['rain'])['rain']:.2f} mm"] for c in STATS]),
 sub('9.1 温度差异'),text('在本年度网格样本中，重庆年均温 19.41 °C，高于成都 17.96 °C、昆明 16.15 °C 与贵阳 15.57 °C。重庆最高日最高气温为 40.54 °C；昆明对应值为 30.89 °C。切换到 8 月，可见重庆月均温为 30.47 °C，成都为 28.57 °C。'),
 text('昆明最暖月与最冷月的月均温差约 13.41 °C，成都约 22.61 °C。本年度样本显示二者的月均温起伏幅度不同；不能仅据此推断多年气候趋势，也不将城市之间的差异解释为某一个原因。'),
 sub('9.2 降水分布'),text('贵阳全年累计降水 1,443.85 mm，为四城最高；昆明 879.86 mm，为四城最低。贵阳 6 月累计 395.58 mm，约占全年 27.4%。成都降水量最高月为 7 月，其余三城在此样本中均为 6 月。'),
 sub('9.3 可复现的研究操作'),text('把指标切到“日降水量”，月份切到 6 月，再选择贵阳为主城市，可结合阈值线与日历查看集中降水日期。随后切到成都 7 月，对照任务一的堆叠日结构和两页的累计量，交叉验证同一数据的统计一致性。'),
 sub('9.4 研究边界'),text('不把网格数据称为气象站实测；LST 日界线与北京时间不同；研究年份仅为 2024；未做显著性检验或天气预测。关注阈值为探索工具，与预警发布阈值无对应关系。')])

case2=next(r['cases'] for r in CHECKS['results'] if r['name']=='task2 组件断言明细')
page('10  任务二：交互测试与验收',[
 text(f"测试入口：任务二_天气可视化/tests.html。真实浏览器执行 {len(case2)} 条组件断言，全部通过。"),
 table(['序号','测试内容','结果'],[[str(i),r['name'],'通过' if r['pass'] else '失败'] for i,r in enumerate(case2,1)]),
 text('额外页面流程：选择 2 月 29 日，月份应为 2 月、数据表应为 29 行；切换贵阳后保留闰日；设阈值为 23 mm，曲线与卡片同步；关闭对比曲线；键盘选日；读取实际下载文件；重置应恢复 366 行。')])

page('11  任务二：合作分工详细安排',[
 text('以下为待真实成员确认的角色分工方案，与任务一沿用 A/B/C 角色。若独立完成，应将负责人据实改为本人，保留按阶段拆解的工作内容，不虚构其他成员的贡献。'),
 table(['工作包 / 建议日期','负责人','交付与协作内容','估时 / 验收'],[['研究问题与需求\n11/04–11/05','A 主责、C 复核','确定四城同年比较、气温/降水指标、LST 口径；需求 W1–W7','2 h；指标无歧义'],['数据整理\n11/05–11/06','A（姓名待填）','统一六字段；检查闰年、范围、缺测与单位；交付原始及整理数据','3 h；独立数据脚本通过'],['曲线与日历\n11/07–11/10','B（姓名待填）','时间序列、气温带、阈值线、固定色阶、日期选择事件','6 h；21 条组件断言通过'],['多视图联动\n11/10–11/11','B 主责、A 支持','城市/月/指标/阈值统一状态；同日明细、对比条形与 CSV/SVG 导出','4 h；闰日流程与导出一致'],['研究结论与测试\n11/11–11/14','C（姓名待填）','独立复核四城统计；浏览器流程、移动端与离线验证；整理截图','4 h；结论可从数据复算'],['报告与演示\n11/14–11/16','C 主责，全员复核','整合需求、代码接口、限制、分工与展示脚本；确认真实贡献','2 h；11/17 前完成装订和打包']]),
 sub('交接与问题处理'),text('数据负责人对字段、单位与时间标准负责；组件负责人对 render 接口和联动行为负责；测试负责人根据 W1–W7 提供“操作步骤—预期—实际—证据”。重大口径变化必须同时修正文档、数据解释、测试和结论，避免多个视图出现不同计算规则。'),
 text('成员 A：________  真实贡献：________________________\n成员 B：________  真实贡献：________________________\n成员 C：________  真实贡献：________________________')])

page('12  运行、复核与环境说明',[
 sub('12.1 普通查看与演示'),text('解压整个压缩包，双击“期中课程设计/入口.html”。通过入口分别打开两个任务与测试页。也可直接双击对应目录的 index.html 或 tests.html。文件夹内 data.js、component.js、app.js 和 style.css 需保留在同一目录。普通运行不需要 Python、Node.js 或互联网。'),
 sub('12.2 可选本地服务'),code('cd 期中课程设计\npython -m http.server 8000\n# 浏览器访问 http://localhost:8000/入口.html\n# Linux 的命令可能为 python3'),
 sub('12.3 重新整理与校验数据'),code('python 工具/fetch_data.py           # 优先复用 raw 缓存\npython 工具/fetch_data.py --refresh # 联网重新下载\npython 工具/validate_data.py'),
 text('重新下载会使上游订正数据进入项目，数字、截图与报告需同步复核。默认重用原始快照，便于复现本次结果。页面数据是标准 JSON 的脚本封装，从 file:// 打开时无需 fetch 请求。'),
 sub('12.4 自动浏览器复核（可选开发工具）'),code('npm install --no-save playwright\nnpx playwright install chromium\nnode 工具/browser_check.cjs'),
 text('本次实测环境：Windows Chromium / Playwright；1440×1080 桌面、390×844 手机视口；通过 file:// 打开，并拦截全部 HTTP/HTTPS 请求确认离线。两项组件共 39 条断言通过；浏览器验证结果共 24 条成功记录，其中 2 条为组件明细记录、2 条为组件页汇总，其余 20 条为流程、布局与异常检查。'),
 text('浏览器验证结果.json、数据/数据质量验证.json 与验证截图/ 提供验证证据。报告由工具/build_report.py 基于这些真实结果生成；重生成报告需安装 python-docx。')])

page('13  展示脚本、提交检查与参考资料',[
 sub('13.1 建议展示流程（约 5 分钟）'),
 table(['时间','演示动作与说明'],[['0:00–0:40','介绍数据来源、四城、完整闰年和两个任务的选项'],['0:40–1:50','任务一切百分比、开关分组、选中 7 月，解释 15 个 ≥10 mm 日'],['1:50–3:20','任务二选择城市和月份，比较温度；切降水，调整关注阈值，点日历'],['3:20–4:10','展示四城明细、逐日表；导出 CSV/SVG，说明离线运行'],['4:10–5:00','打开测试页、展示验证结果、说明真实分工与数据适用边界']]),
 sub('13.2 交付检查'),text('□ 按真实信息填写学号、班级、专业；封面姓名按原题要求手写。\n□ 据实补齐成员姓名与贡献；独立完成则改为本人负责。\n□ 解压后打开入口、两个任务与两个测试页。\n□ A4 双面打印、简单装订报告。\n□ 电子材料按“期中+学号+姓名”重命名后打包，2026 年 11 月 17 日前提交。'),
 sub('13.3 参考资料与可追溯文件'),
 text('[1] NASA POWER. Daily API Documentation. https://power.larc.nasa.gov/docs/services/api/temporal/daily/ （用于核对接口、逐日数据和请求参数；访问日期 2026-11-04）。'),
 text('[2] NASA POWER. API Tutorial. https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/ （参数与 Python 请求示例；访问日期 2026-11-04）。'),
 text('[3] 本项目四个原始 API 响应，见数据/raw/*_2024.json。完整请求 URL、API 版本、源产品和 SHA-256 保留在数据/weather_2024.json；标准 CSV 可用于外部复核。'),
 text('使用辅助编程工具形成的页面、统计与文字应由提交者理解、复核，并依课程要求如实说明工具使用情况。报告中的分工表是安排模板，未宣称存在未提供姓名的真实团队。')])

def set_font(run,name='宋体',size=10.5,bold=False,color=None):
    run.font.name=name;run.font.size=Pt(size);run.bold=bold
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),name)
    if color:run.font.color.rgb=RGBColor.from_string(color)

def render_table(doc,headers,rows):
    t=doc.add_table(rows=1,cols=len(headers));t.style='Table Grid'
    widths=None
    if len(headers)==2:widths=[4,12]
    if headers[0]=='序号':widths=[1.1,13.2,1.7]
    elif headers[0]=='编号':widths=[1.2,4.5,10.3]
    elif headers[0].startswith('工作包'):widths=[2.7,2.4,7.7,3.2]
    elif headers[0]=='前端字段':widths=[2.5,4.7,8.8]
    for cell,label in zip(t.rows[0].cells,headers):cell.text=label
    header=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');header.append(repeat)
    for values in rows:
        cells=t.add_row().cells
        for cell,value in zip(cells,values):cell.text=str(value)
    for i,row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for ci,cell in enumerate(row.cells):
            if widths:cell.width=Cm(widths[ci])
            if i==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAF2EF');cell._tc.get_or_add_tcPr().append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3);p.paragraph_format.line_spacing=1.08
                for run in p.runs:set_font(run,size=9,bold=i==0,color='24473F' if i==0 else None)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)

def main():
    doc=Document();s=doc.sections[0];s.page_width=Cm(21);s.page_height=Cm(29.7);s.top_margin=Cm(1.9);s.bottom_margin=Cm(1.8);s.left_margin=Cm(2.4);s.right_margin=Cm(2);s.gutter=Cm(.2)
    settings=doc.settings.element;settings.append(OxmlElement('w:mirrorMargins'));s.different_first_page_header_footer=True
    normal=doc.styles['Normal'];normal.font.name='宋体';normal.font.size=Pt(10.5);normal.element.rPr.rFonts.set(qn('w:eastAsia'),'宋体');normal.paragraph_format.line_spacing=1.28;normal.paragraph_format.space_after=Pt(7)
    for name,size in [('Heading 1',17),('Heading 2',12)]:
        style=doc.styles[name];style.font.name='微软雅黑';style.font.size=Pt(size);style.font.color.rgb=RGBColor.from_string('205D53');style.element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑')
    p=s.header.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;set_font(p.add_run('大数据可视化期中课程设计  |  SCAI008312'),size=8,color='74857C')
    p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;set_font(p.add_run('—  '),size=9)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field);set_font(p.add_run('  —'),size=9)
    p=doc.add_paragraph();p.paragraph_format.space_before=Pt(20);p.alignment=1;set_font(p.add_run('2026—2027 第 1 学期'),name='微软雅黑',size=15)
    for title in ['大数据可视化','期中课程设计报告']:
        p=doc.add_paragraph();p.alignment=1;set_font(p.add_run(title),name='微软雅黑',size=25,bold=True,color='205D53')
    p=doc.add_paragraph();p.alignment=1;set_font(p.add_run('西南天气观察\n月度降水日结构组件与四城天气研究'),name='微软雅黑',size=15)
    p=doc.add_paragraph();p.paragraph_format.space_before=Pt(20)
    for label in ['学号：____________________','姓名（手写）：____________','班级：____________________','专业：____________________']:
        p=doc.add_paragraph(label);p.paragraph_format.space_after=Pt(14)
    doc.add_paragraph('课程代码：SCAI008312    提交截止日期：2026 年 11 月 17 日')
    render_table(doc,['展示（20%）','文档（20%）','设计/代码（60%）','总分（100%）'],[['','','','']])
    doc.add_paragraph('批阅人签字及批阅日期：________________________________')
    p=doc.add_paragraph('打印与提交：姓名按原题要求手写；其他文字电脑打字；A4 双面打印、简单装订；全部电子材料按“期中+学号+姓名”打包。');set_font(p.runs[0],size=9,color='647267')
    markdown=['# 大数据可视化期中课程设计报告','\n任务一选堆叠柱状图；任务二选择第二项中的天气数据可视化。\n']
    for title,blocks in PAGES:
        doc.add_page_break();doc.add_heading(title,level=1);markdown.append('\n## '+title+'\n')
        for b in blocks:
            kind=b[0]
            if kind=='text':doc.add_paragraph(b[1]);markdown.append(b[1]+'\n')
            elif kind=='sub':doc.add_heading(b[1],level=2);markdown.append('\n### '+b[1]+'\n')
            elif kind=='table':
                render_table(doc,b[1],b[2]);markdown.append('| '+' | '.join(b[1])+' |\n| '+' | '.join('---' for _ in b[1])+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('\n','<br>') for v in row)+' |' for row in b[2])+'\n')
            elif kind=='code':
                p=doc.add_paragraph();p.paragraph_format.line_spacing=1.08;p.paragraph_format.left_indent=Cm(.3)
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F3F6F5');p._p.get_or_add_pPr().append(shade)
                set_font(p.add_run(b[1]),name='Consolas',size=9);markdown.append('```text\n'+b[1]+'\n```\n')
            elif kind=='image':
                file=ROOT/'验证截图'/b[1]
                if file.exists():doc.add_picture(str(file),width=Cm(b[3]))
                p=doc.add_paragraph(b[2]);p.alignment=1
                for run in p.runs:set_font(run,size=9,color='6D7C73')
                markdown.append(f'![{b[2]}](验证截图/{b[1]})\n')
    doc.core_properties.title='西南天气观察：大数据可视化期中课程设计报告';doc.core_properties.author='个人信息待据实填写';doc.core_properties.subject='任务一：堆叠柱状图；任务二：第二项（天气数据）'
    doc.save(ROOT/'期中课程设计报告.docx')
    (ROOT/'期中课程设计报告.md').write_text('\n'.join(markdown),encoding='utf-8')
    for filename,prefixes in [('任务一_需求文档.md',('3  ','4  ','4.4','4.5','5  ','6  ')),('任务二_需求文档.md',('7  ','8  ','8.4','9  ','10  ','11  '))]:
        chosen=[(title,blocks) for title,blocks in PAGES if title.startswith(prefixes)]
        lines=['# '+filename[:-3],'\n公共数据源、字段和计算口径见《期中课程设计报告.md》第 2 章。\n']
        for title,blocks in chosen:
            lines.append('\n## '+title+'\n')
            for b in blocks:
                if b[0]=='text':lines.append(b[1]+'\n')
                elif b[0]=='sub':lines.append('\n### '+b[1]+'\n')
                elif b[0]=='code':lines.append('```javascript\n'+b[1]+'\n```\n')
                elif b[0]=='table':lines.append('| '+' | '.join(b[1])+' |\n| '+' | '.join('---' for _ in b[1])+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('\n','<br>') for v in row)+' |' for row in b[2])+'\n')
                elif b[0]=='image':lines.append(f'![{b[2]}](验证截图/{b[1]})\n')
        (ROOT/filename).write_text('\n'.join(lines),encoding='utf-8')
    print('报告生成完成：封面 +',len(PAGES),'个分页章节；两份需求文档已写入。')
if __name__=='__main__':main()
