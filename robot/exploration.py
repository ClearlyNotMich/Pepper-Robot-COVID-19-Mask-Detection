from __future__ import print_function

from random import uniform  # Enables for Float nummers

THETA = 0  # pepper doesn't use the THETA variable, but still wants to have it selected.


class Exploration:
    """
    This is a exploration class that is used by the pepper class.
    To load in exploration functions from the pepper API.
    """
    session = radius = exploration_service = None

    """
    initialize the class variables.
    """
    def __init__(self, session):
        self.radius = 0
        self.session = session
        self.exploration_service = self.session.service("ALNavigation")

    """
    Start the exploration of the surrounding.
    """
    def explore(self, radius):
        # Distance is measured in meters
        self.radius = radius
        error_code = self.exploration_service.explore(radius)
        print(error_code)
        if error_code != 0:
            print("Exploration failed.")
            return
        return self

    """
    Stop the exploration of the surrounding. 
    This can be used if the user wants to interrupt the robot midway of the exploring. 
    If no need to interrupt midway there is no need then.
    """
    def stop_exploration(self):
        self.exploration_service.stopExploration()
        return self

    """
    Save the explored map on the computer.
    """
    def save_exploration(self):
        # Save the file of the map on the robot.
        path = self.exploration_service.saveExploration()
        # Tell us what the location of path is.
        print(("Exploration saved at path: \"" + path + "\""))
        return self

    """
    Navigate to location in the loaded map file.
    Check README file for how the sees the coordinates (compass).
    """
    def navigate_to_in_map(self, horizontal, vertical, theta):
        self.exploration_service.navigateToInMap([horizontal, vertical, theta])
        # Points out in the console when the robot has arrived at the location.
        # Anything outside of the range selected in explore and robot skips it.
        print(" I have arrived at the new location.")
        return self

    """
    Stop the exploration of the surrounding. This is used if the user wants to interrupt midway of the exploring.
    """
    def get_robot_position_in_map(self):
        print("I reached:" + str(self.exploration_service.getRobotPositionInMap()[0]))
        return self

    """
    Load a explored map saved on the robot
    """
    def load_exploration(self, exploration_file):
        # load a specific map from the robot
        # The robot selects automatically the last generated using start_localization method.
        self.exploration_service.LoadExploration(exploration_file)
        return self

    """
    Start using the explored map
    """
    def start_localization(self):
        self.exploration_service.startLocalization()  # Turn on the map the robot has loaded.
        return self

    """
    Stop using the explored map.
    """
    def stop_localization(self):
        self.exploration_service.stopLocalization()  # Turn off the map the robot has loaded
        return self

    """
    Make a random location in the map and navigate the robot there.
    """
    def go_to_random(self):
        if self.radius != 0:
            # Generate a random number for the horizontal as
            x = uniform(0, self.radius)
            # Generate a random number for the vertical as
            y = uniform(0, self.radius)
            # THETA is not being used in the pepper but still needs it to do this function.
            self.navigate_to_in_map(x, y, THETA)
        else:
            # Print out that the robot has no map explored/selected and should do that first.
            print("Please explore and/or select the map first")
