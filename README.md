# Pepper robot interaction prototype

Coursework integrating a Pepper robot, a tablet interface and an ESP8266 light
sensor over MQTT. The project explores entrance greetings, face tracking and
navigation during the COVID-19 period.

The repository keeps its historical name, `Pepper-Robot-COVID-19-Mask-Detection`,
but the committed code does **not** contain a trained mask classifier, Java
mask-detection implementation, evaluation dataset or measured detection accuracy.
The robot uses NAOqi face/person detection and speaks a reminder to wear a mask.
The scanner publishes light readings; it does not verify student identities or
operate a building-access system.

## What is here

| Component | Role | Limits |
| --- | --- | --- |
| `main.py`, `robot/` | Python wrappers for NAOqi speech, motion, awareness, face tracking, tablet display and exploration | Requires a compatible Pepper/NAOqi environment; hardware behavior has not been revalidated |
| `tools/` | MQTT clients and explicit local configuration | No broker is contacted by configuration checks |
| `tablet_website/` | Local tablet pages for selecting entrance/surveillance modes and sending commands | Preview opens disconnected; connecting requires operator configuration and credentials |
| `hva_scanner/` | ESP8266/WEMOS D1 Mini sketch using an LDR and a Kalman filter, plus enclosure STL | Publishes sensor readings; no card-decoding or access-control logic |
| `SDK/` | Historical Windows NAOqi Python 2.7 SDK snapshot | Third-party dependency, not original project code or a modern cross-platform environment |

## Inspect without a robot

The configuration checker and offline tests run with Python 3 and its standard
library. They do not require the vendor SDK or a running MQTT broker.

```sh
python3 main.py --help
python3 main.py --check-config --config tools/config.example.json
python3 -m unittest discover -s tests -p 'test_*.py'
```

The example deliberately contains placeholder hosts and references to unset
credential environment variables. A configuration check can therefore report
that it is not ready to run; it never tests network access or credentials.

For the tablet UI, serve only its directory locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory tablet_website
```

Open `http://127.0.0.1:8000/tablet.html`. Viewing the pages does not connect to a
broker or robot. See [tablet setup](tablet_website/README.md) for explicit
connection controls and the JavaScript test command.

## Configure an actual lab deployment

1. Obtain a Pepper-compatible NAOqi SDK/runtime through the institution or vendor.
   The archived SDK directory targets Python 2.7 and 32-bit Windows; it is not a
   Python 3 package. See [SDK notes](SDK/README.md).
2. Use the supported interpreter for that SDK. The MQTT dependency is pinned in
   `requirements-robot.txt`; this is a direct dependency list, not a reproduced
   hardware environment.
3. Copy `tools/config.example.json` to ignored `tools/config.local.json`. Supply
   your robot host, port, tablet URL and authorized MQTT broker endpoints/topics.
   The example command and sensor topics are `pepper/commands` and
   `pepper/scanner`; align them across Python, tablet and firmware.
4. Set the credential environment variables named in your local configuration.
   Keep their values out of source files, command examples and screenshots.
5. Run the offline configuration check, then use `--run` only in the prepared lab:

   ```sh
   python main.py --check-config --config tools/config.local.json
   python main.py --run --config tools/config.local.json
   ```

`--run` connects to the configured robot and brokers and can activate physical
motion. Configuration validation does not establish robot readiness. The original
navigation and interaction routines require supervised hardware validation.
The legacy Python/ESP8266 MQTT transport uses TCP without TLS; use it only on a
controlled lab network. Tablet WebSocket settings are separate.

See [MQTT configuration](tools/README.md) and
[scanner setup](hva_scanner/README.md) for component details. No original
university broker, robot hostname or hosted tablet page is selected by default.

## Validation and remaining limits

The cleanup exercises configuration parsing, import behavior and MQTT lifecycle
with local test doubles. It does not claim a complete end-to-end robot test.
No robot connection, physical movement, broker login, firmware flashing, SDK
binary execution or model training is part of this validation.

There is no recorded mask-detection benchmark. The historical `data.txt` contains
only a robot-local exploration-map path; the referenced map is not included.
Hardware, network permissions and legacy dependency compatibility must be
established for a new deployment.

## Credit and provenance

This is collaborative coursework. The original Git commits are attributed to
Michal Kozdon, but commit authorship alone does not establish sole authorship of
every component. The original team/component division has not been reconstructed.
Existing project documentation, institutional artwork and third-party notices
are retained with their context; no university endorsement is implied.

[Third-party and asset notes](THIRD_PARTY.md) distinguish project code, vendor
SDK files, Eclipse Paho and institutional assets. No blanket license is assigned
to the whole repository.

Historical commits contain two exposed MQTT credentials. Their removal from the
current configuration does not remove historical copies. Owner confirmation of
revocation/rotation remains outstanding; see [credential cleanup](CREDENTIALS.md).

