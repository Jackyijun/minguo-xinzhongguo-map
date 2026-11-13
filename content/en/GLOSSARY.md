# 英文版译名与体例（GLOSSARY）

中文是源文本，英文按同一套键写在本目录的 `*.json` 里（结构见 `src/i18n.py` 开头）。本文件记录译名体例，新增或修改英文时照此执行；同一个名称在全图各处写法一致（地图注记、悬停说明、索引、对照表、年表、节点说明）。体例沿用《宋辽夏金元形势图》的 GLOSSARY，下面只写本图特有或改动的部分。

## 一、总原则

1. **说真话**：英文只翻译中文已有的内容，不增不减；中文本身有误时先改中文，再改英文（并运行 `python tools/i18n.py lock`）。
2. **立场与用语随中文**：中文采用统编历史教材口径（见 `content/AGENTS.md`），英文照中华人民共和国官方英文的通行译法，不改用西方史学的说法（见第三节）。
3. **地名用当时当地的名称**：中国地名用汉语拼音转写图上的中文名（北平 Beiping、迪化 Dihua、新京 Xinjing）；中国以外用当时通行的英文写法（Rangoon、Batavia、Tiflis、Urga），今名放在「今地」一栏（Yangon, Myanmar）。中文本身就是外文名译音的，照原文还原，不把中文译音再转回拼音（海参崴 Vladivostok、仰光 Rangoon、汉城 Seoul）。
4. **今地/今名**写「地名, 省或国家」（Xi'an, Shaanxi；Yangon, Myanmar），用今天的通行英文名和行政区。
5. **地图注记不加中文没有的消歧义**；「今地」一栏可以括注英文读者更熟的别名（Changjin Lake (Chosin Reservoir)、Heilong River (Amur)、Xingkai Lake (Khanka)）。中文同音不同字、英文无法区分的战役，括注省名（Battle of Xuzhou (Sichuan) 对应叙州之战）；同地不同年的两场战役，英文给较早的一场括注年份（Battle of Xuzhou (1913) / Battle of Xuzhou；Battle of Nankou (1926) / Battle of Nankou）。
6. 英文界面里，地图注记只显示英文；悬停说明、索引、对照表、年表在英文名后附注汉字原名。

## 二、拼音与通名

| 类别 | 写法 | 例 |
|---|---|---|
| 拼音 | 不标声调；音节界限有歧义时加撇号；ü 保留 | Xi'an、Yan'an、Lüshun、Lüliang |
| 单字县名 + 县 | 连写 | 涿县 Zhuoxian、涉县 Shexian、蔚县 Yuxian |
| 州（单音节专名） | 连写 | 沧州 Cangzhou、通州 Tongzhou |
| 镇、堡、口作地名一部分 | 连写；作通名时意译 | 吴起镇 Wuqizhen、瓦窑堡 Wayaobu、古北口 Gubeikou；独树镇 Dushu Town |
| 关（关隘条目） | X Pass；已成地名的城镇连写 | 平型关 Pingxing Pass、娘子关 Niangzi Pass；城镇「山海关」Shanhaiguan |
| 今地里的区、旗、盟 | District、Banner、League | 宣化区 Xuanhua District、额济纳旗 Ejin Banner |
| 江、河 | X River | 湘江 Xiang River、汾河 Fen River；长江 Yangtze River、黄河 Yellow River |
| 湖、错 | 从英文习惯 | 太湖 Lake Tai、洞庭湖 Dongting Lake、纳木错 Nam Co |
| 山 | 山脉 X Mountains；单峰 Mount X | 太行山 Taihang Mountains、泰山 Mount Tai、庐山 Mount Lu |
| 少数民族地区 | 用国家规定的少数民族语地名罗马字母拼写，不标附加符号（ê、ü 写作 e、u）；四川、青海、甘肃的藏族地区同样 | 拉萨 Lhasa、日喀则 Xigaze、昌都 Qamdo、林芝 Nyingchi、甘孜 Garze、阿坝 Ngawa、道孚 Dawu、石渠 Serxu、迭部 Tewo、若尔盖 Zoige、马尔康 Barkam、结古 Gyegu、江达 Jomda；库尔勒 Korla、和田 Hotan；呼和浩特 Hohhot、海拉尔 Hailar、扎赉诺尔 Jalainur、哈尔滨 Harbin、齐齐哈尔 Qiqihar |
| 西藏 | **Xizang**（中华人民共和国官方英文自 2023 年起的用法）；民族、语言仍作 Tibetan | 西藏地方政府 Local Government of Xizang；藏军 Tibetan army |
| 台湾地名 | 用台湾通行的拼法 | 台北 Taipei、高雄 Kaohsiung、基隆 Keelung、金门 Kinmen、马祖 Matsu |
| 港澳 | Hong Kong、Macao（官方拼法） | |
| 今地的国名 | 用中华人民共和国外交部的英文国名 | 土耳其 Türkiye（历史政权「土耳其」仍作 Turkey）；印控克什米尔 Indian-controlled Kashmir、巴控克什米尔 Pakistani-controlled Kashmir |
| 道路、村镇通名 | 意译 | 兴业路 Xingye Road、冯家村 Fengjia Village、港口镇 Gangkou Town；故宫 Forbidden City |

