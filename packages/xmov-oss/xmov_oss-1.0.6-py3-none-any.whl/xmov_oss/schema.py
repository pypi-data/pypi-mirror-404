# coding: utf-8
from dataclasses import dataclass
from typing import List
import jwt


@dataclass
class OSSConfigWithSecret:
    """
                    "OSS_ACCESS_KEY_ID": "LTAIJGzcSH51Ofev",
                "OSS_ACCESS_KEY_SECRET": "ehvhJGAE9sJiwbHUszl7gCLWwrPGlj",
    """
    # 加密用的secret（password)
    secret: str
    # 加密后的OSS_ACCESS_KEY_SECRET
    OSS_ACCESS_KEY_SECRET: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJPU1NfQUNDRVNTX0tFWV9TRUNSRVQiOiJlaHZoSkdBRTlzSml3YkhVc3psN2dDTFd3clBHbGoifQ.itTMqDdAOHB7EGfkpV5unnwM1CifFhLHO81meuH8caI"
    # OSS_ENDPOINT: 阿里云OSS的endpoint
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    # OSS_ACCESS_KEY_ID: 阿里云OSS的access key id
    OSS_ACCESS_KEY_ID: str = "LTAIJGzcSH51Ofev"
    # OSS_BUCKET_NAME: 阿里云OSS的bucket name
    OSS_BUCKET_NAME: str = "public-xmov"
    # OSS_BASE_URL: 阿里云OSS的base url
    OSS_BASE_URL: str = "https://public-xmov.oss-cn-hangzhou.aliyuncs.com"
    # need_decode_secret: 是否需要解码OSS_ACCESS_KEY_SECRET
    need_decode_secret: bool = True

    def __post_init__(self):
        # 使用jwt通过secret解码OSS_ACCESS_KEY_SECRET
        if not self.secret:
            raise ValueError("请使用 -p 指定密码")
        if self.need_decode_secret:
            self.OSS_ACCESS_KEY_SECRET = jwt.decode(
                self.OSS_ACCESS_KEY_SECRET, self.secret, algorithms=["HS256"])["OSS_ACCESS_KEY_SECRET"]
        else:
            self.OSS_ACCESS_KEY_SECRET = self.secret
        

