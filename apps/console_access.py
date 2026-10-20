"""Local operator access, signed LAN sessions and same-origin write protection."""
from __future__ import annotations

import hashlib
import hmac
from http.cookies import SimpleCookie, CookieError
import ipaddress
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlparse

from console_support import ConsoleError


class ConsoleAccess:
    def __init__(self,directory,host):
        self.path=Path(directory)/"operation-key"
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if not self.path.exists():
            descriptor=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(descriptor,"w") as handle:handle.write(secrets.token_urlsafe(32)+"\n")
        self.path.chmod(0o600)
        self.secret=self.path.read_text().strip()
        if len(self.secret)<24:raise RuntimeError("操作密钥格式无效")
        public=os.environ.get("ROBOT_STATION_PUBLIC_HOST","192.168.123.100")
        self.hosts={"localhost","127.0.0.1","::1",host,public}
        self.local_addresses={"127.0.0.1","::1"}
        # Only addresses actually assigned to this workstation count as local callers.
        try:
            import socket
            import subprocess,json
            rows=json.loads(subprocess.check_output(["ip","-j","address"],timeout=2))
            self.local_addresses.update(a["local"] for row in rows for a in row.get("addr_info",[]) if a.get("local")==public)
        except Exception:pass
        try:
            bound=ipaddress.ip_address(host)
            if not bound.is_unspecified:self.local_addresses.add(str(bound))
        except ValueError:pass
        self.attempts={}
        self.lock=threading.Lock()

    def sign(self,value):return hmac.new(self.secret.encode(),value.encode(),hashlib.sha256).hexdigest()

    def validate_host(self,headers):
        try:host=urlparse("http://"+headers.get("Host","")).hostname
        except ValueError:raise ConsoleError("访问地址格式无效",403,"host_not_allowed")
        if host not in self.hosts:raise ConsoleError("访问地址未在允许列表中",403,"host_not_allowed")

    def authorized(self,headers,address):
        if ipaddress.ip_address(address).is_loopback or address in self.local_addresses:return True
        try:
            cookie=SimpleCookie(headers.get("Cookie",""))
            value=cookie["robot_station_operator"].value
            expires,signature=value.split(".",1)
            return int(expires)>time.time() and hmac.compare_digest(signature,self.sign("session:"+expires))
        except (KeyError,ValueError,TypeError,CookieError):return False

    def view(self,headers,address):
        authorized=self.authorized(headers,address)
        return {"authorized":authorized,"csrf_token":self.sign("csrf") if authorized else None,
                "message":"已授权操作" if authorized else "当前为只读访问，请使用工作站操作密钥授权"}

    def guard(self,headers,address,login=False):
        self.validate_host(headers)
        origin=headers.get("Origin")
        if origin and urlparse(origin).netloc!=headers.get("Host"):
            raise ConsoleError("拒绝跨来源操作",403,"cross_origin")
        if headers.get("Sec-Fetch-Site") in {"cross-site","same-site"}:
            raise ConsoleError("拒绝跨来源操作",403,"cross_origin")
        if login:return
        if not self.authorized(headers,address):raise ConsoleError("需要操作授权",401,"operator_required")
        if origin or headers.get("Sec-Fetch-Site"):
            if not hmac.compare_digest(headers.get("X-Console-CSRF",""),self.sign("csrf")):
                raise ConsoleError("操作会话已变化，请刷新页面",403,"csrf_required")

    def login(self,token,address):
        with self.lock:
            attempts=[t for t in self.attempts.get(address,[]) if time.monotonic()-t<60]
            self.attempts[address]=attempts
            if len(attempts)>=5:raise ConsoleError("授权尝试过于频繁，请一分钟后重试",429,"login_limit")
            attempts.append(time.monotonic())
            if not isinstance(token,str) or not hmac.compare_digest(token.encode(),self.secret.encode()):
                raise ConsoleError("操作密钥不正确",401,"operator_required")
            self.attempts[address]=[]
            expires=str(int(time.time()+8*3600))
            return "robot_station_operator="+expires+"."+self.sign("session:"+expires)+"; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800"
