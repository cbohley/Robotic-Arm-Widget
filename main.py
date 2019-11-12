# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
START = True
STOP = False
UP = False
DOWN = True
ON = True
OFF = False
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
CLOCKWISE = 0
COUNTERCLOCKWISE = 1
ARM_SLEEP = 2.5
DEBOUNCE = 0.10

lowerTowerPosition = 60
upperTowerPosition = 76


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):

    def build(self):
        self.title = "Robotic Arm"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

cyprus.open_spi()

ballOnTallTower = False

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////

sm = ScreenManager()
arm = stepper(port=0, speed=10)
cyprus.initialize()
cyprus.setup_servo(1)  # cytron
cyprus.setup_servo(2)  # talon

""" 
Port 4: Cytron
Port 5: Talon
Port 6: Tall Tower Sensor
Port 7: Short Tower Sensor
Port 8: N/A

38.9 is the tall tower
30.25 is the short tower
"""
# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    armPosition = 0
    lastClick = time.clock()
    armHeight = False
    magnet = False

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def debounce(self):
        processInput = False
        currentTime = time.clock()
        if ((currentTime - self.lastClick) > DEBOUNCE):
            processInput = True
        self.lastClick = currentTime
        return processInput

    def toggleArm(self):
        print("Process arm movement here")
        self.armHeight = not self.armHeight
        if self.armHeight:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        else:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)

    def toggleMagnet(self):
        print("Process magnet here")
        self.magnet = not self.magnet
        if self.magnet:
            cyprus.set_servo_position(2, 1)
        else:
            cyprus.set_servo_position(2, .5)

    def auto(self):
        print("Run the arm automatically here")
        shortTower = 30.25
        tallTower = 38.9
        if self.isBallOnTallTower():
            shortTower = 38.9
            tallTower = 30.25
        arm.home(1)
        arm.go_to_position(shortTower)
        self.toggleMagnet()
        time.sleep(.5)
        self.toggleArm()
        time.sleep(1)
        self.toggleArm()
        time.sleep(.5)
        arm.go_to_position(tallTower)
        time.sleep(.5)
        self.toggleArm()
        time.sleep(.7)
        self.toggleMagnet()
        time.sleep(.5)
        self.toggleArm()
        time.sleep(.5)
        arm.home(1)

    def setArmPosition(self, position):
        if arm.get_position_in_units() == 0:
            self.ids.moveArm.value = 0
        self.ids.armControlLabel.text = str(position)
        arm.go_to_position(position)

        print(arm.get_position_in_units())
        print("Move arm here")

    def homeArm(self):
        arm.home(0)

    def isBallOnTallTower(self):
        print("Determine if ball is on the top tower")
        if cyprus.read_gpio() & 0b0001:
            sleep(.05)
            if cyprus.read_gpio() & 0b0001:
                print("proximity sensor off")
                return False

        return True


    def isBallOnShortTower(self):
        print("Determine if ball is on the bottom tower")
        if cyprus.read_gpio() & 0B0010:
            print("Nope!")
            return False
        print("Here")
        return True


    def initialize(self):
        print("Home arm and turn off magnet")
        cyprus.initialize()
        cyprus.setup_servo(1)
        cyprus.setup_servo(2)
        cyprus.set_servo_position(2, .5)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        self.homeArm()

    def resetColors(self):
        self.ids.armControl.color = YELLOW
        self.ids.magnetControl.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()