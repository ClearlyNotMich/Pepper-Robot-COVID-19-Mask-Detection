"""Explicit Pepper entry point; help and configuration checks are offline."""
from __future__ import print_function

import argparse
import os
import sys
import time
from tools.config import ConfigError, load_config


def surveillance_mode(robot):
    """Keep historical exploration behavior; return when a new command arrives.

    A navigation API call can still block. This command loop is not an emergency
    stop mechanism and has not been verified on robot hardware.
    """
    robot.exploration().explore(2)
    robot.exploration().save_exploration()
    robot.exploration().start_localization()
    robot.people_perception().start_detection()
    while robot.mqtt_msg is None:
        robot.exploration().go_to_random()
        # Preserve the original one-minute pause but notice commands during it.
        for unused in range(600):
            if robot.mqtt_msg is not None:
                return
            time.sleep(0.1)


def entrance_mode(robot):
    robot.people_perception().start_detection()


def run_robot(configuration, pepper_factory=None):
    """Start actual hardware/network operations only after explicit dispatch."""
    if pepper_factory is None:
        from robot.pepper import Pepper
        pepper_factory = Pepper
    robot = pepper_factory(configuration)
    try:
        robot.start()
        robot.motion().wake_up()
        robot.autonomous_ability().set_autonomous_ability(True)
        robot.tablet().show_website()
        while True:
            command = robot.mqtt_msg
            if command is None:
                time.sleep(0.1)
                continue
            robot.mqtt_msg = None
            if command == "entrance_mode":
                robot.mode = command
                entrance_mode(robot)
            elif command == "surveillance_mode":
                robot.mode = command
                surveillance_mode(robot)
            elif command == "stop":
                # Preserve the historical remote command's shutdown behavior.
                robot.system().shutdown()
                return
    finally:
        robot.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-config", action="store_true", help="validate locally; no robot or broker connection")
    action.add_argument("--run", action="store_true", help="explicitly connect and run the physical robot")
    parser.add_argument("--config", help="local JSON configuration, or set PEPPER_CONFIG")
    args = parser.parse_args(argv)
    path = args.config or os.environ.get("PEPPER_CONFIG")
    if not path:
        parser.error("provide --config PATH or PEPPER_CONFIG")
    try:
        configuration, problems = load_config(path, for_run=args.run)
    except ConfigError as error:
        parser.error(str(error))
    if args.check_config:
        print("Configuration structure is valid; no connections were attempted.")
        if problems:
            print("Not ready for --run: " + "; ".join(problems))
        else:
            print("Required values are present; endpoints and credentials have not been tested.")
        return 0
    try:
        run_robot(configuration)
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        # Network libraries may include sensitive values in exception messages.
        print("Robot run failed (%s); check the local runtime and configuration." % type(error).__name__, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
