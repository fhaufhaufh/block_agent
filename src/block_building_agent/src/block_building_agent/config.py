from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化LLM模型
llm = ChatOpenAI(
    model="qwen3-vl-plus",  # 或者 gpt-4, gpt-3.5-turbo
    temperature=0.1,      # 低温度让输出更稳定
    api_key=os.getenv("CLOUD_QWEN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# build 阶段 Agent 使用的模型
build_advisor_llm = llm
build_validator_llm = llm

# task 阶段 Agent 使用的模型
task_advisor_llm = llm
task_validator_llm = llm