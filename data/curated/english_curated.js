/* ---------- 英语 三件套精写（md2html_converter.py） ---------- */
/* 加载顺序：在 generated 之后加载，覆盖同名 key */
DATA.english['定语从句'] = {
  status:'已过审·三件套精写（试产样板）（2026-08-16）',
  tags:{ type:'语法精讲体', headers:["#", "语法点", "规则", "例句", "易错辨析", "考点预判"], source:'三件套精写' },
  body:[
  { lead:true,text:'<h3>定语从句：关系词的选择题</h3>' },
  { lead:false,text:'定语从句的考点几乎只有一个：<strong>选对关系词</strong>。三步决策：' },
  { lead:false,text:'<strong>第一步：看先行词是人是物</strong><br>- 人：who（作主语/宾语）、whom（作宾语）、whose（作定语"……的"）<br>- 物：which（作主语/宾语）、whose（作定语）<br>- 通用：that（人物皆可，限制性从句）' },
  { lead:false,text:'<strong>第二步：看关系词在从句中作什么成分</strong><br>- 作主语/宾语 → 用关系代词（who/whom/which/that）<br>- 作状语 → 用关系副词（where 地点 / when 时间 / why 原因）<br>- 判断口诀：<strong>从句缺主干成分用代词，从句主干完整用副词</strong><br>  - I will never forget the day ___ we spent together. → <strong>which/that</strong>（spent 缺宾语）<br>  - I will never forget the day ___ we first met. → <strong>when</strong>（从句主干完整，缺时间状语）' },
  { lead:false,text:'<strong>第三步：看限制性还是非限制性</strong><br>- 非限制性（有逗号）：<strong>不用 that</strong>，用 who/which/whose/as<br>- 例：Beijing, ___ is the capital of China, is an ancient city. → <strong>which</strong>' },
  { lead:false,text:'<strong>三个高频特殊规则</strong>：<br>1. <strong>只用 that 不用 which</strong>：先行词被最高级/序数词/the only/the very 修饰；先行词是 all/everything/nothing 等不定代词；先行词既有人又有物<br>2. <strong>介词 + which/whom</strong>：This is the house in which he lived. （= where he lived）<br>3. <strong>where 的抽象用法</strong>：case/point/situation/position/condition 等抽象名词后也用 where——"抽象地点"' },
  { lead:false,text:'<strong>易错警报</strong>：whose 的先行词可以是物！The house whose roof is red...（"房子的屋顶"，whose 表所属关系，不限于人）。' }
  ],
  cards:[
  ['1','关系代词','who/whom/which/that/whose','The man who is speaking is my teacher.','whom 只作宾语，口语常被 who 替代','高频'],
  ['2','关系副词','where/when/why','This is the school where I studied.','主干完整用副词——先判成分','高频'],
  ['3','代词 vs 副词','缺宾语用代词，完整用副词','the day (which) we spent / the day when we met','头号易混：spent 后缺宾语','最高频'],
  ['4','that 与 which','非限制性不用 that','Beijing, which is..., is...','逗号后不能用 that','高频'],
  ['5','只用 that','最高级/序数词/不定代词/人物兼有','This is the best film that I have seen.','the only/the very 修饰也只用 that','高频'],
  ['6','介词+which','in which = where','the house in which he lived','in which 可换 where，反之亦然','辨析'],
  ['7','抽象 where','case/point/situation 后用 where','a case where rules don\'t apply','"抽象地点"——不是真地点也用 where','辨析']
  ],
  quiz:[
  { type:'语法填空（考点 3，头号易混）', body:'I still remember the days ___ we spent together in the countryside.', ans:'<strong>答案：which/that</strong>。spent 后缺宾语——关系代词。' },
  { type:'语法填空（考点 3）', body:'I still remember the days ___ we worked together in the countryside.', ans:'<strong>答案：when</strong>。从句主干完整（we worked together）——关系副词，缺时间状语。' },
  { type:'选择（考点 5）', body:'This is the most interesting book ___ I have ever read.<br>A. which　B. <strong>that</strong>　C. who　D. whose', ans:'<strong>答案：B</strong>。先行词被最高级修饰——只用 that。' },
  { type:'非限制性（考点 4）', body:'Shanghai, ___ lies at the mouth of the Yangtze River, is a global city.<br>A. that　B. <strong>which</strong>　C. where　D. whose', ans:'<strong>答案：B</strong>。逗号＝非限制性定语从句，不用 that；从句缺主语（lies），用 which。' },
  { type:'抽象 where（考点 7）', body:'We are now in a situation ___ every decision matters.<br>A. which　B. that　C. <strong>where</strong>　D. whose', ans:'<strong>答案：C</strong>。situation 是"抽象地点"，用 where。' }
  ]
};
DATA.english['时态总览'] = {
  status:'已过审·三件套精写（试产样板）（2026-08-16）',
  tags:{ type:'语法精讲体', headers:["#", "语法点", "规则", "例句", "易错辨析", "考点预判"], source:'三件套精写' },
  body:[
  { lead:true,text:'<h3>英语时态：一根时间轴，八种时态</h3>' },
  { lead:false,text:'时态的底层逻辑就一句话：<strong>动作发生的时间 × 动作的状态（一般/进行/完成）</strong>。考场最有用的工具是时间轴：' },
  { lead:false,text:'```<br>过去完成 &lt;—— 一般过去 &lt;—— 现在完成 &lt;—— 一般现在/现在进行 &lt;—— 一般将来<br>```' },
  { lead:false,text:'<strong>八大时态速查</strong>：' },
  { lead:false,text:'| 时态 | 结构 | 核心用法 |<br>|---|---|---|<br>| 一般现在 | do/does | 习惯、客观真理；<strong>主将从现</strong> |<br>| 一般过去 | did | 过去某时发生的动作（有明确过去时间） |<br>| 一般将来 | will do / be going to do | 将来；be going to 表示计划或迹象 |<br>| 现在进行 | am/is/are doing | 正在发生；少数动词表将来（go/come/leave） |<br>| 过去进行 | was/were doing | 过去某时正在发生 |<br>| 现在完成 | have/has done | 过去动作对<strong>现在</strong>的影响或持续到现在 |<br>| 过去完成 | had done | 过去的过去 |<br>| 将来进行 | will be doing | 将来某时正在发生（了解即可） |' },
  { lead:false,text:'<strong>两个最高频易错点</strong>：' },
  { lead:false,text:'1. <strong>现在完成时 vs 一般过去时</strong>（上海卷语法填空的头号陷阱）：<br>   - 有明确过去时间（yesterday, in 2020）→ 一般过去<br>   - 强调对现在的影响 / since/for/so far/up to now → 现在完成<br>   - 例：He ___ (live) here since 2018. → has lived（since 是现在完成的时间标志）' },
  { lead:false,text:'2. <strong>主将从现</strong>：时间状语从句和条件状语从句中，主句用将来时，从句用<strong>一般现在时</strong>。<br>   - 例：I will tell him the news when he ___ (come) back. → <strong>comes</strong>（when 从句用一般现在，虽然表将来）' },
  { lead:false,text:'<strong>第三个隐藏考点</strong>：have gone to（去了未回）vs have been to（去过已回）。<br>   - He has gone to Beijing.（人在北京）→ He has been to Beijing twice.（去过两次）' }
  ],
  cards:[
  ['1','一般现在','习惯/真理/主将从现','Water boils at 100℃.','客观真理永远用一般现在','主将从现'],
  ['2','一般过去','明确过去时间','He left yesterday.','与现在完成辨析：有过去时间词用过去时','高频'],
  ['3','一般将来','will / be going to','It is going to rain.','be going to：计划/迹象；will：临时决定','辨析'],
  ['4','现在进行','正在发生','Look! He is running.','表将来的进行体（go/come/leave）','辨析'],
  ['5','现在完成','对现在的影响/持续','I have lived here since 2018.','since+点，for+段；与一般过去是头号易混','最高频'],
  ['6','过去完成','过去的过去','He had left when I arrived.','by+过去时间 是标志','高频'],
  ['7','have been to/gone to','去过已回/去了未回','She has gone to Beijing.','主语还在某地=gone to','辨析']
  ],
  quiz:[
  { type:'语法填空（考点 5，最高频）', body:'He ___ (live) in Shanghai since 2018, and he knows the city well.', ans:'<strong>答案：has lived</strong>。since 2018 是现在完成时标志，且强调"至今仍住"。' },
  { type:'辨析（考点 2/5）', body:'—Where is Tom? —He ___ to the library. He will be back soon.<br>A. has been　B. <strong>has gone</strong>　C. went　D. goes', ans:'<strong>答案：B</strong>。"人在图书馆（未回）"→ has gone to。' },
  { type:'主将从现（考点 1）', body:'I will call you as soon as I ___ (arrive) in Beijing.', ans:'<strong>答案：arrive</strong>。as soon as 引导时间状语从句，主将从现，从句用一般现在。' },
  { type:'过去完成（考点 6）', body:'By the time I got to the station, the train ___ (leave).', ans:'<strong>答案：had left</strong>。by the time＋过去时间→过去完成（过去的过去）。' },
  { type:'语篇语境（综合，真题风格）', body:'完形语境：When I ___ (wake) up this morning, it was raining heavily outside.', ans:'<strong>答案：woke</strong>。有明确过去时间（this morning 叙述过去事件），用一般过去。' }
  ]
};
DATA.english['阅读细节理解题策略'] = {
  status:'已过审·三件套精写（试产样板）（2026-08-16）',
  tags:{ type:'语法精讲体', headers:["#", "策略点", "规则", "示例", "易错辨析", "考点预判"], source:'三件套精写' },
  body:[
  { lead:true,text:'<h3>细节理解题：四步定位法</h3>' },
  { lead:false,text:'细节理解题占阅读理解分值的大头（约 40%）。它的解题策略是<strong>定位→比对→排除</strong>，核心能力是<strong>同义替换识别</strong>。' },
  { lead:false,text:'<strong>四步法</strong>：<br>1. <strong>读题干，划关键词</strong>：专有名词、数字、时间、核心名词（这些词在原文中几乎不换）<br>2. <strong>回原文定位</strong>：找到关键词所在句（答案就在附近 1~2 句）<br>3. <strong>比对选项</strong>：正确选项往往是原文的<strong>同义替换</strong>（换词不换义）<br>4. <strong>排除干扰项</strong>：用"四类陷阱"排除' },
  { lead:false,text:'<strong>四类干扰项（排雷清单）</strong>：<br>- <strong>偷换概念</strong>：把原文的 A 说成 B（原文"most students"→选项"all students"）<br>- <strong>张冠李戴</strong>：把甲做的事安在乙头上<br>- <strong>无中生有</strong>：原文没提的信息<br>- <strong>绝对化</strong>：原文"may/possible"→选项"must/always"' },
  { lead:false,text:'<strong>真题风格示范（人与社会语境）</strong>：<br><blockquote><br>语篇节选：The museum offers free guided tours for school groups on weekdays. Visitors are advised to book tickets online in advance, as on-site tickets are limited during holidays.<br></blockquote><br>&gt;<br><blockquote><br>题：According to the passage, school groups can ___.<br>A. book free tickets at any time　B. <strong>enjoy free guided tours on weekdays</strong>　C. visit the museum free on holidays　D. avoid booking in advance<br></blockquote><br>&gt;<br><blockquote><br>解析：题干关键词"school groups"→定位第一句→"free guided tours for school groups on weekdays"→B 是同义替换。A"any time"绝对化（原文限 weekdays）；C 张冠李戴（免费的是 guided tours，不是门票）；D 与原文"advised to book in advance"矛盾。<br></blockquote>' },
  { lead:false,text:'<strong>考场心法</strong>：细节题<strong>不要凭印象选</strong>——每个选项都要回原文比对一次；正确选项的特征是"换词不换义"，错误选项的特征是"看起来对，其实动过手脚"。' }
  ],
  cards:[
  ['1','划关键词','专名/数字/时间最稳','题干中"school groups"','关键词选"原文不变形"的词','高频'],
  ['2','定位','答案在关键词句±2句内','定位到第一句','定位句≠答案句——答案常在附近','高频'],
  ['3','同义替换','正确选项=换词不换义','free guided tours','同义替换是"识别"不是"寻找原句"','最高频'],
  ['4','偷换概念','范围/对象被改','most→all','程度词（most/some/all）是重灾区','高频'],
  ['5','无中生有','原文未提的信息','原文无"holidays free"','常识正确≠原文正确','高频'],
  ['6','绝对化','may→must 是警报','advised to→must','绝对词（must/always/never）慎选','高频']
  ],
  quiz:[
  { type:'同义替换（考点 3）', body:'语篇：The city plans to replace half of its buses with electric ones within five years.<br>题：What is the city\'s plan?（　）<br>A. To sell all its buses　B. <strong>To use electric buses for half of its fleet in five years</strong>　C. To build new roads　D. To stop using buses', ans:'<strong>答案：B</strong>。"replace half of its buses with electric ones"的同义替换；A"all"绝对化；C/D 无中生有。' },
  { type:'偷换概念（考点 4）', body:'语篇：Many students find online learning more flexible, but some still prefer face-to-face classes.<br>题：According to the passage, ___.<br>A. all students prefer online learning　B. no students like face-to-face classes　C. <strong>some students still prefer face-to-face classes</strong>　D. online learning is not flexible', ans:'<strong>答案：C</strong>。A"all"偷换"many"；B"no"绝对化；D 与原文"more flexible"矛盾。' },
  { type:'无中生有（考点 5）', body:'语篇：The library will extend its opening hours during the exam season.<br>题：What can we learn from the passage?（　）<br>A. The library will be free　B. The library will close earlier　C. <strong>The library will open longer during exams</strong>　D. The library will buy new books', ans:'<strong>答案：C</strong>。A/D 无中生有；B 与原文相反。' },
  { type:'定位练习（考点 1/2）', body:'语篇：Founded in 1920, the club has trained over 3,000 athletes, and 12 of them have won national championships.<br>题：How many athletes from the club have won national championships?（　）<br>A. 3,000　B. 1,920　C. <strong>12</strong>　D. 20', ans:'<strong>答案：C</strong>。数字定位：1920 是年份、3,000 是总人数、12 是冠军数——数字题必须逐一比对。' },
  { type:'策略综合（三层给分）', body:'给一段课外语篇，完成两道细节题，并说明每题使用的定位策略与排除理由。（8 分）<br><strong>评分标准</strong>：答案正确（每题 2 分）；策略说明完整——关键词/定位/比对/排除至少两步（每题 2 分）。', ans:'' }
  ]
};