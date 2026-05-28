#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 涨停板拆解-简版.html 生成三个页面的数据文件"""
import json, re, os
from pypinyin import pinyin, Style

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, '涨停板拆解-简版', '涨停板拆解-简版.html')
SHOW_DIR = os.path.join(BASE_DIR, '涨停板展示')

name_to_code = {}
# 优先从全量A股列表读取（含ST股、更名股等）
stock_list_path = os.path.join(BASE_DIR, 'a_stocks_full.txt')
if os.path.exists(stock_list_path):
    with open(stock_list_path, 'r') as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                name, code = line.rsplit(':', 1)
                name_to_code[name] = code
# 补充：从概念数据源加载（可能包含a_stocks_full没有的旧名）
for fname in ['stocks_detail_with_concepts.md', 'stocks_detail.md']:
    fpath = os.path.join(BASE_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, 'r') as f:
            for line in f:
                m = re.match(r'##\s+\d+\.\s+(.+?)（(\d+)）', line)
                if m:
                    n = m.group(1).replace(' ', '')
                    if n not in name_to_code:
                        name_to_code[n] = m.group(2)

def to_pinyin(name):
    return ''.join(r[0].lower() for r in pinyin(name, style=Style.FIRST_LETTER))

def convert(name):
    code = name_to_code.get(name, '')
    return f'{to_pinyin(name)}({code})' if code else to_pinyin(name)

def load_posts():
    with open(HTML_PATH, 'r') as f:
        content = f.read()
    m = re.search(r'const P=(\[.*?\]);', content, re.DOTALL)
    if not m:
        print("ERROR: Cannot find P array"); exit(1)
    return json.loads(m.group(1))

stock_suffixes = (
    '股份', '科技', '发展', '集团', '控股', '药业', '生物', '智能',
    '软件', '电气', '电力', '能源', '通信', '光电', '微电', '新材',
    '电器', '环保', '生态', '建设', '工程', '银行', '证券', '投资',
    '文化', '传媒', '旅游', '酒店', '食品', '饮料', '服装', '纺织',
    '家具', '家居', '建材', '装饰', '转债', '游戏', '网络', '数据',
    '数字', '芯片', '电池', '锂电', '储能', '精密', '创意', '创新',
    '精工', '国际', '光学', '医疗', '健康', '环境', '水务', '燃气',
    '化工', '化学', '石油', '煤炭', '钢铁', '金属', '矿业', '农业',
    '林业', '渔业', '牧业', '出版', '印刷', '物流', '运输', '港口',
    '航空', '航运', '船舶', '汽车', '轮胎', '光伏', '风电', '核电',
    '水电', '黄金', '白银', '稀土', '钻石', '珠宝', '新能', '工具',
    '模具', '机械', '电声', '智慧', '互联', '玻纤', '合金', '光纤',
    '材料', '实业', '工业', '商业', '贸易', '服务', '广告', '教育',
    '电子', '信息', '硬件', '半导体', '新能源', '化肥', '农药',
    '塑料', '橡胶', '玻璃', '陶瓷', '有色', '采矿', '冶炼', '制造',
    '设备', '仪器', '仪表', '轴承', '齿轮', '传动', '液压', '气动',
    '自动化', '无人机', '卫星', '航天', '海洋', '码头', '装卸',
    '起重', '矿山', '农机', '包装', '造纸', '冶金', '水利', '环卫',
    '污水', '废气', '净水', '变压器', '发电机', '压缩机', '信托',
    '基金', '保险', '期货', '租赁', '担保', '房地产', '置业',
    '地产', '物业', '房产', '住宅', '商场', '超市', '百货',
    '连锁', '加盟', '电商', '直播', '动漫', '影视', '综艺',
    '音乐', '阅读', '社交', '供应链', '物联网', '车联网',
    '大数据', '人工智能', '区块链', '数字货币', '碳中和',
    '节能', '低碳', '零碳', '循环', '绿色', '清洁', '再生',
    '特种', '定制', '柔性', '敏捷', '高效',
    '锂业', '锗业', '钨业', '钴业', '镍业', '锡业', '铅业',
    '锌业', '铝业', '铜业', '镁业', '钛业',
    '有限', '技术', '科技集团', '控股集团', '科技股份',
)

