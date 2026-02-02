
import re,os,json 
import jieba 
import jieba.posseg as pseg
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set
from rank_bm25 import BM25Okapi
    
import pandas as pd 
import numpy as np
from tpf.conf import pc  
pc.set_log_path("/tmp/tousu.log")

class Word:
    def __init__(self) -> None:
        self.jieba = jieba 
        

    @staticmethod
    def add_jieba_dict(data=None, cols=[], save_path=None):
        """追加列的不重复值到save_path,然后将save_path文件的内容添加到jieba字典
        - cols长度为0且save_path文件已存在时，直接加载save_path到jieba字典
        
        
        """
        # 将labels写入save_path文件，一行一个label，后续作为jieba自定义单词字典使用
        if cols and len(cols)>0:
            labels = []
            for lb in cols:
                ll = data[lb].unique().tolist()
                labels.extend(ll)

            # 写入labels到文件，一行一个label
            if save_path:
                # 读取现有文件内容
                existing_labels = set()
                try:
                    with open(save_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                existing_labels.add(line)
                    print(f"从{save_path}读取了{len(existing_labels)}个现有labels")
                except FileNotFoundError:
                    print(f"{save_path}不存在，将创建新文件")

                # 合并并去重
                all_labels = set(labels) | existing_labels

                # 覆盖式写入文件
                with open(save_path, 'w', encoding='utf-8') as f:
                    for label in sorted(all_labels):
                        f.write(str(label) + '\n')
                print(f"已将{len(all_labels)}个去重后的labels写入{save_path}（新增{len(set(labels) - existing_labels)}个）")
                jieba.load_userdict(save_path)
        elif save_path:   
            jieba.load_userdict(save_path)
    
    
    

class TuoMin:
    """
    数据脱敏工具类，包含各种脱敏方法的静态方法
    """
    import re
    import spacy
    from typing import Tuple

    # 初始化spacy模型和感谢语列表
    _nlp = None
    _thank_phrases = None

    @classmethod
    def _init_spacy(cls, zh_core_web_trf="/wks/models/zh_core_web_trf-3.8.0/zh_core_web_trf/zh_core_web_trf-3.8.0"):
        """延迟初始化spacy模型"""
        import spacy
        if cls._nlp is None:
            # 显式导入以确保注册curated_transformer factory
            # import spacy_curated_transformers  # noqa: F401
            # cls._nlp = spacy.load("zh_core_web_trf")
            cls._nlp = spacy.load(zh_core_web_trf)
        return cls._nlp

    @classmethod
    def _init_thank_phrases(cls):
        """延迟初始化感谢语列表"""
        if cls._thank_phrases is None:
            cls._thank_phrases = cls._load_thank_phrases()
        return cls._thank_phrases

    @staticmethod
    def simple_rule_mask(text: str) -> str:
        """
        使用正则规则对银行投诉文本进行简单脱敏处理。
        返回脱敏后的文本。
        """
        import re
        # 身份证号：18位或15位
        text = re.sub(r'\b\d{17}[\dXx]|\d{15}\b', '[身份证号]', text)
        # 银行卡号：13到19位数字，可以被空格或短横线分隔，且连续数字位数加起来是13-19位
        text = re.sub(r'\b(?:\d{4}[-\s]?){2,4}\d{1,5}\b',lambda m: '[银行卡号]' if 13 <= len(re.sub(r'[-\s]', '', m.group())) <= 19 else m.group(),text)
        # 手机号：1开头的11位
        text = re.sub(r'(?:手机号|电话|联系电话|联系手机)?[:：]?\s*(\+?86[-\s]?)?1[3-9]\d{9}', '[手机号]', text)
        # 固定电话：区号+号码
        text = re.sub(r'\b0\d{2,3}-?\d{7,8}\b', '[固定电话]', text)
        # 邮箱地址
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[邮箱地址]', text)
        # 交易流水号：字母数字组合，10-30位，并带关键词提示
        text = re.sub(r'\b[A-Za-z0-9]{10,30}\b(?=.*(?:流水|交易|订单|凭证))', '[交易流水号]', text)
        # 日期：多种格式
        text = re.sub(r'\b(?:\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?|\d{1,2}[-/]\d{1,2}[-/]\d{4})\b', '[日期]', text)
        # 金额：必须带单位"元"，支持逗号与小数
        text = re.sub(r'(￥|¥)?\d+(,\d{3})*(\.\d+)?元', '[金额]', text)
        # 地址：识别常见地理单位（省市区县镇街道...）
        text = re.sub(r'[^，。！？；：\s]{0,10}?(?:省|市|区|县|镇|街道|路|室|楼)[^，。！？；：\s]{0,20}', '[地址]', text)
        # 银行关键词
        bank_keywords = ['建设银行', '工商银行', '农业银行', '中国银行', '交通银行',
                         '招商银行', '浦发银行', '民生银行', '兴业银行', '中信银行']
        for bank in bank_keywords:
            text = text.replace(bank, '[银行名称]')
        # 替换"姓名"相关字段 + 数字/星号
        text = re.sub(r'(客户姓名|姓名|名字)[：:\s]*[\d\*]{2,20}', '[姓名]', text)

        # 替换"电话"相关字段 + 数字/星号（支持 +86 和分隔符）
        text = re.sub(r'(电话号码|手机号|电话号|联系方式|联系电话|电话)[：:\s]*(\+?86[-\s]?)?[\d\*\-]{7,20}', '[手机号]', text)

        # 替换"银行卡号"/"卡号"+ 一串数字/字母/*（中间可能有空格或短横线）
        text = re.sub(r'(银行卡号|卡号)[：:\s]*(\d|[A-Za-z]|\*){10,30}', '[银行卡号]', text)

        # 替换"交易流水号"/"交易编号"/"订单号"等 + 一串数字/字母/*（10-30位）
        text = re.sub(r'(交易流水号|交易编号|交易号|订单号|流水号)[：:\s]*(\d|[A-Za-z]|\*){10,30}', '[交易流水号]', text)

        # 替换"金额"类关键词 + 金额数值整体脱敏
        text = re.sub(r'(金额|交易金额|金额总计|金额为|金额是|应退金额)[：:\s]*(￥|¥)?\d+(,\d{3})*(\.\d+)?元', '[金额]', text)

        # 去除多余空格
        text = re.sub(r'\s+', '', text)

        return text

    @staticmethod
    def remove_special_symbols(text: str) -> str:
        """去除特殊字符"""
        import re
        # 仅去除常见不影响信息结构的特殊字符
        return re.sub(r'[＊*#@&￥%~^<>{}「」\\\…—+=｜|]', '', text)

    @staticmethod
    def _load_thank_phrases():
        """加载感谢语的设定"""
        import os
        thank_phrases = []
        try:
            # 假设thank_phrases.txt在同一目录下
            thank_path = os.path.join(os.path.dirname(__file__),  "thank_phrases.txt")
            with open(thank_path, "r", encoding="utf-8") as f:
                thank_phrases = sorted(
                    [line.strip() for line in f if line.strip()],
                    key=lambda x: -len(x)  # 按长度从长到短排序
                )
            print(f"加载感谢语 {len(thank_phrases)} 条")
        except Exception as e:
            print(f"未能加载感谢语 thank_phrases.txt：{e}")
        return thank_phrases

    @staticmethod
    def remove_thank_phrases(text: str, thank_phrases: list) -> Tuple[str, int]:
        """去除感谢语函数"""
        removed_count = 0
        for phrase in thank_phrases:
            if phrase in text:
                text = text.replace(phrase, ' ')
                removed_count += 1
        return text, removed_count

    @classmethod
    def anonymize_text(cls, text):
        """使用spacy进行命名实体识别和脱敏"""
        nlp = cls._init_spacy()
        doc = nlp(text)

        # 定义需要脱敏的实体类型
        target_entities = ["PERSON", "ORG", "DATE", "MONEY", "PHONE"]

        # 按实体在原文本中的位置排序（避免替换顺序影响结果）
        sorted_entities = sorted(doc.ents, key=lambda x: x.start_char, reverse=True)

        anonymized_text = text
        for ent in sorted_entities:
            if ent.label_ in target_entities:
                # 根据实体类型生成不同的脱敏占位符
                if ent.label_ == "PERSON":
                    placeholder = "[姓名]"
                elif ent.label_ == "ORG":
                    placeholder = "[公司]"
                elif ent.label_ == "DATE":
                    placeholder = "[日期]"
                elif ent.label_ == "MONEY":
                    # 对金额进行部分脱敏（保留前两位数字）
                    money_text = ent.text
                    if any(char.isdigit() for char in money_text):
                        placeholder = money_text[:2] + "##" + money_text[4:] if len(money_text) > 4 else money_text[:2] + "##"
                    else:
                        placeholder = "[金额]"
                else:
                    placeholder = f"[{ent.label_}]"

                # 替换文本
                anonymized_text = anonymized_text[:ent.start_char] + placeholder + anonymized_text[ent.end_char:]

        # 清除带称谓关键词（无上下文）
        title_words = ['先生', '女士', '小姐', '老师', '教授', '博士', '同学', '朋友', '大哥', '大姐', '叔叔', '阿姨']
        for word in title_words:
            anonymized_text = anonymized_text.replace(word, '')

        return anonymized_text

    @classmethod
    def desensitize(cls, text,is_ner=False):
        """
        主要脱敏函数，整合所有脱敏步骤
        """
        import re

        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)

        # Skip empty or invalid texts
        if not text or text.strip() == "":
            return "无效文本"

        # print("去感谢语前：", text)
        thank_phrases = cls._init_thank_phrases()
        text, _ = cls.remove_thank_phrases(text, thank_phrases)   # Step 1: 去除感谢语

        text = cls.simple_rule_mask(text)                          # ✅ Step 2: 先规则脱敏（身份证号、手机号等）

        text = cls.remove_special_symbols(text)  # ✅ Step 2.5: 去除特殊符号

        # Perform NER processing with error handling
        if is_ner:
            try:
                text = cls.anonymize_text(text)                        # ✅ Step 3: NER 识别人名、地址、公司等
                print("NER脱敏后：", text)
            except Exception as e:
                print(f"NER脱敏失败: {e}, 使用规则脱敏结果")
            
        text = re.sub(r'\s+', '', text)                        # Step 4: 清除所有空格

        # Ensure we don't return empty or invalid results
        if not text or text.strip() == "":
            return "无效文本"

        return text

    

