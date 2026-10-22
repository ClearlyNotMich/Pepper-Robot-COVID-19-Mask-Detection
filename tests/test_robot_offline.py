"""Python 3 offline checks; robot, broker, credentials and SDK are all fakes."""
import contextlib
import copy
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main
from robot.pepper import Pepper
from robot.tablet import Tablet
from tools.config import ConfigError, load_config
from tools.paho_mqtt import PahoMqtt


RAW_CONFIG = {
    "robot_host": "robot.lab",
    "robot_port": 9559,
    "tablet_url": "http://tablet.lab/tablet.html",
    "clients": [{
        "name": "test-client", "host": "broker.lab", "port": 1883,
        "username_env": "TEST_MQTT_USER", "password_env": "TEST_MQTT_PASSWORD",
        "command_topic": "pepper/commands",
        "topics": ["pepper/commands", "pepper/scanner"],
    }],
}
TEST_ENV = {"TEST_MQTT_USER": "synthetic-user", "TEST_MQTT_PASSWORD": "synthetic-test-value"}


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"

    def load(self, payload=None, **kwargs):
        self.path.write_text(json.dumps(RAW_CONFIG if payload is None else payload))
        return load_config(str(self.path), **kwargs)

    def test_valid_configuration_reads_credentials_from_environment(self):
        result, issues = self.load(environ=TEST_ENV, for_run=True)
        self.assertEqual(issues, [])
        self.assertEqual(result["clients"][0]["username"], TEST_ENV["TEST_MQTT_USER"])
        self.assertEqual(result["clients"][0]["password"], TEST_ENV["TEST_MQTT_PASSWORD"])
        self.assertEqual(result["robot_port"], 9559)

    def test_missing_credentials_are_reported_without_values(self):
        result, issues = self.load(environ={})
        self.assertIsNone(result["clients"][0]["password"])
        self.assertTrue(any("TEST_MQTT_PASSWORD" in issue for issue in issues))
        with self.assertRaisesRegex(ConfigError, "not ready"):
            self.load(environ={}, for_run=True)

    def test_inline_credentials_are_rejected_without_echo(self):
        payload = copy.deepcopy(RAW_CONFIG)
        payload["clients"][0]["pw"] = "synthetic-must-not-be-echoed"
        with self.assertRaises(ConfigError) as raised:
            self.load(payload, environ=TEST_ENV)
        self.assertNotIn(payload["clients"][0]["pw"], str(raised.exception))

    def test_example_endpoints_are_checkable_but_never_run_ready(self):
        example = Path(main.__file__).parent / "tools/config.example.json"
        result, issues = load_config(str(example), environ={})
        self.assertTrue(issues)
        self.assertTrue(result["robot_host"].endswith(".invalid"))
        with self.assertRaisesRegex(ConfigError, "not ready"):
            load_config(str(example), environ={}, for_run=True)

    def test_invalid_ports_hosts_urls_and_topics_are_rejected(self):
        variants = []
        for key, value in (("robot_port", True), ("robot_port", 70000),
                           ("robot_host", "tcp://robot.lab"),
                           ("tablet_url", "http://user:synthetic-password@tablet.lab")):
            payload = copy.deepcopy(RAW_CONFIG)
            payload[key] = value
            variants.append(payload)
        for key, value in (("port", 0), ("topics", []), ("password_env", "bad variable"),
                           ("command_topic", "unsubscribed/topic")):
            payload = copy.deepcopy(RAW_CONFIG)
            payload["clients"][0][key] = value
            variants.append(payload)
        for payload in variants:
            with self.subTest(field=list(payload)), self.assertRaises(ConfigError):
                self.load(payload, environ=TEST_ENV)

    def test_missing_or_malformed_file_has_sanitized_error(self):
        with self.assertRaisesRegex(ConfigError, "Cannot read"):
            load_config(str(self.path), environ={})
        self.path.write_text('{"pw": "synthetic-do-not-echo", invalid')
        with self.assertRaises(ConfigError) as raised:
            load_config(str(self.path), environ={})
        self.assertEqual(str(raised.exception), "Configuration file is not valid JSON")

    def test_check_config_never_dispatches_run_or_prints_credentials(self):
        self.load(environ=TEST_ENV)
        output = io.StringIO()
        with patch.dict("os.environ", TEST_ENV, clear=True), patch.object(main, "run_robot") as run:
            with contextlib.redirect_stdout(output):
                status = main.main(["--check-config", "--config", str(self.path)])
        self.assertEqual(status, 0)
        run.assert_not_called()
        self.assertNotIn(TEST_ENV["TEST_MQTT_PASSWORD"], output.getvalue())
        self.assertNotIn(TEST_ENV["TEST_MQTT_USER"], output.getvalue())

    def test_invalid_run_configuration_does_not_dispatch(self):
        self.load(environ={})
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(main, "run_robot") as run,
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            main.main(["--run", "--config", str(self.path)])
        self.assertEqual(raised.exception.code, 2)
        run.assert_not_called()

    def test_runtime_exception_messages_are_not_echoed(self):
        self.load(environ=TEST_ENV)
        output = io.StringIO()
        with (
            patch.dict("os.environ", TEST_ENV, clear=True),
            patch.object(main, "run_robot", side_effect=RuntimeError(TEST_ENV["TEST_MQTT_PASSWORD"])),
            contextlib.redirect_stderr(output),
        ):
            status = main.main(["--run", "--config", str(self.path)])
        self.assertEqual(status, 1)
        self.assertNotIn(TEST_ENV["TEST_MQTT_PASSWORD"], output.getvalue())

    def test_environment_can_select_configuration_file(self):
        self.load(environ=TEST_ENV)
        environment = dict(TEST_ENV, PEPPER_CONFIG=str(self.path))
        with patch.dict("os.environ", environment, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main.main(["--check-config"]), 0)