def clean_stock_name(s):
    """清理股票名中的评论性文字
    
    核心原则：含"推"字的条目，如果整体不在name_to_code中，一律丢弃。
    如"推北投科技"是对前面股票的评论，不是股票名。
    "山推股份"是真实股票，在name_to_code中，保留。
    """
    s = s.strip()
    if not s:
        return ''
    # 全角/半角字母转换（用户输入可能是半角，股票列表是全角）
    # 半角A-Z → 全角Ａ-Ｚ，半角a-z → 全角ａ-ｚ
    s_converted = ''
    for c in s:
        if 'A' <= c <= 'Z':
            s_converted += chr(ord(c) + 0xFF21 - 0x41)  # A → Ａ
        elif 'a' <= c <= 'z':
            s_converted += chr(ord(c) + 0xFF41 - 0x61)  # a → ａ
        else:
            s_converted += c
    # 先检查转换后的名称（全角）
    if s_converted in name_to_code:
        return s_converted
    # 再检查原始名称
    if s in name_to_code:
        return s
    # 含"推"字且不在name_to_code中 → 评论，丢弃
    if '推' in s:
        return ''
    return s_converted if s_converted != s else s

def looks_like_sector(line):
    """判断是否像板块名（而非评论性文字）"""
    if len(line) > 12 or len(line) < 2:
        return False
    comment_words = ['的', '了', '不', '是', '有', '在', '这', '那', '很', '都',
                     '感觉', '可能', '应该', '注意', '风险', '预期', '方面',
                     '不做', '不评论', '不清楚', '没办法', '低于', '也是',
                     '推广东', '推浙江', '推上海', '推北京', '推福建', '推江苏',
                     '推山东', '推湖北']
    if any(w in line for w in comment_words):
        return False
    if line[0].isdigit():
        return False
    return True