class TextPreDeal:
    """
    投诉文本预处理类
    提供6级标签投诉文本分类项目的完整文本预处理功能
    """

    def __init__(self,
                 custom_stopwords: List[str] = None,
                 allowed_pos: Set[str] = None,
                 use_custom_dict: bool = True,
                 min_word_length: int = 1,
                 add_custom_keywords=[]):
        """
        初始化文本预处理器

        Args:
            custom_stopwords: 自定义停用词列表
            allowed_pos: 允许的词性集合
            use_custom_dict: 是否使用自定义词典
            min_word_length: 最小词长度
            add_custom_keywords: 额外的自定义关键词列表，会被添加到jieba词典中
                - 这些关键词会被识别为完整词汇，避免被错误分词
                - 例如: ['提前还款', '逾期利息', '信用卡分期']
        """
        # 初始化停用词表 - 移除重要的否定词和语气词
        self.base_stopwords = [
            "的", "了", "在", "是", "我", "有", "和", "就", "人", "都", "一", "一个", "上", "也", "到", "说", "要", "去", "你", "会", "着", "看", "自己", "这", "那", "她", "他", "它", "们", "嗯嗯"
        ]

        # 重要保留词：否定词、语气词、程度副词（从停用词中移除）
        self.important_words = {
            "不", "没有", "无", "未", "别", "勿", "莫", "毫", "绝非", "并非", "决不",
            "很", "非常", "太", "极", "超", "特别", "格外", "尤其", "十分", "相当",
            "吗", "呢", "啊", "吧", "哦", "嗯", "哈", "呵", "唉", "嗨", "哎",
            "还", "还是", "又", "再", "也", "都", "只", "就", "才", "却"
        }

        # 投诉领域专用停用词 - 移除可能包含重要语义的词
        self.complaint_stopwords = [
            "公司", "用户", "投诉", "反馈", "请问", "你好", "谢谢", "客服", "坐席", "工号",
            "解释", "建议", "回复", "情况", "记录", "信息", "内容", "相关", "以下", "上述", "所说", "所述"
        ]

        # 个人信息相关停用词
        self.personal_info_stopwords = [
            "[姓名]", "[手机号]", "[日期]", "[时间]", "[地点]", "[金额]", "客户姓名", "被投诉", "投诉当的", "大概时间", "来电号码", "手机号码", "电话号码"
        ]

        self.custom_stopwords = custom_stopwords or []
        self.stopwords = set(self.base_stopwords + self.complaint_stopwords +
                            self.personal_info_stopwords + self.custom_stopwords)

        # 默认允许的词性：名词、动词、形容词、副词
        self.allowed_pos = allowed_pos or {'n', 'v', 'a', 'd', 'vn', 'an', 'vd'}

        self.min_word_length = min_word_length
        self.use_custom_dict = use_custom_dict
        self.add_custom_keywords = add_custom_keywords or []

        # 加载自定义词典（如果需要）
        if self.use_custom_dict:
            self._load_custom_dict()

    def _load_custom_dict(self):
        """加载投诉领域自定义词典

        加载两部分关键词：
        1. 预定义的投诉领域关键词
        2. 用户通过add_custom_keywords参数传入的自定义关键词
        """
        # 预定义的投诉领域关键词
        complaint_keywords = [
            "逾期", "征信", "贷款", "还款", "催收", "利息", "费用", "罚款",
            "消除", "撤销", "取消", "调取", "录音", "核实", "处理", "解决",
            "不满", "投诉", "举报", "申诉", "投诉", "反馈", "建议", "意见",
            "服务", "态度", "质量", "效率", "专业", "及时", "响应", "解答",
            "银行卡", "信用卡", "借记卡", "网银", "手机银行", "ATM", "柜台",
            "账户", "余额", "流水", "交易", "转账", "汇款", "支付", "收款",
            "理财", "基金", "保险", "股票", "债券", "投资", "收益", "风险",
            "个人贷款", "房屋贷款", "汽车贷款", "消费贷款", "经营贷款", "信用贷款",
            "催收", "催款", "催账", "讨债", "追债", "清收", "核销", "坏账",
            "利率", "利息", "罚息", "复利", "年化", "月供", "分期", "期供",
            "逾期", "违约", "失信", "黑名单", "征信报告", "信用记录", "不良记录",
            "银行", "金融机构", "客服中心", "营业网点", "分支机构", "总行"
        ]

        # 合并预定义关键词和用户自定义关键词
        all_keywords = complaint_keywords + self.add_custom_keywords

        # 将所有关键词添加到jieba词典
        for word in all_keywords:
            jieba.add_word(word)

        # 如果有自定义关键词，打印日志
        if self.add_custom_keywords:
            print(f"已添加 {len(self.add_custom_keywords)} 个自定义关键词到jieba词典")
            print(f"自定义关键词示例: {self.add_custom_keywords[:5]}")

    def clean_text(self, text: str, is_remove: bool = True) -> str:
        """
        文本清洗 - 合并的清洗规则，支持移除或脱敏替换

        Args:
            text: 原始文本
            is_remove: 清洗模式
                - True: 移除敏感信息，替换为空（默认）
                - False: 脱敏处理，替换为占位符如[手机号]、[身份证号]等

        Returns:
            清洗后的文本

        清洗规则包括：
            - HTML标签
            - URL链接
            - 邮箱地址
            - 手机号码（多种格式）
            - 固定电话
            - 身份证号（15位或18位）
            - 银行卡号（13-19位）
            - 交易流水号
            - 日期
            - 金额
            - 地址信息
            - 银行名称
            - 特殊字段标签

        示例:
            >>> tp = TextPreDeal()
            >>> text = "客户张三，电话13812345678，身份证123456789012345678"
            >>> tp.clean_text(text, is_remove=True)   # 移除模式
            '客户张三，电话，身份证'
            >>> tp.clean_text(text, is_remove=False)  # 脱敏模式
            '客户张三，电话[手机号]，身份证[身份证号]'
        """
        if not isinstance(text, str):
            return ""

        # 定义替换映射：根据is_remove选择替换内容
        def get_replacement(pattern_type):
            """获取替换内容"""
            if is_remove:
                return ''  # 移除模式：替换为空
            else:
                # 脱敏模式：替换为占位符
                replacements = {
                    'html': '',
                    'url': '[网址]',
                    'email': '[邮箱地址]',
                    'phone': '[手机号]',
                    'landline': '[固定电话]',
                    'idcard': '[身份证号]',
                    'bankcard': '[银行卡号]',
                    'transno': '[交易流水号]',
                    'date': '[日期]',
                    'money': '[金额]',
                    'address': '[地址]',
                    'bank': '[银行名称]',
                    'name': '[姓名]',
                    'special_chars': ''
                }
                return replacements.get(pattern_type, '')

        # 1. 移除HTML标签
        text = re.sub(r'<[^>]+>', get_replacement('html'), text)

        # 2. 先处理银行名称（在地址之前，避免地址匹配到银行名中的"市"等）
        if not is_remove:  # 仅在脱敏模式下替换银行名称
            bank_keywords = ['建设银行', '工商银行', '农业银行', '中国银行', '交通银行',
                           '招商银行', '浦发银行', '民生银行', '兴业银行', '中信银行',
                           '光大银行', '华夏银行', '平安银行', '广发银行', '邮储银行']
            for bank in bank_keywords:
                text = text.replace(bank, get_replacement('bank'))

        # 3. 移除/替换银行卡号（必须放在手机号之前，避免16-19位数字被手机号正则匹配）
        # 先处理带标签的银行卡号
        text = re.sub(r'(银行卡号|卡号)[：:\s]?\d{10,19}', get_replacement('bankcard'), text)
        # 再处理纯数字卡号（13-19位连续数字）
        text = re.sub(r'\b\d{13,19}\b', get_replacement('bankcard'), text)
        # 带分隔符的卡号
        text = re.sub(r'\b(?:\d{4}[-\s]?){3,4}\d{4}\b',
                     lambda m: get_replacement('bankcard') if 13 <= len(re.sub(r'[-\s]', '', m.group())) <= 19 else m.group(),
                     text)

        # 4. 移除/替换地址信息（在处理数字之前，避免数字被地址匹配）
        # 只匹配以地理单位结尾，且前面至少有一个中文字符的模式
        text = re.sub(r'[\u4e00-\u9fa5]{2,8}(?:省|市|区|县|镇|街道|路|室|楼|村|乡|号)(?![\u4e00-\u9fa5])', get_replacement('address'), text)

        # 5. 移除/替换URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', get_replacement('url'), text)

        # 6. 移除/替换邮箱地址
        text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', get_replacement('email'), text)

        # 7. 先处理带标签的手机号（避免重复处理）
        text = re.sub(r'(手机号|电话号码|联系电话|联系手机|电话|联系方式)[：:\s]*(\+?86[-\s]?)?1[3-9]\d{9}', get_replacement('phone'), text)

        # 8. 再处理纯手机号（1开头的11位，不在[]内）
        text = re.sub(r'(?<!\[)1[3-9]\d{9}(?!\])', get_replacement('phone'), text)

        # 9. 移除/替换固定电话（区号+号码）
        text = re.sub(r'0\d{2,3}-?\d{7,8}', get_replacement('landline'), text)

        # 10. 移除/替换身份证号（15位或18位）
        text = re.sub(r'\d{15}|\d{17}[\dXx]', get_replacement('idcard'), text)

        # 11. 移除/替换交易流水号（字母数字组合，10-30位）
        text = re.sub(r'(交易流水号|交易编号|交易号|订单号|流水号)[：:\s]*[A-Za-z0-9]{10,30}', get_replacement('transno'), text)

        # 12. 移除/替换日期（多种格式）
        text = re.sub(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?', get_replacement('date'), text)
        text = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', get_replacement('date'), text)

        # 13. 移除/替换金额（带单位）
        text = re.sub(r'(金额|交易金额|金额总计|金额为|金额是|应退金额)[：:\s]?(￥|¥)?\d+(,\d{3})*(\.\d+)?元', get_replacement('money'), text)
        text = re.sub(r'(￥|¥)?\d+(,\d{3})*(\.\d+)?元', get_replacement('money'), text)

        # 14. 移除/替换姓名字段
        text = re.sub(r'(客户姓名|姓名|名字)[：:\s]*[\d\*]{2,20}', get_replacement('name'), text)

        # 15. 清理特殊字符（仅在移除模式）
        if is_remove:
            # 保留中文、英文、数字和基本标点
            text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】《》、]', '', text)

        # 16. 移除多余空格和换行
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def normalize_text(self, text: str) -> str:
        """
        文本标准化

        Args:
            text: 输入文本

        Returns:
            标准化后的文本
        """
        if not isinstance(text, str):
            return ""

        # 全角转半角
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('，', ',').replace('。', '.')
        text = text.replace('！', '!').replace('？', '?')
        text = text.replace('；', ';').replace('：', ':')
        
        # 英文大小写统一（小写）
        text = text.lower()

        # 移除重复字符（如：非常好 -> 很好）
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        text = re.sub(r'[＊*#@&￥%~^<>{}「」\\\…—+=｜|]', '', text)

        return text

    def segment_text(self, text: str, use_pos_filter: bool = True) -> List[str]:
        """
        文本分词

        Args:
            text: 输入文本
            use_pos_filter: 是否使用词性过滤

        Returns:
            分词结果列表
        """
        if not isinstance(text, str) or not text.strip():
            return []

        # 分词及词性标注
        words_with_pos = pseg.lcut(text)

        # 过滤处理
        filtered_words = []
        for word, pos in words_with_pos:
            # 优先保留重要词汇（否定词、语气词、程度副词）
            if word in self.important_words:
                filtered_words.append(word)
                continue

            # 跳过停用词
            if word in self.stopwords:
                continue

            # 跳过过短词汇
            if len(word) < self.min_word_length:
                continue

            # 跳过纯数字和纯符号
            if word.isdigit() or not re.search(r'[\u4e00-\u9fff]', word) and len(word) == 1:
                continue

            # 词性过滤
            if use_pos_filter:
                pos_first = pos[0].lower()
                if pos_first not in {p[0] for p in self.allowed_pos}:
                    continue

            filtered_words.append(word)

        return filtered_words

    def extract_ngrams(self, words: List[str], n: int = 2) -> List[str]:
        """
        提取N-gram特征

        Args:
            words: 词语列表
            n: n-gram的n值

        Returns:
            n-gram列表
        """
        if len(words) < n:
            return []

        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ''.join(words[i:i+n])
            ngrams.append(ngram)

        return ngrams

    def preprocess_text(self, text: str,
                       use_ngram: bool = False,
                       ngram_range: Tuple[int, int] = (2, 3),
                       is_remove=False) -> List[str]:
        """
        完整文本预处理流程

        Args:
            text: 原始文本
            use_ngram: 是否使用n-gram
            ngram_range: n-gram范围

        Returns:
            处理后的词语列表
        """
        # 1. 文本清洗
        cleaned_text = self.clean_text(text,is_remove=is_remove)

        # 2. 文本标准化
        normalized_text = self.normalize_text(cleaned_text)

        # 3. 分词
        words = self.segment_text(normalized_text)

        # 4. N-gram处理
        if use_ngram and len(words) >= 2:
            ngrams = []
            for n in range(ngram_range[0], ngram_range[1] + 1):
                ngrams.extend(self.extract_ngrams(words, n))
            words.extend(ngrams)

        return words

    def analyze_label_keywords(self,
                             df: pd.DataFrame,
                             text_column: str,
                             label_column: str,
                             top_k: int = 20) -> Dict:
        """
        分析各标签下的高频词

        Args:
            df: 数据框
            text_column: 文本列名
            label_column: 标签列名
            top_k: 返回前k个高频词

        Returns:
            标签关键词字典
        """
        label_keywords = {}

        for label in df[label_column].unique():
            # 获取该标签下所有文本
            mask = df[label_column] == label
            texts = df.loc[mask, text_column]

            all_words = []
            for text in texts:
                words = self.preprocess_text(text)
                all_words.extend(words)

            # 统计词频
            word_freq = Counter(all_words).most_common(top_k)
            label_keywords[str(label)] = word_freq

            # print(f"标签 {label} 的高频词：")
            # for word, freq in word_freq:
            #     print(f"  {word}: {freq}")
            # print("-" * 50)

        return label_keywords

    def process_dataset(self,
                       df: pd.DataFrame,
                       text_column: str,
                       output_path: str = None,
                       use_ngram: bool = False) -> pd.DataFrame:
        """
        处理整个数据集

        Args:
            df: 输入数据框
            text_column: 文本列名
            output_path: 输出文件路径
            use_ngram: 是否使用n-gram

        Returns:
            处理后的数据框
        """
        print(f"开始处理数据集，共 {len(df)} 条记录...")

        # 创建处理后的文本列
        df['processed_text'] = df[text_column].apply(
            lambda x: ''.join(self.preprocess_text(x, use_ngram=use_ngram))
        )

        # 添加文本长度信息
        df['original_length'] = df[text_column].astype(str).apply(len)
        df['processed_length'] = df['processed_text'].astype(str).apply(len)
        df['word_count'] = df['processed_text'].astype(str).apply(lambda x: len(x.split()))

        # 保存结果
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"处理结果已保存到：{output_path}")

        # 打印统计信息
        print(f"\n预处理统计信息：")
        print(f"平均原始文本长度：{df['original_length'].mean():.2f}")
        print(f"平均处理后文本长度：{df['processed_length'].mean():.2f}")
        print(f"平均词汇数量：{df['word_count'].mean():.2f}")
        print(f"词汇数量为0的记录数：{(df['word_count'] == 0).sum()}")

        return df

    def save_stopwords(self, filepath: str):
        """保存停用词表到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in sorted(self.stopwords):
                f.write(word + '\n')
        print(f"停用词表已保存到：{filepath}")

    def load_stopwords(self, filepath: str):
        """从文件加载停用词表"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                new_stopwords = {line.strip() for line in f if line.strip()}
                self.stopwords.update(new_stopwords)
            print(f"已从 {filepath} 加载 {len(new_stopwords)} 个停用词")

    def get_text_stats(self, text: str) -> Dict:
        """
        获取文本统计信息

        Args:
            text: 输入文本

        Returns:
            文本统计字典
        """
        processed_words = self.preprocess_text(text)

        stats = {
            'original_length': len(text),
            'cleaned_length': len(self.clean_text(text)),
            'word_count': len(processed_words),
            'unique_word_count': len(set(processed_words)),
            'avg_word_length': np.mean([len(word) for word in processed_words]) if processed_words else 0
        }

        return stats