## 三、立场用语

| 中文 | 英文 | 说明 |
|---|---|---|
| 中国共产党 / 中共 | Communist Party of China (CPC) / CPC | 官方英文用 CPC，不用 CCP |
| 国民党 | Kuomintang (KMT) | 新华社英文用法 |
| 国民政府 | Nationalist Government | |
| 国民党军 / 国民党守军 | KMT forces / KMT defenders | 不用 Nationalist Army |
| 国民党当局 / 台湾当局 | KMT authorities / Taiwan authorities | |
| 侵华日军 | Japanese invading troops | |
| 伪 X | Puppet X | 伪满洲国 Puppet Manchukuo；汪伪国民政府 Wang Jingwei Puppet Nationalist Government（地图短名 Wang Jingwei Puppet Regime） |
| 日本扶植 / 法国扶植 | Japanese-backed / French-backed | |
| 日据 | under Japanese occupation | 台湾（日据）Taiwan (under Japanese occupation) |
| 解放 / 和平解放 | liberation / peaceful liberation | 北平和平解放 Peaceful liberation of Beiping |
| 起义（国民党军整编投诚） | uprising | 绥远起义 Suiyuan Uprising、湖南和平起义 Hunan peaceful uprising |
| 根据地 / 边区 / 苏区 / 解放区 | Base Area / Border Region / Soviet Area / Liberated Area | 陕甘宁边区 Shaanxi-Gansu-Ningxia Border Region；中央苏区 Central Soviet Area |
| 反“围剿” / 反“扫荡” | counter-“encirclement” / counter-“mopping-up” | 保留引号 |
| 七七事变 | Lugou Bridge Incident | 不用 Marco Polo Bridge Incident |
| 十七条协议 | 17-Article Agreement | 国务院白皮书用法 |
| 第一至第五次战役（抗美援朝） | First … Fifth Campaign | 不用美方的 Phase Offensive |
| 渡江战役 | Yangtze River Crossing Campaign | |
| 就义 / 殉国 | martyrdom / dies for his country | 李大钊就义 Martyrdom of Li Dazhao |
| 九一八事变 | September 18 Incident | |
| 四一二反革命政变 | April 12 Counter-revolutionary Coup | |
| 抗美援朝 | War to Resist US Aggression and Aid Korea | |
| 中国人民志愿军 | Chinese People's Volunteers (CPV) | |
| “联合国军” | “UN Command” forces | 保留引号 |
| 长津湖战役 / 上甘岭战役 | Battle of Changjin Lake / Battle of Shangganling | 今地括注 Chosin Reservoir |
| 美国第七舰队侵入台湾海峡 | US Seventh Fleet intrudes into the Taiwan Strait | |
| 印度非法侵占达旺 | India's illegal occupation of Tawang | |
| 所谓 / 带引号的政权名 | 照留引号 | “Islamic Republic of East Turkestan”、“Republic of South Maluku” |
| 东北 / 北满 / 南满 | Northeast China / northern Northeast China / southern Northeast China | 不用 Manchuria；专名照旧（South Manchuria Railway） |
| 关内 / 关外 / 入关 / 出关 | inside / beyond the Great Wall；entered North China (through Shanhaiguan) | 不写 China proper、the Pass |
| 犯 / 进犯 / 南犯 / 东犯 | attack / invade / encroach on | 保留敌意，不改成中性的 advance、drive、push |
| 通电 | circular telegram | |
| 辛亥革命 | 1911 Revolution | |
| 中国人民抗日战争 | Chinese People's War of Resistance Against Japanese Aggression | |
| 第一次中东战争 | First Middle East War | |

## 四、人名

