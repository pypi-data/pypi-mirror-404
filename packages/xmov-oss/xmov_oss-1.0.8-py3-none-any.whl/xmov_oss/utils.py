# coding: utf-8
from urllib.request import urlretrieve
import sys
import os

def show_percent_bar(percent: float, extra_message="") -> None:
    """ 显示进度百分比
    Args:
        percent: 进度百分比
    Returns:
        None
    """
    bar_len = 30
    filled = int(bar_len * percent / 100)
    bar = "#" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"\r[{bar}] {percent:5.1f}%{extra_message}")
    sys.stdout.flush()


def show_progress(block_num, block_size, total_size):
    """ 显示下载进度
    Args:
        block_num: 已下载的块数
        block_size: 每个块的大小
        total_size: 总大小
    Returns:
        None
    """
    downloaded = block_num * block_size
    percent = min(downloaded / total_size * 100, 100)
    show_percent_bar(percent)
    if downloaded >= total_size:
        print()  # 换行


def download(url: str, local_file_path: str=None):
    """ 下载文件
    Args:
        url: 文件的url
        local_file_path: 本地文件路径
    Returns:
        None
    """
    # 如果本地文件路径为空，则使用url的文件名
    if local_file_path is None:
        local_file_path = os.path.basename(url)
    urlretrieve(url, local_file_path, reporthook=show_progress)

