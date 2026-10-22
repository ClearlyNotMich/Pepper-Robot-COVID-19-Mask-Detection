# Pepper tablet pages

These static pages preserve the coursework's branding and images. They start as
an offline preview: opening a page, loading settings or following a preview link
does not contact an MQTT broker. The bundled Paho JavaScript is used locally;
there is no CDN or remote font dependency.

From the repository root, a local static server can serve the pages:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory tablet_website
```

Then open `http://127.0.0.1:8000/tablet.html` in a browser. This is a suggested
preview command, not a claim that a browser preview was validated during cleanup.
The four pages link to one another; navigation disconnects the current session.

## Explicit MQTT connection

The browser needs a broker's MQTT-over-WebSocket endpoint, not its raw TCP port.
The robot's Python configuration must use the same command topic.

1. Enter the hostname, WebSocket port/path and topic in the form. Alternatively,
   copy `config.example.json` to ignored `config.local.json`, fill in your broker
   hostname and endpoint settings, and select that file using **Import settings**.
   The example's empty hostname deliberately requires local configuration.
2. Enter broker credentials in the page only if the configured broker requires
   them, then select **Connect**. Configuration files reject credential fields.
3. Command buttons enable after connection and topic subscription succeed.
   Disconnect explicitly when finished. Reconnection requires another deliberate
   Connect action; the page does not reconnect or resend commands automatically.

TLS is enabled by default. Credentials are kept in memory for the active Paho
connection and cleared from the form after submission. This page does not save
credentials in files, cookies, localStorage or sessionStorage. Browser-managed
password saving is outside the page's control. Do not place credentials in the
HTML, JavaScript, configuration JSON, URL or committed files.

Commands use topic `pepper/commands` by default and the original payloads:
`stop`, `surveillance_mode` and `entrance_mode`. **Shut down robot** sends
`stop`, which invokes the project's robot shutdown routine. It is not an
emergency stop. Publishing uses QoS 0 and no retained flag; a sent message or
received echo is not proof that the robot executed it. Mode commands keep the
page open so navigation does not interrupt the publish.

The page shows incoming text using `textContent`, never as HTML. There is no
command queue while disconnected. Connection/subscription failures keep commands
disabled, and callbacks from a disconnected session cannot reactivate them.

## Offline checks and limits

```bash
node --test tablet_website/tests/mqtt.test.js
```

The tests use fake Paho clients and a minimal fake DOM; they make no network
connections. Production JavaScript uses ES5 syntax. The actual Pepper tablet
browser, rendered layout, broker connection, WebSocket/TLS endpoint, robot
execution and emergency-stop behavior were not validated during this cleanup.

The two bundled Paho files and their IBM/Eclipse notices are unchanged. See the
repository's `THIRD_PARTY.md` for third-party attribution and license status.
