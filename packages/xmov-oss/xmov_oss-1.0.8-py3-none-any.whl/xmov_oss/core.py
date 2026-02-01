# coding: utf-8
import os
import oss2
from datetime import datetime
from xmov_oss.schema import OSSConfigWithSecret
from typing import List, Dict, Any, Union
from typing import Generator
from xmov_oss.utils import show_percent_bar

def progress_callback(consumed_bytes, total_bytes):
    """ 显示上传进度
    Args:
        consumed_bytes: 已上传的字节数
        total_bytes: 总字节数
    Returns:
        None
    """
    show_percent_bar(consumed_bytes / total_bytes * 100, extra_message=f"({consumed_bytes}/{total_bytes})")
    if consumed_bytes >= total_bytes:
        print()  # 换行


class XmovOSSBucket(object):
    def __init__(self, config: OSSConfigWithSecret):
        """ 初始化XmovOSSBucket
        Args:
            config: OSSConfigWithSecret
        Returns:
            None
        """
        self.config = config
        self.auth = oss2.Auth(config.OSS_ACCESS_KEY_ID, config.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, config.OSS_ENDPOINT, config.OSS_BUCKET_NAME)

    def ls(self, prefix: str, with_tag: bool = True )->List[dict]:
        """ 列出文件
        Args:
            prefix: 文件前缀
            with_tag: 是否包含标签
        Returns:
            List[dict]: 文件列表
        """
        file_paths = []
        next_marker = ""
        print(f"[SDK CACHE] video directory: {prefix}")
        while True:
            result = self.bucket.list_objects(
                prefix=prefix, marker=next_marker, max_keys=1000
            )
            for obj in result.object_list:
                item = {
                    "key": obj.key,
                    "url": f"{self.config.OSS_BASE_URL}/{obj.key}",
                }
                if with_tag:
                    item["tag"] = obj.tag
                file_paths.append(item)
            if result.is_truncated:
                next_marker = result.next_marker
            else:
                break
        return file_paths
    
    def upload_file(self, local_file_path: str, remote_file_path: str=None, overwrite: bool = False)->dict:
        """ 上传文件
        Args:
            local_file_path: 本地文件路径
            remote_file_path: 远程文件路径
            overwrite: 是否覆盖
        Returns:
            dict: 文件信息
        """
        if remote_file_path is None:
            time_str = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.basename(local_file_path)
            remote_file_path = f"tmp/xmov_oss/{time_str}/{file_name}"
        print(f"上传文件: {local_file_path} 到 {remote_file_path}")

        f = LocalFile(local_file_path)
        
        if not f.is_exists():
            raise FileNotFoundError(f"File {local_file_path} not found")
        
        total_size = f.size()
        uploaded_size = 0

        if total_size == 0:
            raise ValueError(f"File {local_file_path} is empty")
        if self.exists(remote_file_path) and not overwrite:
            raise FileExistsError(f"File {remote_file_path} already exists")
        
        # if total_size > 1024 * 1024 * 2:
        #     # 分片上传
        #     upload_id = self.bucket.init_multipart_upload(remote_file_path).upload_id
        #     parts = []
        #     progress_callback(0, total_size)
        #     for idx, chunk in enumerate(f.chunk_it(1024*500), start=1):
        #         result = self.bucket.upload_part(remote_file_path, upload_id, idx, chunk)
        #         parts.append(oss2.models.PartInfo(idx, result.etag))
        #         uploaded_size += len(chunk)
        #         # 显示整体进度
        #         progress_callback(uploaded_size, total_size)
        #     obj = self.bucket.complete_multipart_upload(
        #         remote_file_path, upload_id, parts)
        # else:
        obj = self.bucket.put_object(
            remote_file_path, f.read(), progress_callback=progress_callback)
        
        file_info = self.bucket.get_object(remote_file_path)
        return {
            "url": f"{self.config.OSS_BASE_URL}/{remote_file_path}",
            "etag": file_info.etag,
        }

    def upload_dir(self, local_dir_path: str, remote_dir_path: str=None, overwrite: bool = False)->List[dict]:
        """ 上传目录
        Args:
            local_dir_path: 本地目录路径
            remote_dir_path: 远程目录路径
            overwrite: 是否覆盖
        Returns:
            List[dict]: 文件列表
        """
        print(f"上传目录: {local_dir_path} 到 {remote_dir_path}")
        file_infos = []
        if remote_dir_path is None:
            time_str = datetime.now().strftime("%Y%m%d%H%M%S")
            remote_dir_path = f"tmp/xmov_oss/{time_str}"
        for file_name in os.listdir(local_dir_path):
            if os.path.isfile(os.path.join(local_dir_path, file_name)):
                file_path = os.path.join(local_dir_path, file_name)
                file_info = self.upload_file(
                    local_file_path=file_path, 
                    remote_file_path=os.path.join(remote_dir_path, file_name), 
                    overwrite=overwrite)
                file_infos.append(file_info)
            else:
                print(f"跳过目录: {file_name}")
        return file_infos

    def upload(self, local_dir_path: str, remote_dir_path: str = None, overwrite: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """ 上传文件或目录
        Args:
            local_dir_path: 本地目录路径
            remote_dir_path: 远程目录路径
            overwrite: 是否覆盖
        Returns:
            dict | List[dict]: 文件信息
        """
        if os.path.isfile(local_dir_path):
            return self.upload_file(local_dir_path, remote_dir_path, overwrite)
        elif os.path.isdir(local_dir_path):
            return self.upload_dir(local_dir_path, remote_dir_path, overwrite)
        else:
            raise ValueError(f"File {local_dir_path} is not a file or directory")

    def download(self, remote_file_path: str):
        """ 下载文件
        Args:
            remote_file_path: 远程文件路径
        Returns:
            None
        """
        local_file_path = os.path.basename(remote_file_path)
        self.bucket.get_object_to_file(remote_file_path, local_file_path)
        print(f"下载文件: {remote_file_path} 到 {local_file_path}")

    # 删除文件操作太危险，不支持
    # def delete(self, remote_file_path: str):
    #     self.bucket.delete_object(remote_file_path)

    def exists(self, remote_file_path: str):
        """ 检查文件是否存在
        Args:
            remote_file_path: 远程文件路径
        Returns:
            bool: 是否存在
        """
        return self.bucket.object_exists(remote_file_path)

    def size(self, remote_file_path: str):
        """ 获取文件大小
        Args:
            remote_file_path: 远程文件路径
        Returns:
            int: 文件大小
        """
        return self.bucket.head_object(remote_file_path).content_length

    def last_modified(self, remote_file_path: str):
        """ 获取文件最后修改时间
        Args:
            remote_file_path: 远程文件路径
        Returns:
            datetime: 最后修改时间
        """
        return self.bucket.head_object(remote_file_path).last_modified

    def content_type(self, remote_file_path: str):
        """ 获取文件内容类型
        Args:
            remote_file_path: 远程文件路径
        Returns:
            str: 内容类型
        """
        return self.bucket.head_object(remote_file_path).content_type


class LocalFile(object):
    def __init__(self, file_path: str):
        """ 初始化LocalFile
        Args:
            file_path: 文件路径
        Returns:
            None
        """
        self.file_path = file_path

    def read(self) -> bytes:
        """ 读取文件
        Args:
            None
        Returns:
            bytes: 文件内容
        """
        with open(self.file_path, "rb") as f:
            return f.read()

    def write(self, data: bytes) -> None:
        """ 写入文件
        Args:
            data: 文件内容
        Returns:
            None
        """
        with open(self.file_path, "wb") as f:
            f.write(data)
    
    def size(self) -> int:
        """ 获取文件大小
        Args:
            None
        Returns:
            int: 文件大小
        """
        return os.path.getsize(self.file_path)
    
    def is_exists(self) -> bool:
        """ 检查文件是否存在
        Args:
            None
        Returns:
            bool: 是否存在
        """
        return os.path.exists(self.file_path)
    
    def chunk_it(self, chunk_size: int = 1024 * 1024 * 2) -> Generator[bytes, None, None]:
        """ 分块读取文件
        Args:
            chunk_size: 块大小
        Returns:
            Generator[bytes]: 文件块
        """
        with open(self.file_path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data