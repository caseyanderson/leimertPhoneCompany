#!/usr/bin/env python

'''
original software by trapheals
'''

from time import sleep

import RPi.GPIO as GPIO
import os
import pygame

pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

buttonDown = False
onHook = False

# GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(4, GPIO.IN) # on hook trigger
GPIO.setup(17, GPIO.IN) # button pressed trigger
GPIO.setup(18, GPIO.IN) # outA
GPIO.setup(23, GPIO.IN) # outB
GPIO.setup(24, GPIO.IN) # outC
GPIO.setup(25, GPIO.IN) # outD

GPIO.setup(27, GPIO.IN) # coin in 1

# directory paths
phoneSoundDir = '/home/pi/audio'
visionAudioDir = '/home/pi/visionNov132026-EDITS/audio'

# Phone sounds
TONE_FILES = {
    '0': 'DTMF-0.wav',
    '1': 'DTMF-1.wav',
    '2': 'DTMF-2.wav',
    '3': 'DTMF-3.wav',
    '4': 'DTMF-4.wav',
    '5': 'DTMF-5.wav',
    '6': 'DTMF-6.wav',
    '7': 'DTMF-7.wav',
    '8': 'DTMF-8.wav',
    '9': 'DTMF-9.wav',
    '*': 'DTMF-star.wav',
    '#': 'DTMF-pound.wav',
}

key_sounds = {
    key: pygame.mixer.Sound(os.path.join(phoneSoundDir, filename))
    for key, filename in TONE_FILES.items()
}
soundDialTone = pygame.mixer.Sound(os.path.join(phoneSoundDir, 'dialtone.wav'))

# Keypad recordings
MENU_FILES = {
    '0': 'SKIN0.wav',
    '1': 'AmaraKiona.wav',
    '2': 'BenCaldwell.wav',
    '3': 'Benu.wav',
    '4': 'HughAugustine.wav',
    '5': 'Jimetta.wav',
    '6': 'MaryChristian.wav',
    '7': 'MattGibson.wav',
    '8': 'Mitebrafoagindotan.wav',
    '9': 'WeLoveLeimertAudioCollage.wav',
}

menu_sounds = {
    key: pygame.mixer.Sound(os.path.join(visionAudioDir, filename))
    for key, filename in MENU_FILES.items()
}
menu = menu_sounds['0']


def stopSound():
    pygame.mixer.stop()


def stopSomeSounds():
    for key in '0123456789*#':
        key_sounds[key].stop()


def playSelection(keyNum):
    sound = menu_sounds.get(keyNum)
    if sound is not None:
        sound.play()


def playKey(keyNum):
    sound = key_sounds.get(keyNum)
    if sound is not None:
        if keyNum in '0123456789':
            stopSound()
        sound.play()


# Maps binary output to a button number.
GPIO_KEYS = {
    (1, 0, 0, 0): '2',
    (0, 0, 0, 0): '1',
    (0, 1, 0, 0): '3',
    (1, 0, 1, 0): '5',
    (0, 0, 1, 0): '4',
    (0, 1, 1, 0): '6',
    (1, 0, 0, 1): '8',
    (0, 0, 0, 1): '7',
    (0, 1, 0, 1): '9',
    (1, 0, 1, 1): '0',
    (0, 0, 1, 1): '*',
    (0, 1, 1, 1): '#',
}


def keyPress(outA, outB, outC, outD):
    return GPIO_KEYS.get((outA, outB, outC, outD), 'F')


while True:

    # Main loop.
    # Trigger for input(4) goes low (false) when activated.
    # Check to see if we are moving from being on the hook to off the hook...

    if(GPIO.input(4) == True and onHook == False):
        print("on hook")
        onHook = True # moving to on state
        stopSound() # stop all sounds
        buttonDown = False # just in case someone puts phone down while pressing button...

    elif(GPIO.input(4) == False and onHook == True):
        print("off hook")
        menu.play(loops=999)
        onHook = False

    elif(onHook == False):

        # If phone is picked up, handle button presses

        if(GPIO.input(17) == True and buttonDown == False):

            # Button pressed.
            # To test, print out formatted binary from 74C922 chip.

            currentKey = keyPress(GPIO.input(18), GPIO.input(23), GPIO.input(24), GPIO.input(25))
            playKey(currentKey)
            buttonDown = True
#            print str(GPIO.input(18)) + " " + str(GPIO.input(23)) + " " + str(GPIO.input(24)) + " " + str(GPIO.input(25))
#            print "button pressed: " + currentKey

        # otherwise, if button released, print that and set state.
        # if neither of these is true, the handle is up and no buttons are pressed, so do nothing.

        elif(GPIO.input(17) == False and buttonDown == True):

            # Button released - stop all DTMF sounds, reset buttonDown

            stopSound()
            currentKey = keyPress(GPIO.input(18), GPIO.input(23), GPIO.input(24), GPIO.input(25))
            playSelection(currentKey)
            print("button released: " + currentKey)
            buttonDown = False

        elif(pygame.mixer.get_busy() == False):

            menu.play()

    # Sleep for 100 ms then repeat.

    # print keyPress(GPIO.input(18), GPIO.input(23), GPIO.input(24), GPIO.input(25))
    # print str(GPIO.input(18)) + " " + str(GPIO.input(23)) + " " + str(GPIO.input(24)) + " " + str(GPIO.input(25))
    sleep(0.025);



