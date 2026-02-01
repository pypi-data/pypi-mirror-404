
# coding: utf-8

import os
from xmov_oss.core import XmovOSSBucket
from xmov_oss.schema import OSSConfigWithSecret
from xmov_oss.args import parse_args
from xmov_oss.utils import download
from pprint import pprint
import click
from xmov_oss.rich_console import rich_console


@click.group()
def cli():
    pass

@cli.command("upload", help="上传文件, 示例: xmov_oss upload README.md")
@click.argument("local_file_path")
@click.argument("remote_file_path")
@click.option("--secret", type=str, default=os.getenv("XMOV_OSS_SECRET"))
@click.option("--overwrite", is_flag=True, default=False)
def upload(local_file_path, remote_file_path, secret, overwrite):
    config = OSSConfigWithSecret(secret=secret)
    bucket = XmovOSSBucket(config)
    file_info = bucket.upload(local_file_path, remote_file_path, overwrite)
    click.echo(file_info)


@cli.command("download", help="下载文件, 示例: xmov_oss download /tmp/xmov_oss/README.md")
@click.argument("remote_file_path")
@click.option("--secret", type=str, default=os.getenv("XMOV_OSS_SECRET"))
def download(remote_file_path, secret):
    config = OSSConfigWithSecret(secret=secret)
    bucket = XmovOSSBucket(config)
    bucket.download(remote_file_path)
    click.echo(f"下载文件: {remote_file_path} 到 {os.path.basename(remote_file_path)}")


@cli.command()
@click.argument("remote_file_path", required=False, default="tmp/xmov_oss")
@click.option("--secret", type=str, default=os.getenv("XMOV_OSS_SECRET"))
@click.option("--rich", is_flag=True, default=False)
def ls(remote_file_path, secret, rich):
    config = OSSConfigWithSecret(secret=secret)
    bucket = XmovOSSBucket(config)
    data = bucket.ls(remote_file_path, with_tag=False)
    if rich:
        rich_console.table.print(data, title="File List")
    else:
        for item in data:
            click.echo(f"{item['key']} {item['url']}")


@cli.command()
def doc():
    docs = """
# 设置密码, 如果不使用export, 需要在命令行使用 -p ***指定
export XMOV_OSS_SECRET=***

# 显示列表
xmov_oss ls tmp/xmov_oss

# 上传文件
xmov_oss upload README.md 
        """
    click.echo(docs)

def main():
    cli()


if __name__ == "__main__":
    main()