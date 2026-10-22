from __future__ import print_function

import threading
import time


class PeoplePerception:
    """
    This is an PeoplePerception class. The goal of this class is to be aware of human presence and to react to
    them
    """
    # Empty variables
    session = face_detection_service = memory_service = tracker_service = motion_service = \
        ba_service = people_perception = None
    detection_started = False
    on_face_detected_callback = None
    time_out_time = 0
    last_time_detected = None
    pepper = None

    """ Initialising the class variables"""

    def __init__(self, pepper):
        self._detection_resources_active = False
        self.subscribers_list = []
        self.is_speech_recognition_started = False
        self.last_detected_person = 0

        self.pepper = pepper
        self.session = pepper.session
        self.people_perception_service = self.session.service("ALPeoplePerception")
        self.face_detection_service = self.session.service("ALFaceDetection")
        self.memory_service = self.session.service("ALMemory")
        self.tracker_service = self.session.service("ALTracker")
        self.motion_service = self.session.service("ALMotion")
        self.ba_service = self.session.service("ALBasicAwareness")
        self.connect_callback("ALBasicAwareness/HumanTracked", self.on_human_tracked)
        self.connect_callback("ALBasicAwareness/HumanLost", self.on_people_left)

    """ Starts the face detection method"""

    def process_face_detection(self):
        import qi
        last_detected_face = None
        while self.detection_started:
            time.sleep(0.5)
            try:
                val = self.memory_service.getData("FaceDetected", 0)
            except Exception:
                self.detection_started = False
                print("Face detection stopped after a robot-service error")
                return

            # Check if we find some face
            if val and isinstance(val, list) and len(val) > 0:
                # We detected faces !
                # For each face, we can read its shape info and ID.

                timestamp = val[0]
                faceInfoArray = val[1]

                # Stops the loop
                if not self.detection_started:
                    break
                # ???
                if self.time_out_time > 0 and self.last_time_detected and (
                        (self.last_time_detected / 1000000) + self.time_out_time) > (qi.systemClockNow() / 1000000):
                    continue
                # Starting an array list for amount of faces
                face_count = len(faceInfoArray) - 1

                # Looks at the last moment when face is detected
                self.last_time_detected = qi.systemClockNow()

                # Here we count the amount of faces true callback function
                if self.on_face_detected_callback:
                    self.on_face_detected_callback(face_count)

    """ Starting detection method """

    def start_detection(self):
        if self.detection_started:
            return
        self.detection_started = True
        self._detection_resources_active = True
        # Starts Awareness method
        self.ba_service.startAwareness()
        # Starts the method of the API
        self.face_detection_service.setTrackingEnabled(False)
        self.face_detection_service.subscribe("Test_Face", 500, 0.0)
        PeoplePerception.start_face_tracking(self)

        worker = threading.Thread(target=self.process_face_detection)
        worker.daemon = True
        worker.start()

    """ Creating a callback method for detected faces"""

    def set_on_face_detected_callback(self, callback):
        self.on_face_detected_callback = callback

    """ Setting timeout vabriable """

    def set_timeout(self, time_out_time):
        self.time_out_time = time_out_time

    """ Stops detection method"""

    def stop_detection(self):
        self.detection_started = False
        self._detection_resources_active = False
        for cleanup in (
                lambda: self.face_detection_service.unsubscribe("Test_Face"),
                self.stop_face_tracking,
                self.ba_service.stopAwareness):
            try:
                cleanup()
            except Exception:
                pass

    """ Starts face tracking method """

    def start_face_tracking(self):
        # Add target to track.
        target_name = "Face"
        face_width = 0.1
        self.tracker_service.registerTarget(target_name, face_width)
        list = []

        list = self.tracker_service.getTargetPosition()

        # Then, start tracker.
        self.tracker_service.track(target_name)

    """ Stops face tracking method"""

    def stop_face_tracking(self):
        self.tracker_service.stopTracker()
        # Cleans all registerd targets
        self.tracker_service.unregisterAllTargets()
        self.motion_service.rest()

    """ connect a callback for a given event """

    def connect_callback(self, event_name, callback_func):

        subscriber = self.memory_service.subscriber(event_name)
        subscriber.signal.connect(callback_func)
        self.subscribers_list.append(subscriber)

    """ callback for event HumanTracked """

    def on_human_tracked(self, value):
        if value >= 0 and value != self.last_detected_person:  # found a new person
            print("got HumanTracked: detected person with ID:", str(value))

            if self.pepper.mode == "entrance_mode":
                self.pepper.speech().random_language()
                self.pepper.motion().wave()
                self.pepper.speech().say("Scan je pasje en vergeet niet een mondkapje te dragen")

            if self.pepper.mode == "surveillance_mode":
                self.pepper.speech().random_language()  # Chooses randomly one of the 4 languages as greeting
                self.pepper.speech().random_news()  # Chooses randomly pre written facts
                self.pepper.motion().wave()  # Waves at the person

            position_human = self.get_people_perception_data(value)
            [x, y, z] = position_human
            print("The tracked person with ID", value, "is at the position:", \
                "x=", x, "/ y=", y, "/ z=", z)

    """ callback for event PeopleLeft """

    def on_people_left(self, value):

        print("got PeopleLeft: lost person", str(value))

    """ Getting data on the tracked person"""

    def get_people_perception_data(self, id_person_tracked):
        memory_key = "PeoplePerception/Person/" + str(id_person_tracked) + \
                     "/PositionInWorldFrame"
        return self.memory_service.getData(memory_key)

    """ Creating a method for engagement with the target"""

    def set_engagement_mode(self, mode):
        self.ba_service.setEngagementMode(mode)
        return self

    """ Getting the list of tracked humans method"""

    def get_human_tracked_list(self):
        return self.subscribers_list
