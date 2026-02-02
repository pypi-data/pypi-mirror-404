# 系统配置
import os
import torch

# 项目根路径（自动获取）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # config.py 所在目录
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # 往上一级才是整个项目根路径

print("BASE_DIR",BASE_DIR,)
global_log_path = "/tmp/tousu.log"

feature_sim_top_k=5
feature_label_top_k=3

model_vec_embedding = os.path.join(BASE_DIR, "models/bge-base-zh-v1.5")
model_path_rerank = os.path.join(BASE_DIR, "models/bge-reranker-large")
model_path_ms  = os.path.join(BASE_DIR, "models/ms-marco-MiniLM-L6-v2")
model_path_lr  = os.path.join(BASE_DIR, "models/tousu/lrv1.pkl")
model_eval_path= os.path.join(BASE_DIR, "models/tousu/lrv1.dict")
data_train_csv = os.path.join(BASE_DIR, "data/tmp/data_train.csv")
data_bm25_csv  = os.path.join(BASE_DIR, "data/tmp/data_bm25.csv") 
data_predict_3label = os.path.join(BASE_DIR, "data/tmp/data_predict_3label.csv")
data_predict_csv    = os.path.join(BASE_DIR, "data/tmp/data_predict.csv")
data_test_csv       = os.path.join(BASE_DIR, "data/tmp/data_test.csv")
data_eval_3label    = os.path.join(BASE_DIR, "data/tmp/data_eval_3label.csv")
model_save_dir      = os.path.join(BASE_DIR, "models/tousu")
best_prob_ks = 0 #0.6388，top3 label命中率为90%，三选一最低30%,与标签对比也不会有高于30%的准备率了


#--------------------------------------------------------------------
#--源数据 配置 开始 csv文件-------------------------------------------
#--------------------------------------------------------------------
#最开始的源数据文件，来自客户的文件路径
yuanshi_data_path = os.path.join(BASE_DIR, "data/data_new.csv")
yuanshi_label_path = os.path.join(BASE_DIR, "data/label_new.csv")

# 原始文件的列名
col1 = ['问题简述','银行编码一级分类',	'银行编码二级分类',	'银行编码三级分类',	'银行编码四级分类',	'银行编码五级分类',	'银行编码六级分类']
# 目标文件列名，代码处理固定的列名，与原始文件的列名一一对应
col2 = ['text','label_1','label_2','label_3','label_4','label_5','label_6']

# 原始label文件列名
col3 = ['银行编码一级分类','银行编码二级分类',	'银行编码三级分类',	'银行编码四级分类',	'银行编码五级分类',	'银行编码六级分类']
#目标label文件列名，代码处理固定的列名，与原始目标文件的列名一一对应
col4 = ['label_1','label_2','label_3','label_4','label_5','label_6']

tmp_data_file  = os.path.join(BASE_DIR, 'data/tmp/data.csv')
tmp_label_file = os.path.join(BASE_DIR, 'data/tmp/label.csv')

# 目标文件路径,这两个文件可以被插入，不可删除，会保留历史数据，读取时再去重
target_data_file  = os.path.join(BASE_DIR, 'data/data_saved.csv')
target_data_file2  = os.path.join(BASE_DIR, 'data/data_saved2.csv') #标签下text个数>2的数据
target_label_file = os.path.join(BASE_DIR, 'data/label_saved.csv')


# 脱敏后的数据文件，可删除
DESENSITIZED_COMPLAINTS_FILE = os.path.join(BASE_DIR, 'data/tmp/data1_tuomin.csv')

#--源数据 配置 结束 csv文件 --------------------------------------------------

# 模型路径
# 静态模型文件
LOCAL_BERT = os.path.join(BASE_DIR, 'models/bert_classifier')
VECTOR_MODEL_NAME = model_vec_embedding
RANK_MODEL_NAME   = model_path_rerank


# 动态生成的模型相关文件
RULE_ENGINE_PATH = os.path.join(BASE_DIR, 'models/saved/rules.json')
COMPLAINT_VECTOR_DB_PATH = os.path.join(BASE_DIR, 'models/saved/complaint_vector_db.pkl')
LABEL_VECTOR_DB_PATH = os.path.join(BASE_DIR, 'models/saved/label_vector_db.pkl')
BERT_MODEL_PATH = os.path.join(BASE_DIR, 'models/saved/bert_classifier')

#缓存路径
CACHE_PATH = os.path.join(BASE_DIR, 'data/cache')

#标签编码文件
LABLE_ENCODE_PATH = os.path.join(BASE_DIR, 'data/cache/label_encode.pkl')
# 训练/测试集脱敏数据缓存文件
TRAIN_DESENSITIZED_CACHE = os.path.join(BASE_DIR, 'data/cache/train_texts_desensitized.pkl')
TEST_DESENSITIZED_CACHE = os.path.join(BASE_DIR, 'data/cache/test_texts_desensitized.pkl')


# 相似度阈值 如果达不到这个值 启动分类模型 达到就先优先相似度
LABEL_SIMILARITY_THRESHOLD = 0.8
COMPLAINT_SIMILARITY_THRESHOLD = 0.8
TOP_K_SIMILAR = 15
top_k_rank = 1 
top_k_vector = TOP_K_SIMILAR
label_text_count_threshold = 10


# 模型参数
MAX_LENGTH = 128
BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 2e-5

# 聚类和采样参数
MAX_SAMPLES_PER_LABEL = 100  # 每个标签最多保留的样本数
CLUSTERING_METHOD = 'kmeans'  # 'kmeans' 或 'dbscan'
KMEANS_CLUSTERS_PER_LABEL = 10  # 每个标签的聚类数
DBSCAN_EPS = 0.3  # DBSCAN邻域半径
DBSCAN_MIN_SAMPLES = 5  # DBSCAN最小样本数


from tpf.conf import pc   
pc.set_log_path(global_log_path)

tmp_dir = os.path.join(BASE_DIR, 'data/tmp')
top_k_rank_csv = os.path.join(tmp_dir, 'top_k_rank.csv')
zh_core_web_trf=os.path.join(BASE_DIR, 'models/zh_core_web_trf-3.8.0/zh_core_web_trf/zh_core_web_trf-3.8.0')


max_text_len=100
max_label_len=80
batch_size = 16
d_model = 256
num_layers = 5
num_epochs = 1000
t5_model_path = os.path.join(BASE_DIR, 'models/t5_summary_en_ru_zh_base_2048')
# 自动设备检测配置 - 优先使用GPU，如果没有则使用CPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
target_data_summary = os.path.join(BASE_DIR, 'data/summary.csv')
use_summary = False
label_split1='-'
label_split2='->'

use_keyword = False
use_hanlp = False
quick_start = True # 如果已经存在向量库文件，则直接加载，不再从数据文件生成向量;反而每次都会从数据文件生成向量