def test_optimization():
    """测试优化后的预处理效果"""
    print("=== 测试优化后的文本预处理效果 ===\n")

    # 初始化预处理器
    preprocessor = TextPreDeal(
        use_custom_dict=True,
        min_word_length=2
    )

    # 测试用例
    test_cases = [
        "[姓名]客户来电咨询之前的贷款具体下放时间，之前支行有工作人员联系，客户表示不认可，要求提供具体贷款时间，并且表示没有合理回复，客户表示要投诉协助处",
        "客户对服务态度非常不满意，要求立即处理",
        "银行系统异常，导致无法正常转账，客户很生气",
        "虽然客服解释了，但客户还是不理解，认为银行做法错误",
        "客户要求取消逾期记录，但银行表示不符合规定"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"原文: {text}")
        processed_words = preprocessor.preprocess_text(text)
        print(f"处理后: {''.join(processed_words)}")
        print("-" * 80)

def text_pre_deal(df=None, input_file = None, output_dir = "",
                  
                  use_ngram=False,
                  show_demo=False,
                  use_cols=['processed_text', 'label']):
    """提取关键词

    功能说明：
    1. 初始化投诉领域专用的文本预处理器（带自定义词典）
    2. 从CSV文件读取或直接使用DataFrame作为输入
    3. 分析每个标签下的高频关键词（如果存在label列）
    4. 对文本进行预处理：清洗、标准化、分词
    5. 可选：添加N-gram特征以增强语义表达
    6. 保存处理结果和中间文件

    Args:
        df (pd.DataFrame, optional): 输入数据框，包含'text'列和可选的'label'列
            - 如果为None，则从input_file读取CSV文件
            - 如果不为None，则直接使用该DataFrame
        input_file (str, optional): CSV文件路径，当df为None时使用
        output_dir (str): 输出目录路径，用于保存处理结果和中间文件，默认为'/tmp/'
        use_ngram (bool): 是否使用N-gram特征增强，默认为False
            - False: 仅进行基础分词和清洗
            - True: 在基础分词基础上添加2-gram和3-gram特征
        show_demo (bool): 是否显示预处理效果示例，默认为False
            - True: 打印前3条样本的原始文本、处理后文本和统计信息
        use_cols (list): 返回的DataFrame包含的列名列表，默认为['processed_text', 'label']
            - processed_text: 处理后的文本列（会被重命名为'text'）
            - label: 标签列（如果原始数据中存在）

    Returns:
        pd.DataFrame or None: 处理后的数据框
            - 包含processed_text列（重命名为'text'）和label列（如果存在）
            - 如果处理失败则返回None

    输出文件：
        在output_dir目录下生成以下文件：
        - processed_basic.csv: 基础预处理结果（不带N-gram）
        - processed_ngram.csv: 带N-gram的预处理结果（当use_ngram=True时）
        - label_keywords.json: 各标签的高频关键词分析结果（如果存在label列）
        - stopwords.txt: 停用词表

    处理步骤（TextPreDeal预处理器）：
        1. 文本清洗：移除HTML标签、URL、邮箱、电话号码、身份证号、银行卡号
        2. 文本标准化：全角转半角、英文统一小写、移除重复字符
        3. 分词：使用jieba分词，支持自定义词典和词性过滤
        4. 停用词过滤：移除基础停用词、投诉领域停用词、个人信息占位符
        5. 词性过滤：保留名词、动词、形容词、副词等有意义的词性
        6. N-gram生成（可选）：添加2-gram和3-gram特征增强语义表达

    示例1 - 基础预处理（从文件读取）:
        >>> import pandas as pd
        >>> from tpf.nlp.text import text_pre_deal
        >>>
        >>> # 从CSV文件读取并预处理
        >>> df_processed = text_pre_deal(
        ...     input_file='/path/to/complaints.csv',
        ...     output_dir='/path/to/output',
        ...     use_ngram=False,
        ...     show_demo=True
        ... )
        >>>
        >>> # df_processed包含两列：'text'（处理后）, 'label'

    示例2 - 使用N-gram特征增强:
        >>> # 带N-gram的预处理，增强语义表达
        >>> df_processed = text_pre_deal(
        ...     input_file='/path/to/complaints.csv',
        ...     output_dir='/path/to/output',
        ...     use_ngram=True,  # 启用N-gram
        ...     show_demo=False
        ... )
        >>>
        >>> # 处理后的文本会包含2-gram和3-gram特征
        >>> # 例如："客户投诉银行服务" -> "客户投诉 银行服务 客户投诉银行 投诉银行服务"

    示例3 - 直接使用DataFrame:
        >>> # 使用已有的DataFrame进行处理
        >>> df = pd.DataFrame({
        ...     'text': ['客户投诉银行服务态度不好', '贷款逾期催收太频繁'],
        ...     'label': ['服务态度', '催收问题']
        ... })
        >>>
        >>> df_processed = text_pre_deal(
        ...     df=df,
        ...     output_dir='/tmp/output',
        ...     use_ngram=False
        ... )

    注意事项：
        - 输入数据必须包含'text'列
        - 预处理器使用投诉领域自定义词典（贷款、征信、催收等关键词）
        - 停用词表会自动保存到output_dir
        - 如果use_ngram=True，处理时间会增加，但可以增强语义表达
        - 处理后的文本列会被重命名为'text'（从'processed_text'）

    预处理器配置（TextPreDeal）：
        - use_custom_dict=True: 使用投诉领域自定义词典
        - min_word_length=2: 最小词长度为2
        - allowed_pos: 名词、动词、形容词、副词等
        - stopwords: 基础停用词 + 投诉领域停用词 + 个人信息占位符
    """
    # 先测试优化效果
    # test_optimization()

    print("\n" + "="*80 + "\n")

    # 初始化预处理器
    preprocessor = TextPreDeal(
        use_custom_dict=True,
        min_word_length=2
    )

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 读取数据
    print(f"读取数据文件：{input_file}")
    try:
        if df is None:
            df = pd.read_csv(input_file)
            print(f"数据读取成功，共 {len(df)} 条记录")
            print(f"列名：{df.columns.tolist()}")

            # 显示前几条数据
            print("\n原始数据示例：")
            print(df[['text']].head(3))

        # 分析各标签高频词
        if 'label' in df.columns:
            print("\n=== 分析各标签高频词 ===")
            label_keywords = preprocessor.analyze_label_keywords(
                df, text_column='text', label_column='label', top_k=15
            )

            # 保存标签关键词分析结果
            keywords_file = os.path.join(output_dir, 'label_keywords.json')
            with open(keywords_file, 'w', encoding='utf-8') as f:
                # 转换为可序列化的格式
                serializable_keywords = {
                    k: [{'word': w, 'freq': f} for w, f in v]
                    for k, v in label_keywords.items()
                }
                json.dump(serializable_keywords, f, ensure_ascii=False, indent=2)
            print(f"标签关键词分析结果已保存到：{keywords_file}")

        # 处理数据集
        print("\n=== 开始文本预处理 ===")

        # 输出文件路径
        output_file_basic = os.path.join(output_dir, 'processed_basic.csv')
        output_file_ngram = os.path.join(output_dir, 'processed_ngram.csv')

        if use_ngram:
            # 带N-gram的预处理
            processed_df_ngram = preprocessor.process_dataset(
                df.copy(),
                text_column='text',
                output_path=output_file_ngram,
                use_ngram=True
            )
            df = processed_df_ngram[use_cols]
        else:
            # 基础预处理
            processed_df_basic = preprocessor.process_dataset(
                df.copy(),
                text_column='text',
                output_path=output_file_basic,
                use_ngram=False
            )
            df = processed_df_basic[use_cols]
            
        # 保存停用词表
        stopwords_file = os.path.join(output_dir, 'stopwords.txt')
        preprocessor.save_stopwords(stopwords_file)

        if show_demo:
        # 文本统计示例
            print("\n=== 文本预处理效果示例 ===")
            sample_indices = [0, 1, 2] if len(df) >= 3 else range(len(df))

            for idx in sample_indices:
                original_text = df.iloc[idx]['text']
                processed_text = processed_df_basic.iloc[idx]['processed_text']
                stats = preprocessor.get_text_stats(original_text)

                print(f"\n样本 {idx + 1}:")
                print(f"原始文本：{original_text[:100]}...")
                print(f"处理后文本：{processed_text[:100]}...")
                print(f"统计信息：{stats}")

        print(f"\n=== 处理完成 ===")
        print(f"输出文件：")
        print(f"- 基础预处理：{output_file_basic}")
        print(f"- 带N-gram预处理：{output_file_ngram}")
        print(f"- 停用词表：{stopwords_file}")
        df.rename(columns={'processed_text': 'text'}, inplace=True)
        return df

    except Exception as e:
        print(f"处理过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
    
    return None 


def text_clear(df, text_col='text', is_remove=False, output_dir=None):
    """文本清洗 - 批量处理DataFrame中的文本列

    功能说明：
    对DataFrame中指定列的每个文本进行清洗和标准化处理

    Args:
        df (pd.DataFrame): 包含文本数据的DataFrame
        text_col (str): 文本列名，默认为'text'
        output_dir (str, optional): 输出目录，用于保存中间结果

    Returns:
        pd.DataFrame: 处理后的DataFrame，text_col列已被清洗和标准化

    处理流程：
        1. 文本清洗 (clean_text): 移除HTML标签、URL、邮箱等
        2. 文本标准化 (normalize_text): 全角转半角、大小写统一等

    示例:
        >>> import pandas as pd
        >>> from tpf.nlp.text import text_clear
        >>>
        >>> df = pd.DataFrame({
        ...     'text': ['<p>测试文本</p>', 'HTTP://EXAMPLE.COM 测试']
        ... })
        >>> result = text_clear(df, text_col='text')
        >>> print(result['text'].tolist())
        ['测试文本', '测试']
    """
    # 初始化预处理器
    tp = TextPreDeal(
        use_custom_dict=True,
        min_word_length=2
    )

    

    # 复制DataFrame，避免修改原数据
    df = df.copy()

    # 批量处理文本
    texts = df[text_col].tolist()

    # 1. 文本清洗
    cleaned_texts = [tp.clean_text(text,is_remove=is_remove) for text in texts]

    # 2. 文本标准化
    normalized_texts = [tp.normalize_text(text) for text in cleaned_texts]

    # 将处理后的结果赋值回df
    df[text_col] = normalized_texts
    # 确保输出目录存在
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir,"data_clear.csv")
        df.to_csv(save_path, index=False)
    return df 


