from DebugLog.DebugLog import *
from JoystickController.JoystickController import *

import sys
import pygame
from pygame.locals import *


class JoystickControllerGUI:
    FPS = 60
    SCREEN_WIDTH = 500
    SCREEN_HEIGHT = 500
    SCREEN_COLOUR = (0, 0, 0)

    CURSOR_LEFT = 225
    CURSOR_TOP = 225
    CURSOR_WIDTH = 50
    CURSOR_HEIGHT = 50
    CURSOR_XTEXTPOSITION = (20, 450)
    CURSOR_YTEXTPOSITION = (20, 470)
    CURSOR_MOVEMENTMULTIPLIER = 1 / MotorController.MOTOR_STEP_SIZE
    CURSOR_COLOUR = (255, 0, 0)

    POSITIONTEXT_COLOUR = (255, 255, 255)

    # For Testing: Use keyboard input to move GUI cursor
    KEYBOARD_TEST = False

    def __init__(self):
        self.joystickcontroller = None
        self.keyboardcontroller = None

        if JoystickControllerGUI.KEYBOARD_TEST:
            self.keyboardcontroller = KeyboardController(250, 250, 250, 250)
        else:
            # note: TMC5072 boards do not have unique identifiers that can be detected
            # fine motors must be connected to lower COM port to be correctly assigned
            self.__fine_motors = Motors_TMC5072_eval(2)
            self.__coarse_motor = Motors_TMC5130_eval(1)
            self.joystickcontroller = JoystickController(self.__fine_motors, self.__coarse_motor, 250, 250, 250, 250)

    def update_screen(self, screen, cursor, clock):
        screen.fill(self.SCREEN_COLOUR)

        # update cursor position
        if JoystickControllerGUI.KEYBOARD_TEST:
            cursor.x += self.keyboardcontroller.x_change * self.CURSOR_MOVEMENTMULTIPLIER
            cursor.y += self.keyboardcontroller.y_change * self.CURSOR_MOVEMENTMULTIPLIER
        else:
            cursor.x += self.joystickcontroller.x_change * self.CURSOR_MOVEMENTMULTIPLIER
            cursor.y += self.joystickcontroller.y_change * self.CURSOR_MOVEMENTMULTIPLIER

        # cursor bounds
        if cursor.x < 0:
            cursor.x = 0
        elif cursor.x > self.SCREEN_WIDTH - self.CURSOR_WIDTH:
            cursor.x = self.SCREEN_WIDTH - self.CURSOR_WIDTH
        if cursor.y < 0:
            cursor.y = 0
        elif cursor.y > self.SCREEN_HEIGHT - self.CURSOR_HEIGHT:
            cursor.y = self.SCREEN_HEIGHT - self.CURSOR_HEIGHT

        # update motor position
        if JoystickControllerGUI.KEYBOARD_TEST:
            self.keyboardcontroller.update_position(cursor.centerx, cursor.centery)
        else:
            self.joystickcontroller.update_position(cursor.centerx, cursor.centery)

        pygame.draw.rect(screen, self.CURSOR_COLOUR, cursor)

        # update position text
        positionfont = pygame.font.Font('freesansbold.ttf', 16)
        currentposition = None
        if JoystickControllerGUI.KEYBOARD_TEST:
            currentposition = self.keyboardcontroller.get_position()
        else:
            currentposition = self.joystickcontroller.get_position()
        xpositiontext = positionfont.render("X : " + str(currentposition[0]), True, self.POSITIONTEXT_COLOUR) #cursor.centerx
        ypositiontext = positionfont.render("Y : " + str(currentposition[1]), True, self.POSITIONTEXT_COLOUR) #cursor.centery
        screen.blit(xpositiontext, self.CURSOR_XTEXTPOSITION)
        screen.blit(ypositiontext, self.CURSOR_YTEXTPOSITION)

        # update screen
        pygame.display.update()
        clock.tick(self.FPS)

    def start(self):
        pygame.init()
        pygame.display.set_caption('JoystickController')
        screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        clock = pygame.time.Clock()

        cursor = pygame.Rect(self.CURSOR_LEFT, self.CURSOR_TOP, self.CURSOR_WIDTH, self.CURSOR_HEIGHT)

        pygame.joystick.init()

        while True:
            self.update_screen(screen, cursor, clock)

            for event in pygame.event.get():
                # plugging/unplugging controller
                if event.type == JOYDEVICEADDED:
                    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
                    # assuming only one controller exists at a time
                    if self.joystickcontroller is not None:
                        del self.joystickcontroller
                    self.joystickcontroller = JoystickController(self.__fine_motors, self.__coarse_motor, 250, 250, 250, 250, joysticks[0].get_name())

                elif event.type == JOYDEVICEREMOVED:
                    # assuming only one controller exists at a time
                    del self.joystickcontroller

                # joystick motion
                elif event.type == JOYAXISMOTION:
                    if self.joystickcontroller is not None:
                        self.joystickcontroller.joystick_event(event)

                # button press
                elif event.type == JOYBUTTONDOWN:
                    if self.joystickcontroller is not None:
                        self.joystickcontroller.button_event(event)

                # For Testing: keyboard press
                if JoystickControllerGUI.KEYBOARD_TEST:
                    if event.type == KEYDOWN and (event.key == K_LEFT or event.key == K_RIGHT or event.key == K_UP or event.key == K_DOWN):
                        self.keyboardcontroller.arrowkeysdown_event(event)
                    elif event.type == KEYUP and (event.key == K_LEFT or event.key == K_RIGHT or event.key == K_UP or event.key == K_DOWN):
                        self.keyboardcontroller.arrowkeysup_event(event)
                    elif event.type == KEYDOWN and event.key == K_SPACE:
                        self.keyboardcontroller.spacekeydown_event(event)
                    elif event.type == KEYDOWN and event.key == K_x:
                        self.keyboardcontroller.xkeydown_event(event)

                # end process
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):

                    DebugLog.debugprint(self, event)

                    if JoystickControllerGUI.KEYBOARD_TEST:
                        del self.keyboardcontroller
                    else:
                        del self.joystickcontroller

                    pygame.quit()
                    sys.exit()


if __name__ == '__main__':
    joystickcontrollerGUI = JoystickControllerGUI()
    joystickcontrollerGUI.start()