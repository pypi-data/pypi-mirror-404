from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

import os
import json
from openai import OpenAI

from tpf.llm.prompt import return_json1 
from tpf.llm.tools import Tools 
from tpf.llm.funcall import FuncCall

tools = Tools()

def chat(prompt_user, prompt_system=None, 
         response_format="text", 
         model='deepseek-r1:1.5b', 
         temperature=1, 
         base_url='http://localhost:11434/v1/',api_key='key',
         return_json=False):
    """大模型对话问答

    params
    --------------------------------
    - prompt_user:用户prompt 
    - prompt_system:系统prompt，，默认None 
    = response_format:'json_object'或'text'
    - model:模型路径，如果是ollama，可通过ollama list查看模型名称
    - temperature: 温度系数，默认1 
    - base_url：LLM http地址
    
    example 1 local 
    -------------------------------
    from tpf.llm import chat
    prompt = "你好"
    response = chat(prompt_user=prompt, 
                    prompt_system=None, 
                    response_format="text", 
                    model='deepseek-r1:1.5b', 
                    temperature=1, 
                    base_url='http://localhost:11434/v1/')
    print(response)
    
    
    
    example 2 online  
    -------------------------------
    import os
    from dotenv import load_dotenv  
    load_dotenv("/home/llm/conf/env.txt")  # 加载".env"文件 
    deepseek_base_url = os.getenv("deepseek_base_url")  
    deepseek_api_key = os.getenv("deepseek_api_key")  
    
    from tpf.llm import chat
    prompt = "你好"
    response = chat(prompt_user=prompt, 
                    prompt_system=None, 
                    model='deepseek-chat', 
                    temperature=1, 
                    base_url=deepseek_base_url,
                    api_key=deepseek_api_key,
                    return_json=True)
    response

    
    
    """
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,    #必需但可以随便填写
    )
    
    if return_json:
        output_format1 = return_json1()
        prompt_user = f"""
        {prompt_user}
        
        {output_format1}
        """
    
    if prompt_system is None:
        message = [{'role': 'user','content': prompt_user,}]
    else:
        message = [
            {
                "role": "system",
                "content": prompt_system  # 注入新知识
            },
            {
                "role": "user",
                "content": prompt_user  # 问问题
            },
        ]

    response = client.chat.completions.create(
        model=model,
        messages=message,
        temperature=temperature,   # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")
    
    content = response.choices[0].message.content
    if return_json:
        try:
            json_str = tools.get_json_str(content)
            json_dict = json.loads(json_str)
            is_parse_ok = True 
        except Exception as e:
            print(e)
            is_parse_ok = False 
            
        if is_parse_ok:
            return json_dict

    return content          # 返回模型生成的文本



class MyChat():
    def __init__(self, env_file=".env"):
        """
        初始化 MyChat 类，从环境配置文件加载各个 LLM 服务的连接信息

        参数配置说明:
        -----------
        env_file : str, optional (default=".env")
            - 环境变量配置文件路径
            - 如果指定的文件不存在，会自动尝试使用备用路径: "/wks/bigmodels/conf/env.txt"
            - 配置文件采用 .env 格式，每行一个配置，格式为: KEY=VALUE

        环境变量命名规范:
        ---------------
        所有 LLM 服务的配置遵循统一的命名模式:
        - f"{llm_name}_base_url" : LLM 服务的 API 地址
        - f"{llm_name}_api_key" : LLM 服务的 API 密钥

        支持的 LLM 服务:
        ----------------
        1. DeepSeek (深度求索)
           - deepseek_base_url: DeepSeek API 服务地址
           - deepseek_api_key: DeepSeek API 访问密钥

        2. OpenAI
           - OPENAI_API_KEY: OpenAI API 密钥
           - OPENAI_BASE_URL: OpenAI API 服务地址（可选，用于代理或自定义端点）

        3. 千帆 (百度文心)
           - qianfan_base_url: 千帆平台 API 地址
           - qianfan_api_key: 千帆平台访问密钥

        4. 通义千问 (阿里云)
           - DASHSCOPE_API_KEY: 通义千问 API 密钥
           - DASHSCOPE_BASE_URL: 通义千问服务地址

        实例变量说明:
        -------------
        self._deepseek_base_url : str
            - DeepSeek API 的 base URL
            - 用于调用 deepseek-chat、deepseek-reasoner 等模型
            - 示例: "https://api.deepseek.com" 或本地服务地址

        self._deepseek_api_key : str
            - DeepSeek API 的访问密钥
            - 必需参数，用于身份验证
            - 可在 DeepSeek 开放平台申请

        self.OPENAI_API_KEY : str
            - OpenAI 的 API 密钥
            - 用于调用 GPT-4、GPT-3.5 等模型
            - 可在 https://platform.openai.com/api-keys 申请

        self.OPENAI_BASE_URL : str
            - OpenAI API 的 base URL（可选）
            - 默认为 "https://api.openai.com/v1"
            - 可配置为代理地址或其他兼容端点

        self._qianfan_base_url : str
            - 百度千帆平台的 API 地址
            - 用于调用文心系列模型（ernie-4.5-turbo 等）

        self._qianfan_api_key : str
            - 百度千帆平台的 API 密钥
            - 包含认证信息的密钥字符串

        self._DASHSCOPE_API_KEY : str
            - 阿里云通义千问的 API 密钥
            - 用于调用 qwen 系列模型

        self._DASHSCOPE_BASE_URL : str
            - 阿里云通义千问的服务地址
            - 默认为 DashScope API 端点

        self.fc : FuncCall
            - 函数调用功能模块
            - 用于实现模型的 Function Calling 能力
            - 支持自定义函数注册和调用

        使用示例:
        --------
        >>> # 使用默认配置文件
        >>> chat = MyChat()
        >>>
        >>> # 指定配置文件
        >>> chat = MyChat(env_file="/path/to/custom.env")
        >>>
        >>> # 调用不同模型
        >>> result = chat.deepseek("你好")
        >>> result = chat.tongyi("介绍一下Python")
        >>> result = chat.qianfan("什么是机器学习")

        配置文件示例 (.env):
        -----------------------
        # DeepSeek 配置
        deepseek_base_url=https://api.deepseek.com
        deepseek_api_key=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # OpenAI 配置
        OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        OPENAI_BASE_URL=https://api.openai.com/v1

        # 千帆配置
        qianfan_base_url=https://aip.baidubce.com/rpc/2.0/ai_custom/v1
        qianfan_api_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        # 通义千问配置
        DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1

        """
        # 检查配置文件是否存在，不存在则使用备用路径
        if not os.path.exists(env_file):
            env_file = "/wks/app/conf/env.txt"

        # 加载环境变量配置文件
        load_dotenv(env_file)  # 使用 dotenv 库加载 .env 文件到环境变量

        # 从环境变量中读取各个 LLM 服务的配置信息
        self._deepseek_base_url = os.getenv("deepseek_base_url")
        self._deepseek_api_key  = os.getenv("deepseek_api_key")
        self.OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
        self.OPENAI_BASE_URL    = os.getenv("OPENAI_BASE_URL")
        self._qianfan_base_url  = os.getenv("qianfan_base_url")
        self._qianfan_api_key   = os.getenv("qianfan_api_key")
        self._DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
        self._DASHSCOPE_BASE_URL= os.getenv("DASHSCOPE_BASE_URL")
        self._ARK_API_KEY       = os.getenv("ARK_API_KEY")
        self._ARK_BASE_URL      = os.getenv("ARK_BASE_URL")
        
        self._API_KEY           = os.getenv("API_KEY")
        self._BASE_URL          = os.getenv("BASE_URL")
        
        self._glm_base_url      = os.getenv("glm_base_url")
        self._glm_api_key       = os.getenv("glm_api_key")


        # 初始化函数调用模块
        self.fc = FuncCall() 
        
    def set_local_model(self,model_name_list):
        """添加本地ollama模型名称"""
        for model_name in model_name_list:
            self.fc.set_ollama_local_model(model_name)
        
    def get_local_model(self):
        return self.fc.ollama_local_model_name
        
    def func_call(self,query,
                  model_list=["gpt-4o-mini","gpt-4o",'DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'],
                   func_index=3, answer_index=2,base_url='http://localhost:11434/v1/',api_key='key'):
        res = self.fc.chat(query=query, 
                     model_list=model_list, func_index=func_index, answer_index=answer_index,base_url=base_url,api_key=api_key)

        return res 
    
    def request(self, prompt_user=None, models=[], prompt_system=None,
                message=None, temperature=0.1, 
                base_url=None, api_key=None, 
                **params):
        """通用请求方法，支持自定义 OpenAI 兼容接口

        参数说明:
        ---------
        prompt_user : str, optional
            用户提示词
        models : list or str
            模型名称列表或单个模型名称
        prompt_system : str, optional
            系统提示词
        message : list, optional
            已构建的消息列表，如果提供则忽略 prompt_user 和 prompt_system
        temperature : float, default=0.1
            温度参数，控制输出随机性
        base_url : str, optional
            API 基础 URL，默认从环境变量读取
        api_key : str, optional
            API 密钥，默认从环境变量读取
        **params : dict
            其他请求参数，包括：
            - n : int, 生成候选数量，默认 1
            - stream : bool, 是否流式输出，默认 False
            - presence_penalty : float, 存在惩罚，默认 0
            - frequency_penalty : float, 频率惩罚，默认 0
            - max_tokens : int, 最大生成 token 数
            - top_p : float, 核采样参数
            等其他 OpenAI API 支持的参数

        返回值:
        -------
        str : 模型响应内容

        使用示例:
        --------
        >>> chat = MyChat()
        >>>
        >>> # 示例 1: 对应 curl 请求 - Agentar-Scale-SQL 模型
        >>> # curl -H "Accept:application/json" \\
        >>> # -H "Content-type:application/json" \\
        >>> # -X POST \\
        >>> # -d'{"model":"Agentar-Scale-SQL", \\
        >>> #     "messages":[{"role":"user","content":"hello"}], \\
        >>> #     "temperature":0.7, "n":1, "stream": false, \\
        >>> #     "presence_penalty":0, "frequency_penalty": 0}' \\
        >>> # http://36.114.30.47:30065/v1/chat/completions
        >>>
        response = chat.request(
            prompt_user="hello",
            models=["Agentar-Scale-SQL"],
            base_url="http://36.114.30.47:30065/v1",
            temperature=0.7,
            n=1,
            stream=False,
            presence_penalty=0,
            frequency_penalty=0
        )
        >>>
        >>> # 示例 2: 使用环境变量配置的 base_url 和 api_key
        >>> response = chat.request(
        ...     prompt_user="你好",
        ...     models=["Agentar-Scale-SQL"]
        ... )
        >>>
        >>> # 示例 3: DeepSeek API 请求
        >>> # curl https://api.deepseek.com/chat/completions \\
        >>> #   -H "Content-Type: application/json" \\
        >>> #   -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \\
        >>> #   -d '{"model": "deepseek-chat", \\
        >>> #       "messages": [ \\
        >>> #         {"role": "system", "content": "You are a helpful assistant."}, \\
        >>> #         {"role": "user", "content": "Hello!"} \\
        >>> #       ], \\
        >>> #       "stream": false}'
        >>>
        response = chat.request(
            prompt_user="Hello!",
            models=["deepseek-chat"],
            prompt_system="You are a helpful assistant.",
            base_url="https://api.deepseek.com",
            api_key="your-deepseek-api-key",
            stream=False
        )
        >>>
        >>> # 示例 4: 通义千问 API 请求
        >>> # curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
        >>> # -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
        >>> # -H "Content-Type: application/json" \
        >>> # -d '{"model": "qwen-plus", \
        >>> #     "messages": [ \
        >>> #         {"role": "system", "content": "You are a helpful assistant."}, \
        >>> #         {"role": "user", "content": "你是谁？"} \
        >>> #     ]}'
        >>>
        response = chat.request(
            prompt_user="你是谁？",
            models=["qwen-plus"],
            prompt_system="You are a helpful assistant.",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="your-dashscope-api-key"
        )
        >>>
        >>> # 示例 5: 带系统提示词
        >>> response = chat.request(
        ...     prompt_user="介绍一下 Python",
        ...     models=["gpt-4o"],
        ...     prompt_system="你是一个专业的编程助手",
        ...     temperature=0.7,
        ...     n=1,
        ...     stream=False,
        ...     presence_penalty=0,
        ...     frequency_penalty=0
        ... )
        """
        import requests

        if isinstance(models,list):
            if len(models)==0:
                raise Exception('请输入模型名称，首个元素为要使用的模型')
            model = models[0]
        else:
            model = models

        if message is None:
            if prompt_system is None:
                message = [{'role': 'user','content': prompt_user,}]
            else:
                message = [
                    {
                        "role": "system",
                        "content": prompt_system  # 注入新知识
                    },
                    {
                        "role": "user",
                        "content": prompt_user  # 问问题
                    },
                ]

        # 如果没有指定 base_url，使用环境变量中的默认值
        if base_url is None:
            base_url = self._BASE_URL

        # 如果没有指定 api_key，使用环境变量中的默认值
        if api_key is None:
            api_key = self._API_KEY
            


        # 验证必要参数
        if not base_url:
            raise Exception('请提供 base_url 参数或在环境变量中设置 BASE_URL')

        # 构建 API URL
        # 移除末尾的斜杠（如果有）
        base_url = base_url.rstrip('/')
        # 确保以 /v1 结尾
        if not base_url.endswith('/v1'):
            if not base_url.endswith('/v1/'):
                base_url = f"{base_url}/v1"

        url = f"{base_url}/chat/completions"

        # 构建请求体
        # 默认参数
        # default_params = {
        #     'n': 1,
        #     'stream': False,
        #     'presence_penalty': 0,
        #     'frequency_penalty': 0,
        # }

        # 合并用户提供的参数（会覆盖默认值）
        # request_params = params

        # 完整的请求数据
        data = {
            "model": model,
            "messages": message,
            "temperature": temperature,
            **params
        }

        # 请求头
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
        }

        # 如果提供了 api_key，添加到请求头
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            # 发送 POST 请求
            response = requests.post(url, headers=headers, json=data, timeout=120)

            # 检查响应状态
            if response.status_code == 200:
                result = response.json()

                # 提取并返回响应内容
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"响应格式错误: {result}")
            else:
                raise Exception(f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}")

        except requests.exceptions.Timeout:
            raise Exception(f"请求超时: {url}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求异常: {str(e)}")

    def tongyi(self, prompt_user,
                prompt_system=None,
                models=['qwen3-coder-plus',"qwen-plus"],
                temperature=0,
                return_json=True):
        response = chat(prompt_user=prompt_user,
                prompt_system=prompt_system,
                model=models[0],
                temperature=temperature,
                base_url=self._DASHSCOPE_BASE_URL,
                api_key=self._DASHSCOPE_API_KEY,
                return_json=return_json)
        return  response

    def tongyi_func_call(self, query, model_list=['qwen3-coder-plus','qwen-max','qwen-plus','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'],
             func_index=0, answer_index=None, use_custom_func=True,
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list,
                            func_index=func_index, answer_index=answer_index,
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._DASHSCOPE_BASE_URL,api_key=self._DASHSCOPE_API_KEY)
                return response
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list,
                    func_index=func_index,
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._DASHSCOPE_BASE_URL,api_key=self._DASHSCOPE_API_KEY)

        ans_model = model_list[func_index]
        response = self.tongyi(prompt_user=prompt_answer,
            prompt_system=prompt_system,
            models=[ans_model],
            temperature=0,
            return_json=True)

        return response
 
    def tongyi_image(self, prompt, outdir=None,
                     models=["wan2.6-t2i", "qwen-image-max", "qwen-image", "z-image-turbo","qwen-image-plus-2026-01-09"],
                     size="1024*1024",
                     url = None,
                     negative_prompt=None,
                     prompt_extend=True,
                     watermark=False,
                     max_retries=3,
                     timeout=120):
        """
        通义千问图像生成，支持自动下载到本地目录

        参数说明:
        --------
        prompt : str
            - 图像生成提示词，描述想要生成的图片内容
        outdir : str, optional (default=None)
            - 图片保存目录路径
            - 如果为 None，只返回图片 URL，不下载
            - 如果指定路径，会自动下载图片到该目录
            - 如果目录不存在，会自动创建
        model : str, optional (default="qwen-image-max")
            - 使用的图像生成模型
            - qwen-image-max: 通义千问最强图像生成模型
            - qwen-image-v1: 通义千问图像生成模型 V1
        size : str, optional (default="1024*1024")
            - 图片尺寸，格式: "宽度*高度"
            - 支持的尺寸: "1024*1024", "1664*928", "1920*1080", "720*1280" 等
            - 注意使用星号 * 而非字母 x
        negative_prompt : str, optional (default=None)
            - 负面提示词，描述不希望出现的内容
            - 默认: "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。"
        prompt_extend : bool, optional (default=True)
            - 是否自动扩展提示词以提升生成质量
        watermark : bool, optional (default=False)
            - 是否添加水印
        max_retries : int, optional (default=3)
            - 最大重试次数
        timeout : int, optional (default=120)
            - 请求超时时间（秒）

        返回值:
        -------
        tuple : (url, img_save_path)
            - url: 图片的 URL 地址（字符串）
            - img_save_path: 图片保存的本地完整路径（字符串），如果未下载则为 None

        使用示例:
        --------
        >>> chat = MyChat()
        >>>
        >>> # 示例1: 只生成图片，不下载
        >>> url, path = chat.tongyi_image("一只可爱的小猫")
        >>> print(f"图片URL: {url}")
        >>>
        >>> # 示例2: 生成并下载到指定目录
        >>> url, path = chat.tongyi_image(
        ...     prompt="美丽的风景画",
        ...     outdir="./images"
        ... )
        >>>
        >>> # 示例3: 使用自定义尺寸和负面提示词
        >>> url, path = chat.tongyi_image(
        ...     prompt="科技感城市夜景",
        ...     outdir="./downloads/posters",
        ...     size="1920*1080",
        ...     negative_prompt="模糊，低质量"
        ... )

        注意事项:
        --------
        - 下载的图片文件名会使用时间戳格式：tongyi_YYYYMMDD_HHMMSS.png
        - 确保有写入权限到指定的目录
        - 下载失败会打印错误信息，但不会抛出异常
        - 通义千问图像生成 API 参考: https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-wanxiang-apidescription
        """
        import os
        import time
        import requests

        # 通义千问图像生成API端点
        if url is None:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
            
        # 从环境变量获取API密钥
        api_key = self._DASHSCOPE_API_KEY

        # 验证必要参数
        if not api_key:
            print(f"[通义图像] ✗ 错误: 未配置 DASHSCOPE API 密钥")
            print(f"[通义图像] 请在环境变量中设置: DASHSCOPE_API_KEY")
            return None, None

        # 设置默认负面提示词
        if negative_prompt is None:
            negative_prompt = "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。"

        # 请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        if isinstance(models, list):
            model = models[0]
        else:
            model = models 
        
        # 请求体
        data = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
                "size": size
            }
        }

        img_save_path = None

        # 重试机制
        for retry in range(max_retries):
            try:
                print(f"[通义图像生成] 尝试: {retry + 1}/{max_retries} | Model: {model}")
                print(f"[通义图像生成] URL: {url}")
                print(f"[通义图像生成] Size: {size}")
                print(f"[通义图像生成] Prompt 长度: {len(prompt)} 字符")
                print(f"[通义图像生成] 超时设置: {timeout}秒")

                response = requests.post(url, headers=headers, json=data, timeout=timeout)

                print(f"[通义图像生成] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    print(f"[通义图像生成] ✓ 模型 {model} 生成成功！")
                    result = response.json()

                    # 提取图片URL
                    # 通义千问的响应格式: {"output": {"choices": [{"message": {"content": [{"image": "..."}]}}]}}
                    image_url = None
                    if 'output' in result and 'choices' in result['output'] and len(result['output']['choices']) > 0:
                        choices = result['output']['choices'][0]
                        if 'message' in choices and 'content' in choices['message'] and len(choices['message']['content']) > 0:
                            content = choices['message']['content'][0]
                            if 'image' in content:
                                image_url = content['image']
                                print(f"[通义图像生成] 图片URL: {image_url}")

                    if image_url:
                        # 如果指定了输出目录，自动下载图片
                        if outdir is not None:
                            if outdir.strip() == "":
                                outdir = "./"

                            try:
                                # 创建目录（如果不存在）
                                os.makedirs(outdir, exist_ok=True)
                                print(f"[通义图像下载] 输出目录: {outdir}")

                                # 生成文件名：tongyi_时间戳.png
                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                filename = f"tongyi_{timestamp}.png"
                                filepath = os.path.join(outdir, filename)

                                print(f"[通义图像下载] 文件名: {filename}")
                                print(f"[通义图像下载] 完整路径: {os.path.abspath(filepath)}")
                                print(f"[通义图像下载] 正在从 URL 下载图片...")

                                # 下载图片
                                img_response = requests.get(image_url, timeout=60)

                                if img_response.status_code == 200:
                                    with open(filepath, 'wb') as f:
                                        f.write(img_response.content)
                                    file_size = os.path.getsize(filepath)
                                    img_save_path = os.path.abspath(filepath)
                                    print(f"[通义图像下载] ✓ 保存成功!")
                                    print(f"[通义图像下载] ✓ 文件路径: {img_save_path}")
                                    print(f"[通义图像下载] ✓ 文件大小: {file_size / 1024:.2f} KB")
                                else:
                                    print(f"[通义图像下载] ✗ 下载失败: HTTP {img_response.status_code}")

                            except Exception as e:
                                print(f"[通义图像下载] ✗ 下载异常: {str(e)}")
                                # 即使下载失败，也返回 URL

                        return image_url, img_save_path
                    else:
                        print(f"[通义图像生成] ✗ 响应格式错误")
                        print(f"[通义图像生成] 响应内容: {result}")
                        return None, None

                else:
                    print(f"[通义图像生成] ✗ HTTP {response.status_code}")
                    print(f"[通义图像生成] 错误详情: {response.text[:200]}")

                    # 如果是客户端错误（4xx），不需要重试
                    if 400 <= response.status_code < 500:
                        print(f"[通义图像生成] 提示: 客户端错误，停止重试")
                        return None, None

            except requests.exceptions.Timeout as e:
                print(f"[通义图像生成] ✗ 超时: 第 {retry + 1} 次尝试超时")
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5  # 递增等待时间：5s, 10s, 15s
                    print(f"[通义图像生成] 等待 {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"[通义图像生成] 放弃: 已达最大重试次数")

            except requests.exceptions.RequestException as e:
                print(f"[通义图像生成] ✗ 请求异常: {str(e)}")
                if retry < max_retries - 1:
                    print(f"[通义图像生成] 5秒后重试...")
                    time.sleep(5)
                else:
                    print(f"[通义图像生成] 放弃: 已达最大重试次数")

        return None, None 
    
    def qianfan(self, prompt_user, 
                prompt_system=None, 
                models=['ernie-4.5-turbo-128k','ernie-4.5-turbo-vl','ernie-4.0-turbo-8k'], 
                temperature=0, 
                return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - temperature：[0,1]
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        response = chat(prompt_user=prompt_user, 
                prompt_system=prompt_system, 
                model=models[0], 
                temperature=temperature, 
                base_url=self._qianfan_base_url,
                api_key=self._qianfan_api_key,
                return_json=return_json)
        return  response
    def qianfan_func_call(self, query, model_list=['ernie-4.5-turbo-128k','ernie-4.5-turbo-vl','ernie-4.0-turbo-8k','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=None, use_custom_func=True, 
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._qianfan_base_url,api_key=self._qianfan_api_key)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._qianfan_base_url,api_key=self._qianfan_api_key)

        ans_model = model_list[func_index]
        response = self.qianfan(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    def deepseek(self, prompt_user, 
                prompt_system=None, 
                models=['deepseek-chat','deepseek-reasoner'], 
                temperature=0, 
                return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - temperature：[0,1]
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        response = chat(prompt_user=prompt_user, 
                prompt_system=prompt_system, 
                model=models[0], 
                temperature=temperature, 
                base_url=self._deepseek_base_url,
                api_key=self._deepseek_api_key,
                return_json=return_json)
        return  response
    
    def deepseek_func_call(self, query, model_list=['deepseek-chat','deepseek-reasoner','DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=None, use_custom_func=True, 
             output_format=None):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format,
                            base_url=self._deepseek_base_url,api_key=self._deepseek_api_key)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format,
                    base_url=self._deepseek_base_url,api_key=self._deepseek_api_key)

        ans_model = model_list[func_index]
        response = self.deepseek(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    def text2image(self, prompt, 
                base_url,
                api_key,
                outdir=None,
                models=['doubao-seedream-4-5-251128'],
                size="2K",
                response_format="url",
                ):
        """
        豆包图像生成，支持自动下载到本地目录

        参数说明:
        --------
        prompt : str
            - 图像生成提示词，描述想要生成的图片内容
        outdir : str, optional (default=None)
            - 图片保存目录路径
            - 如果为 None，只返回图片 URL，不下载
            - 如果指定路径，会自动下载图片到该目录
            - 如果目录不存在，会自动创建
        models : list, optional (default=['doubao-seedream-4-5-251128'])
            - 模型列表，默认使用第一个模型
            - 可通过调整顺序来切换模型
        size : str, optional (default="2K")
            - 图片尺寸，如 "2K", "1024x1024" 等
        response_format : str, optional (default="url")
            - 返回格式，通常为 "url"

        返回值:
        -------
        str : 图片的 URL 地址
            - 如果 outdir 为 None，只返回 URL
            - 如果 outdir 不为 None，下载图片后仍返回 URL

        使用示例:
        --------
        >>> chat = MyChat()
        >>>
        >>> # 示例1: 只生成图片，不下载
        >>> url = chat.doubao_image("一只可爱的小猫")
        >>> print(f"图片URL: {url}")
        >>>
        >>> # 示例2: 生成并下载到指定目录
        >>> url = chat.doubao_image(
        ...     prompt="美丽的风景画",
        ...     outdir="./images"
        ... )
        >>>
        >>> # 示例3: 使用自定义文件名
        >>> import os
        >>> outdir = "./downloads/posters"
        >>> url = chat.doubao_image("科技感城市夜景", outdir=outdir)

        注意事项:
        --------
        - 下载的图片文件名会使用时间戳格式：doubao_YYYYMMDD_HHMMSS.png
        - 确保有写入权限到指定的目录
        - 下载失败会打印错误信息，但不会抛出异常
        """
        import os
        import time
        import requests

        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        print(f"[豆包图像生成] Model: {models[0]}")
        print(f"[豆包图像生成] Prompt: {prompt[:50]}...")
        print(f"[豆包图像生成] Size: {size}")

        imagesResponse = client.images.generate(
            model=models[0],
            prompt=prompt,
            size=size,
            response_format=response_format,
            extra_body={
                "watermark": True,  # 启用水印
            },
        )

        url = imagesResponse.data[0].url

        img_save_path = None 
        # 如果指定了输出目录，自动下载图片
        if outdir is not None :
            if outdir.strip()=="":
                outdir ="./"
            try:
                # 创建目录（如果不存在）
                os.makedirs(outdir, exist_ok=True)
                print(f"outdir: {outdir}")

                # 生成文件名：doubao_时间戳.png (格式: doubao_20260112_164803.png)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"img_{timestamp}.png"
                filepath = os.path.join(outdir, filename)


                # 下载图片
                response = requests.get(url, timeout=60)
                img_save_path = os.path.abspath(filepath)
                print(img_save_path)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    file_size = os.path.getsize(filepath)
                    
                    print(f"[图像下载] ✓ 保存成功!")
                    print(f"[图像下载] ✓ 文件路径: {img_save_path}")
                    print(f"[图像下载] ✓ 文件大小: {file_size / 1024:.2f} KB")
                else:
                    print(f"[图像下载] ✗ 下载失败: HTTP {response.status_code}")

            except Exception as e:
                print(f"[图像下载] ✗ 下载异常: {str(e)}")
                # 即使下载失败，也返回 URL

        return url,img_save_path
    
    
    def glm_image(self, prompt, outdir=None,
                  models=["glm-image", "cogview-3"],
                  size="1024x1024",
                  max_retries=3,
                  timeout=120):
        """
        智谱AI图像生成，支持自动下载到本地目录

        参数说明:
        --------
        prompt : str
            - 图像生成提示词，描述想要生成的图片内容
        outdir : str, optional (default=None)
            - 图片保存目录路径
            - 如果为 None，只返回图片 URL，不下载
            - 如果指定路径，会自动下载图片到该目录
            - 如果目录不存在，会自动创建
        models : list, optional (default=['glm-image', 'cogview-3'])
            - 模型列表，优先使用第一个
            - 可通过调整顺序来切换模型
            - glm-image: 智谱AI最新图像生成模型
            - cogview-3: 智谱AI CogView-3 模型
        size : str, optional (default="2K")
            - 图片尺寸，如 "2K", "1024x1024" 等
            - 智谱AI支持的尺寸: "1024x1024", "768x768", "512x512"
        max_retries : int, optional (default=3)
            - 最大重试次数
        timeout : int, optional (default=120)
            - 请求超时时间（秒）

        返回值:
        -------
        tuple : (url, img_save_path)
            - url: 图片的 URL 地址（字符串）
            - img_save_path: 图片保存的本地完整路径（字符串），如果未下载则为 None

        使用示例:
        --------
        >>> chat = MyChat()
        >>>
        >>> # 示例1: 只生成图片，不下载
        >>> url, path = chat.glm_image("一只可爱的小猫")
        >>> print(f"图片URL: {url}")
        >>>
        >>> # 示例2: 生成并下载到指定目录
        >>> url, path = chat.glm_image(
        ...     prompt="美丽的风景画",
        ...     outdir="./images"
        ... )
        >>>
        >>> # 示例3: 使用自定义模型和尺寸
        >>> url, path = chat.glm_image(
        ...     prompt="科技感城市夜景",
        ...     outdir="./downloads/posters",
        ...     models=["cogview-3", "glm-image"],
        ...     size="1024x1024"
        ... )

        注意事项:
        --------
        - 下载的图片文件名会使用时间戳格式：glm_YYYYMMDD_HHMMSS.png
        - 确保有写入权限到指定的目录
        - 下载失败会打印错误信息，但不会抛出异常
        - 智谱AI的图片尺寸要求：宽度512-2048，必须是16的倍数
        """
        import os
        import time
        import requests

        # 智谱AI图像生成API端点
        

        # 从环境变量获取API密钥和Base URL
        api_key = self._glm_api_key
        base_url = self._glm_base_url
        url = base_url

        # 验证必要参数
        if not api_key:
            print(f"[GLM图像] ✗ 错误: 未配置 GLM API 密钥")
            print(f"[GLM图像] 请在环境变量中设置: glm_api_key")
            return None, None

        # 请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        img_save_path = None
        if isinstance(models,list):
            model = models[0]
        else: 
            model = models
        for retry in range(max_retries):
            data = {
                "model": model,
                "prompt": prompt,
                "size": size
            }

            try:
                print(f"[GLM图像生成] 尝试: {retry + 1}/{max_retries} | Model: {model}")
                print(f"[GLM图像生成] URL: {url}")
                print(f"[GLM图像生成] Size: {data['size']}")
                print(f"[GLM图像生成] Prompt 长度: {len(prompt)} 字符")
                print(f"[GLM图像生成] 超时设置: {timeout}秒")

                response = requests.post(base_url, headers=headers, json=data, timeout=timeout)

                print(f"[GLM图像生成] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    print(f"[GLM图像生成] ✓ 模型 {model} 生成成功！")
                    result = response.json()

                    # 提取图片URL
                    if 'data' in result and len(result['data']) > 0:
                        image_url = result['data'][0].get('url', '')
                        print(f"[GLM图像生成] 图片URL: {image_url}")

                        # 如果指定了输出目录，自动下载图片
                        if outdir is not None:
                            if outdir.strip() == "":
                                outdir = "./"

                            try:
                                # 创建目录（如果不存在）
                                os.makedirs(outdir, exist_ok=True)
                                print(f"[GLM图像下载] 输出目录: {outdir}")

                                # 生成文件名：glm_时间戳.png
                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                filename = f"glm_{timestamp}.png"
                                filepath = os.path.join(outdir, filename)

                                print(f"[GLM图像下载] 文件名: {filename}")
                                print(f"[GLM图像下载] 完整路径: {os.path.abspath(filepath)}")
                                print(f"[GLM图像下载] 正在从 URL 下载图片...")

                                # 下载图片
                                img_response = requests.get(image_url, timeout=60)

                                if img_response.status_code == 200:
                                    with open(filepath, 'wb') as f:
                                        f.write(img_response.content)
                                    file_size = os.path.getsize(filepath)
                                    img_save_path = os.path.abspath(filepath)
                                    print(f"[GLM图像下载] ✓ 保存成功!")
                                    print(f"[GLM图像下载] ✓ 文件路径: {img_save_path}")
                                    print(f"[GLM图像下载] ✓ 文件大小: {file_size / 1024:.2f} KB")
                                else:
                                    print(f"[GLM图像下载] ✗ 下载失败: HTTP {img_response.status_code}")

                            except Exception as e:
                                print(f"[GLM图像下载] ✗ 下载异常: {str(e)}")
                                # 即使下载失败，也返回 URL

                        return image_url, img_save_path
                    else:
                        print(f"[GLM图像生成] ✗ 响应格式错误")
                        return None, None

                else:
                    print(f"[GLM图像生成] ✗ HTTP {response.status_code}")
                    print(f"[GLM图像生成] 错误详情: {response.text[:200]}")

                    # 如果是客户端错误（4xx），不需要重试
                    if 400 <= response.status_code < 500:
                        print(f"[GLM图像生成] 提示: 客户端错误，停止重试")
                        return None, None

            except requests.exceptions.Timeout as e:
                print(f"[GLM图像生成] ✗ 超时: 第 {retry + 1} 次尝试超时")
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 5  # 递增等待时间：5s, 10s, 15s
                    print(f"[GLM图像生成] 等待 {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"[GLM图像生成] 放弃: 已达最大重试次数")

            except requests.exceptions.RequestException as e:
                print(f"[GLM图像生成] ✗ 请求异常: {str(e)}")
                if retry < max_retries - 1:
                    print(f"[GLM图像生成] 5秒后重试...")
                    time.sleep(5)
                else:
                    return None, None

      

        # 所有模型都失败了
        print(f"[GLM图像生成] ✗ 所有模型尝试失败")
        return None, None 
    
    
    def doubao_image(self, prompt, outdir=None,
                models=['doubao-seedream-4-5-251128'],
                size="2K",
                response_format="url",):
        """
        豆包图像生成，支持自动下载到本地目录

        参数说明:
        --------
        prompt : str
            - 图像生成提示词，描述想要生成的图片内容
        outdir : str, optional (default=None)
            - 图片保存目录路径
            - 如果为 None，只返回图片 URL，不下载
            - 如果指定路径，会自动下载图片到该目录
            - 如果目录不存在，会自动创建
        models : list, optional (default=['doubao-seedream-4-5-251128'])
            - 模型列表，默认使用第一个模型
            - 可通过调整顺序来切换模型
        size : str, optional (default="2K")
            - 图片尺寸，如 "2K", "1024x1024" 等
        response_format : str, optional (default="url")
            - 返回格式，通常为 "url"

        返回值:
        -------
        str : 图片的 URL 地址
            - 如果 outdir 为 None，只返回 URL
            - 如果 outdir 不为 None，下载图片后仍返回 URL

        使用示例:
        --------
        >>> chat = MyChat()
        >>>
        >>> # 示例1: 只生成图片，不下载
        >>> url = chat.doubao_image("一只可爱的小猫")
        >>> print(f"图片URL: {url}")
        >>>
        >>> # 示例2: 生成并下载到指定目录
        >>> url = chat.doubao_image(
        ...     prompt="美丽的风景画",
        ...     outdir="./images"
        ... )
        >>>
        >>> # 示例3: 使用自定义文件名
        >>> import os
        >>> outdir = "./downloads/posters"
        >>> url = chat.doubao_image("科技感城市夜景", outdir=outdir)

        注意事项:
        --------
        - 下载的图片文件名会使用时间戳格式：doubao_YYYYMMDD_HHMMSS.png
        - 确保有写入权限到指定的目录
        - 下载失败会打印错误信息，但不会抛出异常
        """
        import os
        import time
        import requests

        client = OpenAI(
            base_url=self._ARK_BASE_URL,
            api_key=self._ARK_API_KEY,
        )

        print(f"[豆包图像生成] Model: {models[0]}")
        print(f"[豆包图像生成] Prompt: {prompt[:50]}...")
        print(f"[豆包图像生成] Size: {size}")

        imagesResponse = client.images.generate(
            model=models[0],
            prompt=prompt,
            size=size,
            response_format=response_format,
            extra_body={
                "watermark": True,  # 启用水印
            },
        )

        url = imagesResponse.data[0].url

        img_save_path = None 
        # 如果指定了输出目录，自动下载图片
        if outdir is not None :
            if outdir.strip()=="":
                outdir ="./"
            try:
                # 创建目录（如果不存在）
                os.makedirs(outdir, exist_ok=True)
                print(f"outdir: {outdir}")

                # 生成文件名：doubao_时间戳.png (格式: doubao_20260112_164803.png)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"img_{timestamp}.png"
                filepath = os.path.join(outdir, filename)


                # 下载图片
                response = requests.get(url, timeout=60)
                img_save_path = os.path.abspath(filepath)
                print(img_save_path)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    file_size = os.path.getsize(filepath)
                    
                    print(f"[图像下载] ✓ 保存成功!")
                    print(f"[图像下载] ✓ 文件路径: {img_save_path}")
                    print(f"[图像下载] ✓ 文件大小: {file_size / 1024:.2f} KB")
                else:
                    print(f"[图像下载] ✗ 下载失败: HTTP {response.status_code}")

            except Exception as e:
                print(f"[图像下载] ✗ 下载异常: {str(e)}")
                # 即使下载失败，也返回 URL

        return url,img_save_path
      
    
    def openai(self, prompt_user, 
                prompt_system=None, 
                models=["gpt-4o","o1-mini-2024-09-12"], 
                temperature=0, 
                base_url=None,
                api_key=None,
                return_json=True):
        """凡是支持openai接口的model都可以 
        - models:默认使用model[0]，使用时调整其顺序即可;也支持直接填写模型名称
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        if isinstance(models,list):
            
            model_name = models[0]
        else:
            model_name = models
        if base_url is not None and api_key is not None:
            response = chat(prompt_user=prompt_user, 
                    prompt_system=prompt_system, 
                    model=model_name, 
                    temperature=temperature, 
                    base_url=base_url,
                    api_key =api_key,
                    return_json=return_json)
        else:
            response = chat(prompt_user=prompt_user, 
                    prompt_system=prompt_system, 
                    model=model_name, 
                    temperature=temperature, 
                    base_url=self.OPENAI_BASE_URL,
                    api_key=self.OPENAI_API_KEY,
                    return_json=return_json)
        return  response
    
    def openai_func_call(self, query, model_list=["gpt-4o-mini","gpt-4o",'DeepSeek-R1-14B-Q8:latest','DeepSeek-R1-14B-F16:latest'], 
             func_index=0, answer_index=0, use_custom_func=True, output_format=None,):
        if answer_index or answer_index is not None:
            ans_model = model_list[answer_index]
            if ans_model in self.get_local_model(): #使用本地模型整合
                response = self.fc.chat(query, model_list=model_list, 
                            func_index=func_index, answer_index=answer_index, 
                            use_custom_func=use_custom_func, output_format=output_format)
                return response 
        ##使用在线模型整合
        prompt_answer,prompt_system = self.fc.chat_func_prompt(query, model_list=model_list, 
                    func_index=func_index, 
                    use_custom_func=use_custom_func, output_format=output_format)

        ans_model = model_list[func_index]
        response = self.openai(prompt_user=prompt_answer, 
            prompt_system=prompt_system, 
            models=[ans_model], 
            temperature=0, 
            return_json=True)

        return response 
    
    def ollama(self,prompt_user, prompt_system=None, 
               model=["DeepSeek-R1-32B-Q8:latest","DeepSeek-R1-32B-Q6:latest","DeepSeek-R1-14B-F16:latest","DeepSeek-R1-14B-Q8:latest"], 
               temperature=0,base_url='http://localhost:11434/v1/',return_json=True):
        """
        - models:默认使用model[0]，使用时调整其顺序即可
        - return_json：
            输出格式：json格式，包含在```json ```标记中，
                1. query字段，string类型，其value为用户的问题
                2. result字段，string类型，其value为最终回复结果
                3. thinking字段，list类型，
                3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
                3.2 若无思考步骤，则列表为空
        """
        res = chat(prompt_user=prompt_user, prompt_system=prompt_system, temperature=temperature, 
           model=model[0],
           base_url=base_url,api_key='key',return_json=return_json)
        return res  
    
    def add_funcs(self,function_infos,function_mappings):
        """
        添加函数调用信息

        Args:
            function_infos: 函数信息列表，包含函数的名称、描述和参数定义
            function_mappings: 函数映射字典，将函数名称映射到实际的函数对象

        Returns:
            返回 fc.add_funcs() 的执行结果
        """
        return self.fc.add_funcs(function_infos=function_infos,function_mappings=function_mappings )

    def register_function(self, name, description, parameters, function, **kwargs):
        return self.fc.register_function(name=name, description=description, parameters=parameters, function=function, **kwargs)

    
    def prompt_system(self):
        return self.fc.prompt_system()
    
    def tool_list(self):
        return self.fc.get_tool_list()
    
    





global client 
client = None





# 基于 prompt 生成文本
# gpt-3.5-turbo 
def get_completion(prompt, response_format="text", model="gpt-4o-mini"):
    
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    messages = [{"role": "user", "content": prompt}]    # 将 prompt 作为用户输入
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,                                  # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")

    return response.choices[0].message.content          # 返回模型生成的文本


def chat_openai(prompt, response_format="text", model="gpt-4o-mini"):
    """对话
    - prompt:输入文本
    - response_format:text,json_object
    
    """
    return get_completion(prompt, response_format, model)




def chat_stream(msg,model="gpt-4o-mini"):
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": msg}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            
            