class BM25Reranker:
    def __init__(self, df=None, use_cols=['text','label'],texts=[],k1=1.8, b=0.75,score_name='score'):
        """初始化索引
        - 针对全体文本
        - use_cols:共有两个元素，第1个元素为文本列，第2个元素为标签列
        """
        if len(texts)==0:
            if df is None:
                raise Exception("texts为空时，请输入数据集df")
            self.text_name = use_cols[0]
            self.label_name = use_cols[1]
            self.score_name = score_name
            texts = df[use_cols[0]].tolist()
        self.df = df[use_cols]   
        # 对中文文档进行分词
        tokenized_texts = [jieba.lcut(text) for text in texts]
        self.tokenized_texts = tokenized_texts
        self.k1 = k1 
        self.b = b 
        self.bm25 = BM25Okapi(tokenized_texts, k1=k1, b=b)
        
    def epoch_cross_scores(self, sim_top_k=5, label_top_k=3, pring_num=50, save_path=None):
        """计算BM25分数，按轮次
        - 每个轮次取第i行数据，对剩下的n-1行数据，计算BM25分数
        - 对于每个轮次来说，最终结果只有sim_top_k*label_top_k行数据
        """
        data = self.df.copy()
        data_len = len(self.tokenized_texts)
        pc.lg(f"data.columns: {data.columns.tolist()}")

        # 全局数据框列表，用于收集所有批处理结果
        df_results = []
        for i in range(data_len):
            new_query = data.iloc[i][self.text_name]
            label     = data.iloc[i][self.label_name]
            others    = data.drop(data.index[i])
            
            tokenized_query = self.tokenized_texts[i]
            tokenized_texts = [doc for j, doc in enumerate(self.tokenized_texts) if j != i]
            bm25 = BM25Okapi(tokenized_texts, k1=self.k1, b=self.b)
            # 第i行相对剩下n-1行的文本计算BM25分数
            others[self.score_name] = bm25.get_scores(tokenized_query)
            
            df3 = others.groupby('label').apply(
                lambda x: pd.Series({
                    self.text_name: x.nlargest(sim_top_k, self.score_name)[self.text_name].iloc[0],  # 取分数最高的第一个样本的text
                    self.label_name: x.name,
                    'mean_score': x.nlargest(sim_top_k, self.score_name)[self.score_name].mean()  # 计算前5个分数的均值
                }),
                include_groups=False
            ).reset_index(drop=True)

            # 按mean_score降序排列
            df3_sorted = df3.sort_values('mean_score', ascending=False)
            label_topk = df3_sorted[:label_top_k]
            label_topk = label_topk[[self.label_name, 'mean_score']]
            labels = label_topk[self.label_name].tolist()
            
            df_topk = others[others[self.label_name].isin(labels)]

            df_result_list = []
            for lab in labels:
                # 筛选当前label的数据
                label_data = df_topk[df_topk[self.label_name] == lab]
                # 按score降序排序并取前sim_top_k条
                top_similar = label_data.nlargest(sim_top_k, self.score_name)
                df_result_list.append(top_similar)

            # 合并所有结果
            if df_result_list:
                df_topk = pd.concat(df_result_list, axis=0, ignore_index=True)
            df_topk=df_topk.merge(label_topk, on=self.label_name,how='left')
            df_topk = df_topk.rename(columns={self.text_name: 'sim_text'})
            
             # 添加真实标签和重命名标签列
            df_topk['real_label'] = label
            df_topk['query_text'] = new_query
            df_topk = df_topk.rename(columns={self.label_name: 'sim_label','score':'sim_score'})
            # pc.lg(f"df_topk.columns: {df_topk.columns.tolist()}")
            # print(f"df_topk.columns: {df_topk.columns.tolist()}")
            # pc.lg(f"df_topk.shape: {df_topk.shape}")
            # 将当前结果添加到全局列表
            df_results.append(df_topk)
            if i%pring_num == 0 or i==data_len-1:
                print(f"处理第{i+1}/{data_len}条数据，单条sim_label数量: {len(df_topk)}")

        # 按行拼接所有结果
        if df_results:
            df_final = pd.concat(df_results, axis=0, ignore_index=True)
            print(f"批量处理完成，总计处理{data_len}条查询，返回{len(df_final)}条结果")
            if save_path is not None:
                df_final.to_csv(save_path, index=False, encoding='utf-8-sig')
                print(f"保存CSV文件到: {save_path}")
                print(f"记录数: {len(df_final)}")
                print(f"字段数: {len(df_final.columns.tolist())}")
            return df_final
        else:
            print("未处理任何数据，返回空数据框")
            return pd.DataFrame() 
        
            
    def sim_scores(self, new_query):
        """计算相似度： 对于新的投诉文本，分词后使用 get_scores 方法即可得到它与已有文本的BM25相似度分数
        """
        tokenized_query = jieba.lcut(new_query)
        scores = self.bm25.get_scores(tokenized_query)
        return scores
    
    
    def label_topk(self, new_query, sim_top_k=5, label_top_k=3, outdir=""):
        """取前label_top_k个标签
        处理BM25分数，计算每个标签前sim_top_k个样本的均值分数

        Args:
            df: 原始数据框，包含text, label, label_text_count列
            sim_top_k: top k个相似分数
            label_top_k: top k个标签

        Returns:
            df3_sorted: 按mean_score降序排列的数据框
            
        Out Files:
            bm25_scores.csv: 原始分数
            bm25_scores_mean5.csv: 按mean_score降序排列的数据
        """
        
        # 添加分数列
        self.df[self.score_name] = self.sim_scores(new_query)

        # 保存原始分数
        bm25_path = os.path.join(outdir, "bm25_scores.csv")
        self.df.to_csv(bm25_path, index=False)

        df2 = self.df 

        # 按标签分组，取每个标签分数最高的前5个样本的均值
        df3 = df2.groupby('label').apply(
            lambda x: pd.Series({
                self.text_name: x.nlargest(sim_top_k, self.score_name)[self.text_name].iloc[0],  # 取分数最高的第一个样本的text
                self.label_name: x.name,
                'mean_score': x.nlargest(sim_top_k, self.score_name)[self.score_name].mean()  # 计算前5个分数的均值
            }),
            include_groups=False
        ).reset_index(drop=True)

        # 按mean_score降序排列
        df3_sorted = df3.sort_values('mean_score', ascending=False)

        # 保存结果
        df3_path = os.path.join(outdir, "bm25_scores_mean5.csv")
        df3_sorted.to_csv(df3_path, index=False)

        return df3_sorted[:label_top_k]

    
    def data_topk(self, new_query, sim_top_k=5, label_top_k=3,outdir=""):
        """取与new_query相似的sim_top_k*label_top_k条数据

        Args:
            new_query (_type_): _description_
            sim_top_k (int, optional): _description_. Defaults to 5.
            label_top_k (int, optional): _description_. Defaults to 3.
            outdir (str, optional): _description_. Defaults to "".

        Returns:
            _type_: _description_
        """
        #与new_query相似的标签
        label_topk = self.label_topk(new_query, sim_top_k, label_top_k,outdir=outdir)
        label_topk = label_topk[[self.label_name, 'mean_score']]
        labels = label_topk[self.label_name].tolist()
        
        df = self.df.copy()
        # 添加分数列,df的text为相似的文本,而非新的文本new_query
        df[self.score_name] = self.sim_scores(new_query)
        df_topk = df[df[self.label_name].isin(labels)]

        # 对df_topk中每个label下按score降序排序，取前sim_top_k条数据
        df_result_list = []
        for label in labels:
            # 筛选当前label的数据
            label_data = df_topk[df_topk[self.label_name] == label]
            # 按score降序排序并取前sim_top_k条
            top_similar = label_data.nlargest(sim_top_k, self.score_name)
            df_result_list.append(top_similar)

        # 合并所有结果
        if df_result_list:
            df_topk = pd.concat(df_result_list, axis=0, ignore_index=True)
        df_topk=df_topk.merge(label_topk, on=self.label_name,how='left')
        df_topk = df_topk.rename(columns={self.text_name: 'sim_text'})
        return df_topk
         

    def data_topk_batch(self, df, sim_top_k=5, label_top_k=3,p_num=50,outdir=""):
        """
        批量处理数据，返回所有结果的拼接数据框

        Args:
            df: 输入数据框，第1列为text，第2列为label
            sim_top_k: 相似度top_k
            label_top_k: 标签top_k

        Returns:
            pd.DataFrame: 按行拼接所有df_tmp的结果
        """
        # 全局数据框列表，用于收集所有批处理结果
        df_results = []
        df_len = len(df)

        # 遍历输入数据的每一行
        for i, tup in enumerate(df.itertuples(index=False)):   # index=True 把索引也带出来
            new_query = tup[0]  #取df的第1列
            
            # 调用data_topk方法获取单个查询的结果
            df_tmp = self.data_topk(new_query, sim_top_k=sim_top_k, label_top_k=label_top_k,outdir=outdir)

            # 添加真实标签和重命名标签列
            if len(tup)>1:
                label = tup[1]
                df_tmp['real_label'] = label
            df_tmp['query_text'] = new_query
            df_tmp = df_tmp.rename(columns={self.label_name: 'sim_label','score':'sim_score'})

            # 添加批次信息，便于追踪
            df_tmp['batch_index'] = i

            # 将当前结果添加到全局列表
            df_results.append(df_tmp)
            if i%p_num == 0 or i==df_len-1:
                print(f"处理第{i+1}/{len(df)}条数据，单条sim_label数量: {len(df_tmp)}")

        # 按行拼接所有结果
        if df_results:
            df_final = pd.concat(df_results, axis=0, ignore_index=True)
            print(f"批量处理完成，总计处理{len(df)}条查询，返回{len(df_final)}条结果")
            return df_final
        else:
            print("未处理任何数据，返回空数据框")
            return pd.DataFrame() 

