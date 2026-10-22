"""Offline, Python 2.7-compatible validation of local Pepper configuration."""
from __future__ import print_function

import io
import json
import os
import re
try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

try:
    string_types = (basestring,)
    integer_types = (int, long)
except NameError:
    string_types = (str,)
    integer_types = (int,)


class ConfigError(ValueError):
    """A configuration problem, reported without credential values."""


def _text(value, field):
    if not isinstance(value, string_types) or not value.strip():
        raise ConfigError(field + " must be a nonempty string")
    return value.strip()


def _port(value, field):
    if isinstance(value, bool) or not isinstance(value, integer_types) or not 1 <= value <= 65535:
        raise ConfigError(field + " must be an integer from 1 to 65535")
    return value


def _host(value, field):
    value = _text(value, field)
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", value):
        raise ConfigError(field + " must be a hostname or IPv4 address, without a URL scheme")
    return value


def _environment_name(value, field):
    value = _text(value, field)
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        raise ConfigError(field + " must name an environment variable")
    return value


def load_config(path, environ=None, for_run=False):
    """Validate JSON without connecting or importing qi/paho.

    Return validated configuration and readiness problems. Credentials are read
    only from named environment variables; readiness errors never contain them.
    Offline checking accepts reserved .invalid example endpoints but reports
    them as not ready. Explicit runs require all readiness checks to pass.
    """
    environ = os.environ if environ is None else environ
    try:
        with io.open(path, "r", encoding="utf-8") as source:
            raw = json.load(source)
    except (IOError, OSError):
        raise ConfigError("Cannot read the selected configuration file")
    except ValueError:
        raise ConfigError("Configuration file is not valid JSON")
    if not isinstance(raw, dict):
        raise ConfigError("Configuration must be a JSON object")
    host = _host(raw.get("robot_host"), "robot_host")
    port = _port(raw.get("robot_port", 9559), "robot_port")
    tablet_url = _text(raw.get("tablet_url"), "tablet_url")
    try:
        parsed = urlsplit(tablet_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError()
    except ValueError:
        raise ConfigError("tablet_url must be an HTTP(S) URL without embedded credentials")
    clients = raw.get("clients")
    if not isinstance(clients, list) or not clients:
        raise ConfigError("clients must be a nonempty list")
    result = {"robot_host": host, "robot_port": port, "tablet_url": tablet_url, "clients": []}
    problems = []
    if host.lower().endswith(".invalid") or parsed.hostname.lower().endswith(".invalid"):
        problems.append("replace the reserved robot/tablet example endpoints")
    seen = set()
    for index, client in enumerate(clients):
        prefix = "clients[%d]" % index
        if not isinstance(client, dict):
            raise ConfigError(prefix + " must be an object")
        if any(key in client for key in ("user", "pw", "password", "username")):
            raise ConfigError(prefix + " must use username_env/password_env instead of inline credentials")
        name = _text(client.get("name"), prefix + ".name")
        if name in seen:
            raise ConfigError("client names must be unique")
        seen.add(name)
        broker = _host(client.get("host"), prefix + ".host")
        broker_port = _port(client.get("port"), prefix + ".port")
        topics = client.get("topics")
        if not isinstance(topics, list) or not topics:
            raise ConfigError(prefix + ".topics must be a nonempty list")
        topics = [_text(topic, prefix + ".topics") for topic in topics]
        command_topic = _text(client.get("command_topic", "pepper/commands"), prefix + ".command_topic")
        if command_topic not in topics:
            raise ConfigError(prefix + ".command_topic must be included in topics")
        user_env = _environment_name(client.get("username_env"), prefix + ".username_env")
        password_env = _environment_name(client.get("password_env"), prefix + ".password_env")
        username, password = environ.get(user_env), environ.get(password_env)
        for variable, value in ((user_env, username), (password_env, password)):
            if not isinstance(value, string_types) or not value.strip():
                problems.append("missing credential environment variable " + variable)
        if broker.lower().endswith(".invalid"):
            problems.append(prefix + ": replace the reserved broker example endpoint")
        result["clients"].append({
            "name": name, "host": broker, "port": broker_port, "topics": topics,
            "command_topic": command_topic,
            "username_env": user_env, "password_env": password_env,
            "username": username, "password": password,
        })
    if for_run and problems:
        raise ConfigError("Configuration is not ready: " + "; ".join(problems))
    return result, problems
