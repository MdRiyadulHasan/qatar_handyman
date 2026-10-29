import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase


class DeploymentConfigurationTests(SimpleTestCase):
    def load_settings(self, **overrides):
        env = os.environ.copy()
        for name in ("DEBUG", "DJANGO_DEBUG", "SECRET_KEY", "STATIC_ROOT", "MEDIA_ROOT", "SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_HSTS_SECONDS", "TRUST_X_FORWARDED_PROTO"):
            env.pop(name, None)
        env.update(overrides)
        code = "import json; import qatar_handyman.settings as s; print(json.dumps({'debug': s.DEBUG, 'static_url': s.STATIC_URL, 'static_root': str(s.STATIC_ROOT), 'media_root': str(s.MEDIA_ROOT), 'ssl_redirect': s.SECURE_SSL_REDIRECT, 'session_secure': s.SESSION_COOKIE_SECURE, 'csrf_secure': s.CSRF_COOKIE_SECURE, 'proxy_header': getattr(s, 'SECURE_PROXY_SSL_HEADER', None)}))"
        return subprocess.run([sys.executable, "-B", "-c", code], env=env,
                              cwd=Path(__file__).resolve().parent.parent,
                              capture_output=True, text=True)

    def test_local_configuration_allows_http_and_separate_output(self):
        result = self.load_settings(DJANGO_DEBUG="True", SECRET_KEY="")
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertTrue(values["debug"])
        self.assertEqual(values["static_url"], "/static/")
        self.assertTrue(values["static_root"].endswith("staticfiles"))
        self.assertFalse(values["ssl_redirect"])
        self.assertFalse(values["session_secure"])

    def test_production_requires_a_private_key(self):
        result = self.load_settings(DJANGO_DEBUG="False", SECRET_KEY="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private SECRET_KEY", result.stderr)

    def test_production_enables_https_without_trusting_proxy_headers(self):
        result = self.load_settings(DJANGO_DEBUG="False", SECRET_KEY="test-only-" + "abcdef0123456789" * 5)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertFalse(values["debug"])
        for key in ("ssl_redirect", "session_secure", "csrf_secure"):
            self.assertTrue(values[key])
        self.assertIsNone(values["proxy_header"])

    def test_invalid_debug_value_is_rejected(self):
        result = self.load_settings(DJANGO_DEBUG="not-a-boolean")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_DEBUG must be True or False", result.stderr)

    def test_separate_custom_static_and_media_paths(self):
        with TemporaryDirectory() as directory:
            static = str(Path(directory) / "static")
            media = str(Path(directory) / "media")
            result = self.load_settings(DJANGO_DEBUG="True", STATIC_ROOT=static, MEDIA_ROOT=media)
            self.assertEqual(result.returncode, 0, result.stderr)
            values = json.loads(result.stdout)
            self.assertEqual(values["static_root"], static)
            self.assertEqual(values["media_root"], media)

    def test_collectstatic_cannot_target_media_or_source_root(self):
        project = Path(__file__).resolve().parent.parent
        for target in (project, project / "media", project / "media" / "static"):
            with self.subTest(target=target):
                result = self.load_settings(DJANGO_DEBUG="True", STATIC_ROOT=str(target), MEDIA_ROOT=str(project / "media"))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ImproperlyConfigured", result.stderr)
