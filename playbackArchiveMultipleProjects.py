#!/usr/bin/env python3

"""
Multi-project archive phone.

Based on original software by trapheals.
Projects are ordered newest to oldest.
"""

from pathlib import Path
from time import sleep

import pygame
import RPi.GPIO as GPIO

# Preserve the original mixer settings.
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

buttonDown = False
onHook = False
active_key = None
project_index = 0

# Original GPIO configuration
# GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(4, GPIO.IN)  # on hook trigger
GPIO.setup(17, GPIO.IN)  # button pressed trigger
GPIO.setup(18, GPIO.IN)  # outA
GPIO.setup(23, GPIO.IN)  # outB
GPIO.setup(24, GPIO.IN)  # outC
GPIO.setup(25, GPIO.IN)  # outD

GPIO.setup(27, GPIO.IN)  # coin in 1

# Audio folder beside this script
audio_dir = Path(__file__).resolve().parent / "audio"
tones_dir = audio_dir / "phoneTones"

# Ordered newest to oldest. Key "0" is each project's intro.
projects = [
    {
        "name": "weLoveLeimert",
        "folder": audio_dir / "weLoveLeimertArchive-Nov132026",
        "recordings": {
            "0": "noPriorArt1.wav",
            "1": "AmaraKiona.wav",
            "2": "BenCaldwell.wav",
            "3": "Benu.wav",
            "4": "HughAugustine.wav",
            "5": "Jimetta.wav",
            "6": "MaryChristian.wav",
            "7": "MattGibson.wav",
            "8": "Mitebrafoagindotan.wav",
            "9": "WeLoveLeimertAudioCollage.wav",
        },
    },
    {
        "name": "noPriorArt",
        "folder": audio_dir / "noPriorArt",
        "recordings": {
            "0": "ButtonPrompts.wav",
            "1": "VisionOfSankofaCity.wav",
            "2": "KAOSKids.wav",
            "3": "AvailableRoutes.wav",
            "4": "WhereWeAreNow.wav",
            "5": "CallTheFuture.wav",
            "6": "PreparingForOlympics.wav",
            "7": "TransportToTheFunkaverse.wav",
        },
    },
]

TONE_FILES = {
    "0": "DTMF-0.wav",
    "1": "DTMF-1.wav",
    "2": "DTMF-2.wav",
    "3": "DTMF-3.wav",
    "4": "DTMF-4.wav",
    "5": "DTMF-5.wav",
    "6": "DTMF-6.wav",
    "7": "DTMF-7.wav",
    "8": "DTMF-8.wav",
    "9": "DTMF-9.wav",
    "*": "DTMF-star.wav",
    "#": "DTMF-pound.wav",
}

# Original binary-output-to-key mapping
GPIO_KEYS = {
    (1, 0, 0, 0): "2",
    (0, 0, 0, 0): "1",
    (0, 1, 0, 0): "3",
    (1, 0, 1, 0): "5",
    (0, 0, 1, 0): "4",
    (0, 1, 1, 0): "6",
    (1, 0, 0, 1): "8",
    (0, 0, 0, 1): "7",
    (0, 1, 0, 1): "9",
    (1, 0, 1, 1): "0",
    (0, 0, 1, 1): "*",
    (0, 1, 1, 1): "#",
}


def keyPress(outA, outB, outC, outD):
    return GPIO_KEYS.get((outA, outB, outC, outD), "F")


def stopSound():
    pygame.mixer.stop()


def play_intro():
    project = projects[project_index]
    channel.play(intro_sounds[project_index], loops=-1)
    print(f"Intro: {project['name']} — {project['recordings']['0']}")


def press_key(key):
    global active_key

    if active_key is not None:
        return

    if key not in key_sounds:
        print(f"Ignoring unknown key: {key}")
        return

    # Ignore boundary navigation without interrupting playback.
    if key == "#" and project_index == len(projects) - 1:
        print("Already at the oldest project.")
        return

    if key == "*" and project_index == 0:
        print("Already at the newest project.")
        return

    project = projects[project_index]

    if key not in ("*", "#") and key not in project["recordings"]:
        print(f"No recording on key {key} in {project['name']}.")
        return

    stopSound()
    active_key = key
    channel.play(key_sounds[key], loops=-1)
    print(f"Pressed: {key}")


def release_key():
    global active_key, project_index

    # Ignored presses must not interrupt existing playback.
    if active_key is None:
        return

    key = active_key
    active_key = None
    channel.stop()

    if key in ("*", "#"):
        project_index += 1 if key == "#" else -1
        print(f"Changed to project {project_index}: {projects[project_index]['name']}")
        play_intro()
        return

    project = projects[project_index]
    filename = project["recordings"][key]
    recording = pygame.mixer.Sound(str(project["folder"] / filename))
    channel.play(recording)
    print(f"Released: {key}. Playing: {project['name']} — {filename}")


try:
    # Check required filenames before starting the phone loop.
    required_files = [tones_dir / filename for filename in TONE_FILES.values()]

    for project in projects:
        required_files.extend(
            project["folder"] / filename for filename in project["recordings"].values()
        )

    missing_files = [path for path in required_files if not path.is_file()]

    if missing_files:
        missing_list = "\n".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Required audio files are missing:\n{missing_list}")

    # Preload tones and intros; load other recordings when selected.
    key_sounds = {
        key: pygame.mixer.Sound(str(tones_dir / filename))
        for key, filename in TONE_FILES.items()
    }

    intro_sounds = [
        pygame.mixer.Sound(str(project["folder"] / project["recordings"]["0"]))
        for project in projects
    ]

    channel = pygame.mixer.Channel(0)

    print("Multi-project phone ready.")

    while True:
        # Receiver placed on hook
        if GPIO.input(4) == True and onHook == False:
            print("on hook")
            onHook = True
            stopSound()
            buttonDown = False
            active_key = None
            project_index = 0

        # Receiver lifted
        elif GPIO.input(4) == False and onHook == True:
            print("off hook")
            project_index = 0
            active_key = None
            buttonDown = False
            onHook = False
            play_intro()

        elif onHook == False:
            # Key pressed
            if GPIO.input(17) == True and buttonDown == False:
                currentKey = keyPress(
                    GPIO.input(18),
                    GPIO.input(23),
                    GPIO.input(24),
                    GPIO.input(25),
                )
                press_key(currentKey)
                buttonDown = True

            # Key released: use the accepted key captured on press.
            elif GPIO.input(17) == False and buttonDown == True:
                release_key()
                buttonDown = False

            # Playback finished: return to this project's intro.
            elif buttonDown == False and active_key is None and not channel.get_busy():
                play_intro()

        sleep(0.025)

except KeyboardInterrupt:
    print("\nStopping phone.")

finally:
    stopSound()
    pygame.mixer.quit()
    GPIO.cleanup()
