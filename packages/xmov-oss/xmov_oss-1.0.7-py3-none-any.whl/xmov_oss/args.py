# coding: utf-8
import argparse
from dataclasses import dataclass
from typing import Literal
import os


@dataclass
class CLIArgs:
    action: str = Literal["upload", "download", "ls", "doc"]
    local_file_path: str = None  # 本地文件路径
    remote_file_path: str = None  # 远程文件路径
    overwrite: bool = False # 是否覆盖
    secret: str = None  # 密码


def parse_args() -> CLIArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["upload", "download", "ls", "doc"])
    parser.add_argument('-l', "--local_file_path", type=str, help="本地文件/文件夹路径")
    parser.add_argument('-r', "--remote_file_path", type=str, required=False, help="OSS远端相对路径")
    parser.add_argument('-o', "--overwrite", type=bool, required=False, default=False, help="是否覆盖同名文件")
    parser.add_argument('-p', "--password", type=str, required=False,
                        default=os.getenv("XMOV_OSS_SECRET"), help="密码, 可以使用export XMOV_OSS_SECRET=*** 通过环境变量设置密码")
    args = parser.parse_args()
    return CLIArgs(
        action=args.action,
        local_file_path=args.local_file_path,
        remote_file_path=args.remote_file_path,
        overwrite=args.overwrite,
        secret=args.password,
    )
