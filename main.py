from typing import *
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty
from kivy.clock import Clock
import ctypes
import random

class GameInfo(EventDispatcher):
    player_score_a = NumericProperty(0)
    player_score_b = NumericProperty(0)
    TOTAL_SCORE = 5  # 达到5分游戏结束
    TOTAL_TIME = 90  # 达到90秒游戏结束
    
    def __init__(self, **kwargs):
        pass
    
    def reset(self, **kwargs):
        kwargs.get("ball").reset()
        kwargs.get("player_a").reset()
        kwargs.get("player_b").reset()
        kwargs.get("score").win()
        
    def clear(self, *args):
        gameinfo.player_score_a = 0
        gameinfo.player_score_b = 0
        global HANDLE
        if HANDLE is None:
            HANDLE = Clock.schedule_interval(lambda *args: update(**items), 1 / FPS)
gameinfo = GameInfo()


class Point(EventDispatcher):
    
    x = NumericProperty(0)
    y = NumericProperty(0)
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return f"x:{self.x} y:{self.y}"
    

def on_resize(*args):
    Window.size = (800, 600)
    
Window.on_resize = on_resize
WINDOW_SIZE = Point(Window.size[0], Window.size[1])
FPS = 60
items = None  # 字典，可以通过它访问各个控件
HANDLE = None # 通过改句柄，可以冻结游戏

# 加载库，并访问全局数组
kbm = ctypes.CDLL('./kbm.dll')
uint8_t_array_256 = ctypes.c_uint8 * 256
KBM_KEYS_STATE = uint8_t_array_256.in_dll(kbm, "KBM_KEYS_STATE")
VK_W = 0x57
VK_S = 0x53
VK_UP = 0x26
VK_DOWN = 0x28


class Collide:

    def __init__(self, middle=None):
        self._top: Point = Point()
        self._bottom: Point = Point()
        self._left: Point = Point()
        self._right: Point = Point()
        self._middle: Point = Point()
        self._leftbottom = Point()
        self._middle = middle if middle else Point()
        self._middle.bind(x=self.calculate_keys)
        self._middle.bind(y=self.calculate_keys)
        self.v_x = 0 # 0 per second
        self.v_y = 0
        self.name = None
    
    def collide(self, other: Self) -> bool:
        
        crash = {"self": self, "other": other, "self_speed": [self.v_x, self.v_y], "other_speed": [other.v_x, other.v_y]}
        # 进行判断是否发生碰撞
        flag = \
            self.__isInKeypoint(self._top, 
                other._top, other._bottom, other._left, other._right) or\
            self.__isInKeypoint(self._bottom, 
                other._top, other._bottom, other._left, other._right)
        if flag:
            crash["axis"] = "x" # 碰撞截面方向
            return crash
        
        flag = \
            self.__isInKeypoint(self._left, 
                other._top, other._bottom, other._left, other._right) or\
            self.__isInKeypoint(self._right, 
                other._top, other._bottom, other._left, other._right)
        if flag:
            crash["axis"] = "y"
            return crash
        
        crash["axis"] = None
        return crash
    
    def __isInKeypoint(self, key: Point, t: Point, b: Point, l: Point, r: Point) -> bool:
        # 判断key是否在t、b、l、r当中
        flag =\
            l.x <= key.x and\
            key.x <= r.x and\
            b.y <= key.y and\
            key.y <= t.y
        return flag
    
    def calculate_keys(self, *args):
        pass
    
    def update(self, crash):
        dx = (1 / FPS) * self.v_x
        dy = (1 / FPS) * self.v_y
        self._middle.x += dx
        self._middle.y += dy
    
    
