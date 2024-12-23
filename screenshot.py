import mss
import numpy as np
import cv2
import time
from location_compute import Loc
def to_gray(screenshot):
    """
    将mss的截图转为np数组并做灰度处理
    """
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def full_screenshot():
    """
    全图截屏
    :return:屏幕图像的np数组
    """
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[0])  # 获取屏幕的截图

    img = to_gray(screenshot)
    return img


def part_screenshot(min_x,min_y,max_x,max_y):
    """
    选取区域截屏
    :params min_x: 左坐标
    :params min_y: 上坐标
    :params max_x: 右坐标
    :params max_y: 下坐标
    """
    assert (max_x > min_x) and (max_y > min_y),'输入的范围不合法'
    region = {
        'top' : min_y,
        'left': min_x,
        'width': max_x - min_x,
        'height':max_y - min_y
        }
    with mss.mss() as sct:
        screenshot = sct.grab(region)
    img = to_gray(screenshot)
    return img

def window_screenshot(loc,title_height=30,resolution=(1600,900)):
    """
    窗口截图
    :loc:tuple,窗口左上角
    :title_height:int,窗口标题高度(30)
    :resolution:tuple,(height,width)窗口大小（分辨率）
    """
    min_x,min_y = loc
    width,height = resolution
    height += title_height
    max_x = min_x + width
    max_y = min_y + height
    return part_screenshot(min_x,min_y,max_x,max_y)
    
