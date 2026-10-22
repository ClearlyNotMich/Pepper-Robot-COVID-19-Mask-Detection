# Third-party code, assets and attribution

This document records identifiable sources and the owner's permission basis.
It does not assign a new license to project code or replace existing terms.

## NAOqi SDK

`SDK/pynaoqi-python2.7-2.5.7.1-win32-vs2013/` is a bundled vendor SDK snapshot,
including Python wrappers, Windows DLL/PYD/EXE files and debug symbols. Its
contents are preserved byte-for-byte. These are Aldebaran/SoftBank Robotics and
third-party components, not code authored for this coursework.

The snapshot contains existing notices within source files but no standalone
SDK license/notice manifest was found. The owner explicitly confirmed permission
for public redistribution of the SDK and third-party binaries, including retained
history, on 22 October 2026. Specific grant documents or additional attribution
requirements were not supplied; that confirmation is not an independently
verified license grant to downstream users. Obtain the applicable vendor terms
and a compatible installation through your institution/vendor before reuse.

## Eclipse Paho

`tablet_website/src/paho-mqtt.js` and `paho-mqtt-min.js` retain their original IBM
copyright and contributor notices. Their headers identify Eclipse Public License
1.0 and Eclipse Distribution License 1.0. The copies are unchanged by cleanup.
License texts are included at [EPL-1.0](LICENSES/EPL-1.0.txt) and
[EDL-1.0](LICENSES/EDL-1.0.txt), obtained from the
[upstream Paho repository](https://github.com/eclipse-paho/paho.mqtt.javascript/blob/master/epl-v10)
and [Eclipse Foundation](https://www.eclipse.org/org/documents/edl-v10/EDL-1.0.txt).
These texts apply to the identified third-party component; they do not license
all repository contents.

The Python client is an external dependency. The chosen legacy API version is
documented by [Paho MQTT 1.6.1](https://pypi.org/project/paho-mqtt/1.6.1/).
The browser wrapper and application scripts are separate files and are not
represented as the unmodified Paho library.

## Scanner dependencies

`hva_scanner/hvascannerwemos.ino` uses ESP8266WiFi, PubSubClient and
SimpleKalmanFilter. These libraries are not bundled here. Install them separately
under their own terms; the original sketch did not record reproducible versions.
The STL is a project hardware asset, not an Arduino library.

## Institutional and project assets

The repository retains HvA branding, two copies of the Wibauthuis floor plan,
the robot-coordinate compass graphic, the scanner enclosure STL and `data.txt`.
The latter holds only a robot-local exploration-map path, not the map itself.
Original scanner documentation also links to externally hosted device/demo
images. Those remote files are not part of this Git archive or the preservation
check, and are not rehosted by this cleanup.

The owner confirmed team authority, institution/course permission, and public
redistribution rights for these assets and retained Git history on 22 October
2026. Specific asset creators and additional required attribution wording were
not supplied. Existing labels, logos, filenames and documentation remain; no
institutional endorsement or new asset license is claimed.

## Project contributions

The original commits are attributed to Michal Kozdon. The project includes
collaborative coursework and third-party material; no sole-authorship claim or
unverified allocation of teammate contributions is made. Git author metadata and
all original commits are preserved.