class Racket(Widget, Collide):
    
    WIDTH = 50
    HEIGHT = 300
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_keys()
        self.SPEED = 200
        
    def calculate_keys(self, *args) -> None:
        self._top.x = self._middle.x
        self._top.y = self._middle.y + self.HEIGHT / 2
        self._bottom.x = self._middle.x
        self._bottom.y = self._middle.y - self.HEIGHT / 2
        self._left.x = self._middle.x - self.WIDTH / 2
        self._left.y = self._middle.y
        self._right.x = self._middle.x + self.WIDTH / 2
        self._right.y = self._middle.y
        self._leftbottom.x = self._middle.x - self.WIDTH / 2
        self._leftbottom.y = self._middle.y - self.HEIGHT / 2
    
    def update(self, crash):
        if self.name == "player_a":
            if KBM_KEYS_STATE[VK_W]:
                self.v_y = self.SPEED
            elif KBM_KEYS_STATE[VK_S]:
                self.v_y = -self.SPEED
            else:
                self.v_y = 0
        
        elif self.name == "player_b":
            if KBM_KEYS_STATE[VK_UP]:
                self.v_y = self.SPEED
            elif KBM_KEYS_STATE[VK_DOWN]:
                self.v_y = -self.SPEED
            else:
                self.v_y = 0
                
        else:
            pass
        
        if crash.get("axis") == "x":
            self.v_y = 0
            if crash.get("other").name == "wall_top":
                self._middle.y = crash.get("other")._bottom.y - self.HEIGHT / 2
            if crash.get("other").name == "wall_bottom":
                self._middle.y = crash.get("other")._top.y + self.HEIGHT / 2
       
        super().update(crash)
        
    def reset(self):
        if self.name == "player_a":
            self._middle.x = 50
            self._middle.y = WINDOW_SIZE.y / 2
        if self.name == "player_b":
            self._middle.x = WINDOW_SIZE.x - 50
            self._middle.y = WINDOW_SIZE.y / 2
            
    
        
        
class Ball(Widget, Collide):
    
    RADIUS = 50
    SPEED = 150
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_keys()
        self.v_x = -self.SPEED
        self.name = "ball"
        self.signal = -1
        
    def calculate_keys(self, *args):
        self._top.x = self._middle.x
        self._top.y = self._middle.y + self.RADIUS
        self._bottom.x = self._middle.x
        self._bottom.y = self._middle.y - self.RADIUS
        self._left.x = self._middle.x - self.RADIUS
        self._left.y = self._middle.y
        self._right.x = self._middle.x + self.RADIUS
        self._right.y = self._middle.y
        self._leftbottom.x = self._middle.x - self.RADIUS
        self._leftbottom.y = self._middle.y - self.RADIUS
        
    def update(self, crash: Dict):   # 每一帧都会被调用
        if crash:
            self.score(crash)
            
            axis = crash.get("axis")
            other_speed_vy = crash.get("other_speed")[1]
            offset_vy = random.random() * other_speed_vy
            
            if axis == "x":
                self.v_y = -self.v_y
            if axis == "y":
                self.v_x = -self.v_x
                self.v_y += offset_vy
            else:
                pass
                
        super().update(crash)
        
    def score(self, crash: Dict):
        if crash.get("axis") == "y":
            if crash.get("other").name == "wall_left":
                gameinfo.player_score_b += 1
            if crash.get("other").name == "wall_right":
                gameinfo.player_score_a += 1
                
        
    def reset(self):
        self._middle.x = WINDOW_SIZE.x / 2
        self._middle.y = WINDOW_SIZE.y / 2
        self.v_y = 0
        self.v_x = -self.SPEED * self.signal
        self.signal *= -1
        
        
class Wall(Collide):
    def __init__(self, middle=None):
        super().__init__()
        self.HEIGHT = 100
        self.WIDTH = WINDOW_SIZE.x + 1000
        self.calculate_keys()
        
    def calculate_keys(self, *args):
        self._top.x = self._middle.x
        self._top.y = self._middle.y + self.HEIGHT / 2
        self._bottom.x = self._middle.x
        self._bottom.y = self._middle.y - self.HEIGHT / 2
        self._left.x = self._middle.x - self.WIDTH / 2
        self._left.y = self._middle.y
        self._right.x = self._middle.x + self.WIDTH / 2
        self._right.y = self._middle.y
        self._leftbottom.x = self._middle.x - self.WIDTH / 2
        self._leftbottom.y = self._middle.y - self.HEIGHT / 2
    
    
