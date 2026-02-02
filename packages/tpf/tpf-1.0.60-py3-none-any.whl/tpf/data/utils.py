
import pandas as pd  
import numpy as np 
import re 
from tpf.conf import pc

class ReadDeal():

    def __init__(self,):
        pass 
    
    @classmethod
    def _merge_label(cls, df, need_to_one_cols,label_new_name='label', null_flag='', split_flag = '-'):
        """
        对need_to_one_cols中的列进行拼接，先去除空格，然后按split_flag拼接为label列
        """
        tmp_label_col = need_to_one_cols

        #对tmp_label_col中的列进行拼接，先去除空格，然后按split_flag拼接为label列

        # 对每个标签列去除空格，然后按split_flag拼接
        df[label_new_name] = df[tmp_label_col].apply(
            lambda row: split_flag.join([str(x).strip() if pd.notna(x) and str(x).strip() != '' else null_flag for x in row]),
            axis=1
        )

        # 移除末尾的split_flag（如果有）
        df[label_new_name] = df[label_new_name].apply(lambda x: x.rstrip(split_flag) if x.endswith(split_flag) else x)

        df.drop(columns=tmp_label_col, inplace=True)
        return df 
    
    @classmethod
    def text2Xy(cls, data_path, 
                use_cols=[], to_col2=[], 
                need_merge_cols = [],
                label_new_name='label',lable_padding="lable_padding",
                null_flag='', split_flag = '-', log_path=None):
        """读取CSV文件并转换列名，合并多个标签列为单一标签列

        功能说明：
        1. 自动检测文件编码（支持GBK、UTF-8、latin-1）读取CSV文件
        2. 从CSV中选择指定列（use_cols），可选择重命名为新列名（to_col2）
        3. 如果提供了need_merge_cols，对最后一列（通常是label6）进行清洗处理：
           - 去除所有空白字符
           - 将None或长度小于3的值替换为lable_padding
        4. 将指定的标签列（need_merge_cols）合并为单一标签列（label_new_name）
        5. 删除原始的多个标签列，只保留合并后的标签列

        Args:
            data_path (str): CSV文件路径
            use_cols (list): 要从CSV中提取的列名列表，如['投诉内容', '一级分类', ..., '六级分类']
            to_col2 (list): 可选，重命名后的列名列表，如['text', 'label1', 'label2', ..., 'label6']
                - 如果为None或空列表，则不进行列重命名
                - 如果提供，必须与use_cols长度相同
                - 最后一列（to_col2[6]）会进行特殊清洗处理（当need_merge_cols不为空时）
            need_merge_cols (list): 需要合并的标签列名列表，如['label1', 'label2', ..., 'label6']
                - 如果为None或空列表，则不进行标签合并，直接返回处理后的DataFrame
                - 这些列应该是to_col2中的列名（如果to_col2不为空）或use_cols中的列名
            label_new_name (str): 合并后的标签列名，默认为'label'
            lable_padding (str): 用于填充无效标签的占位符，默认为'lable_padding'
                - 当标签为None、空字符串或长度小于3时使用
            null_flag (str): 合并标签时用于替换空值的占位符，默认为''（空字符串）
            split_flag (str): 合并标签时的分隔符，默认为'-'
            log_path (str): 日志文件路径，如果为None则不设置日志

        Returns:
            pd.DataFrame or None: 处理后的数据框
                - 如果need_merge_cols为空：返回use_cols指定的列（可能已重命名）
                - 如果need_merge_cols不为空：返回文本列 + 合并后的标签列
                如果处理失败则返回None

        处理流程：
            1. 文件读取：依次尝试GBK、UTF-8、latin-1编码读取CSV
            2. 列选择：从CSV中提取use_cols指定的列
            3. 列重命名（可选）：如果to_col2不为空，将use_cols重命名为to_col2
            4. 标签清洗（可选）：如果need_merge_cols不为空，对最后一列去除空白并填充无效值
            5. 标签合并（可选）：如果need_merge_cols不为空，将指定列合并为单一标签列
            6. 列清理：删除原始的标签列，只保留合并后的标签列

        示例1 - 只读取指定列，不进行标签合并:
            >>> import pandas as pd
            >>> from tpf.data.utils import ReadDeal
            >>>
            >>> # 只读取两列，不重命名，不合并
            >>> df = ReadDeal.text2Xy(
            ...     data_path='/path/to/data.csv',
            ...     use_cols=['投诉内容', '一级分类'],
            ...     to_col2=[],  # 不重命名
            ...     need_merge_cols=[]  # 不合并
            ... )
            >>>
            >>> # 返回的df包含两列：'投诉内容', '一级分类'

        示例2 - 读取列、重命名并合并标签:
            >>> df = ReadDeal.text2Xy(
            ...     data_path='/path/to/data.csv',
            ...     use_cols=['投诉内容', '一级分类', '二级分类', '三级分类',
            ...                '四级分类', '五级分类', '六级分类'],
            ...     to_col2=['text', 'label1', 'label2', 'label3',
            ...              'label4', 'label5', 'label6'],
            ...     need_merge_cols=['label1', 'label2', 'label3', 'label4', 'label5', 'label6'],
            ...     label_new_name='label',
            ...     lable_padding='unknown',
            ...     null_flag='未知',
            ...     split_flag='-'
            ... )
            >>>
            >>> # 返回的df包含两列：
            >>> # - text: 投诉内容
            >>> # - label: '零售业务-个人贷款-场景消费贷-还款与催收问题-客户未如期还款-其他原因'

        示例3 - 使用自定义分隔符合并标签:
            >>> df = ReadDeal.text2Xy(
            ...     data_path='/path/to/data.csv',
            ...     use_cols=['text', 'cat1', 'cat2', 'cat3'],
            ...     to_col2=['text', 'l1', 'l2', 'l3'],
            ...     need_merge_cols=['l1', 'l2', 'l3'],
            ...     split_flag='/',  # 使用/作为分隔符
            ...     null_flag='NULL'  # 空值替换为NULL
            ... )
            >>>
            >>> # 合并后的标签格式: '零售业务/个人贷款/场景消费贷'

        示例4 - 处理无效标签:
            >>> # 如果label6列为None或短文本（长度<3），会被替换
            >>> # 假设原始数据中某行的label6为None或''
            >>> # 处理后会变成: '零售业务-个人贷款-场景消费贷-还款与催收问题-客户未如期还款-unknown'

        注意事项：
            - use_cols必须存在于CSV文件中
            - 如果to_col2不为空，必须与use_cols长度相同
            - need_merge_cols应该是to_col2的子集（如果to_col2不为空）
            - 最后一列（索引6）会进行特殊清洗：去除空白，长度<3时用lable_padding替换
            - 如果need_merge_cols为None或空列表，不会进行标签合并
            - 如果文件编码不是GBK、UTF-8或latin-1，会读取失败
            - 如果CSV文件行数<=1（只有表头或为空），返回None
        """
        if log_path is not None: 
            pc.set_log_path(log_path=log_path)
            
        try:
            # 获取配置参数
            data = data_path
            col1 = use_cols
            col2 = to_col2

            # 读取原始数据，不指定usecols，让pandas自动检测列
            pc.lg(f"process_data_text正在读取数据文件: {data}")
            try:
                df = pd.read_csv(data, encoding='gbk')
                pc.lg(f"使用GBK编码成功读取数据")
            except UnicodeDecodeError:
                pc.lg(f"GBK编码读取失败，尝试UTF-8编码...")
                try:
                    df = pd.read_csv(data, encoding='utf-8')
                    pc.lg(f"使用UTF-8编码成功读取数据")
                except UnicodeDecodeError:
                    pc.lg(f"UTF-8编码也失败，尝试latin-1编码...")
                    df = pd.read_csv(data, encoding='latin-1')
                    pc.lg(f"使用latin-1编码读取数据")

            pc.lg(f"原始数据形状: {df.shape}")

            # 检查文件是否为空（只有表头或完全为空）
            if df.shape[0] <= 1:
                pc.lg(f"文件为空或只有表头，行数: {df.shape[0]}")
                return None

            # 优化列处理逻辑
            # 检查列数是否足够
            if len(df.columns) < len(col1):
                pc.lg(f"列数不足，实际列数: {len(df.columns)}, 需要列数: {len(col1)}")
                return None
            
            if col2 is not None and len(col2)>0:

                # 创建列映射字典 - 只映射存在的列
                available_cols = df.columns.tolist()
                col_mapping = {}
                for old_col, new_col in zip(col1, col2):
                    if old_col in available_cols:
                        col_mapping[old_col] = new_col
                    else:
                        pc.lg(f"列 '{old_col}' 不存在，跳过重命名")

                # 重命名列
                df = df[col1]
                df_processed = df.rename(columns=col_mapping)
                pc.lg(f"列名转换完成，映射数量: {len(col_mapping)}")
                pc.lg(f"处理后数据形状: {df_processed.shape}\n")
            if need_merge_cols is None or len(need_merge_cols)==0:
                return df 
            
            def label6_deal(s):
                flag = lable_padding
                if s is None:
                    return flag 
                s = str(s)
                s = re.sub(r'\s+', '', s)
                if len(s) < 3:
                    return flag 
                return s 
            df_processed[col2[6]] = df_processed[col2[6]].apply(label6_deal)
            pc.lg(f"df_processed[col2[1:]][:3]:\n{df_processed[col2[1:]][:3]}")
            
            pc.lg(f"标签合并...start")
            df_processed = cls._merge_label(df_processed, 
                                            need_to_one_cols=need_merge_cols, 
                                            label_new_name=label_new_name,
                                            null_flag=null_flag, 
                                            split_flag = split_flag)
            pc.lg(f"标签合并...end")

            return df_processed

        except Exception as e:
            pc.lg(f"处理数据时发生错误: {e}")
            return None




