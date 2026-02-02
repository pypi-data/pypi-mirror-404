import os 
import joblib
# import torch 
from tpf.d1 import pkl_load,pkl_save 
from tpf.conf import pc 




class MLBase:
    def __init__(self,  
                 model_type='lr', 
                 model_version=2,  
                 model_save_dir='',
                 feature_cols=[],
                 log_path='ml.log',
                 **model_params):
        """机器学习模型训练预测方法封装
        
        - model_type:lr,lgbmc
        
        example:
        -------------------------------------------
        from tpf.mlib.modelbase import MLBase  
        X_train, X_test, y_train, y_test = MLBase.data_ruxianai()
        feature_cols = X_train.columns.tolist()

        ml = MLBase(
            model_type='lr',
            model_version=2,
            model_save_dir='/tmp/models',
            feature_cols=feature_cols,
            log_path='ml.log',
            max_iter=10000)

        model = ml.fit(X_train, y_train)
        y_probs = ml.predict_proba(model,X_test)
        ml.model_save(model) #默认文件中存储了其他相关信息

        # 测试模型保存和加载
        ml2 = MLBase()
        model = ml2.model_load(ml.model_save_path)
        print(ml2.model_save_path)  # '/tmp/models/lr_2.pkl'
        y_probs2 = ml.predict_proba(model,X_test)
        y_probs2[0]
        
        example-多版本加载:
        ---------------------------------------
        from tpf.mlib.modelbase import MLBase  
        X_train, X_test, y_train, y_test = MLBase.data_ruxianai()
        feature_cols = X_train.columns.tolist()
        
        ml = MLBase(log_path='ml.log', model_save_dir='/tmp/models')
        ml.set_model_msg(model_type='lr', model_version=2, feature_cols=feature_cols)
        ml.fit(X_train,y_train)
        ml.model_save()

        ml.set_model_msg(model_type='lr', 
                        model_version=3, 
                        feature_cols=feature_cols,
                        model_params={"max_iter":10000})
        ml.fit(X_train,y_train)
        ml.model_save()

        ml.set_model_msg(model_type='lgbmc', 
                        model_version=1, 
                        feature_cols=feature_cols)
        ml.fit(X_train,y_train)
        ml.model_save()

        ##或者，直接通过版本与类型加载到model_libs中
        ml = MLBase(log_path='ml.log', model_save_dir='/tmp/models')
        ml.model_load(model_type='lr', model_version=2)
        ml.model_load(model_type='lr', model_version=3)
        
        y_probs = ml.predict_proba(X_test, model_type='lr', model_version=2)
        y_probs[0]
        
        y_probs = ml.predict_proba(X_test, model_type='lr', model_version=2)
        y_probs[0]

        
        others:
        ----------------------------------
        from tpf.d1 import DataDeal as dtl
        train,test = dtl.data_split(X=data, y=data['match'], test_size=0.2, random_state=42)
        pc.lg(f"数据切分完成，训练集维度: {train.shape}, 测试集维度: {test.shape}")

        y_train = train[label_name]
        X_train = train.drop(columns=[label_name])

        y_test = test[label_name]
        X_test = test.drop(columns=[label_name])

        """
        self.model_type    = model_type 
        self.model_version = model_version   
        self.feature_cols  = feature_cols
        self.model_params  = model_params
        self.model_name    = f"{model_type}_{model_version}"
        self.model_save_dir  = model_save_dir
        self.model_save_path = os.path.join(model_save_dir, f"{self.model_name}.pkl")

        # 确保模型保存目录存在
        save_dir = os.path.dirname(self.model_save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
    
        self._lgbm_name_list = ["LightGBM".lower(),"lgbm","LightGBM"]
        self._lgbmc_name_list = ["LGBMClassifier".lower(),"lgbmc"]
        self._svm_name_list = ["svm","svc","SVM"]
        self._lr_name_list = ["lr","logisticregression"]
        self.alg_types = self._lgbm_name_list+["lgbm","lgbmc","xgbc","catboost","copod","svm","svc","lr","LR","SVM","LightGBM","COPOD","LGBMClassifier","DLSeqOne","dlseqone","DLSEQONE","XGBClassifier","XGBClassifier".lower(), "CatBoostClassifier", "CatBoostClassifier".lower()]

        if log_path is not None:
            pc.set_log_path(log_path)
        self.model_libs = {}
    def set_model_msg(self, model_type, model_version, feature_cols=None, model_params=None):
        self.model_type    = model_type
        self.model_version = model_version 
        self.model_name    = f"{model_type}_{model_version}"
        if feature_cols is not None:
            self.feature_cols  = feature_cols 
        if model_params is not None:
            self.model_params  = model_params 
        self.model_save_path = os.path.join(self.model_save_dir, f"{self.model_name}.pkl")
    
    def get_model(self,model_type,model_version):
        model_name = f"{model_type}_{model_version}" 
        if model_name not in self.model_libs:
            self.model_load(model_type = model_type, model_version = model_version)
        model,model_msg = self.model_libs.get(f"{model_type}_{model_version}") 
        return model,model_msg
        
    
    def fit(self, X, y, X_valid=None, y_valid=None, cat_features=None):
        """
        example:
        -------------------------------------------
        ml = MLBase(
            model_type='lr',
            model_version=2,
            feature_cols=use_cols,
            log_path=None,
            model_save_dir='/tmp/models',
            max_iter=10000)

        model = ml.fit(X_train, y_train)
        ml.model_save()
        y_probs = ml.predict_proba(X_test)

        #模型的训练，就是特征列与参数的不同，如此形成了版本的不同，另外就是模型的类型不同
        ml.set_model_msg(
            model_type='lr',
            model_version=3,
            feature_cols=use_cols,
            model_params={"max_iter":10000})

        model = ml.fit(X_train, y_train)
                
        """
        X = self.getX(X)
        model = None
        # 训练预测
        if self.model_type.lower() in self._lr_name_list:
            from sklearn.linear_model import LogisticRegression
            if self.model_params is None:
                self.model_params = {}
            model = LogisticRegression(**self.model_params)
            model.fit(X=X,y=y)
            
        if self.model_type.lower() in self._lgbmc_name_list:
            from tpf.mlib.tree import lgbmc_02
            if self.model_params is None:
                self.model_params = {}
            model = lgbmc_02(X, y, 
                            X_valid=X_valid, y_valid=y_valid, 
                            cat_features=cat_features,params=self.model_params)
            
            
        self.model = model 
        self.model_libs[self.model_name] = model,self.model_msg()
        return model  
    
    
    def predict(self, X, model=None, model_type=None, model_version=None):
        """
        获取预测结果
        """
 
        if model is None and model_type is None:
            model = self.model
            X = self.getX(X)
        elif model_type is not None and model_version is not None:
            model,model_msg = self.get_model(model_type=model_type, model_version=model_version)
            X = X[model_msg['feature_cols']]  #如果从文件中加载则使用文件中的列
        y_pred = None
        # 使用测试集进行预测
        if self.model_type.lower() in self._lr_name_list or self.model_type.lower() in self._lgbmc_name_list:
            y_pred = model.predict(X)     
        return y_pred 
    
    def predict_proba(self, X, model=None, model_type=None, model_version=None):
        """
        获取预测概率
        - 支持根据版本号获取相应模型；如果不指定则为当前模型
        """
        if model is None and model_type is None:
            model = self.model
            X = self.getX(X)
        elif model_type is not None and model_version is not None:
            model,model_msg = self.get_model(model_type=model_type, model_version=model_version)
            
            X = X[model_msg['feature_cols']]  #如果从文件中加载则使用文件中的列

        y_pred = None
        # 使用测试集进行预测
        if self.model_type.lower() in self._lr_name_list or self.model_type.lower() in self._lgbmc_name_list:
            y_pred = model.predict_proba(X)     
        return y_pred 
    
    def score(self, X, y, model=None, model_type=None, model_version=None):
        if model is None and model_type is None:
            model = self.model
            X = self.getX(X)
        elif model_type is not None and model_version is not None:
            model,model_msg = self.get_model(model_type=model_type, model_version=model_version)
            X = X[model_msg['feature_cols']]  #如果从文件中加载则使用文件中的列
        
        score = None  
        if self.model_type.lower() in self._lr_name_list:
            score = model.score(X=X,y=y)
        return score
    
    def precision_score(self, y_label, y_pred, reverse=False):
        """ 计算精确率
        - 计算预测为1的数据中真实为1的比例（精确率）,仅限二值分类问题
        
        """
        from sklearn.metrics import precision_score
        precision = precision_score(y_label, y_pred)
        # index=1
        # fenmu = (y_pred==index).sum()
        # fenzi = y_pred[(y_pred==index) & (y_label==index)].sum()
        if reverse == True:
            precision = 1-precision
        return round(precision,4)
    
    def recall_score(self, y_label, y_pred):
        from sklearn.metrics import recall_score
        recall = recall_score(y_label, y_pred)
        return round(recall,4)
    
    def set_model_version(self, model_version=2):
        self.model_version = model_version 
    
    def feature_names(self):
        """
        获取特征列名称,固定为升序排序
        """
        feature_cols = set(self.feature_cols)
        feature_cols = sorted(feature_cols)
        self.feature_cols = feature_cols
        return feature_cols
    
    def getX(self, X):
        return X[self.feature_names()]

    def model_msg(self):
        """
        获取模型信息字典
        Returns:
            dict: 包含模型类型、版本、特征列、参数等信息的字典
        """
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'model_version': self.model_version,
            'feature_cols': self.feature_names(),
            'feature_count': len(self.feature_cols),
            'model_params': self.model_params,
            'model_save_dir': self.model_save_dir,
            'model_save_path': self.model_save_path
        } 
    
    def model_save(self, model_save_path=None, model=None):
        """
        保存训练好的LR模型同时加载到model_libs
        Args:
            model: 训练好的模型对象
            model_save_path (str): 模型保存路径
        """
        if model_save_path is None:
            model_save_path = self.model_save_path
        if model is None:
            if self.model is None:
                raise Exception("模型对象为空，请先训练模型")
            else:
                model = self.model

        # import joblib
        # joblib.dump(model, model_save_path)
        self.model_libs[self.model_name] = model,self.model_msg()
        pkl_save(data=(model,self.model_msg()),file_path=model_save_path, use_joblib= True)
        pc.lg(f"LR模型已保存到: {model_save_path}")

    def model_load(self, model_save_path=None, 
                   model_save_dir=None, model_type=None, model_version=None):
        """
        加载训练好的模型并恢复模型元数据

        Args:
            model_save_path (str): 模型文件路径，可以是相对model_save_dir的路径，也可以是绝对路径
            only_load_model (bool): 是否仅加载模型对象，True时仅返回模型不更新实例属性
            model_save_dir (str): 模型保存目录，用于处理相对路径或目录迁移场景。
                                 如果为None，使用保存时的目录；如果指定，则更新为新的目录

        Returns:
            model: 加载的模型对象

        Raises:
            FileNotFoundError: 当模型文件不存在时抛出异常

        Note:
            - 加载时会自动恢复模型的元数据（类型、版本、特征列、参数等）
            - 如果model_save_path是相对路径，会自动与model_save_dir拼接
            - only_load_model=True时适用于仅需预测不需要更新元数据的场景
        """
        if model_save_path is None and model_version is None :
            model_save_path = self.model_save_path 
        elif model_type is not None and model_version is not None:
            self.model_name = model_type + "_" + str(model_version)
            if model_save_dir is not None:
                self.model_save_dir = model_save_dir
                model_save_path = os.path.join(model_save_dir, f"{self.model_name}.pkl")
            else:
                model_save_path = os.path.join(self.model_save_dir, f"{self.model_name}.pkl")
    
        # import joblib
        if not os.path.exists(model_save_path):
            raise FileNotFoundError(f"模型文件不存在: {model_save_path}")
        model, model_msg = pkl_load(file_path=model_save_path,use_joblib=True)
        self.model = model 
        
        # model = joblib.load(model_save_path)
        pc.lg(f"LR模型已从 {model_save_path} 加载")
        self.model_name = model_msg['model_name']
        self.model_type = model_msg['model_type']
        self.model_version = model_msg['model_version']
        self.feature_cols = model_msg['feature_cols']
        self.model_params = model_msg['model_params']
        if model_save_dir is None:
            model_save_dir = model_msg['model_save_dir']

        # 如果model_save_path是相对路径，则与model_save_dir拼接
        if model_save_path and not os.path.isabs(model_save_path):
            self.model_save_path = os.path.join(model_save_dir, model_save_path)
        else:
            self.model_save_path = model_save_path
            
        self.model_libs[self.model_name] = model,self.model_msg()

        return model
    
    @classmethod
    def data_split(cls, data, label_name, test_size=0.2, random_state=None, is_returnXy=True):
        """
        - data: 数据集,pandas数表，包含标签列
        - label_name:标签列名称,按此分组，如果拆分为Xy,会自动从X中删除lable_name列
        
        exmaples:
        -----------------------------------------
        X_train, X_test, y_train, y_test = MLBase.data_split(data=data, label_name='label', test_size=0.2, random_state=42)
        """
        from tpf.d1 import DataDeal as dtl
        train,test = dtl.data_split(X=data, y=data[label_name], test_size=test_size, random_state=random_state)
        pc.lg(f"数据切分完成，训练集维度: {train.shape}, 测试集维度: {test.shape}")
        if is_returnXy:
            y_train = train[label_name]
            X_train = train.drop(columns=[label_name])

            y_test = test[label_name]
            X_test = test.drop(columns=[label_name])
            return X_train, X_test, y_train, y_test
        else:
            return train, test

    
    
    
    
    @classmethod
    def data_ruxianai(cls):
        """
        example:
        -------------------------------------------
        from tpf.mlib.modelbase import MLBase  
        X_train, X_test, y_train, y_test = MLBase.data_ruxianai()
        
        """
        from sklearn.datasets import load_breast_cancer
        from sklearn.model_selection import train_test_split
        import pandas as pd

        # 1. 加载乳腺癌数据集
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = data.target
        pc.lg(f"数据集形状: {X.shape}, 标签分布: {pd.Series(y).value_counts().to_dict()}")

        # 2. 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        pc.lg(f"训练集: {X_train.shape}, 测试集: {X_test.shape}")
        return X_train, X_test, y_train, y_test
        

    @classmethod
    def show_lr(cls, model_save_dir='/tmp/models'):
        """
        LR算法在乳腺癌数据集上的完整示例：训练、预测、保存、加载
        Args:
            model_save_dir: 模型保存目录
        """
        from sklearn.datasets import load_breast_cancer
        from sklearn.model_selection import train_test_split
        import pandas as pd

        # 1. 加载乳腺癌数据集
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = data.target
        pc.lg(f"数据集形状: {X.shape}, 标签分布: {pd.Series(y).value_counts().to_dict()}")

        # 2. 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        pc.lg(f"训练集: {X_train.shape}, 测试集: {X_test.shape}")

        # 3. 创建MLModelBase实例（使用前5个特征作为示例）
        feature_cols = data.feature_names[:5].tolist()
        ml_model = cls(
            model_type='lr',
            model_version=1,
            feature_cols=feature_cols,
            model_save_dir=model_save_dir,
            max_iter=10000
        )

        # 4. 训练模型
        pc.lg("\n===== 开始训练模型 =====")
        model = ml_model.fit(X_train, y_train)
        pc.lg("模型训练完成")

        # 5. 模型评估
        train_score = ml_model.score(model, X_train, y_train)
        test_score = ml_model.score(model, X_test, y_test)
        pc.lg(f"训练集准确率: {train_score:.4f}")
        pc.lg(f"测试集准确率: {test_score:.4f}")

        # 6. 预测示例
        pc.lg("\n===== 预测示例 =====")
        y_pred = ml_model.perdict(model, X_test)
        y_pred_proba = ml_model.predict_proba(model, X_test)
        pc.lg(f"预测结果前5个: {y_pred[:5]}")
        pc.lg(f"预测概率前5个: {y_pred_proba[:5]}")

        # 7. 显示模型信息
        pc.lg("\n===== 模型信息 =====")
        model_info = ml_model.model_msg()
        for key, value in model_info.items():
            pc.lg(f"{key}: {value}")

        # 8. 保存模型
        pc.lg("\n===== 保存模型 =====")
        ml_model.model_save(model)
        pc.lg(f"模型已保存到: {ml_model.model_save_path}")

        # 9. 加载模型
        pc.lg("\n===== 加载模型 =====")
        loaded_model = ml_model.model_load()
        pc.lg("模型加载完成")

        # 10. 使用加载的模型进行预测验证
        y_pred_loaded = ml_model.perdict(loaded_model, X_test)
        test_score_loaded = ml_model.score(loaded_model, X_test, y_test)
        pc.lg(f"加载模型的测试集准确率: {test_score_loaded:.4f}")
        pc.lg(f"预测结果一致性: {(y_pred == y_pred_loaded).all()}")

        pc.lg("\n===== 示例完成 =====")
        return ml_model, model



