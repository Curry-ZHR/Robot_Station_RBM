from pathlib import Path
import tempfile
import unittest

from console_access import ConsoleAccess
from console_support import ConsoleError


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.access=ConsoleAccess(Path(self.temp.name),"192.168.123.100")
        self.headers={"Host":"192.168.123.100:9999","Origin":"http://192.168.123.100:9999"}

    def test_lan_requires_signed_session_and_browser_csrf(self):
        with self.assertRaises(ConsoleError):self.access.guard(self.headers,"192.168.123.50")
        cookie=self.access.login(self.access.secret,"192.168.123.50").split(";",1)[0]
        self.headers["Cookie"]=cookie
        self.assertTrue(self.access.authorized(self.headers,"192.168.123.50"))
        with self.assertRaises(ConsoleError):self.access.guard(self.headers,"192.168.123.50")
        self.headers["X-Console-CSRF"]=self.access.view(self.headers,"192.168.123.50")["csrf_token"]
        self.access.guard(self.headers,"192.168.123.50")
        self.assertNotEqual(self.headers["X-Console-CSRF"],self.access.secret)

    def test_loopback_cli_allowed_but_foreign_origin_and_host_rejected(self):
        self.access.guard({"Host":"127.0.0.1:12947"},"127.0.0.1")
        for changes in [{"Origin":"http://foreign.test"},{"Host":"foreign.test:9999"},{"Sec-Fetch-Site":"cross-site"}]:
            with self.assertRaises(ConsoleError):self.access.guard({**self.headers,**changes},"127.0.0.1")

    def test_credentials_persist_privately_and_wrong_tokens_rate_limit(self):
        recovered=ConsoleAccess(Path(self.temp.name),"192.168.123.100")
        self.assertEqual(recovered.secret,self.access.secret)
        self.assertEqual(self.access.path.stat().st_mode&0o777,0o600)
        for _ in range(5):
            with self.assertRaises(ConsoleError):self.access.login("wrong","192.168.123.51")
        with self.assertRaises(ConsoleError) as ctx:self.access.login("wrong","192.168.123.51")
        self.assertEqual(ctx.exception.status,429)


if __name__=="__main__":unittest.main()
