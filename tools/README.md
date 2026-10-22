# Local configuration

`config.example.json` contains reserved example endpoints and environment-variable
names, never usable credentials. Copy it to the ignored `tools/config.local.json`,
set the robot host, tablet URL, broker host/port and topics, then set the named
credential variables in your local environment. Do not commit the local file or
put usernames/passwords directly in JSON. Previously committed credentials remain
in Git history; removing this file does not revoke them.

```sh
python main.py --check-config --config tools/config.example.json
```

This offline check needs only the standard library. A valid schema exits zero
and separately reports missing credential variables or reserved example endpoints.
It does not test credentials, endpoint availability, the SDK, or robot behavior.
`--config PATH` can be replaced by the `PEPPER_CONFIG` environment variable.
Only an explicit `--run` starts network connections and robot actions, and it
rejects missing credential values and `.invalid` endpoints first.

Each client has `name`, `host`, `port`, `username_env`, `password_env`, `topics`,
and optional `command_topic` (default `pepper/commands`, included in `topics`).
Only that topic accepts `entrance_mode`, `surveillance_mode`, or `stop` commands.
Scanner payloads on other topics are not executed or printed. The historical
`stop` command shuts the robot down; application cleanup is not an emergency stop.

The runtime targets the archived Python 2.7 NAOqi SDK and Paho MQTT 1.6.1. Python 3
is used for offline checks with fakes; no robot-runtime compatibility is claimed.
MQTT transport here remains plaintext, without TLS. Use only an isolated,
controlled lab network with appropriate broker access controls. Never reuse the
historically exposed credentials. Hardware behavior, navigation limits and
reconnection procedures still require supervised validation.