def is_stock_name(s):
    """判断是否为股票名（基于全量A股列表）"""
    s = clean_stock_name(s)
    s = s.strip()
    if not s or len(s) < 2 or len(s) > 10:
        return False
    # 数字开头排除
    if s[0].isdigit():
        return False
    # 包含非股票字符排除（允许中文、半角/全角字母、星号）
    # 全角字母范围：Ａ-Ｚ (U+FF21-U+FF3A), ａ-ｚ (U+FF41-U+FF5A)
    if not re.match(r'^[一-鿿A-Za-zＡ-Ｚａ-ｚ*]+$', s):
        return False
    # 概念/行业标签（非股票名，需过滤）
    concept_tags = {
        '人工智能', '光伏', '芯片', '消费电子', '化工', '游戏', '核电', '房地产', '汽车', '物流',
        '新能源', '储能', '锂电池', '医药', '医疗', '教育', '金融', '银行', '证券', '保险',
        '军工', '航天', '航空', '高铁', '基建', '建材', '钢铁', '有色', '煤炭', '石油',
        '电力', '水务', '环保', '农业', '林业', '渔业', '食品', '饮料', '家电', '家居',
        '纺织', '服装', '造纸', '印刷', '传媒', '影视', '音乐', '体育', '旅游', '酒店',
        '商业', '零售', '电商', '外贸', '港口', '航运', '公路', '仓储', '配送',
        '软件', '硬件', '半导体', '通信', '云计算', '大数据', '区块链', '物联网', '网络安全',
        '机器人', '智能', '自动化', '机械', '电气', '仪表', '光学', '电子', '显示', '照明',
        '电池', '电机', '发动机', '齿轮', '轴承', '模具', '工具', '包装', '广告',
        '地产', '物业', '装饰', '园林', '环卫', '消防', '安防', '检测', '认证', '黄金', '稀土',
        '锂电', '锂业', '风电', '期货', '合金', '玻璃', '橡胶', '化肥', '农药', '农机',
        '净水', '海洋', '金属', '光纤', '电器', '数据',
        'ai医疗', 'ai影视', 'ai教育', 'ai游戏', 'ai电商', 'ai环保', 'ai传媒', 'al电器',
        '三板', '三胎', '业绩', '中药', '乳业', '代糖', '互金', '中俄', '中报', '上海', '二波',
        '氢能源', '固态电池', '量子科技', '算力硬件', '第三代半导体',
        '充电桩', '无人驾驶', '数字货币', '跨境电商', '存储芯片', '消费', '电网',
        '重组', '次新', '零售', '航运', '数字要素', '数字经济', '数据中心', '数据安全',
        '核电避险', '油气', '算力', '算力产业链', '算力硬件', '算力电源',
        'Ai应用', 'Ai算力', 'Ai医疗', 'Ai智能体', 'Ai伴侣', 'Ai眼镜',
        'DS', 'DS应用', 'DS算力', 'DS软件', 'CPO', 'RWA', 'PET铜箔',
        '其余形式独苗', '题材独苗', '独苗', '未分类', '情绪回落', '情绪强化', '情绪稳定',
        '周一计划', '周二计划', '周三计划', '周四计划', '周五计划',
        '谨慎接力', '避险属性', '烂板吸金', '反包结构', '食之无味', '看不懂',
        '不评论了', '不清楚', '没办法', '低于预期', '有待观察', '注意业绩',
        '公告利好', '个股利好', '新闻刺激', '名字玄学', '趋势型', '趋势中',
        '机构股', '华字辈', '中字头', '大飞机', '特斯拉', '小米汽车', '华为方向',
        '浙江股', '广东股', '推广东股', '推浙江', '推军工', '推基建', '推环保',
        '推纺织', '推航天', '推芯片', '推核电股',
        '磷化工', '煤化工', '氟化工', '油化工', '油气化工',
        '纺织机械', '纺织外贸', '纺织服装', '纺织电商', '纺织贸易',
        '工程机械', '建筑机械', '矿山机械', '煤矿机械',
        '房地产相关', '房地产基建', '房地产装修', '基建房地产', '地产基建',
        '消费电子', '消费包装', '消费家电', '消费电商', '消费食品', '消费饮料', '消费零售',
        '汽车产业链', '汽车电子', '汽车芯片', '汽车配件', '汽车检测', '汽车消费',
        '芯片光刻机', '芯片半导体', '芯片封装', '芯片存储', '芯片重组',
        '医药避险', '医药相关', '医药消费', '医药合资', '医药流通',
        '军工电子', '军工低空', '军工避险', '军工反包', '军工补涨',
        '有色涨价', '有色先手', '有色出口', '有色化工', '有色反制',
        '光伏储能', '光伏化工', '光伏材料', '光伏属性', '光伏支架', '光伏收购',
        '航天星链', '航天军工', '航天通信', '航天软件', '航天小弟',
        '锂电储能', '锂电光伏', '锂电回收', '锂电铜箔', '锂电设备', '锂电相关',
        '算力租赁', '算力液冷', '算力电源', '算力电网', '算力芯片', '算力相关',
        '化工涨价', '化工纺织', '化工补涨', '化工能板', '化工风电',
        '金融证券', '金融软件', '金融拉升', '金融弹性', '金融独苗',
        '电力电网', '电力设备', '电力建设', '电力工程', '电力避险',
        '环保工程', '环保题材', '环保设备', '环保发电',
        '储能光伏', '储能电池', '储能风电',
        '商业航天', '卫星通信', '卫星航天',
        '影视传媒', '游戏传媒', '传媒游戏', '传媒短剧', '传媒类',
        '造纸', '印刷', '广告电商', '广告营销', '出版教育', '在线教育',
        '食品饮料', '食品消费', '饮料', '酿酒饮料',
        '智能家居', '智能制造', '智能驾驶', '智能穿戴', '智能交通', '智能体',
        '旅游消费', '假期旅游', '太空旅游', '内需旅游',
        '电子烟', '电子纸', '电子布',
        '数字认证', '数字经济', '数字货币', '数据中心', '数据要素', '数据安全',
        '包装印刷', '包装物流', '包装股',
        '港口航运', '港口物流', '跨境物流',
        '航运涨价', '航运物流',
        '外贸支付', '外贸物流', '外贸电商', '外贸跨境',
        '电商零售', '电商数据', '电商营销', '电子商务', '直播电商', '抖音电商',
        '黄金避险', '黄金涨价', '黄金白银', '黄金有色',
        '稀土永磁', '稀土有色', '稀土金属', '稀土外贸',
        '固态电池', '燃料电池', '磷电池', '钒电池',
        '一带一路', '带路基建', '带路物流',
        '高铁设备', '高铁电气', '高铁陪跑',
        '大消费', '大消费相关',
        '海洋经济', '海洋生物', '海洋军工',
        '碳交易', '碳中和', '绿电光伏', '绿电碳中和',
        '网络安全', '区块链', '元宇宙',
        '装饰装修', '装修家居', '装修建材',
        '煤化工', '煤化工', '煤化工',
        '低空经济', '低空推航天',
        '重组股转', '重组算力', '重组芯片',
        '参股证券', '参股芯片',
        '电网设备', '电网电力', '电网电气',
        '水利基建', '水务环保',
        '房屋检测', '建筑检测',
        '燃气轮机', '发电设备',
        '制冷剂', '制冷设备',
        '核污染', '核辐射',
        '天然气', '油气开采',
        '光刻机', '光刻胶', '光芯片', '光通信',
        '钠电池', '钛合金', '铝合金', '钼概念',
        '猪肉', '鸡肉', '水产', '种业',
        '乡村振兴', '城镇化',
        '冰雪体育', '冰雪经济',
        '冬奥会', '亚运会',
        '可控核聚变', '超导概念', '超导材料',
        '血液制品', '体外诊断', '医疗器械',
        '代糖', '预制菜', '社区团购',
        '元宇宙', 'NFT', 'Web3',
        '端侧ai', '端侧消费电子',
        '外围算力', '国产算力', '国产ai', '国产芯片', '国产软件',
        '今日黄金', '今日买卖',
        '电动汽车', '飞行汽车', '新能源汽车', '新能源车', '新能源电力',
        '煤化工', '煤炭机械', '煤炭避险', '煤炭补涨',
        '光伏发电', '光伏玻璃', '光伏涨价', '光伏铜箔',
        '锂电薄膜', '锂电派系', '锂电身位', '锂电抱团',
        '宇树机器人', '数控机器人', '汽车机器人',
        '期货涨停', '做期货',
        '公积金', '社保基金',
        '首板供应总结', '题材总结', '题材风口',
        '也是包装', '也是包装推包装', '光纤推光纤', '包装推包装',
    }
    if s in concept_tags:
        return False
    # 描述性短语特征（论坛描述，非股票名）
    phrase_words = ['一个', '两个', '几个', '也有', '买入', '不是', '不管', '不过', '不清',
        '以前', '今天', '假期', '一起', '不做', '不然', '不能', '但是', '套利', '避除',
        '低价', '高度', '隐形', '结金', '主线',
        '推广东', '推浙江', '推上海', '推北京', '推福建', '推江苏', '推山东', '推湖北']
    if any(w in s for w in phrase_words):
        return False
    # 【核心】在全量A股列表中 → 直接确认为股票
    if s in name_to_code:
        return True
    # 有股票后缀但不在列表中 → 可能是新股/已更名，仍接受
    has_suffix = any(s.endswith(suf) for suf in stock_suffixes)
    if has_suffix:
        return True
    # 不在列表、无后缀 → 不是股票
    return False

