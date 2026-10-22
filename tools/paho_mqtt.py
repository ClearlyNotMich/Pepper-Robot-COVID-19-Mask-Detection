"""Explicit MQTT connections for the historical Paho 1.x/Python 2.7 runtime."""
from __future__ import print_function

import uuid

COMMANDS = ("entrance_mode", "surveillance_mode", "stop")


class PahoMqtt(object):
    def __init__(self, pepper, configurations, client_factory=None):
        self.pepper = pepper
        self.clients = []
        self._topics = {}
        self._command_topics = {}
        if client_factory is None:
            import paho.mqtt.client as mqtt
            client_factory = mqtt.Client
        try:
            for configuration in configurations:
                client = client_factory(client_id="pepper-" + uuid.uuid4().hex)
                # Retain even a partially connected client so failure closes it.
                self.clients.append(client)
                self._topics[id(client)] = configuration["topics"]
                self._command_topics[id(client)] = configuration["command_topic"]
                client.username_pw_set(configuration["username"], configuration["password"])
                client.on_connect = self.on_connect
                client.on_message = self.on_message
                client.connect(configuration["host"], configuration["port"])
                client.loop_start()
        except BaseException:
            self.close()
            raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe([(topic, 0) for topic in self._topics[id(client)]])
        else:
            print("MQTT connection rejected; result code %s" % rc)

    def on_message(self, client, userdata, msg):
        # Do not log raw scanner payloads or treat them as robot commands.
        if msg.topic != self._command_topics.get(id(client)):
            return
        try:
            payload = msg.payload.decode("utf-8") if isinstance(msg.payload, bytes) else msg.payload
        except UnicodeError:
            return
        if payload in COMMANDS:
            self.pepper.mqtt_msg = payload

    def close(self):
        """Best-effort shutdown of every client, including failed connections."""
        for client in self.clients:
            try:
                client.disconnect()
            except Exception:
                pass
            try:
                client.loop_stop()
            except Exception:
                pass
        self.clients = []
        self._topics = {}
        self._command_topics = {}