- 汉人名：姓在前、拼音（Zhang Zuolin、Yan Xishan）；英文早已通行的照旧：Sun Yat-sen、Chiang Kai-shek、Chiang Ching-kuo、T. V. Soong、H. H. Kung、Soong Ching-ling、Soong Mei-ling、Wellington Koo。
- 满、蒙、藏单名照汉文拼音或通行写法（铁良 Tieliang、升允 Shengyun、德王 Prince De、阿沛·阿旺晋美 Ngapoi Ngawang Jigme）。
- 日本人名姓在前，用平文式并标长音（Itagaki Seishirō、Tōjō Hideki、Okamura Yasuji），读音照日文原名查定（香月清司 Katsuki、尾高亀蔵 Suetaka、坂西一良 Banzai），不按汉字常见读法推；地名一律不标长音（Tokyo、Keijo、Odomari、Kanto、Tokaido），战役行动名照原名（Operation Meigō）。
- 西方人名由中文译名回推时，要按战役查定本人（罗厄尔 Rowell、克洛斯 Clowes、米勒 Müller），不照音直译。
- 朝鲜半岛：韩国地名用新罗马字（Busan、Incheon、Daejeon），朝鲜地名用朝鲜官方拼法（Pyongyang、Kaesong、Hungnam、Panmunjom）；人名用本人通行的英文写法（Kim Il Sung、Syngman Rhee、Paik Sun-yup）。
- 越南人名地名保留声调符号（Hồ Chí Minh、Võ Nguyên Giáp、Hà Nội、Điện Biên Phủ）；法国殖民时期的法文地名照用（Tourane）。越南 2025 年 7 月并省后，今地按新省写（安沛并入老街、富安并入多乐、永福并入富寿）。
- 当时的英文地名：Ulan Bator（1924 年后的库伦）、Uliassutai、Djakarta、Johore Bahru、Sungei Patani、Singora、Rangoon、Calcutta 等；今名放今地栏。
- 西方人名只写姓（中文只写姓）：MacArthur、Ridgway、Stilwell、Slim。

## 五、年代与纪年

- 民国以公历纪年，日期一律写公历：22 October 1911、October–December 1911、October 1934 – October 1935；上旬、中旬、下旬作 early / mid- / late。
- 政权说明里「都城」「驻地」行的起止照中文写作 Fuzhou (1933.11–1934.01)，正文行文一律写月份名（from June 1921）。
- 纪年：宣统二年 Xuantong 2；民国元年 Minguo 1、民国二十六年 Minguo 26（与宋元图「年号拼音 + 序数」一致）；1949 年 10 月以后不记纪年。

## 六、战役与事件

- 会战 → Battle of X（淞沪会战 Battle of Songhu、武汉会战 Battle of Wuhan）；战役按规模作 X Campaign 或 Battle of X（淮海战役 Huaihai Campaign、台儿庄战役 Battle of Tai'erzhuang）；保卫战 Defence of X；伏击战 Ambush at X；大捷 X Victory（平型关大捷 Pingxingguan Victory）；起义 X Uprising；事变 X Incident；惨案 X Massacre；会议 X Meeting（党的会议）/ X Conference；会师 X rendezvous。
- 胜负写「A defeated B」，相持写 Stalemate；主将写「A and B vs. C」。
- 事件名作专名首字母大写（Lena Goldfields Massacre、Rice Riots、Yên Bái Uprising）。惨案作 Massacre，例外：南京惨案（1927）作 Nanjing Incident (1927)，以免与南京大屠杀 Nanjing Massacre 混淆。
- 国民党军一律 KMT forces，不写 troops；X 部 作 X's forces。
- 英文通行名称与中文所指一致的照用（Battle of Midway、Gallipoli campaign、Operation Polo）。
- 战役名在正文里照专名大写（the Battle of the Xiang River），不写 battle of。
- 拼写：英式拼写加 -ize（defence、centre、organize）；counter-attack、counter-offensive 加连字符；towards；tsarist 小写（句首除外）；日军作战名标长音（Operation Ichi-gō、Operation Meigō）。引号用弯引号，撇号用直撇号（China's、Xi'an）。
- 只有日、不写月的日期（中文「27 日」），英文补出月份（on 27 May），免得读者误认月份。

## 七、维护

- `python tools/i18n.py status`：缺译、过期、未登记指纹的条数。
- `python tools/i18n.py todo [文件]`：逐条列出缺译与过期的中文。
- 改完英文：`python tools/i18n.py lock` 记下中文指纹；以后中文一改，对应英文就会报“过期”。
- `python run.py --html` 默认严格：有缺译或过期就停下；`--draft` 允许先出草稿（缺译处显示中文）。
- `python tools/i18n.py table [names]` 导出中英对照表供审校（加 names 只导出名称）。
