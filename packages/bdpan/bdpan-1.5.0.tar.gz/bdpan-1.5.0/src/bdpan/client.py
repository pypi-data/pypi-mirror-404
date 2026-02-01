from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import requests

from bdpan.utils import extract_params

from .cookies import load_cookies
from .exceptions import BaiduPanApiError, BaiduPanAuthError, BaiduPanHttpError
from .progress import UploadProgress

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BaiduPanConfig:
    cookie_file: str | Path | None = None
    cookies: dict[str, str] | None = None
    app_id: str = "250528"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    remote_root: str = "/apps/bdpan"
    chunk_size: int = 4 * 1024 * 1024
    upload_workers: int = 4
    state_dir: str | Path | None = None
    timeout_s: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.5


class BaiduPanClient:
    def __init__(self, config: BaiduPanConfig):
        self._config = config
        cookies = dict(config.cookies or {})
        if not cookies and config.cookie_file is not None:
            cookies = load_cookies(config.cookie_file)
        if not cookies:
            raise BaiduPanAuthError("missing cookies (provide config.cookies or config.cookie_file)")

        self._cookies = cookies
        self._tls = threading.local()
        self._bdstoken: str = ""
        self._cdn_hosts: list[str] | None = None
        self._remote_root = self._normalize_remote_root(config.remote_root)

    @property
    def remote_root(self) -> str:
        return self._remote_root

    @staticmethod
    def _normalize_remote_root(remote_root: str) -> str:
        remote_root = (remote_root or "").strip().replace("\\", "/")
        if not remote_root.startswith("/"):
            remote_root = "/" + remote_root
        remote_root = remote_root.rstrip("/")
        if remote_root == "":
            remote_root = "/"
        return remote_root

    def normalize_remote_path(self, remote_path: str) -> str:
        remote_path = (remote_path or "").strip().replace("\\", "/")
        if not remote_path:
            raise ValueError("remote_path is empty")
        if remote_path.startswith("/"):
            return remote_path
        return f"{self._remote_root}/{remote_path}".replace("//", "/")

    def _get_session(self) -> requests.Session:
        s: requests.Session | None = getattr(self._tls, "session", None)
        if s is None:
            s = requests.Session()
            s.cookies.update(self._cookies)
            self._tls.session = s
        return s

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
        timeout_s: int | None = None,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
        allow_redirect: bool = True,
    ) -> requests.Response:
        timeout_s = int(timeout_s or self._config.timeout_s)
        max_retries = int(max_retries or self._config.max_retries)
        backoff_factor = float(backoff_factor or self._config.backoff_factor)

        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self._get_session().request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=timeout_s,
                    allow_redirects=allow_redirect,
                )
                if resp.status_code < 500:
                    return resp
                raise BaiduPanHttpError(
                    f"http {resp.status_code} for {url}",
                    status_code=resp.status_code,
                    url=url,
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                logger.warning("request failed (%s) attempt %s/%s: %s", url, attempt, max_retries, exc)
            except BaiduPanHttpError as exc:
                last_exc = exc
                logger.warning("%s attempt %s/%s", exc, attempt, max_retries)

            if attempt < max_retries:
                time.sleep(backoff_factor * (2 ** (attempt - 1)))
        raise BaiduPanHttpError(f"request failed after retries: {url}: {last_exc}", url=url)

    @property
    def bdstoken(self) -> str:
        if self._bdstoken:
            return self._bdstoken

        if not self._cookies.get("STOKEN") and not self._cookies.get("BDUSS"):
            raise BaiduPanAuthError("missing STOKEN/BDUSS in cookies; login cookies required")

        url = "https://pan.baidu.com/disk/main"
        resp = self._request("GET", url, headers={"User-Agent": self._config.user_agent})
        match = re.search(r"bdstoken[\'\":\\s]+([0-9a-f]{32})", resp.text)
        if not match:
            raise BaiduPanAuthError("failed to locate bdstoken from pan.baidu.com response")
        self._bdstoken = match.group(1)
        return self._bdstoken

    @property
    def cdn_hosts(self) -> list[str]:
        if self._cdn_hosts is not None:
            return self._cdn_hosts

        url = "https://d.pcs.baidu.com/rest/2.0/pcs/file?method=locateupload"
        resp = self._request("GET", url, headers={"User-Agent": self._config.user_agent})
        payload = resp.json()
        if payload.get("error_code") == 0:
            self._cdn_hosts = payload.get("server", []) or []
        else:
            self._cdn_hosts = []
        return self._cdn_hosts

    def filemetas(self, remote_paths: list[str]) -> list[dict]:
        """
        Resolve remote path(s) to metadata via `https://pan.baidu.com/api/filemetas`.

        Returns the raw `info` list from the API response.
        """
        if not remote_paths:
            return []

        normalized = [self.normalize_remote_path(p) for p in remote_paths]
        url = "https://pan.baidu.com/api/filemetas"
        params = {
            "clienttype": "0",
            "app_id": self._config.app_id,
            "web": "1",
            "channel": "chunlei",
            "version": str(int(time.time() * 1000)),
            "bdstoken": self.bdstoken,
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": "https://pan.baidu.com/disk/main",
            "Origin": "https://pan.baidu.com",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        data = {
            "target": json.dumps(normalized, ensure_ascii=False, separators=(",", ":")),
        }

        resp = self._request("POST", url, params=params, headers=headers, data=data)
        payload = resp.json()
        if payload.get("errno") != 0:
            raise BaiduPanApiError("filemetas failed", payload=payload)

        info = payload.get("info") or []
        if not isinstance(info, list):
            raise BaiduPanApiError("filemetas invalid response", payload=payload)
        return info

    def get_fs_id(self, remote_path: str) -> int:
        info = self.filemetas([remote_path])
        if not info:
            raise BaiduPanApiError("filemetas returned empty info", payload={"remote_path": remote_path})
        fs_id = info[0].get("fs_id")
        if fs_id is None:
            raise BaiduPanApiError("filemetas missing fs_id", payload={"info0": info[0]})
        return int(fs_id)

    def _state_dir(self) -> Path:
        if self._config.state_dir:
            d = Path(self._config.state_dir)
        else:
            d = Path.home() / ".bdpan" / "upload_state"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _state_path(self, local_path: str, remote_path: str) -> Path:
        key = f"{os.path.abspath(local_path)}|{remote_path}"
        h = hashlib.md5(key.encode("utf-8")).hexdigest()
        return self._state_dir() / f"{h}.json"

    def _load_upload_state(self, local_path: str, remote_path: str) -> dict | None:
        p = self._state_path(local_path, remote_path)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("load upload state failed: %s", p)
            return None

    def _save_upload_state(self, local_path: str, remote_path: str, state: dict) -> None:
        p = self._state_path(local_path, remote_path)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, p)

    def _clear_upload_state(self, local_path: str, remote_path: str) -> None:
        p = self._state_path(local_path, remote_path)
        try:
            p.unlink(missing_ok=True)  # py3.8+ supports missing_ok on Path
        except Exception:
            logger.exception("clear upload state failed: %s", p)

    def _scan_file_slices(self, file_path: str) -> tuple[list[str], list[tuple[int, int]]]:
        md5_list: list[str] = []
        slices: list[tuple[int, int]] = []
        offset = 0
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(self._config.chunk_size)
                if not chunk:
                    break
                md5_list.append(hashlib.md5(chunk).hexdigest())
                slices.append((offset, len(chunk)))
                offset += len(chunk)
        return md5_list, slices

    def _read_slice(self, file_path: str, offset: int) -> bytes:
        with open(file_path, "rb") as f:
            f.seek(offset)
            return f.read(self._config.chunk_size)

    def _upload_precreate(
        self,
        remote_path: str,
        *,
        size: int,
        local_mtime: int,
        block_list: list[str],
        overwrite: bool,
    ) -> dict:
        url = "https://pan.baidu.com/api/precreate"
        params = {
            "bdstoken": self.bdstoken,
            "app_id": self._config.app_id,
            "channel": "chunlei",
            "web": "1",
            "clienttype": "0",
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": "https://pan.baidu.com/disk/main",
            "Origin": "https://pan.baidu.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "path": remote_path,
            "size": str(size),
            "isdir": "0",
            "autoinit": "1",
            "block_list": json.dumps(block_list, separators=(",", ":")),
            "local_mtime": str(local_mtime),
        }
        # Baidu uses rtype to control overwrite behavior in some endpoints.
        # 0/1/2/3 meanings vary across APIs; use 3 as "overwrite" when enabled.
        if overwrite:
            data["rtype"] = "3"

        resp = self._request("POST", url, params=params, headers=headers, data=data)
        payload = resp.json()
        if payload.get("errno") != 0:
            raise BaiduPanApiError("precreate failed", payload=payload)
        return payload

    def _upload_superfile_with_host(
        self,
        host: str,
        *,
        file_path: str,
        offset: int,
        remote_path: str,
        uploadid: str,
        part_index: int,
    ) -> dict:
        chunk = self._read_slice(file_path, offset)
        base_url = f"https://{host}/rest/2.0/pcs/superfile2"
        params = {
            "method": "upload",
            "app_id": self._config.app_id,
            "channel": "chunlei",
            "web": "1",
            "clienttype": "0",
            "path": remote_path,
            "uploadid": uploadid,
            "uploadsign": "0",
            "partseq": str(part_index),
        }
        headers = {
            "Origin": "https://pan.baidu.com",
            "Referer": "https://pan.baidu.com/",
            "User-Agent": self._config.user_agent,
        }
        files = {"file": ("blob", chunk, "application/octet-stream")}
        resp = self._request("POST", base_url, params=params, headers=headers, files=files)
        try:
            return resp.json()
        except Exception as exc:
            raise BaiduPanApiError(f"superfile2 non-json response: {resp.status_code}") from exc

    def _upload_part_with_retry(
        self,
        *,
        file_path: str,
        offset: int,
        remote_path: str,
        uploadid: str,
        part_index: int,
        max_retries: int = 5,
        backoff_s: float = 0.8,
    ) -> dict:
        hosts = self.cdn_hosts
        if not hosts:
            raise BaiduPanApiError("no cdn hosts available")

        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            host = hosts[(attempt - 1) % len(hosts)]
            try:
                payload = self._upload_superfile_with_host(
                    host,
                    file_path=file_path,
                    offset=offset,
                    remote_path=remote_path,
                    uploadid=uploadid,
                    part_index=part_index,
                )
                if "md5" in payload or payload.get("errno") in (0, None):
                    return payload
                raise BaiduPanApiError("upload part failed", payload=payload)
            except Exception as exc:
                last_err = exc
                logger.warning(
                    "%s: part %s attempt %s/%s failed: %s",
                    remote_path,
                    part_index,
                    attempt,
                    max_retries,
                    exc,
                )
                if attempt < max_retries:
                    time.sleep(backoff_s * (2 ** (attempt - 1)))
        raise BaiduPanApiError(f"part upload failed after retries: {last_err}")

    def _upload_create(
        self,
        *,
        remote_path: str,
        uploadid: str,
        size: int,
        block_list: list[str],
        local_mtime: int,
    ) -> dict:
        url = "https://pan.baidu.com/api/create"
        params = {
            "isdir": "0",
            "bdstoken": self.bdstoken,
            "app_id": self._config.app_id,
            "channel": "chunlei",
            "web": "1",
            "clienttype": "0",
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": "https://pan.baidu.com/disk/main",
            "Origin": "https://pan.baidu.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "path": remote_path,
            "size": str(size),
            "uploadid": uploadid,
            "block_list": json.dumps(block_list, separators=(",", ":")),
            "local_mtime": str(local_mtime),
        }
        resp = self._request("POST", url, params=params, headers=headers, data=data)
        payload = resp.json()
        if payload.get("errno") != 0:
            raise BaiduPanApiError("create failed", payload=payload)
        return payload

    def upload_file(
        self,
        local_path: str | Path,
        *,
        remote_path: str | None = None,
        resume: bool = True,
        overwrite: bool = False,
        on_progress: Callable[[UploadProgress], None] | None = None,
    ) -> dict:
        local_path = str(local_path)
        if not os.path.isfile(local_path):
            raise FileNotFoundError(local_path)

        if remote_path is None:
            remote_path = os.path.basename(local_path)
        remote_path = self.normalize_remote_path(remote_path)

        stat = os.stat(local_path)
        size = int(stat.st_size)
        if size <= 0:
            raise ValueError(f"empty file not supported: {local_path}")
        local_mtime = int(stat.st_mtime)

        block_list, slices = self._scan_file_slices(local_path)
        total_parts = len(slices)
        if not total_parts:
            raise ValueError(f"empty file not supported: {local_path}")

        state = self._load_upload_state(local_path, remote_path) if resume else None
        reusable = (
            state
            and state.get("size") == size
            and state.get("mtime") == local_mtime
            and state.get("chunk_size") == self._config.chunk_size
            and state.get("remote_path") == remote_path
            and state.get("total_parts") == total_parts
            and state.get("block_list") == block_list
            and state.get("uploadid")
        )

        if reusable:
            uploadid = str(state["uploadid"])
            done = set(state.get("done_parts", []))
            logger.info("%s: resume uploadid=%s done=%s/%s", remote_path, uploadid, len(done), total_parts)
        else:
            pre = self._upload_precreate(
                remote_path,
                size=size,
                local_mtime=local_mtime,
                block_list=block_list,
                overwrite=overwrite,
            )
            uploadid = str(pre.get("uploadid") or "")
            if not uploadid and int(pre.get("return_type") or 0) == 2:
                # Rapid upload path (server says file already exists and is created).
                return pre
            if not uploadid:
                raise BaiduPanApiError("precreate missing uploadid", payload=pre)
            done = set()
            state = {
                "version": 1,
                "local_path": os.path.abspath(local_path),
                "remote_path": remote_path,
                "size": size,
                "mtime": local_mtime,
                "chunk_size": self._config.chunk_size,
                "uploadid": uploadid,
                "total_parts": total_parts,
                "done_parts": [],
                "block_list": block_list,
            }
            self._save_upload_state(local_path, remote_path, state)
            logger.info("%s: start uploadid=%s parts=%s", remote_path, uploadid, total_parts)

        lock = threading.Lock()

        def part_worker(part_index: int, offset: int) -> None:
            self._upload_part_with_retry(
                file_path=local_path,
                offset=offset,
                remote_path=remote_path,
                uploadid=uploadid,
                part_index=part_index,
            )
            with lock:
                done.add(part_index)
                state["done_parts"] = sorted(done)
                self._save_upload_state(local_path, remote_path, state)
                if on_progress:
                    uploaded_bytes = min(size, len(done) * self._config.chunk_size)
                    on_progress(
                        UploadProgress(
                            local_path=local_path,
                            remote_path=remote_path,
                            total_bytes=size,
                            uploaded_bytes=uploaded_bytes,
                            part_index=part_index,
                            total_parts=total_parts,
                        )
                    )

        futures = []
        with ThreadPoolExecutor(max_workers=self._config.upload_workers) as ex:
            for part_index, (offset, _part_size) in enumerate(slices):
                if part_index in done:
                    continue
                futures.append(ex.submit(part_worker, part_index, offset))
            for fu in as_completed(futures):
                fu.result()

        if len(done) != total_parts:
            raise BaiduPanApiError(f"not all parts uploaded: {len(done)}/{total_parts}")

        result = self._upload_create(
            remote_path=remote_path,
            uploadid=uploadid,
            size=size,
            block_list=block_list,
            local_mtime=local_mtime,
        )
        self._clear_upload_state(local_path, remote_path)
        return result

    def upload_dir(
        self,
        local_dir: str | Path,
        *,
        remote_dir: str | None = None,
        resume: bool = True,
        overwrite: bool = False,
        on_progress: Callable[[UploadProgress], None] | None = None,
    ) -> list[dict]:
        local_dir = str(local_dir)
        if not os.path.isdir(local_dir):
            raise NotADirectoryError(local_dir)

        base_name = os.path.basename(os.path.abspath(local_dir).rstrip("\\/"))
        remote_dir = base_name if remote_dir is None else remote_dir
        remote_dir = self.normalize_remote_path(remote_dir)

        results: list[dict] = []
        for root, _dirs, files in os.walk(local_dir):
            for name in files:
                full_path = os.path.join(root, name)
                rel = os.path.relpath(full_path, local_dir).replace("\\", "/")
                remote_path = f"{remote_dir}/{rel}".replace("//", "/")
                results.append(
                    self.upload_file(
                        full_path,
                        remote_path=remote_path,
                        resume=resume,
                        overwrite=overwrite,
                        on_progress=on_progress,
                    )
                )
        return results

    def upload(
        self,
        local_path: str | Path,
        *,
        remote_path: str | None = None,
        resume: bool = True,
        overwrite: bool = False,
        on_progress: Callable[[UploadProgress], None] | None = None,
    ) -> dict | list[dict]:
        local_path = str(local_path)
        if os.path.isdir(local_path):
            return self.upload_dir(
                local_path,
                remote_dir=remote_path,
                resume=resume,
                overwrite=overwrite,
                on_progress=on_progress,
            )
        return self.upload_file(
            local_path,
            remote_path=remote_path,
            resume=resume,
            overwrite=overwrite,
            on_progress=on_progress,
        )

    def share(self, remote_path: str, *, password: str | None = None, period_days: int = 7) -> str:
        remote_path = self.normalize_remote_path(remote_path)
        fs_id = self.get_fs_id(remote_path)

        url = "https://pan.baidu.com/share/pset"
        params = {
            "channel": "chunlei",
            "clienttype": "0",
            "web": "1",
            "bdstoken": self.bdstoken,
            "app_id": self._config.app_id,
        }
        data = {
            "fid_list": json.dumps([fs_id], separators=(",", ":")),
            "schannel": "0",
            "channel_list": "[]",
            "linkOrQrcode": "link",
            "eflag_disable": "true",
            "public": "0",
            "is_knowledge": "0",
            "period": str(int(period_days)),
        }
        if password:
            data["pwd"] = password
            data["schannel"] = "4"

        headers = {"User-Agent": self._config.user_agent}
        resp = self._request("POST", url, params=params, data=data, headers=headers)
        payload = resp.json()
        print(payload)
        link = payload.get("link") or ""
        if not link:
            raise BaiduPanApiError("share failed", payload=payload)
        return link

    def iter_uploaded_files(self, local_dir: str | Path) -> Iterable[tuple[str, str]]:
        """
        Convenience helper: yields (local_path, remote_path) as upload_dir would map them.
        """
        local_dir = str(local_dir)
        base_name = os.path.basename(os.path.abspath(local_dir).rstrip("\\/"))
        remote_dir = self.normalize_remote_path(base_name)
        for root, _dirs, files in os.walk(local_dir):
            for name in files:
                full_path = os.path.join(root, name)
                rel = os.path.relpath(full_path, local_dir).replace("\\", "/")
                yield full_path, f"{remote_dir}/{rel}".replace("//", "/")

    def get_dir_list(self, remote_dir: str) -> list[dict]:
        remote_dir = self.normalize_remote_path(remote_dir)
        url = "https://pan.baidu.com/api/list"
        params = {
            "dir": remote_dir,
            "num": "100",
            "order": "time",
            "desc": "1",
            "clienttype": "0",
            "app_id": self._config.app_id,
            "web": "1",
        }
        headers = {
            "User-Agent": self._config.user_agent,
        }
        resp = self._request("GET", url, params=params, headers=headers)
        payload = resp.json()
        if payload.get("errno") == -9:
            return []
        return payload.get("list") or []

    def create_folder(self, remote_dir: str) -> dict:
        remote_dir = self.normalize_remote_path(remote_dir)
        existing = self.get_dir_list(remote_dir)
        if existing:
            return existing[0]
        url = "https://pan.baidu.com/api/create"
        params = {
            "commit": "true",
            "bdstoken": self.bdstoken,
            "app_id": self._config.app_id,
            "web": "1",
            "clienttype": "0",
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": "https://pan.baidu.com/disk/main",
        }
        data = {
            "path": remote_dir,
            "isdir": "1",
            "block_list": "[]",
        }
        resp = self._request("POST", url, params=params, headers=headers, data=data)
        payload = resp.json()
        if payload.get("errno") != 0:
            raise BaiduPanApiError("create folder failed", payload=payload)
        return payload

    def transfer_share(
        self,
        share_link: str,
        *,
        password: str | None = None,
        remote_dir: str | None = None,
    ) -> dict:
        """
        Transfer a shared file/folder to own Baidu Pan.

        Returns the list of transferred files info.
        """
        
        headers = {"User-Agent": self._config.user_agent}
        share_link_params = extract_params(share_link)
        surl = share_link_params.get('surl', '') # without prefix 1
        if not password:
            password = share_link_params.get('pwd', '')
        if not surl:
            con = share_link.split('/s/')
            if len(con) >= 2:
                surl = con[1].split('?')[0][1:]
            if not surl:
                raise BaiduPanApiError("invalid share link, missing surl")
            
        # must-have call before verify
        url = "https://pan.baidu.com/share/tplconfig"
        params = {
            "surl": '1' + surl,
            "fields": "LRURPVSDB",
            "view_mode": "1",
            "channel": "chunlei",
            "web": "1",
            "app_id": self._config.app_id,
            "bdstoken": self.bdstoken,
            "clienttype": "0",
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": f"https://pan.baidu.com/share/init?surl={surl}",
        }
        resp = self._request("GET", url, params=params, headers=headers)
        payload = resp.json()
        if payload.get("errno") != 0:
            raise BaiduPanApiError("tplconfig failed", payload=payload)
        
            
        # Verify share link and get BDCLND cookie
        url = "https://pan.baidu.com/share/verify"
        params = {
            "t": int(time.time() * 1000),
            "surl": surl,
            "channel": "chunlei",
            "web": "1",
            "app_id": self._config.app_id,
            "bdstoken": self.bdstoken,
            "clienttype": "0",
        }
        data = {
            'pwd': password or "",
            'vcode': "",
            'vcode_str': "",
        }
        resp = self._request("POST", url, params=params, data=data, headers=headers)
        cookie = resp.cookies.get_dict()
        bdclnd = cookie.get("BDCLND")
        self._get_session().cookies.set("BDCLND", bdclnd or "")
        if not bdclnd:
            raise BaiduPanApiError("share verify failed", payload=resp.json())
        
        # Get share info: uk, share_id, fs_id list
        url = "https://pan.baidu.com/share/list"
        params = {
            "app_id": self._config.app_id,
            "desc": "1",
            "showempty": "0",
            "page": "1",
            "num": "20",
            "order": "time",
            "shorturl": surl,
            "root": "1",
            "view_mode": "1",
            "channel": "chunlei",
            "web": "1",
            "bdstoken": self.bdstoken,
            "clienttype": "0",
        }
        headers = {
            "User-Agent": self._config.user_agent,
            "Referer": f"https://pan.baidu.com/s/1{surl}",
        }
        
        resp = self._request("GET", url, params=params, headers=headers)
        result = resp.json()
        
        uk = result.get("uk", "")
        share_id = result.get("share_id", "")
        fsid_list: list[str] = []
        for item in result.get("list", []):
            fsid_list.append(item.get("fs_id", ""))
        if not (uk and share_id and fsid_list):
            show_msg = result.get("show_msg", "")
            if show_msg:
                raise BaiduPanApiError(f"share list failed: {show_msg}", payload=result)
            raise BaiduPanApiError("share list failed", payload=result)
        
        
        # ensure folder exists
        if remote_dir:
            self.create_folder(remote_dir)
            
        # Transfer the shared file/folder
        url = "https://pan.baidu.com/share/transfer"
        params = {
            "shareid": share_id,
            "from": uk,
            "channel": "chunlei",
            "web": "1",
            "app_id": self._config.app_id,
            "bdstoken": self.bdstoken,
            "clienttype": "0",
        }
        data = {
            "fsidlist": json.dumps(fsid_list, separators=(",", ":")),
            "path": remote_dir or self._remote_root,
        }

        resp = self._request("POST", url, params=params, data=data, headers=headers)
        payload = resp.json()
        if payload.get("errno") != 0:
            show_msg = payload.get("show_msg", "")
            if show_msg:
                raise BaiduPanApiError(f"transfer share failed: {show_msg}", payload=payload)
            raise BaiduPanApiError("transfer share failed", payload=payload)
        return payload.get('extra', {}).get('list', {})
    
    def is_share_link(self, share_link: str) -> bool:
        """
        Check if a given link is a valid Baidu Pan share link.
        """
        if 'baidu' not in share_link:
            return False
        share_link_params = extract_params(share_link)
        surl = share_link_params.get('surl', '')
        if surl:
            return True
        con = share_link.split('/s/')
        if len(con) >= 2:
            surl = con[1].split('?')[0]
        return bool(surl)
    
    def is_link_stale(self, share_link: str) -> bool:
        """
        Check if a given share link is stale (expired or invalid).
        """
        headers = {"User-Agent": self._config.user_agent}
        resp = self._request("GET", share_link, headers=headers)
        if resp.status_code == 404:
            return True
        if '链接失效申诉' in resp.text:
            return True
        return False
        