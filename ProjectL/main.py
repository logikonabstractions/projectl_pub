# ProjectL/main.py
import yaml
import os
import logging
from game_objects import GameManager
from logging_utils import setup_logging

# TODO: configure as a default general configs the maximal dimensions of the card

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(dir_path)  # since configs are in project root
file_path = os.path.join(parent_dir, 'configs.yaml')


def main():
    configs_dict = read_yaml(file_path)

    # Set up logging
    logger = setup_logging(configs_dict)

    logger.info("Starting ProjectL game", extra={"normal": True})
    logger.debug("Loaded configuration: %s", configs_dict, extra={"normal": False})

    gm = GameManager(configs_dict, logger)
    logger.info("Game initialized with configuration", extra={"normal": True})
    logger.debug("Running game...", extra={"normal": False})

    gm.run()

    logger.info("Game completed", extra={"normal": True})


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        return data


if __name__ == "__main__":
    main()