class MqttTests(unittest.TestCase):
    def setUp(self):
        self.pepper = SimpleNamespace(mqtt_msg=None)
        self.configuration = dict(RAW_CONFIG["clients"][0], username="fake-user", password="fake-password")
        self.client = Mock()

    def make(self):
        return PahoMqtt(self.pepper, [self.configuration], client_factory=Mock(return_value=self.client))

    def test_explicit_client_setup_uses_selected_topics_and_credentials(self):
        adapter = self.make()
        self.client.username_pw_set.assert_called_once_with("fake-user", "fake-password")
        self.client.connect.assert_called_once_with("broker.lab", 1883)
        self.client.loop_start.assert_called_once_with()
        adapter.on_connect(self.client, None, {}, 0)
        self.client.subscribe.assert_called_once_with([("pepper/commands", 0), ("pepper/scanner", 0)])
        adapter.close()
        self.client.disconnect.assert_called_once_with()
        self.client.loop_stop.assert_called_once_with()
        self.assertEqual(adapter.clients, [])

    def test_commands_require_command_topic_and_valid_text(self):
        adapter = self.make()
        for topic, payload in (("pepper/scanner", b"stop"), ("pepper/commands", b"unknown"),
                               ("pepper/commands", b"\xff")):
            adapter.on_message(self.client, None, SimpleNamespace(topic=topic, payload=payload))
            self.assertIsNone(self.pepper.mqtt_msg)
        adapter.on_message(self.client, None, SimpleNamespace(topic="pepper/commands", payload=b"entrance_mode"))
        self.assertEqual(self.pepper.mqtt_msg, "entrance_mode")
        adapter.close()

    def test_late_connection_failure_closes_all_created_clients(self):
        second = Mock()
        second.connect.side_effect = OSError("synthetic connection failure")
        factory = Mock(side_effect=[self.client, second])
        with self.assertRaises(OSError):
            PahoMqtt(self.pepper, [self.configuration, self.configuration], client_factory=factory)
        for client in (self.client, second):
            client.disconnect.assert_called_once_with()
            client.loop_stop.assert_called_once_with()

    def test_loop_stop_is_attempted_even_if_disconnect_fails(self):
        adapter = self.make()
        self.client.disconnect.side_effect = RuntimeError("synthetic disconnect failure")
        adapter.close()
        self.client.loop_stop.assert_called_once_with()


class RobotLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.factory = Mock(return_value=self.session)
        self.robot = Pepper(RAW_CONFIG, session_factory=self.factory)

    def test_construction_is_offline_and_start_initializes_modules_once(self):
        self.factory.assert_not_called()
        with patch.object(self.robot, "load_modules") as modules, patch.object(self.robot, "load_tools") as tools:
            self.robot.start()
        self.session.connect.assert_called_once_with("tcp://robot.lab:9559")
        modules.assert_called_once_with()
        tools.assert_called_once_with()
        self.robot.close()

    def test_failed_connection_does_not_recurse_and_releases_session(self):
        self.session.connect.side_effect = RuntimeError("synthetic failure")
        with self.assertRaises(RuntimeError):
            self.robot.start()
        self.factory.assert_called_once_with()
        self.session.close.assert_called_once_with()

    def test_failed_module_setup_releases_session(self):
        with patch.object(self.robot, "load_modules", side_effect=RuntimeError("setup")):
            with self.assertRaises(RuntimeError):
                self.robot.start()
        self.session.close.assert_called_once_with()

    def test_cleanup_releases_session_even_when_mqtt_cleanup_fails(self):
        self.robot.session = self.session
        self.robot._paho_mqtt = Mock()
        self.robot._paho_mqtt.close.side_effect = RuntimeError("cleanup")
        self.robot.close()
        self.session.close.assert_called_once_with()

    def test_disconnection_is_reported_without_automatic_reconnect(self):
        self.robot.session = self.session
        self.session.isConnected.return_value = False
        with self.assertRaisesRegex(RuntimeError, "restart"):
            self.robot.check_connection()
        self.factory.assert_not_called()

    def test_tablet_does_not_show_page_until_explicit_call(self):
        tablet = Tablet(self.session, "http://tablet.lab/tablet.html")
        service = self.session.service.return_value
        service.enableWifi.assert_not_called()
        service.showWebview.assert_not_called()
        tablet.show_website()
        service.showWebview.assert_called_once_with("http://tablet.lab/tablet.html")

    def test_dispatch_start_failure_always_closes_robot(self):
        robot = Mock()
        robot.start.side_effect = RuntimeError("startup")
        with self.assertRaises(RuntimeError):
            main.run_robot(RAW_CONFIG, pepper_factory=Mock(return_value=robot))
        robot.close.assert_called_once_with()
        robot.motion.assert_not_called()

    def test_explicit_stop_preserves_shutdown_and_releases_resources(self):
        robot = Mock()
        robot.mqtt_msg = "stop"
        main.run_robot(RAW_CONFIG, pepper_factory=Mock(return_value=robot))
        robot.system.return_value.shutdown.assert_called_once_with()
        robot.close.assert_called_once_with()


class ImportSafetyTests(unittest.TestCase):
    def test_all_project_python_modules_import_without_qi_or_paho(self):
        root = Path(main.__file__).resolve().parent
        script = r'''
import builtins
import importlib
import os
from pathlib import Path
import runpy
import sys
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
original_import = builtins.__import__
def checked_import(name, *args, **kwargs):
    if name.split('.')[0] in {'qi', 'paho'}:
        raise AssertionError('Runtime dependency imported during offline operation')
    return original_import(name, *args, **kwargs)
builtins.__import__ = checked_import
before = dict(os.environ)
for folder in ('robot', 'tools'):
    for path in (root / folder).glob('*.py'):
        importlib.import_module(folder + '.' + path.stem)
import main
assert main.main(['--check-config', '--config', str(root / 'tools/config.example.json')]) == 0
try:
    main.main(['--help'])
except SystemExit as error:
    assert error.code == 0
assert dict(os.environ) == before
'''
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-B", "-I", "-c", script, str(root)],
                cwd=directory, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
