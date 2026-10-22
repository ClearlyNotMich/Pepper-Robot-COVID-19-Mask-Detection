"""Hardware wrappers loaded only by an explicitly started Pepper instance."""
from __future__ import print_function

from .autonomous_ability import AutonomousAbility
from .tablet import Tablet
from .speech import Speech
from .motion import Motion
from .people_perception import PeoplePerception
from .system import System
from .exploration import Exploration
from tools.paho_mqtt import PahoMqtt


class Pepper(object):
    def __init__(self, configuration, session_factory=None, mqtt_factory=None):
        self.configuration = configuration
        self.ip = configuration["robot_host"]
        self.port = configuration["robot_port"]
        self._session_factory = session_factory
        self._mqtt_factory = mqtt_factory or PahoMqtt
        self.session = None
        self._paho_mqtt = None
        self._people_perception = None
        self.mqtt_msg = None
        self.detection_callback = False
        self.mode = None

    def load_modules(self):
        self._autonomous_ability = AutonomousAbility(self)
        self._people_perception = PeoplePerception(self)
        self._speech = Speech(self.session)
        self._motion = Motion(self.session)
        self._tablet = Tablet(self.session, self.configuration["tablet_url"])
        self._system = System(self.session)
        self._exploration = Exploration(self.session)

    def load_tools(self):
        self._paho_mqtt = self._mqtt_factory(self, self.configuration["clients"])

    def start(self):
        try:
            self.connect()
            self.load_modules()
            self.load_tools()
        except BaseException:
            self.close()
            raise

    def connect(self):
        factory = self._session_factory
        if factory is None:
            import qi
            factory = qi.Session
        self.session = factory()
        self.session.connect("tcp://" + self.ip + ":" + str(self.port))

    def check_connection(self):
        # Avoid the original unbounded recursive reconnect/module initialization.
        if self.session is None or not self.session.isConnected():
            raise RuntimeError("Robot disconnected; restart the application explicitly")

    def close(self):
        """Release application resources; this is not a robot emergency stop."""
        if self._people_perception is not None and self._people_perception._detection_resources_active:
            try:
                self._people_perception.stop_detection()
            except Exception:
                pass
        if self._paho_mqtt is not None:
            try:
                self._paho_mqtt.close()
            except Exception:
                pass
            self._paho_mqtt = None
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None

    def autonomous_ability(self):
        self.check_connection()
        return self._autonomous_ability

    def people_perception(self):
        self.check_connection()
        return self._people_perception

    def speech(self):
        self.check_connection()
        return self._speech

    def motion(self):
        self.check_connection()
        return self._motion

    def exploration(self):
        self.check_connection()
        return self._exploration

    def tablet(self):
        self.check_connection()
        return self._tablet

    def system(self):
        self.check_connection()
        return self._system

    def mqtt(self):
        return self._paho_mqtt