class NLP:
    def __init__(self):
        self.t5_model = None 
        self.t5_tokenizer = None 
        self.t5_device = 'cpu'
        self.nlp = None

    def init_t5(self, model_path='/wks/models/t5_summary_en_ru_zh_base_2048', device='cpu'):
        self.t5_device = device
        from modelscope import T5ForConditionalGeneration, T5Tokenizer
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        model.eval()
        model.to(device)
        generation_config = model.generation_config
        # for quality generation
        generation_config.length_penalty = 0.6
        generation_config.no_repeat_ngram_size = 2
        generation_config.num_beams = 10
        
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        self.t5_tokenizer = tokenizer 
        self.t5_model = model
        self.t5_generation_config = generation_config
        
    def summary_t5(self, text, limit_len=200):
        """
        使用T5模型生成文本摘要

        参数:
        text: 输入文本
        limit_len: 长度限制，如果文本长度超过此值则进行摘要生成，否则返回原文本

        返回:
        str: 摘要结果或原文本
        """
        # 检查文本长度，如果不超过限制则直接返回原文本
        if len(text) <= limit_len:
            return text

        if self.t5_model is None:
            self.init_t5()

        # text summary generate
        prefix = 'summary to zh: '
        src_text = prefix + text
        input_ids = self.t5_tokenizer(src_text, return_tensors="pt")

        generated_tokens = self.t5_model.generate(**input_ids.to(self.t5_device), generation_config=self.t5_generation_config)

        result = self.t5_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

        # 返回第一个结果（通常只有一个摘要结果）
        return result[0] if result else text
    
    def summary_hanlp(self,text,top_n=8, limit_len=200):
        if self.nlp is None:
            self.nlp = TLP()
        # 检查文本长度，如果不超过限制则直接返回原文本
        if len(text) <= limit_len:
            return text
        ss = self.nlp.summary_str(text,top_n=top_n)
        return ss