class Score(Widget, Collide): # 继承collide，但是不使用其中的功能
    sc1 = NumericProperty(0)
    sc2 = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        gameinfo.bind(player_score_a=self.sync)
        gameinfo.bind(player_score_b=self.sync)
        
    def sync(self, *args):
        self.sc1 = gameinfo.player_score_a
        self.sc2 = gameinfo.player_score_b
        
        
    def win(self, **kwargs):
        if self.sc1 >= gameinfo.TOTAL_SCORE or self.sc2 >= gameinfo.TOTAL_SCORE:
            if self.sc1 >= self.sc2:
                self.ids["show"].text = "Winner            Loser!"
            else:
                self.ids["show"].text = "Loser            Winner!"
                
            global HANDLE
            if HANDLE is not None:
                HANDLE.cancel()
                HANDLE = None
            Clock.schedule_once(gameinfo.clear, 5)


class RootLayout(FloatLayout):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 获取玩家和球的实例
        self.player_a: Racket = self.ids["player_a"]
        self.player_b: Racket = self.ids["player_b"]
        self.ball: Ball = self.ids["ball"]
        
        self.player_a._middle.x = 50
        self.player_a._middle.y = WINDOW_SIZE.y / 2
        self.player_a.name = "player_a"

        self.player_b._middle.x = WINDOW_SIZE.x - 50
        self.player_b._middle.y = WINDOW_SIZE.y / 2
        self.player_b.name = "player_b"
        
        self.ball._middle.x = WINDOW_SIZE.x / 2
        self.ball._middle.y = WINDOW_SIZE.y / 2
        
        # 创建上下墙壁的实例
        self.wall_top = Wall()
        self.wall_bottom = Wall()
        self.wall_top.name = "wall_top"
        self.wall_bottom.name = "wall_bottom"
        
        self.wall_top._middle.x = WINDOW_SIZE.x / 2
        self.wall_top._middle.y = WINDOW_SIZE.y
        
        self.wall_bottom._middle.x = WINDOW_SIZE.x / 2
        self.wall_bottom._middle.y = 0
        
        # 创建左右墙壁实例
        self.wall_left = Wall()
        self.wall_right = Wall()
        self.wall_left.name = "wall_left"
        self.wall_right.name = "wall_right"
        
        self.wall_left._middle.x = -500
        self.wall_left._middle.y = WINDOW_SIZE.y / 2
        
        self.wall_right._middle.x = WINDOW_SIZE.x + 500
        self.wall_right._middle.y = WINDOW_SIZE.y / 2
        
        self.wall_left.WIDTH = 100
        self.wall_left.HEIGHT = WINDOW_SIZE.y
        
        self.wall_right.WIDTH = 100
        self.wall_right.HEIGHT = WINDOW_SIZE.y
        
        self.wall_left.calculate_keys()
        self.wall_right.calculate_keys()
        
        # 获取分数显示实例
        self.score = self.ids["score"]
        

def update(**kwargs): # 所有需要刷新的类
    ball: Ball = kwargs.get("ball")
    keys = [key for key, item in kwargs.items()]
    items = [item for key, item in kwargs.items()]
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            key1 = keys[i]
            key2 = keys[j]
            item1 = items[i]
            item2 = items[j]
            
            crash1 = item1.collide(item2)
            crash2 = item2.collide(item1)
            item1.update(crash1)
            item2.update(crash2)
            
    kwargs.get("score").win(**kwargs)


class PongGameApp(App):
    
    def build(self):
        rootlayout = RootLayout()
        global items
        items = {
            "ball": rootlayout.ball,
            "player_a": rootlayout.player_a,
            "player_b": rootlayout.player_b,
            "wall_top": rootlayout.wall_top,
            "wall_bottom": rootlayout.wall_bottom,
            "wall_left": rootlayout.wall_left,
            "wall_right": rootlayout.wall_right,
            "score": rootlayout.score
        }
        global HANDLE
        HANDLE = Clock.schedule_interval(lambda *args: update(**items), 1 / FPS)
        return rootlayout
    
    def on_start(self):
        kbm.MonitorStart()
        gameinfo.bind(player_score_a=lambda *args: gameinfo.reset(**items))
        gameinfo.bind(player_score_b=lambda *args: gameinfo.reset(**items))
        return super().on_start()
    
    

if __name__ == "__main__":
    PongGameApp().run()
    
