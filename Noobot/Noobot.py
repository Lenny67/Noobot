from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
import math
import time


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class Noobot(BaseAgent):
    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.controller = SimpleControllerState()

        # Constants
        self.DODGE_TIME = 0.2
        self.DISTANCE_TO_DODGE = 500
        self.DISTANCE_FROM_BALL_TO_BOOST = 1500
        self.POWERSLIDE_ANGLE = 120

        # Game values
        self.bot_pos = None
        self.bot_yaw = None
        

        # Dodging
        self.should_dodge = False
        self.on_second_jump = False
        self.next_dodge_time = 0


    def aim(self, target_x, target_y):
        angle_between_bot_and_target = math.atan2(target_y - self.bot_pos.y, target_x - self.bot_pos.x)
        
        angle_front_to_target = math.degrees(angle_between_bot_and_target - self.bot_yaw)
        
        kickOff = False

        # Correct the values
        if angle_front_to_target < -180:
            angle_front_to_target += 2 * 180
        if angle_front_to_target > 180:
            angle_front_to_target -= 2 * 180

        
         # Steering and Powersliding
        if angle_front_to_target < (-3.5) and abs(angle_front_to_target) < self.POWERSLIDE_ANGLE and kickOff == False:
            self.controller.steer = -1
            self.controller.handbrake = 0
        elif angle_front_to_target > 3.5 and abs(angle_front_to_target) < self.POWERSLIDE_ANGLE and kickOff == False:
            self.controller.steer = 1
            self.controller.handbrake = 0
        elif angle_front_to_target < (-3.5) and abs(angle_front_to_target) > self.POWERSLIDE_ANGLE and kickOff == False:
            self.controller.steer = -1
            self.controller.handbrake = 1
        elif angle_front_to_target > 3.5 and abs(angle_front_to_target) > self.POWERSLIDE_ANGLE and kickOff == False:
            self.controller.steer = 1
            self.controller.handbrake = 1
        else:
            self.controller.steer = 0
            self.controller.handbrake = 0


    def check_for_dodge(self):
        if self.should_dodge and time.time() > self.next_dodge_time:
            self.controller.jump = True
            self.controller.pitch = -1

            if self.on_second_jump:
                self.on_second_jump = False
                self.should_dodge = False
            else:
                self.on_second_jump = True
                self.next_dodge_time = time.time() + self.DODGE_TIME

    # Closest point to hit ball on target
    def closest_point(self, x1, y1, x2, y2, x3, y3):
        k = ((y2 - y1) * (x3 - x1) - (x2 - x1) * (y3 - y1)) / ((y2 - y1) ** 2 + (x2 - x1) ** 2)
        x4 = x3 - k * (y2 - y1)
        y4 = y3 + k * (x2 - x1)

        return x4, y4

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        self.bot_yaw = packet.game_cars[self.team].physics.rotation.yaw
        self.bot_pos = packet.game_cars[self.index].physics.location
        ball_pos = packet.game_ball.physics.location


        # Kickoff 
        if ball_pos.x == 0 and ball_pos.y == 0:
            kickOff = True
            # Right corner
            if (self.bot_pos.x < -1918 and self.bot_pos.x > -2050 and self.team == 0) or (self.bot_pos.x > 1918 and self.bot_pos.x < 2050 and self.team == 1):
                self.controller.throttle = 1
                self.aim(ball_pos.x, ball_pos.y)
            # Left corner
            elif (self.bot_pos.x > 1918 and self.bot_pos.x < 2050 and self.team == 0) or (self.bot_pos.x < -1918 and self.bot_pos.x > -2050 and self.team == 1):
                self.controller.throttle = 1
                self.aim(ball_pos.x, ball_pos.y)
            # Back right
            elif (self.bot_pos.x < -254 and self.bot_pos.x > -258 and self.team == 0) or (self.bot_pos.x > 254 and self.bot_pos.x < 258 and self.team == 1):
                self.controller.throttle = 1
                self.aim(ball_pos.x, ball_pos.y)
            # Back left
            elif (self.bot_pos.x < 258 and self.bot_pos.x > 254 and self.team == 0) or (self.bot_pos.x > -258 and self.bot_pos.x < -254 and self.team == 1):
                self.controller.throttle = 1
                self.aim(ball_pos.x, ball_pos.y)
            # Center
            elif (self.bot_pos.x < 2 and self.bot_pos.x > -2 and self.team == 0) or (self.bot_pos.x > -2 and self.bot_pos.x < 2 and self.team == 1):
                self.controller.throttle = 1
                self.aim(ball_pos.x, ball_pos.y)
        else:
            kickOff = False
            self.controller.throttle = 1
        

        # Behind ball
        if (self.index == 0 and self.bot_pos.y < ball_pos.y) or (self.index == 1 and self.bot_pos.y > ball_pos.y):
            self.aim(ball_pos.x, ball_pos.y)
            if distance(self.bot_pos.x, self.bot_pos.y, ball_pos.x, ball_pos.y) > self.DISTANCE_FROM_BALL_TO_BOOST and self.bot_pos.z < 18:
                # Boost
                self.controller.boost = True
            elif distance(self.bot_pos.x, self.bot_pos.y, ball_pos.x, ball_pos.y) < self.DISTANCE_TO_DODGE and self.bot_pos.z < 18 and ball_pos.z < 220:
                # Dodge
                self.controller.boost = False
                self.should_dodge = True
        else: 
            # Go to goal
            if self.team == 0 and kickOff == False:
                # Blue team
                self.aim(0, -5000)
            elif kickOff == False:
                # Orange team
                self.aim(0, 5000)


        self.controller.jump = 0

        self.check_for_dodge()

        return self.controller
