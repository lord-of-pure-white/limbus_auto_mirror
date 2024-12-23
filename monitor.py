from screenshot import window_screenshot
from location_compute import  match_template, Loc, match_template_all
import os
from ocr import img_ocr
class WindowMonitor:
    def __init__(self,icons_path = 'page_icons/',resolution=(1600,900),lib_file_path='resource/loc_lib.csv'):
        self.window_loc = None
        self.title_height = None
        self.screen = None
        self.icons_path = icons_path
        self.resolution = resolution
        self.refresh()
        # self.static_location = StaticLocation(resolution,lib_file_path)

    def refresh(self):
        loc,title_height = get_main_loc()
        self.window_loc,self.title_height = loc,title_height
        if self.window_loc:
            self.screen = window_screenshot(self.window_loc,self.title_height)
            return True
        else:
            self.screen = None
            return False
    
    def find(self,obj,range=None,**kwargs):
        # if obj in self.static_location.loc_lib:
        #     return self.static_location.get_static_loc(obj)
        file_path = os.path.join(self.icons_path,'{}.png'.format(obj))
        if not os.path.exists(file_path):
            return False, None, None
        found,loc,tem_size= match_template(self.screen,file_path,**kwargs)
        if found:
            loc = Loc(loc)
            window_loc = Loc(self.window_loc)
            loc = loc + window_loc
            return found, loc.to_tuple(), tem_size
        else:
            return False, None, None
    def find_all(self,obj,min_distance=10,range=None,**kwargs):
        # if obj in self.static_location.loc_lib:):
        file_path = os.path.join(self.icons_path,'{}.png'.format(obj))
        if not os.path.exists(file_path):
            print(f"Unknown path : {file_path}")
            return []
        if not range:
            range = [(0,0)]
        locs = [(Loc(x) + self.window_loc + range[0]).to_tuple() for x in match_template_all(self.screen,file_path,min_distance,**kwargs)]
        return locs
    def ocr(self,range=None):
        # range like ((x1,y1),(x2,y2))，左上和右下
        # 去掉标题
        img = self.screen[self.title_height:,:]
        if range:
            img = img[range[0][1]:range[1][1],range[0][0]:range[1][0]]
        else:
            pass
        return img_ocr(img)
    def new_find(self,obj,range=None,**kwargs):
        self.refresh()
        return self.find(obj,range,**kwargs)



def get_main_loc():
    """
    获取窗口位置
    :return: 左上角横纵坐标(tuple)，title模板高度
    """
    from screenshot import full_screenshot
    screen = full_screenshot()
    result = match_template(screen,'page_icons/game_title.png')
    if not result[0]:
        return None,None
    else:
        title_center = Loc(result[1])
        title_temp_size = Loc(result[2])
        window_loc = title_center - title_temp_size*0.5
        title_h = title_temp_size.loc_y
        return window_loc.to_tuple(), title_h

