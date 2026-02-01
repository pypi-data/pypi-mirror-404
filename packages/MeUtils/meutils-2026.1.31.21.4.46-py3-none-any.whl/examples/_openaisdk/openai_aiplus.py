#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : openai_siliconflow
# @Time         : 2024/6/26 10:42
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from openai import OpenAI
from openai import OpenAI, APIStatusError

api_key = "QC-bf5cc6f65c2cf7dc1c9cfa03c55b21e3-5aaaa10f8720eac3713b64ee58919941"

client = OpenAI(
    base_url="https://aiping.cn/api/v1",
    api_key=api_key,
)
# print(client.models.list())
model = "Qwen3-Max:provider=阿里云百炼"
# model = "bailian/qwen3-235b-a22b"
# model = "DeepSeek-V3.2:latency:provider=阿里云百炼"
# model = "DeepSeek-V3.2:latency:provider=DeepSeek"
# model = "MiniMax-M2.1:latency:provider=MiniMax"
# model = "GLM-4.7:latency:provider=智谱"
# model = "DeepSeek-V3.2:latency:provider=硅基流动,阿里云百炼"

# model = "DeepSeek-V3.2:provider=阿里云百炼"
# DeepSeek-R1:throughput:latency<500,input_price<1.0
# model = "DeepSeek-V3.2:provider:provider=百度智能云"
model = "kimi-k2-0905:throughput"

try:
    completion = client.chat.completions.create(
        model=model,
        # model="xxxxxxxxxxxxx",
        messages=[
            {"role": "user", "content": "你是谁"}
        ],
        # top_p=0.7,
        # top_p=None,
        # temperature=None,
        # stream=True,
        # max_tokens=6000,

        # extra_body={
        #     "provider": {
        #         "only": ["阿里云百炼"],
        #         "order": [],
        #         "sort": None,
        #         "output_price_range": [],
        #         "latency_range": []
        #     }
        # }
        # extra_body={
        #     "provider": {
        #         "only": ["阿里云百炼"],
        #         "order": [],
        #         "sort": None,
        #         "output_price_range": [],
        #         "latency_range": []
        #     }
        # }
    )
    print(completion)
except APIStatusError as e:
    print(e.status_code)

    print(e.response)
    print(e.message)
    print(e.code)

for chunk in completion:
    print(chunk.choices[0].delta.content)

# r = client.images.generate(
#     model="cogview-3-plus",
#     prompt="a white siamese cat",
#     size="1024x1024",
#     quality="hd",
#     n=1,
# )


