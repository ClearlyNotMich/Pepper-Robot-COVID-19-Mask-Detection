from __future__ import print_function

from random import randint

DEFAULT_PITCH = 1.2  # 1.2 is considered a normal pitch voice of the robot.


class Speech:
    """This class is used by pepper.py to load the Speech functions for the robot"""
    session = tts_service = animated_speech_service = speak_move_service = None

    """This is where the class variables are initialized"""

    def __init__(self, session):
        self.session = session
        self.tts_service = self.session.service("ALTextToSpeech")
        self.set_default_pitch()
        self.set_language("Dutch")  # Set the robot automatically in Dutch Accent.

    """Here you can adjust the sound volume of the robot"""

    def set_volume(self, volume):
        self.tts_service.setVolume(volume)  # From 0 being MIN-volume and 1.0 being MAX-volume
        return self

    """Here you can change the language of the robot"""

    def set_language(self, language):
        # English, Dutch are installed on the robot.
        # Chinese is installed as well, but unreachable because of not accepting the Chinese characters.
        self.tts_service.setLanguage(language)
        return self

    """Here you can adjust the sound pitch of the robot"""

    def set_pitch(self, pitch):
        # 1 being Min and 4.0 being Max
        self.tts_service.setParameter("pitchShift", pitch)
        return self

    """Here you can choose the default pitch for the robot"""

    def set_default_pitch(self):
        self.tts_service.setParameter("pitchShift", DEFAULT_PITCH)
        return self

    """Here you can type a text, and the robot will say it"""

    def say(self, text):
        self.tts_service.say(text)
        return self

    """Here the robot will talk in English"""

    def uk_intro(self):
        self.set_language("English")
        self.tts_service.say("Hello")
        self.set_language("Dutch")
        self.tts_service.say("welkom in het wibauthuis")
        return self

    """Here the robot will talk in Dutch"""

    def nl_intro(self):
        self.set_language("Dutch")
        self.tts_service.say("Hallo welkom in het Wibauthuis")
        return self

    """Here the robot will talk in Japanese"""

    def jp_intro(self):
        self.set_language("English")  # Japanese is not installed on the robot
        self.tts_service.say("Kohnnichiwa")  # Adjusted for the accent
        self.set_language("Dutch")
        self.tts_service.say("welkom in het wibauthuis")
        return self

    """Here the robot will talk in Italian"""

    def it_intro(self):
        self.set_language("Dutch")  # Italian is not installed on the robot
        self.tts_service.say("tsiao")  # Adjusted for the accent
        self.set_language("Dutch")
        self.tts_service.say("welkom in het wibauthuis")
        return self

    """Here the robot will say one of the four languages randomly"""

    def random_language(self):
        self.set_volume(1.0)  # Environment is noisy therefore the robot automatically speaks in max volume.
        language_value = randint(0, 3)  # Generate a random number between 0 and 3 for language selection.
        if language_value == 0:
            Speech.uk_intro(self)
        if language_value == 1:
            Speech.nl_intro(self)
        if language_value == 2:
            Speech.jp_intro(self)
        if language_value == 3:
            Speech.it_intro(self)
        self.set_language("Dutch")  # Sets back to dutch for the future usage.
        # used to check which number the the robot randomly generates so we know what language corresponds to it.
        print(language_value)
        return self

    """Here the robot will tell random facts about the hva"""

    def random_news(self):
        self.set_language("Dutch")  # Sets the language to Dutch for future usage.
        random = randint(0, 3)
        if random == 0:
            self.say("Wist je dat het wibauthuis is vernoemd naar Floor Wibaut")
        if random == 1:
            self.say("Kom een keer langs ons cafe achter het gebouw")
        if random == 2:
            self.say("Wist je dat dit gebouw 12 etages heeft")
        if random == 3:
            self.say("Wist je dat het HvA bijna 47 duizend studenten heeft op 89 opleidingen")
