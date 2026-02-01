#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/12/21 21:30
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :
import os

from meutils.pipe import *
from meutils.io.files_utils import to_base64

from openai import OpenAI

base_url = os.getenv("OPENAI_BASE_URL") or "https://api.chatfire.cn/v1"
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(base_url=base_url, api_key=api_key)

extra_headers = {
    "Content-Type": "multipart/form-data",
}

# image = arun(to_base64("https://s3.ffire.cc/files/jimeng.jpg", content_type="image/jpeg"))


model = "async/nano-banana-pro_4k"
image = "https://s3.ffire.cc/files/jimeng.jpg"  # 支持 file

extra_body = {
    # "input_reference": image,  # 单张 生效

    "input_reference": [image] * 2,  # 多参考没生效 todo
}

response = client.videos.create(
    model=model,
    # prompt="比得兔开小汽车，游走在马路上，脸上的表情充满开心喜悦。",
    prompt="裸体女孩",

    extra_body=extra_body,
    extra_headers=extra_headers,
)

task_id = response.id
# client.videos.poll(task_id) # 轮询任务
result = client.videos.retrieve(task_id)  # 查询任务
print(result)