def parse_day(text):
    lines = text.split('\n')
    first_board, lianban = {}, {}
    current_level, in_first, in_comment, current_sector = None, False, False, None
    level_processed = False  # 标志位：当前级别的连板是否已处理
    level_re = re.compile(r'^(首板|二板晋级|三板晋级|四板晋级|五板晋级|六板晋级|七板晋级|八板晋级|九板晋级|十板晋级|十一板晋级|十二板晋级|二板|三板|四板|五板|六板|七板|八板|九板|十板|十一板|十二板)[,，]?')
    end_markers = ('观察计划', '高标情绪', '竞价最优解', '气质股', '思考题', '二板总结', '三板总结', '隔日个股', '明日计划', '今日买卖', '明日观察', '明日预期', '今日竞价', '今日操作', '今日最优', '明日破局', '明日个人', '盘面细节', '今日套利', '连板总结', '连板观察', '隔夜预期', '隔夜动作', '隔夜计划', '选择题', '问答题', '高考题', '盘面暗示', '首板供应总结', '今日总结', '题材总结', '题材风口')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        m = level_re.match(line)
        if m:
            current_level = m.group(1).replace('晋级', '')
            in_first = (current_level == '首板')
            in_comment = False
            current_sector = None
            level_processed = False  # 新级别，重置标志
            # 连板格式处理
            # 格式1: 同一行 "- 股票A，股票B，股票C"
            # 格式2: 跨行，每行一个股票 "股票名、描述" 或 "股票名，描述"
            remaining = line[m.end():].strip()
            
            # 如果同一行有内容且以 - 开头，处理逗号分隔的多股票
            if remaining and (remaining.startswith('-') or remaining.startswith('–')):
                remaining = remaining[1:].strip()
                if remaining:
                    # 检查是否有中文逗号分隔
                    if '，' in remaining:
                        for stock in re.split(r'[，,]+', remaining):
                            stock = stock.strip()
                            for sep in ['。', '：', ':']:
                                if sep in stock:
                                    stock = stock.split(sep)[0].strip()
                            if is_stock_name(stock):
                                lianban.setdefault(current_level, [])
                                lianban[current_level].append(stock)
                    else:
                        # 短横分隔
                        for part in re.split(r'\s*[-–]\s+', remaining):
                            part = part.strip()
                            if '，' in part:
                                stock = part.split('，')[0].strip()
                            elif ',' in part:
                                stock = part.split(',')[0].strip()
                            else:
                                stock = part
                            if '。' in stock:
                                stock = stock.split('。')[0].strip()
                            if is_stock_name(stock):
                                lianban.setdefault(current_level, [])
                                lianban[current_level].append(stock)
            
            # 跨行格式：跳过空行，逐行读取股票（直到遇到结束标记或非股票行）
            if not remaining:
                for j in range(i + 1, min(i + 50, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue  # 跳过空行
                    # 检查是否是结束标记
                    if any(next_line.startswith(marker) for marker in end_markers):
                        break
                    # 检查是否是下一个级别
                    if level_re.match(next_line):
                        break
                    # 检查是否以 - 开头（另一种跨行格式）
                    if next_line.startswith('-') or next_line.startswith('–'):
                        stock_line = next_line[1:].strip()
                        if stock_line:
                            # 检查逗号分隔
                            if '，' in stock_line:
                                for stock in re.split(r'[，,]+', stock_line):
                                    stock = stock.strip()
                                    for sep in ['。', '：', ':']:
                                        if sep in stock:
                                            stock = stock.split(sep)[0].strip()
                                    if is_stock_name(stock):
                                        lianban.setdefault(current_level, [])
                                        lianban[current_level].append(stock)
                            else:
                                # 单股票
                                for sep in ['、', '：', ':', '，', ',', '。']:
                                    if sep in stock_line:
                                        stock = stock_line.split(sep)[0].strip()
                                        break
                                else:
                                    stock = stock_line
                                if is_stock_name(stock):
                                    lianban.setdefault(current_level, [])
                                    lianban[current_level].append(stock)
                    else:
                        # 每行一个股票格式：股票名、描述 或 股票名，描述
                        # 用顿号或逗号分隔，取第一部分作为股票名
                        stock_line = next_line
                        # 去掉描述部分
                        for sep in ['、', '：', ':', '，', ',', '。']:
                            if sep in stock_line:
                                stock = stock_line.split(sep)[0].strip()
                                break
                        else:
                            stock = stock_line
                        if is_stock_name(stock):
                            lianban.setdefault(current_level, [])
                            lianban[current_level].append(stock)
                        else:
                            # 非股票行，跳过继续看下一行
                            continue
            level_processed = True  # 标记已处理
            continue
        if re.match(r'^首板总结', line):
            if not in_first:
                in_first = True
                current_level = '首板'
                in_comment = False
                current_sector = None
            continue
        if line == '——':
            if in_first:
                current_sector = None; in_comment = False
            continue
        if in_first and re.match(r'^首封时间', line):
            in_comment = True
            continue
        if line.startswith(end_markers):
            continue
        if in_comment:
            if not re.match(r'^\d{1,2}[:：]', line) and not re.match(r'^\d+[^\d]', line):
                in_comment = False
            else:
                continue
        if re.match(r'^\d+[^\d]', line):
            in_comment = True
            continue
        if in_first:
            if '，' in line or ',' in line:
                if current_sector is None:
                    current_sector = '未分类'
                first_board.setdefault(current_sector, [])
                for p in re.split(r'[，,、]+', line):
                    p = p.strip().rstrip('。！？；')
                    if is_stock_name(p):
                        first_board[current_sector].append(p)
            else:
                if current_sector and is_stock_name(line):
                    first_board.setdefault(current_sector, [])
                    first_board[current_sector].append(line)
                else:
                    if looks_like_sector(line):
                        current_sector = line
                        first_board.setdefault(current_sector, [])
        else:
            if current_level is None:
                continue
            if level_processed:
                continue  # 当前级别的连板已在跨行处理中解析，跳过
            if re.match(r'^\d+[，,\s\d]*$', line) or '复制链接' in line:
                continue
            # 连板格式：股票名、描述 或 股票名，描述
            # 先用顿号分割（可能多个股票）
            if '、' in line:
                for part in re.split(r'、+', line):
                    part = part.strip()
                    # 再去掉逗号/句号后的描述
                    for sep in ['：', ':', '、', '，', ',', '。']:
                        if sep in part:
                            part = part.split(sep)[0].strip()
                    if is_stock_name(part):
                        lianban.setdefault(current_level, [])
                        lianban[current_level].append(part)
            else:
                sn = line
                # Try colon/period first (before comma)
                for sep in ['：', ':', '。', '、', '，', ',']:
                    if sep in sn:
                        sn = sn.split(sep)[0].strip()
                if is_stock_name(sn):
                    lianban.setdefault(current_level, [])
                    lianban[current_level].append(sn)
    return first_board, lianban

def stock_with_code(name):
    """添加代码到股票名，返回全角格式（与 stock_detail_map.js 键一致）"""
    # 全角/半角转换
    name_converted = ''
    for c in name:
        if 'A' <= c <= 'Z':
            name_converted += chr(ord(c) + 0xFF21 - 0x41)  # A → Ａ
        elif 'a' <= c <= 'z':
            name_converted += chr(ord(c) + 0xFF41 - 0x61)  # a → ａ
        else:
            name_converted += c
    
    # 查找代码（先全角后半角）
    code = name_to_code.get(name_converted, '')
    if not code:
        code = name_to_code.get(name, '')
    
    # 拼音用原始名（用户输入习惯）
    py = to_pinyin(name)
    if code:
        return f'{name_converted}（{py}）{code}'
    return name_converted  # 无代码也返回全角


def load_existing_dates():
    """读取已有 zt_data.js 中的日期集合"""
    fpath = os.path.join(SHOW_DIR, 'zt_data.js')
    if not os.path.exists(fpath):
        return set(), []
    with open(fpath, 'r', encoding='utf-8') as f:
        c = f.read()
    dates = set(re.findall(r'"d":\s*"(\d{4}-\d{2}-\d{2})"', c))
    return dates, c

def entry_to_js(item):
    """把单条记录转成 JS 对象字符串"""
    d = json.dumps(item['d'], ensure_ascii=False)
    l = json.dumps(item['l'], ensure_ascii=False)
    t_raw = item['t'].replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    return f'  {{\n    "d": {d},\n    "l": {l},\n    "t": `\n{t_raw}\n`\n  }}'

def gen_classify(posts):
    existing_dates, existing_content = load_existing_dates()
    new_data = []
    for item in posts:
        if item['date'] in existing_dates:
            continue  # 跳过已存在的日期
        fb, lb = parse_day(item['text'])
        tl = []
        ss = sum(len(v) for v in fb.values())
        if ss:
            tl.append('首板')
            for s, stk in fb.items():
                if stk:
                    tl.append(s)
                    for j in range(0, len(stk), 8):
                        tl.append('，'.join(stock_with_code(x) for x in stk[j:j+8]))
        for lv in ['二板','三板','四板','五板','六板','七板','八板','九板','十板','十一板','十二板']:
            if lb.get(lv):
                tl.append('')  # 空行分隔首板与连板
                tl.append(lv)
                tl.append('，'.join(stock_with_code(x) for x in lb[lv]))
        new_data.append({'d': item['date'], 'l': item['link'], 't': '\n'.join(tl)})

    if not new_data:
        if existing_content:
            print(f'  zt_data.js（{len(existing_dates)} 天，无新增）')
            return
        print('  zt_data.js（0 天）')
        return

    # 统一模式：合并已有+新增数据，整体重新生成（保证排序）
    all_data = list(new_data)
    if existing_content:
        # 从现有文件解析已有条目
        import re as _re
        pattern = r'\{\s*"d":\s*"([^"]+)",\s*"l":\s*"([^"]+)",\s*"t":\s*`([\s\S]*?)`\s*\}'
        for d, l, t in _re.findall(pattern, existing_content):
            if not any(x['d'] == d for x in all_data):
                all_data.append({'d': d, 'l': l, 't': t})
        # 按日期降序排序
        all_data.sort(key=lambda x: x['d'], reverse=True)
    # 新建模式
    else:
        # 新建模式
        new_content = 'const P=[\n'
        for i, item in enumerate(all_data):
            new_content += entry_to_js(item)
            new_content += ',' if i < len(all_data) - 1 else ''
            new_content += '\n'
        new_content += '];'

    with open(os.path.join(SHOW_DIR, 'zt_data.js'), 'w', encoding='utf-8') as f:
        f.write(new_content)
    total = len(all_data)
    print(f'  zt_data.js（{total} 天，新增 {len(new_data)} 条）')

def gen_stock_data(posts):
    stocks = {}
    for item in posts:
        fb, lb = parse_day(item['text'])
        d = item['date']
        for sec, st in fb.items():
            for s in st:
                stocks.setdefault(s, [])
                stocks[s].append(d + '|首板|' + sec)
        for lv, st in lb.items():
            if lv:
                for s in st:
                    stocks.setdefault(s, [])
                    stocks[s].append(d + '|' + lv + '|')
    result = sorted([{'n': k, 'e': v, 'c': len(v),
                       'p': to_pinyin(k), 'g': to_pinyin(k)[0].upper()}
                      for k, v in stocks.items()], key=lambda x: x['n'])
    with open(os.path.join(SHOW_DIR, 'zt_stock_data.js'), 'w', encoding='utf-8') as f:
        f.write('const S=[\n')
        for i, item in enumerate(result):
            pretty = json.dumps(item, ensure_ascii=False, indent=2)
            pretty_lines = pretty.split('\n')
            f.write('  ' + ('\n  '.join(pretty_lines)))
            f.write(',' if i < len(result) - 1 else '')
            f.write('\n')
        f.write('];')
    print(f'  zt_stock_data.js（{len(result)} 只）')


if __name__ == '__main__':
    if not os.path.exists(HTML_PATH):
        print(f'ERROR: 找不到 {HTML_PATH}')
        exit(1)
    posts = load_posts()
    print(f'Loaded {len(posts)} posts, {len(name_to_code)} codes')
    gen_classify(posts)
    # gen_stock_data(posts)  # 已删除涨停板按股票页面
    print('Done.')
