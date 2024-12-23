import cv2
import numpy as np
# import pandas as pd
import math

class Loc:
    def __init__(self, *args):
        # 检查传入的是一个长度为2的列表或元组
        if len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:

            self.loc_x, self.loc_y = args[0]
        # 检查传入的是两个独立的整数
        elif len(args) == 2 and all(isinstance(arg, int) for arg in args):
            self.loc_x, self.loc_y = args
        else:
            raise TypeError("Either provide a tuple/list of length 2 or two integers.")

    def __add__(self, loc):
        if isinstance(loc, Loc):
            return Loc((self.loc_x + loc.loc_x, self.loc_y + loc.loc_y))
        elif isinstance(loc, (tuple, list)) and len(loc) == 2:
            return Loc((self.loc_x + loc[0], self.loc_y + loc[1]))
        else:
            raise TypeError('Operand must be a Loc object or a list/tuple of length 2')

    def __sub__(self, loc):
        if isinstance(loc, Loc):
            return Loc((self.loc_x - loc.loc_x, self.loc_y - loc.loc_y))
        elif isinstance(loc, (tuple, list)) and len(loc) == 2:
            return Loc((self.loc_x - loc[0], self.loc_y - loc[1]))
        else:
            raise TypeError('Operand must be a Loc object or a list/tuple of length 2')
    def __mul__(self, multiple):
        new_x = round(self.loc_x * multiple)
        new_y = round(self.loc_y * multiple)
        return Loc(new_x,new_y)
    
    def add(self,loc):
        if isinstance(loc, Loc):
            self.loc_x += loc.loc_x
            self.loc_y += loc.loc_y
        elif isinstance(loc, (tuple, list)) and len(loc) == 2:
            self.loc_x += loc[0]
            self.loc_y += loc[1]
        else:
            raise TypeError('Operand must be a Loc object or a list/tuple of length 2')

    def to_tuple(self):
        return (self.loc_x, self.loc_y)
    
    def distance_s(self):
        return self.loc_x**2 + self.loc_y**2

    def __repr__(self):
        return f"Loc({self.loc_x}, {self.loc_y})"


def match_template(screen, template_path, threshold=0.8,img_func=lambda a:a):
    """
    使用模板匹配检查屏幕是否包含指定模板
    :param screen: 当前屏幕图像 (numpy array)
    :param template_path: 模板图像路径
    :param threshold: 匹配阈值
    :return: 是否匹配 (bool), 匹配的中心点坐标 (tuple 或 None),模板的长宽
    """
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    # 图像处理
    screen = img_func(screen)
    template = img_func(template)

    # 模板匹配
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    max_loc = Loc(max_loc)
    if max_val >= threshold:
        template_h, template_w = template.shape[:2]
        center = max_loc + Loc(template_w,template_h)*0.5
        return True, center.to_tuple(), (template_w,template_h)
    return False, None, None

# class StaticLocation:
#     """
#     通过屏幕分辨率和对应的lib获取对应的图标位置
#     """
#     def __init__(self,resolution=(1600,900),lib_file_path='resource/loc_lib.csv'):
#         # 窗口分辨率
#         self.width,self.height = resolution
#         # 获取固定图标位置库
#         self.loc_lib = self.get_loc_lib(lib_file_path)
#     def get_static_loc(self,obj):
#         # 从库中获取固定图标在图像中的相对比例
#         x_rate, y_rate = self.loc_lib.get(obj)
#         # 计算相对比例
#         loc_x = round(self.width * x_rate)
#         loc_y = round(self.height * y_rate)

#         assert loc_x <= self.width,'x坐标超出窗口分辨率'
#         assert loc_y <= self.height,'y坐标超出窗口分辨率'

#         return (loc_x,loc_y)

#     def get_loc_lib(self,lib_file_path):
#         # 读取固定图标库
#         loc_df = pd.read_csv(lib_file_path).to_dict(orient='records')
#         loc_dict = {x['obj']:(x['x_rate'],x['y_rate'])for x in loc_df}
#         self.loc_lib = loc_dict


def match_template_all(screen, template_path,min_distance=10,threshold=0.8,img_func=lambda x:x):
    """
    使用模板匹配检查屏幕包含指定模板的位置
    :param screen: 当前屏幕图像 (numpy array)
    :param template_path: 模板图像路径
    :param min_distance: 一般图标之间的间距
    :param threshold: 匹配阈值
    :return: 是否匹配 (bool), 匹配的中心点坐标 (tuple 或 None),模板的长宽
    """
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    # 图像处理
    screen = img_func(screen)
    template = img_func(template)

    # 模板匹配
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    # 通过 np.where() 获取匹配点的坐标
    locations = np.where(result >= threshold)  # 找到所有匹配值大于阈值的位置

    match_points = list(zip(*locations[::-1]))
    filtered_points = filter_nearby_points(match_points, min_distance)

    # 计算中心位置
    template_h, template_w = template.shape[:2]
    temp_center = Loc(template_w, template_h) * 0.5

    all_center_points = [(Loc(x) + temp_center).to_tuple() for x in filtered_points]
    return all_center_points

def filter_nearby_points(points, min_distance=50):
    """
    过滤掉过于接近的匹配点
    :param points: 匹配点列表 [(x, y), (x, y), ...]
    :param min_distance: 点之间的最小距离，低于此距离的点将被丢弃
    :return: 过滤后的匹配点列表
    """
    filtered_points = []
    
    for pt in points:
        if not filtered_points:
            filtered_points.append(pt)
        else:
            # 判断当前点和已选择点的距离
            add_point = True
            for fpt in filtered_points:
                distance = math.sqrt((fpt[0] - pt[0]) ** 2 + (fpt[1] - pt[1]) ** 2)
                if distance < min_distance:
                    add_point = False
                    break
            if add_point:
                filtered_points.append(pt)
    
    return filtered_points    


if __name__ == "__main__":
    img = cv2.imread('test0.png')
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    match_template_all(img_gray,'page_icons/event_juge_high.png')
