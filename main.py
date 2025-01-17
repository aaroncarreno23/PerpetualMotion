# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import os
import math
import sys
import time
import threading

from hpmudext import close_device
from smbus2.smbus2 import union_i2c_smbus_data

os.environ["DISPLAY"] = ":0.0"

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
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *

dpiComputer = DPiComputer()
dpiStepper = DPiStepper()
dpiStepper.setBoardNumber(0)

if dpiComputer.initialize():
    print("Successfully communicating with DPiComputer")
else:
    print("Failed to communicate with DPiComputer.")

if dpiStepper.initialize():
    print("Successfully communicating with DPiStepper board")
else:
    print("Failed to communicate with DPiStepper board.")

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper Motor goes into MOTOR 0 )
    Limit Switch associated with Stepper Motor goes into HOME 0
    One Sensor goes into IN 0
    Another Sensor goes into IN 1
    Servo Motor associated with the Gate goes into SERVO 1
    Motor Controller for DC Motor associated with the Stairs goes into SERVO 0"""
# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 2
RAMP_LENGTH = 725
# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////

class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////

class MainScreen(Screen):

    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()
        self.servo_gate = 1
        self.servo_stair = 0
        self.closed_servo = True
        self.run_servo = True
        self.ramp_stepper = True
        self.motor_enabled = True
        stepper_num = 0
        dpiComputer.writeServo(self.servo_gate, 30)
        dpiComputer.writeServo(self.servo_stair, 90)
        dpiStepper.enableMotors(True)
        dpiStepper.setCurrentPositionInRevolutions(stepper_num, 0)



    def toggleGate(self):

        if self.closed_servo:
            dpiComputer.writeServo(self.servo_gate, 30)
            self.ids.gate.text = "Open Gate"
            self.closed_servo = False
        else:
            dpiComputer.writeServo(self.servo_gate, 180)
            self.ids.gate.text = "Close Gate"
            self.closed_servo = True

    def toggleStaircase(self):

        if self.run_servo:
            dpiComputer.writeServo(self.servo_stair, 90)
            self.ids.staircase.text = "Staircase Off"
            self.run_servo = False

        else:
            slider_value = self.ids.staircaseSpeed.value
            dpiComputer.writeServo(self.servo_stair, slider_value)
            self.ids.staircase.text = "Staircase On"
            self.run_servo = True


    def toggleRamp(self):

        stepper_num = 0
        wait_to_finish_moving_flg = True

        if self.ramp_stepper:
            dpiStepper.moveToRelativePositionInRevolutions(stepper_num, -28.5,wait_to_finish_moving_flg )
            self.ids.ramp.text = "Ramp to Bottom"
            self.ramp_stepper = False

        else:
            dpiStepper.moveToRelativePositionInRevolutions(stepper_num, 28.5, wait_to_finish_moving_flg)
            self.ids.ramp.text = "Ramp to Top"
            self.ramp_stepper = True
        
    def auto(self):

        value0 = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0)
        print(str(value0))
        stepper_num = 0
        wait_to_finish_moving_flg = True
        if value0 !=1:
            dpiStepper.enableMotors(True)
            dpiComputer.writeServo(self.servo_gate, 30)
            dpiStepper.moveToRelativePositionInRevolutions(stepper_num, -28.5, wait_to_finish_moving_flg)
            dpiComputer.writeServo(self.servo_stair, 90)
            sleep(1)
            dpiComputer.writeServo(self.servo_stair, 180)
            sleep(6)
            dpiComputer.writeServo(self.servo_stair, 90)
            value1 = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1)
            print(str(value1))
            if value1 != 0:
                dpiStepper.moveToRelativePositionInRevolutions(stepper_num, 28.5, wait_to_finish_moving_flg)
            dpiComputer.writeServo(self.servo_gate, 180)
            sleep(1)
            dpiComputer.writeServo(self.servo_gate, 30)

    def setRampSpeed(self, slider, value):

        dpiStepper.setSpeedInRevolutionsPerSecond(0, value)
        self.ids.rampSpeedLabel.text = f"Ramp Speed: {int(value)} revolutions/second"
        print(f"Ramp Speed: {int(value)} revolutions/second")

    def setStaircaseSpeed(self, slider, value):

        display_value = int(value - 90)
        self.ids.staircaseSpeedLabel.text = f"Staircase Speed: {int(display_value)}"
        if self.run_servo:
            dpiComputer.writeServo(self.servo_stair, value)
            self.ids.staircaseSpeedLabel.text = f"Staircase Speed: {int(display_value)}"
            print(f"Staircase Speed: {int(display_value)}")
        else:
            pass

    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        MyApp().stop()

# //moves the stairs up
#   print("Rotate Servo 0 CCW")
#   i = 0
#   servo_number = 0
#   for i in range(180, 0, -1):
#       dpiComputer.writeServo(servo_number, i)
#       sleep(.05)

# // opens gate
#   print("  Rotate Servo 1 CW")
#   i = 1
#   servo_number = 1
#   for i in range(180):
#       dpiComputer.writeServo(servo_number, i)
#       sleep(.05)

# // closes gate
#   print("Rotate Servo 1 CCW")
#   i = 0
#   servo_number = 1
#   for i in range(180,0,-1):
#       dpiComputer.writeServo(servo_number, i)
#       sleep(0.05)

#   servo_number = 1
#   dpiComputer.writeServo(servo_number, 30)

# // POSITIVE IS BACKWARDS, NEGATIVE IS FORWARD

# // 0 IS HOME, -45600 IS AWAY

# // stepper 0 turned on
#   dpiStepper.enableMotors(True)

# // stepper 0 turned off
#   dpiStepper.enableMotors(False)

# // setting to 0 steps
#   stepper_num = 0
#   dpiStepper.setCurrentPositionInSteps(stepper_num, 0)

# // BOTTOM TO TOP
#   stepper_num = 0
#   steps = -45600
#   wait_to_finish_moving_flg = True
#   dpiStepper.moveToRelativePositionInSteps(stepper_num, steps, wait_to_finish_moving_flg)

# // IN-1 IS TOP, 1 = NOTHING, 0 = SOMETHING

# // IN-0 IS BOTTOM

# // IF BALL AT IN-0 THEN PUSHES BALL UP, 1 = NOTHING, 0 = SOMETHING
#   value = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0)
#   print(str(value))
#   stepper_num = 0
#   wait_to_finish_moving_flg = True
#   if value !=1:
#       dpiStepper.moveToRelativePositionInSteps(stepper_num, -1600, wait_to_finish_moving_flg)

# // IF BALL AT IN-1 THEN SERVO-0 (stairs) WAITS 3 SEC THEN GOES FOR 4 SEC THEN STOPS
#   value = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1)
#   print(str(value))
#   servo_number = 0
#   if value !=1:
#       dpiComputer.writeServo(servo_number, 90)
#       sleep(3)
#       dpiComputer.writeServo(servo_number, 180)
#       sleep(4)
#       dpiComputer.writeServo(servo_number, 90)

# // ONE CYCLE ALL THE WAY THROUGH
#   value = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0)
#   print(str(value))
#   stepper_num = 0
#   servo_stair = 0
#   servo_gate = 1
#   wait_to_finish_moving_flg = True
#   if value !=1:
#       dpiComputer.writeServo(servo_gate, 30)
#       dpiStepper.setSpeedInRevolutionsPerSecond(stepper_num, 5)
#       dpiStepper.moveToRelativePositionInRevolutions(stepper_num, -28.5, wait_to_finish_moving_flg)
#       dpiComputer.writeServo(servo_stair, 90)
#       sleep(1)
#       dpiComputer.writeServo(servo_stair, 180)
#       sleep(6)
#       dpiComputer.writeServo(servo_stair, 90)
#       dpiComputer.writeServo(servo_gate, 30)
#       sleep(1)
#       dpiComputer.writeServo(servo_gate, 180)

# // GO UP THEN DOWN
#   value = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0)
#   print(str(value))
#   stepper_num = 0
#   servo_stair = 0
#   servo_gate = 1
#   wait_to_finish_moving_flg = True
#   if value != 1:
#       dpiStepper.setSpeedInRevolutionsPerSecond(stepper_num, 5)
#       dpiStepper.moveToRelativePositionInRevolutions(stepper_num, -28.5, wait_to_finish_moving_flg)
#   value2 = dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_1)
#   print(str(value2))
#   if value2 != 0:
#       dpiStepper.setSpeedInRevolutionsPerSecond(stepper_num, 5)
#       dpiStepper.moveToRelativePositionInRevolutions(stepper_num, 28.5, wait_to_finish_moving_flg)





sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    # Window.fullscreen = True
    # Window.maximize()
    MyApp().run()