class ModelBase:
    dl_name_list = ["dlseqone","seqonedl","seqone"]
    def __init__(self, pc = pc, log_path=None):
        if log_path is not None:
            pc.set_log_path(log_path)
    @classmethod
    def model_load(cls, model_path, model=None, params=None, alg_name=None):
        """深度学习参数文件以.dict保存 
        """
        if alg_name is not None and alg_name in ["seqone"]:
            from tpf.mlib.seq import SeqOne
            seq_len    = params["seq_len"]
            model = SeqOne(seq_len=seq_len, out_features=2)
        elif model_path.endswith(".dict"):
            import torch 
            if model is None:
                if "seqone" in model_path.lower():
                    from tpf.mlib.seq import SeqOne
                    seq_len    = params["seq_len"]
                    model = SeqOne(seq_len=seq_len, out_features=2)
            model.load_state_dict(torch.load(model_path,weights_only=False))
        else:
            model = pkl_load(file_path=model_path, use_joblib=True)
        return model

    @classmethod
    def model_save(cls,model, model_path, alg_name=None):
        if model_path.endswith(".dict") or (alg_name is not None and alg_name in cls.dl_name_list):
            import torch 
            torch.save(model.state_dict(), model_path)
        else:
            pkl_save(model, file_path=model_path, use_joblib=True)

