# hva-pepper-scan


## Local configuration

The sketch reads `secrets.h`, which is intentionally untracked. Copy
`secrets.example.h` to `secrets.h` and fill in Wi-Fi and broker settings locally.
Use a distinct MQTT client ID for each scanner. The example contains no working
credentials or broker hostname and uses the generic topic `pepper/scanner`.
Configure the robot's scanner subscription to match.

Keep the populated header out of Git. The original committed infrastructure
values have been removed from the current sketch; this does not remove old
values from Git history or rotate any exposed credentials.

The sketch depends on ESP8266 board support, `PubSubClient` and
`SimpleKalmanFilter`. It reads the analog LDR input and publishes the original
`ldr` and `scan_state` messages. Its existing `WiFiClient` transport uses plain
TCP MQTT; setting a TLS port alone does not add TLS support. Flashing starts the
hardware connection loop, so configuration and flashing are deliberate operator
steps, not part of the offline tablet preview.

No Arduino toolchain was available during cleanup. Compilation, wiring,
calibration, networking and live scanner behavior have not been validated.
The media below documents the historical prototype; it was not regenerated.

## Hardware setup

LDR connected to ESP8266 (WEMOS D1 Mini).

Image of device:

![image](https://i.imgur.com/pz5vonu.png)


## Measurements

Success:

![image](https://i.imgur.com/g7VptcJ.gif)

Error (Limited scan < 1 minute):

![image](https://i.imgur.com/iMbPieQ.gif)

Generic error:

![image](https://i.imgur.com/BKYaZzE.gif)
