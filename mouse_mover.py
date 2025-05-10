import ctypes
import time
import random

# 定义鼠标事件常量
MOUSEEVENTF_LEFTDOWN = 0x0002  # 鼠标左键按下
MOUSEEVENTF_LEFTUP = 0x0004    # 鼠标左键抬起
MOUSEEVENTF_RIGHTDOWN = 0x0008 # 鼠标右键按下
MOUSEEVENTF_RIGHTUP = 0x0010   # 鼠标右键抬起

# 获取 Windows API 的用户库
user32 = ctypes.windll.user32

def move_mouse(loc):
    """
    直接移动鼠标到指定位置
    :param loc: tuple:(x,y)
    """
    user32.SetCursorPos(loc[0], loc[1])

def get_mouse_position():
    """
    获取当前鼠标位置
    :return: (x, y) 当前鼠标坐标
    """
    point = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return (point.x, point.y)

def move_mouse_smooth(loc, duration=0.5,random_range=8, jitter=3):
    """
    平滑移动鼠标到目标位置
    :param x: 目标横坐标
    :param y: 目标纵坐标
    :param duration: 移动所需时间（秒）
    """
    x,y = loc
    start_x, start_y = get_mouse_position()
    # 随机步数 80~120
    steps = 100
    steps += random.randint(-20,20)
    sleep_time = duration / steps  # 每步的间隔时间

    dx = (x + random.randint(-random_range,random_range) - start_x) / steps
    dy = (y + random.randint(-random_range,random_range) - start_y) / steps

    for step in range(steps):
        intermediate_x = int(start_x + dx * step + random.randint(-jitter, jitter))
        intermediate_y = int(start_y + dy * step + random.randint(-jitter, jitter))
        user32.SetCursorPos(intermediate_x, intermediate_y)
        time.sleep(sleep_time)


def mouse_click(button="left", double_click=False):
    """
    模拟鼠标点击
    :param button: 按钮类型 ("left" 或 "right")
    :param double_click: 是否双击
    """
    if button == "left":
        down_button = MOUSEEVENTF_LEFTDOWN
        up_button = MOUSEEVENTF_LEFTUP
    elif button == "right":
        down_button = MOUSEEVENTF_RIGHTDOWN
        up_button = MOUSEEVENTF_RIGHTUP
    else:
        raise ValueError("Unsupported button type: Use 'left' or 'right'.")
    ctypes.windll.user32.mouse_event(down_button, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(up_button, 0, 0, 0, 0)
    if double_click:
        time.sleep(0.1)  # 双击间隔
        ctypes.windll.user32.mouse_event(down_button, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(up_button, 0, 0, 0, 0)
        time.sleep(0.3)
    

def mouse_continuous_clicks(button="left",click_times = 10):
    """
    模拟鼠标多次点击
    :param x: 横坐标
    :param y: 纵坐标
    :param button: 按钮类型 ("left" 或 "right")
    :param double_click: 是否双击
    """
    if button == "left":
            down_button = MOUSEEVENTF_LEFTDOWN
            up_button = MOUSEEVENTF_LEFTUP
    elif button == "right":
        down_button = MOUSEEVENTF_RIGHTDOWN
        up_button = MOUSEEVENTF_RIGHTUP
    else:
        raise ValueError("Unsupported button type: Use 'left' or 'right'.")
    for _ in range(click_times):
        ctypes.windll.user32.mouse_event(down_button, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(up_button, 0, 0, 0, 0)
        time.sleep(0.2)


def move_and_click(loc,**kwargs):
    move_mouse_smooth(loc,**kwargs)
    time.sleep(random.uniform(0.2, 0.5))
    mouse_click()

def mouse_drag(loc_list,wait_time = 0):
    """
    实现鼠标拖拽的功能
    :param coordinate_list: 需要经过的坐标列表
    """
    if len(loc_list) < 2:
        raise ValueError("坐标列表至少需要两个点")
        
    
    # 第一步：移动到第一个坐标并按下鼠标左键
    first_loc = loc_list[0]
    move_mouse_smooth(first_loc,0.5,2,1)  # 移动到起始点
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)  # 按下左键
    time.sleep(0.05)  # 等待一会儿，模拟用户按下的动作

    # 第二步：依次移动到坐标列表中的每个坐标
    for loc in loc_list[1:]:
        move_mouse_smooth(loc,0.5,2,1)  # 移动鼠标到下一个坐标
        time.sleep(0.05)  # 延迟，模拟平滑拖动效果
    time.sleep(wait_time)

    # 第三步：松开鼠标左键
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)  # 放开左键
    time.sleep(0.05)  # 等待一会儿，模拟用户松开鼠标的动作