class GroupDeal:
    def __init__(self):
        pass
    
    @classmethod
    def label_score_transform(cls, df,
                    group_key='label',
                    score_col='score',
                    transform_type='mean',
                    score_col_new=None):
        """按分组计算统计指标，将结果添加到原DataFrame

        功能说明：
        1. 按指定列（支持单列或多列）对数据进行分组
        2. 对每组计算指定的统计变换
        3. 将统计结果作为新列添加到原DataFrame
        4. 原DataFrame的行数保持不变，每行都会获得其所属分组的统计值
        5. 自动处理空值和异常值（如'nil', 'null', None等）

        Args:
            df (pd.DataFrame): 输入数据框
            group_key (str or list): 分组键，支持单列字符串或多列列表
                - 单列: 'label' 或 ['label']
                - 多列: ['category', 'label'] 或 ['year', 'month', 'label']
            score_col (str): 需要计算统计指标的列名，默认为'score'
            transform_type (str): 统计变换类型，默认为'mean'
                可选值：
                - 'mean': 平均值
                - 'sum': 求和
                - 'count': 计数
                - 'std': 标准差
                - 'var': 方差
                - 'min': 最小值
                - 'max': 最大值
                - 'median': 中位数
                - 'first': 第一个值
                - 'last': 最后一个值
                - 'zscore': 标准化分数（z-score），std为0时返回0
            score_col_new (str): 新生成的统计列名，默认为'{score_col}_{transform_type}'

        Returns:
            pd.DataFrame: 原数据框基础上添加了新列，包含每个分组对应的统计值

        特殊处理：
            - 自动将空字符串、'nil'、'null'等转换为NaN
            - zscore计算时，如果标准差为0，则返回0
            - 所有NaN值在统计计算时会被自动忽略

        示例1 - 单列分组计算平均值:
            >>> import pandas as pd
            >>> from tpf.data.utils import GroupDeal
            >>>
            >>> # 创建示例数据
            >>> data = {
            ...     'text': ['文本1', '文本2', '文本3', '文本4', '文本5', '文本6'],
            ...     'label': ['A', 'A', 'B', 'B', 'C', 'C'],
            ...     'score': [0.9, 0.8, 0.7, 0.6, 0.5, 0.95]
            ... }
            >>> df = pd.DataFrame(data)
            >>>
            >>> # 计算每个标签的平均分数
            >>> result = GroupDeal.label_score_transform(
            ...     df,
            ...     group_key='label',
            ...     score_col='score',
            ...     transform_type='mean',
            ...     score_col_new='label_mean_score'
            ... )
            >>> print(result)
            >>> #    text label  score  label_mean_score
            >>> # 0  文本1     A   0.90            0.850  (0.9+0.8)/2
            >>> # 1  文本2     A   0.80            0.850
            >>> # 2  文本3     B   0.70            0.650  (0.7+0.6)/2
            >>> # 3  文本4     B   0.60            0.650
            >>> # 4  文本5     C   0.50            0.725  (0.5+0.95)/2
            >>> # 5  文本6     C   0.95            0.725

        示例2 - 计算z-score用于标准化:
            >>> import pandas as pd
            >>> from tpf.data.utils import GroupDeal
            >>>
            >>> # 创建包含异常值的数据
            >>> data = {
            ...     'text': ['文1', '文2', '文3', '文4', '文5'],
            ...     'label': ['X', 'X', 'X', 'Y', 'Y'],
            ...     'score': [0.5, 0.6, 0.7, 0.1, 0.9]  # X均值=0.6, Y均值=0.5
            ... }
            >>> df = pd.DataFrame(data)
            >>>
            >>> # 计算z-score
            >>> result = GroupDeal.label_score_transform(
            ...     df,
            ...     group_key='label',
            ...     score_col='score',
            ...     transform_type='zscore',
            ...     score_col_new='z_score'
            ... )
            >>> print(result)
            >>> #   text label  score    z_score
            >>> # 0  文1     X   0.5   -1.0  (0.5-0.6)/std
            >>> # 1  文2     X   0.6    0.0  (0.6-0.6)/std
            >>> # 2  文3     X   0.7    1.0  (0.7-0.6)/std
            >>> # 3  文4     Y   0.1   -1.0  (0.1-0.5)/std
            >>> # 4  文5     Y   0.9    1.0  (0.9-0.5)/std

        示例3 - 处理空值和常数值:
            >>> # 包含'nil'、空字符串、NaN的数据
            >>> data = {
            ...     'text': ['文1', '文2', '文3', '文4'],
            ...     'label': ['X', 'X', 'X', 'X'],
            ...     'score': [0.5, 0.5, 'nil', '']
            ... }
            >>> df = pd.DataFrame(data)
            >>>
            >>> # 计算z-score（常数值的std为0，z-score返回0）
            >>> result = GroupDeal.label_score_transform(
            ...     df,
            ...     group_key='label',
            ...     score_col='score',
            ...     transform_type='zscore'
            ... )
            >>> print(result)
            >>> #   text label  score z_score
            >>> # 0  文1     X   0.5       0  # std=0，返回0
            >>> # 1  文2     X   0.5       0  # std=0，返回0
            >>> # 2  文3     X  nan      -  # 空值被替换为-
            >>> # 3  文4     X  nan      -  # 空值被替换为-

        示例4 - 多列分组计算z-score:
            >>> import pandas as pd
            >>> from tpf.data.utils import GroupDeal
            >>>
            >>> # 创建示例数据：多个查询文本和相似标签组合
            >>> data = {
            ...     'query_text': ['查询1', '查询1', '查询1', '查询2', '查询2', '查询2'],
            ...     'sim_label': ['A', 'A', 'B', 'A', 'B', 'B'],
            ...     'score': [0.8, 0.6, 0.7, 0.9, 0.5, 0.4]
            ... }
            >>> df = pd.DataFrame(data)
            >>>
            >>> # 按(query_text, sim_label)两列分组计算z-score
            >>> # 分组1: (查询1, A) -> [0.8, 0.6] -> 均值=0.7 -> z=[1.0, -1.0]
            >>> # 分组2: (查询1, B) -> [0.7] -> 均值=0.7, std=0 -> z=[0]
            >>> # 分组3: (查询2, A) -> [0.9] -> 均值=0.9, std=0 -> z=[0]
            >>> # 分组4: (查询2, B) -> [0.5, 0.4] -> 均值=0.45 -> z=[1.0, -1.0]
            >>> result = GroupDeal.label_score_transform(
            ...     df,
            ...     group_key=['query_text', 'sim_label'],  # 多列分组
            ...     score_col='score',
            ...     transform_type='zscore',
            ...     score_col_new='score_zscore'
            ... )
            >>> print(result)
            >>> #   query_text sim_label  score  score_zscore
            >>> # 0      查询1         A    0.8          1.0  (0.8-0.7)/std
            >>> # 1      查询1         A    0.6         -1.0  (0.6-0.7)/std
            >>> # 2      查询1         B    0.7          0.0  # std=0，返回0
            >>> # 3      查询2         A    0.9          0.0  # std=0，返回0
            >>> # 4      查询2         B    0.5          1.0  (0.5-0.45)/std
            >>> # 5      查询2         B    0.4         -1.0  (0.4-0.45)/std
        """
        if score_col_new is None:
            score_col_new = f"{score_col}_{transform_type}"

        # 预处理：将score列转换为数值类型，并处理特殊空值
        # 将'nil'、'null'、空字符串等转换为NaN
        def clean_score(x):
            """清理分数值，将各种空值表示转换为NaN"""
            if pd.isna(x):
                return x
            if isinstance(x, str) and x.strip().lower() in ['nil', 'null', 'none', '', 'na', 'n/a']:
                return np.nan
            try:
                return float(x)
            except (ValueError, TypeError):
                return np.nan

        # 创建清理后的分数列（添加到DataFrame作为临时列）
        temp_col_name = '__temp_score_clean__'
        df[temp_col_name] = df[score_col].apply(clean_score)

        # # 确定分组键
        # if isinstance(group_key, list):
        #     # 多列分组
        #     grouper = group_key
        # else:
        #     # 单列分组
        #     grouper = group_key
        grouper = group_key

        if transform_type == 'zscore':
            # 特殊处理z-score：计算每组的均值和标准差
            def compute_zscore(group):
                """计算z-score，处理std=0的情况"""
                mean_val = group.mean()
                std_val = group.std()

                # 如果标准差为0或NaN，所有值的z-score设为0
                if pd.isna(std_val) or std_val == 0:
                    return pd.Series([0] * len(group), index=group.index)
                else:
                    return (group - mean_val) / std_val

            # 按组计算z-score
            if isinstance(grouper, list):
                # 多列分组
                df[score_col_new] = df[temp_col_name].groupby([df[col] for col in grouper]).transform(compute_zscore)
            else:
                # 单列分组
                df[score_col_new] = df[temp_col_name].groupby(grouper).transform(compute_zscore)
            # df[score_col_new] = df[temp_col_name].groupby(grouper).transform(compute_zscore)
        else:
            # 其他统计变换：使用pandas内置方法
            df[score_col_new] = df.groupby(grouper)[temp_col_name].transform(transform_type)

        # 删除临时列
        df.drop(columns=[temp_col_name], inplace=True)

        # 将NaN替换为0
        df[score_col_new] = df[score_col_new].fillna(0)

        return df
        
    
    
    @classmethod
    def topk_label_score_mean(cls, df, group_key='label',
                             score_col='score',
                             top_k=5,
                             score_col_new='mean_score',
                             keep_name='text'):
        """按标签分组，计算每个标签分数最高的前K个样本的均值分数

        功能说明：
        1. 按指定列（支持单列或多列）对数据进行分组
        2. 在每个分组内，按分数列（默认为score）降序排列，取前top_k个样本
        3. 计算这top_k个样本的分数均值
        4. 保留每个分组中分数最高的第一个样本的指定列（默认为text）
        5. 按均值分数降序排列返回结果

        Args:
            df (pd.DataFrame): 输入数据框，必须包含group_key和score_col列
            group_key (str or list): 分组键，支持单列字符串或多列列表
                - 单列: 'label' 或 ['label']
                - 多列: ['category', 'label'] 或 ['year', 'month', 'label']
            score_col (str): 分数列名，默认为'score'
            top_k (int): 每个分组取前K个高分样本，默认为5
            score_col_new (str): 新生成的均值分数列名，默认为'mean_score'
            keep_name (str): 从每个分组保留的列名（取top_k中第一个），默认为'text'

        Returns:
            pd.DataFrame: 结果数据框，包含以下列：
                - keep_name: 每个分组中分数最高的样本的指定列内容
                - 如果group_key是单列: 包含该列
                - 如果group_key是多列: 包含所有分组列
                - score_col_new: 前top_k个样本的均值分数
                按score_col_new降序排列

        示例1 - 单列分组:
            >>> import pandas as pd
            >>> from tpf.data.utils import GroupDeal
            >>>
            >>> # 创建示例数据
            >>> data = {
            ...     'text': ['文本1', '文本2', '文本3', '文本4', '文本5', '文本6'],
            ...     'label': ['A', 'A', 'A', 'B', 'B', 'B'],
            ...     'score': [0.9, 0.8, 0.7, 0.6, 0.5, 0.95]
            ... }
            >>> df = pd.DataFrame(data)
            >>>
            >>> # 计算每个标签前2个高分样本的均值分数
            >>> result = GroupDeal.topk_label_score_mean(
            ...     df,
            ...     group_key='label',
            ...     score_col='score',
            ...     top_k=2,
            ...     score_col_new='mean_score',
            ...     keep_name='text'
            ... )
            >>> print(result)
            >>> #    text label  mean_score
            >>> # 0  文本6     B       0.775  (0.95 + 0.6) / 2
            >>> # 1  文本1     A       0.850  (0.9 + 0.8) / 2

        示例2 - 多列分组:
            >>> import pandas as pd
            >>> from tpf.data.utils import GroupDeal
            >>>
            >>> # 创建多列分组示例数据
            data = {
                'text': ['文1', '文2', '文3', '文4', '文5', '文6', '文7', '文8'],
                'category': ['类别A', '类别A', '类别A', '类别A', '类别B', '类别B', '类别B', '类别B'],
                'label': ['X', 'X', 'Y', 'Y', 'X', 'X', 'Y', 'Y'],
                'score': [0.9, 0.8, 0.7, 0.6, 0.95, 0.85, 0.75, 0.65]
            }
            df = pd.DataFrame(data)
            >>>
            >>> # 按category和label两列分组，计算每组前2个高分样本的均值
            >>> result = GroupDeal.topk_label_score_mean(
            ...     df,
            ...     group_key=['category', 'label'],  # 多列分组
            ...     score_col='score',
            ...     top_k=2,
            ...     score_col_new='mean_score',
            ...     keep_name='text'
            ... )
            >>> print(result)
            >>> #   text category label  mean_score
            >>> # 0  文5      类别B     X      0.900  (0.95 + 0.85) / 2
            >>> # 1  文7      类别B     Y      0.700  (0.75 + 0.65) / 2
            >>> # 2  文1      类别A     X      0.850  (0.9 + 0.8) / 2
            >>> # 3  文3      类别A     Y      0.650  (0.7 + 0.6) / 2
        """
        # 统一处理group_key为列表格式
        if isinstance(group_key, str):
            group_keys = [group_key]
        else:
            group_keys = group_key if isinstance(group_key, list) else list(group_key)

        # 按标签分组，取每个标签分数最高的前K个样本，计算均值分数
        def process_group(x):
            """处理每个分组，取top_k并计算均值"""
            top_k_data = x.nlargest(top_k, score_col)
            result_dict = {
                keep_name: top_k_data[keep_name].iloc[0],  # 取分数最高的第一个样本的text
                score_col_new: top_k_data[score_col].mean()  # 计算前K个分数的均值
            }
            # 添加所有分组键
            for key in group_keys:
                result_dict[key] = x.name if len(group_keys) == 1 else x.name[group_keys.index(key)]
            return pd.Series(result_dict)

        # 使用多列分组
        df3 = df.groupby(group_keys).apply(
            process_group,
            include_groups=False
        ).reset_index(drop=True)

        # 按均值分数降序排列
        df3_sorted = df3.sort_values(score_col_new, ascending=False)
        return df3_sorted
        
    
    
    





