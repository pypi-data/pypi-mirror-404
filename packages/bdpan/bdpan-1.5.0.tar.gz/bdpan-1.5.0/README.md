# bdpan

一个可复用的百度网盘（pan.baidu.com）小库，支持：

- 目录递归上传
- 分片并发上传（默认 4MB 分片、4 线程）
- 断点续传（本地保存 upload state）
- 创建分享链接（通过 `api/filemetas` 获取 `fs_id`）

## 安装

在本仓库中可直接：

```bash
pip install -e .
```

## 准备 cookies

需要登录后的 cookies（至少包含 `BDUSS`/`STOKEN` 等）。支持两种格式：

- 形如 `key=value; key2=value2` 的 Cookie Header 文本
- 浏览器导出的 Netscape `cookies.txt`

## 使用（库）

```python
from bdpan import BaiduPanClient, BaiduPanConfig

client = BaiduPanClient(
    BaiduPanConfig(
        cookie_file="cookies.txt",
        remote_root="/apps/bdpan",
        state_dir="./data/bd_upload_state",
    )
)

client.upload("local_folder_or_file")
link = client.share("remote_dir_name", password="1234", period_days=7)
print(link)
```

## 使用（命令行）

```bash
bdpan --cookie-file .\\auth\\baidu\\cookies.txt upload .\\data
bdpan --cookie-file .\\auth\\baidu\\cookies.txt share remote_dir --password 1234 --period-days 7
```

## 本地验证

```bash
python -m unittest discover -s tests -p "test_*.py"
```