nlp = NLP()


class TLP:
    def __init__(self) -> None:
        
        pass 
    
    @staticmethod
    def cut_words(text):
        """使用结巴分词对文本进行分词
        """
        words = jieba.cut(text, cut_all=False)
        return words 
    
    @staticmethod
    def summary_str(text,top_n=8):
        # 尝试导入pyhanlp，如果未安装则设为None
        try:
            from pyhanlp import HanLP
            PYHANLP_AVAILABLE = True
        except ImportError:
            HanLP = None
            PYHANLP_AVAILABLE = False
    
        summary_sentences = HanLP.extractSummary(text,top_n)
        st =""
        for sentence in summary_sentences:
            st += sentence+","
        st = st.removesuffix(",")
        return st
    
    @staticmethod
    def summary(text, n=5):
        """使用HanLP进行文本摘要

        Args:
            text (str): 待摘要的文本
            n (int): 返回的摘要数量

        Returns:
            list: 摘要列表，如果pyhanlp未安装则返回空列表
        """
        try:
            from pyhanlp import HanLP
            PYHANLP_AVAILABLE = True
        except ImportError:
            HanLP = None
            PYHANLP_AVAILABLE = False
            
        if not PYHANLP_AVAILABLE:
            print("警告: pyhanlp未安装，无法使用HanLP进行文本摘要")
            return []

        try:
            # 使用HanLP进行摘要
            summary_result = HanLP.extractSummary(text, n)
            return [str(item) for item in summary_result]
        except Exception as e:
            print(f"HanLP摘要失败: {e}")
            return []

    @staticmethod
    def segment(text):
        """使用HanLP进行分词

        Args:
            text (str): 待分词的文本

        Returns:
            list: 分词结果，如果pyhanlp未安装则返回空列表
        """
        try:
            from pyhanlp import HanLP
            PYHANLP_AVAILABLE = True
        except ImportError:
            HanLP = None
            PYHANLP_AVAILABLE = False
            
        if not PYHANLP_AVAILABLE:
            print("警告: pyhanlp未安装，无法使用HanLP进行分词")
            return []

        try:
            # 使用HanLP进行分词
            segment_result = HanLP.segment(text)
            return [str(item) for item in segment_result]
        except Exception as e:
            print(f"HanLP分词失败: {e}")
            return [] 