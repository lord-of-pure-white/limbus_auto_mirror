from mouse_mover import move_and_click,move_mouse_smooth,mouse_continuous_clicks,mouse_drag
import time
from location_compute import Loc
from monitor import WindowMonitor
import numpy as np
import cv2
import random
import re
from config import *

class Checker:
    def __init__(self,monitor):
        self.monitor = monitor
        self.window_status = "start"
    def check_screen(self):
        for _ in range(MAX_RETRY):
            if self.monitor.refresh():
                self.window_status = 'live'
                return True
            else:
                time.sleep(5)
        self.window_status = 'dead'
        return False


class Solver():
    def __init__(self,monitor):
        self.monitor = monitor
        self.status = 'start'
    def move_free(self,offset=(150,150)):
        # 鼠标移动到其他位置避免遮挡
        window_loc = Loc(self.monitor.window_loc) + offset
        move_mouse_smooth(window_loc.to_tuple())
    

class FreeFightChecker(Checker):
    def __init__(self,monitor):
        super().__init__(monitor)

    def is_in(self):
        return self.monitor.find('in_fight')[0]
    
    def is_end(self):
        return self.monitor.find('confirm')[0]
    
    def is_out(self):
        return self.monitor.find('out_fight')[0]
    
    def is_go(self):
        return self.monitor.find('choosing_card')[0]
    
    def is_wait(self):
        return self.monitor.find('start_fight',threshold=0.65)[0]
    
    def is_event(self):
        return self.monitor.find('in_event')[0]
    
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_in():
                    return 'in_battle'
                elif self.is_end():
                    return 'end_battle'
                elif self.is_out():
                    return 'end_battle'
                elif self.is_go():
                    return 'end_battle'
                elif self.is_wait():
                    return 'wait_battle'
                elif self.is_event():
                    return 'into_event'
                else:
                    return 'not_battle'
            else:
                time.sleep(2)
        return 'dead'

class FreeFightSolver(Solver):
    """
    战斗事件（自动）：
    根据是否有'胜率'文字图标进行识别，是否'等待战斗',需要进行操作。
    操作过后进入'正在战斗'状态
    根据是否有'暂停'符号图标进行识别，是否'正在战斗'。
    正在战斗过程完成后,会有多种情况。
    目前有:进入事件（'还没做'）、战斗结束胜利确认('确认'文字图标)、战斗结束失败确认(还没做)，回到地图。
    """
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = FreeFightChecker(self.monitor)

    def to_fight(self):
    
        _,loc,_ = self.monitor.find('start_fight',threshold=0.6)
        loc = Loc(loc)
        # 这里要写一个方法去获取相对位置
        loc_fight = loc + (-120,16)
        # 点击'胜率'
        move_and_click(loc.to_tuple())
        # 点击'start'
        move_and_click(loc_fight.to_tuple())
        # 鼠标移动到其他位置避免遮挡
        super().move_free()
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'in_battle':
                self.retry = 0
                time.sleep(2)
            elif status == 'end_battle':
                return True
            elif status == 'wait_battle':
                self.retry += 1
                self.to_fight()
            elif status == 'into_event':
                event = EventSolver(self.monitor)
                r = event.run()
                if not r:
                    return False
            elif status == 'not_battle':
                s = ResultSolver(self.monitor)
                s.run()
                time.sleep(2)
            elif status == 'dead':
                return False

class EventChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_in(self):
        return self.monitor.find('in_event')[0]
    def is_choice(self):
        return self.monitor.find('event_choice')[0]
    def is_judge(self):
        return self.monitor.find('event_judge')[0]
    def is_continue(self):
        return self.monitor.find('event_continue')[0]
    def is_into_juge(self):
        return self.monitor.find('event_start_judge')[0]
    def is_fight(self):
        return self.monitor.find('event_start_fight')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_continue():
                    return 'continue'
                elif self.is_into_juge():
                    return 'start_juge'
                elif self.is_judge():
                    return 'judge'
                elif self.is_choice():
                    return 'choice'
                elif self.is_fight():
                    return 'fight'
                elif self.is_in():
                    return 'in_event'
                else:
                    return 'not_battle'
            else:
                return 'dead'
        

    

class EventSolver(Solver):
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = EventChecker(self.monitor)
        self.priority0 = EVENT_priority0
        self.priority1 = EVENT_priority1

    def to_choose_judger(self):
        # 选择判定人物，选择其中成功率最高的
        for chance in ['very_high','high','normal','low','very_low']:
            judger = self.monitor.find_all('event_judge_{}'.format(chance))
            if judger:
                judger_loc = Loc(judger[0]) + Loc(0,60)
                print(chance)
                print(judger_loc)
                move_and_click(judger_loc.to_tuple())
                super().move_free()
                break
    def to_start_judge(self):
        _, loc, _ = self.monitor.find('event_start_judge')
        move_and_click(loc)
        time.sleep(2)
        super().move_free()
        mouse_continuous_clicks(click_times = 5)
    def to_continue(self):
        while True:
            self.monitor.refresh()
            found, loc, _ = self.monitor.find('event_continue')
            if found:
                move_and_click(loc)
                time.sleep(1)
            else:
                break
        return True
    def sort_chose(self,chooses,priority_list):
        # TODO：这里应该是有bug的，后面看着改下，不是很影响
        r = []
        if priority_list:
            for p in priority_list:
                for x in chooses:
                    if p in x.get('info'):
                        r.append(x)
        if r:
            return r
        return chooses
    def analysis_choices(self,datas):
        for x in datas:
            info = set()
            text = x.get('text')
            if '判定' in text:
                info.add('judge')
            elif '战斗胜利后' in text:
                info.add('fight')
            else:
                info.add('normal')
            if '饰品' in text:
                info.add('ego')
            if '等级提升' in text:
                info.add('level')
            x['info'] = info
    def to_choose(self):
        top_left = (860,250)
        datas = self.monitor.ocr(range=(top_left,(1450,690)))
        self.analysis_choices(datas)
        for p_list in ([self.priority0,self.priority1]):
            datas = self.sort_chose(datas,p_list)
        print(datas[0])
        r = Loc(datas[0]['loc'][0]) + Loc(top_left)
        r += Loc(self.monitor.window_loc)
        move_and_click(r.to_tuple())
        super().move_free()
        mouse_continuous_clicks(click_times=3)
    def into_fight(self):
        _, loc, _ = self.monitor.find('event_start_fight')
        move_and_click(loc)
        time.sleep(1)

    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'in_event':
                window_loc = Loc(self.monitor.window_loc) + (300,300)
                move_mouse_smooth(window_loc.to_tuple())
                mouse_continuous_clicks()
            elif status == 'fight':
                self.into_fight()
                return True
            elif status == 'judge':
                self.to_choose_judger()
            elif status == 'start_juge':
                self.to_start_judge()
            elif status == 'continue':
                if self.to_continue():
                    found, _ , _ = self.monitor.new_find('in_event')
                    if not found:
                        return True
            elif status == 'choice':
                self.to_choose()
            elif status == 'dead':
                return False



def arrow_img_func(img):
    """
    处理镜牢背景图像
    """
    sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)  # X方向
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)  # Y方向
    sobel_combined = cv2.magnitude(sobel_x, sobel_y)     # 合并梯度
    img = np.uint8(np.absolute(sobel_combined))
    img = cv2.Canny(img, threshold1=100, threshold2=400, apertureSize=3, L2gradient=True)
    img = cv2.GaussianBlur(img, (13, 13), 0)
    return img


class RouteChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_goto(self):
        return self.monitor.find('route_goto')[0]
    def is_on_way(self):
        return self.monitor.find('out_fight')[0] and self.monitor.find('on_way')[0]
    
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_goto():
                    return 'goto'
                elif self.is_on_way():
                    return 'on_way'
                else:
                    time.sleep(1)
            else:
                return 'dead'
        return 'on_way'




class RouteSolver(Solver):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = RouteChecker(self.monitor)
    def chose_route(self):
        found, loc_now, _ = self.monitor.new_find('now_loc')
        if not found:
            print(11111111)
            return False
        loc_now = Loc(loc_now)
        loc_now = loc_now + Loc(0,45)
        # 找箭头位置，火车头位置到箭头位置向量*2则是鼠标要移动的向量
        for arrow in ('arrow_ahead','arrow_low_ahead','arrow_high_ahead'):
            found, loc_arrow, _ = self.monitor.find(arrow,threshold = 0.7,img_func=arrow_img_func)
            if found:
                loc_arrow = Loc(loc_arrow)
                loc0 = loc_arrow * 2 - loc_now
                move_and_click(loc0.to_tuple())
                time.sleep(1)   
                return True
        # 如果图像不清楚导致找不到，则调整阈值并筛选图像
        for arrow in ('arrow_ahead','arrow_low_ahead','arrow_high_ahead'):
            locs = self.monitor.find_all(arrow,threshold = 0.4,img_func=arrow_img_func)
            
            if arrow == 'arrow_ahead':
                loc_expect = loc_now + Loc(160,10)
            elif arrow == 'arrow_low_ahead':
                loc_expect = loc_now + Loc(160,160)
            elif arrow == 'arrow_high_ahead':
                loc_expect = loc_now + Loc(160,-120)
            
            distince_list = []
            locs = [loc for loc in locs if ((loc[0]-loc_now.loc_x)>120 and (loc[0]-loc_now.loc_x)<200 and ((loc[1]-loc_now.loc_y)>-150 and (loc[1]-loc_now.loc_y)<180))]
            print(locs)
            if not locs:
                continue
            for loc in locs:
                loc0 = Loc(loc)
                diff_loc = loc0 - loc_expect
                distince_list.append(diff_loc.distance_s())
            if min(distince_list) < 3000:
                loc_arrow = distince_list.index(min(distince_list))
                loc0 = Loc(locs[loc_arrow]) * 2 - loc_now
                move_and_click(loc0.to_tuple())
                time.sleep(1)   
                return True
        return False
    def to_goto(self):
        found, loc_goto, _ = self.monitor.find('route_goto')
        loc_goto = Loc(loc_goto)
        if found:
            move_and_click(loc_goto.to_tuple())
            time.sleep(1)
            return True
        else:
            return False

    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'on_way':
                self.chose_route()
            elif status == 'goto':
                self.to_goto()
                super().move_free()
                if self.monitor.refresh() and not self.monitor.find('route_goto')[0]:
                    return True
            elif status == 'dead':
                return False

class SinnerChooseChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_already_chose(self):
        d = self.monitor.ocr(range=((300,180),(1280,650)))
        found = [x for x in d if 'SELECTED' in x.get('text')]
        if found:
            return True
        else:
            return False
    def is_in_choose(self):
        if self.monitor.find('sinner_choose_found2')[0] and self.monitor.find('sinner_choose_found1')[0]:
            return True
        else:
            return False
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_in_choose():
                    if self.is_already_chose():
                        return 'already_chose'
                    else:
                        return 'not_chose'
                    
                else:
                    return 'not_in_chose'
            else:
                return 'dead'

        
class SinnerChooseSolver(Solver):
    def __init__(self, monitor,rechoose=False):
        super().__init__(monitor)
        self.retry = 0
        self.checker = SinnerChooseChecker(self.monitor)
        self.sinner_list = self.get_sinner_list()
        self.already_choose = self.find_already_choose()
        time.sleep(0.1)
        if self.already_choose:
            self.not_need = True
        elif rechoose:
            self.not_need = self.rechoose_sinner()
        else:
            self.not_need = False
    def find_already_choose(self):
        return self.monitor.new_find('sinner_full',threshold=0.9)[0]
    
    def rechoose_sinner(self):
        status = self.checker.check_status()
        if status == 'not_chose':
            self.choose_sinner()
            return True
        else:
            _, loc0, _ = self.monitor.new_find('rechoose_sinner')
            move_and_click(loc0)
            time.sleep(1)
            _ , loc0, _ = self.monitor.new_find('rechoose_confirm')
            move_and_click(loc0)
            time.sleep(1)
            return False

    def get_sinner_list(self):
        return SINNERLIST
    def compute_loc(self):
        locs = []
        for x in self.sinner_list:
            loc = Loc(360,300) + self.monitor.window_loc
            if x > 6:
                x -= 6
                loc = loc + Loc(0,270)
            loc += Loc(164*(x-1),0)
            locs.append(loc)
        return locs

    def choose_sinner(self): 
        locs = self.compute_loc()
        for loc in locs:
            move_and_click(loc.to_tuple(),duration=0.2)
        
    def into_fight(self):
        found,start_fight_loc,_ = self.monitor.find('into_fight')
        if found:
            move_and_click(start_fight_loc)
            return True
        else:
            return False

    def run(self):
        
        if self.not_need:
            self.into_fight()
            return True
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'not_chose':
                self.choose_sinner()
            elif status == 'already_chose':
                r = self.into_fight()
                super().move_free()
                if r:
                    if self.monitor.refresh() and not self.monitor.find('already_chose')[0]:
                        return True
                else:
                    continue
            elif status == 'not_in_chose':
                return False
            elif status == 'dead':
                return False


class ShopBuyEgoChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def in_shop(self):
        found,_,_ = self.monitor.find('in_shop')
        return found
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.in_shop():
                    return 'in_shop'
                else:
                    time.sleep(2)
            else:
                return 'dead'

    

class ShopBuyEgoSolver(Solver):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.checker = ShopBuyEgoChecker(self.monitor)
        self.retry = 0
        self.ego_list = self.get_ego_list()
    def get_ego_list(self):
        return BUYEGOATTR
    def get_egos_locs(self):
        ego_list = []
        for x in self.ego_list:
            # 找到对应ego标识
            # TODO:这个还需要做一个ocr版本的，买固定饰品的。
            ego_list.extend(self.monitor.find_all('ego_' + x))
        return ego_list
    def buy_egos(self,loc):
        move_and_click(loc)
        time.sleep(0.5)
        found, loc0, _ = self.monitor.new_find('ego_buy')
        if not found:
            return False
        else:
            move_and_click(loc0)
            return True
    def check_bought(self,loc):
        # 获取的坐标为标志坐标。标志坐标-窗口左上角坐标
        loc0 = Loc(loc) - Loc(self.monitor.window_loc) - (0,self.monitor.title_height)
        data = self.monitor.ocr(range=((loc0-(50,50)).to_tuple(),(loc0+(50,50)).to_tuple()))
        for x in data:
            if '购买' in x.get('text'):
                return True
        return False
    def run(self):
        status = self.checker.check_status()
        ego_locs = self.get_egos_locs()
        print(ego_locs)
        for loc in ego_locs:
            status = self.checker.check_status()
            if status == 'dead':
                return False
            if self.check_bought(loc):
                continue
            r = self.buy_egos(loc)
            super().move_free()
            time.sleep(0.5)
            if r:
                
                found, loc0, _ = self.monitor.new_find('ego_get')
                if not found:
                    found, loc0, _ = self.monitor.find('buy_stop')
                    move_and_click(loc0)
                else:
                    move_and_click(loc0)
            else:
                found, loc0, _ = self.monitor.new_find('shop_not_buy_confirm')
                move_and_click(loc0)
                return False
        return True


class ShopSkillChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def in_shop(self):
        found,_,_ = self.monitor.find('in_shop')
        return found
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.in_shop():
                    return 'in_shop'
                else:
                    time.sleep(2)
            else:
                return 'dead'


class ShopSkillSolver(Solver):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.checker = ShopSkillChecker(self.monitor)
        self.retry = 0
        self.skill_list = self.get_skill_list()
    def get_skill_list(self):
        return SKILLCHANGE
    def exchange_skill(self,loc,x):
        move_and_click(loc)
        time.sleep(0.5)
        found,loc,_= self.monitor.new_find('skill_confirm')
        if found:
            loc0 = Loc(400,450) + Loc(400,0)*(x[1]-1) + Loc(self.monitor.window_loc)
            move_and_click(loc0.to_tuple())
            move_and_click(loc)
            super().move_free()
            found,loc,_= self.monitor.new_find('ego_buy')
            if found:
                move_and_click(loc)
                time.sleep(1)
                found,loc,_= self.monitor.new_find('ego_buy')
                if not found:
                    return True

        while True:
            self.monitor.refresh()
            found,loc,_= self.monitor.find('stop_buy')
            if not found:
                return True
            else:
                move_and_click(loc)
                super().move_free()


    def run(self):
        status = self.checker.check_status()
        if status == 'in_shop':
            top_left = (700,400)
            d = self.monitor.ocr(range=(top_left,(1450,640)))
            for x in self.skill_list:
                if x[0] in d[0].get('text'):
                    r = (Loc(d[0]['loc'][0])+Loc(d[0]['loc'][2]))*0.5 + Loc(top_left) + Loc(0,-90)
                    r += Loc(self.monitor.window_loc)
                    return self.exchange_skill(r.to_tuple(),x)
                else:
                    continue

        

class ShopChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def in_shop(self):
        found,_,_ = self.monitor.find('in_shop')
        return found
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.in_shop():
                    return 'in_shop'
                else:
                    return 'not_in_shop'
            else:
                return 'dead'


class ShopSolver(Solver):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.checker = ShopChecker(self.monitor)
        self.retry = 0
        self.shop_refresh_times = self.get_shop_refresh_times()
        self.shop_act_list = self.get_shop_acts()
    def get_shop_refresh_times(self):
        return SHOP_refresh
    def get_shop_acts(self):
        return SHOP_priority
    def shop_run(self):
        for act in self.shop_act_list:
            if act == 'skill':
                s = ShopSkillSolver(self.monitor)
                s.run()
            elif act == 'ego':
                s = ShopBuyEgoSolver(self.monitor)
                r = s.run()
                if not r:
                    return False
            elif act == 'firm':
                pass # 饰品强化还没做，暂时也不打算做。
        return True
    def out_shop(self):
        return 
    def refresh_shop(self):
        _, loc, _ = self.monitor.find('shop_refresh')
        move_and_click(loc)
        super().move_free()
        time.sleep(0.5)
    def quit_shop(self):
        _, loc, _ = self.monitor.find('out_shop')
        move_and_click(loc)
        time.sleep(0.7)
        _, loc, _ = self.monitor.new_find('out_shop_confirm')
        move_and_click(loc)
        time.sleep(1.5)
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            if status == 'dead':
                return False
            elif status == 'in_shop':
                self.retry += 1
                r = self.shop_run()
                if r:
                    for _ in range(self.shop_refresh_times):
                        self.refresh_shop()
                        self.monitor.refresh()
                        r = self.shop_run()
                        if not r:
                            break
                self.quit_shop()
            elif status == 'not_in_shop':
                return True


class ResultSolver(Solver):
    """
    确认ego的获得等结果
    """
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = ResultChecker(self.monitor)
        self.gift_priority = self.get_gift_priority()
    def get_gift_priority(self):
        return GIFT_priority
    def confirm_ego(self):
        _,loc,_ = self.monitor.find('get_ego')
        loc = Loc(loc) + Loc(-30,100)
        move_and_click(loc.to_tuple())
        time.sleep(0.5)
        _,loc,_ = self.monitor.new_find('ego_confirm')
        move_and_click(loc)
        super().move_free()
        time.sleep(1)
    def confirm_ego1(self):
        _,loc,_ = self.monitor.find('ego_confirm1')
        move_and_click(loc)
        super().move_free()
        time.sleep(2)
    def concat_ocr(self,datas):
        datas.sort(key=lambda x:x.get('loc')[0][0])
        datas_fixed = []
        data = []
        loc = None
        for x in datas:
            if loc is not None and abs(loc[0] - x.get('loc')[0][0]) > 100:
                data.sort(key=lambda x:x.get('loc')[0][1])
                text = ''.join([x.get('text') for x in data])
                datas_fixed.append({'text':text,'loc':loc})
                loc = x.get('loc')[0]
                data = []
            data.append(x)
            loc = x.get('loc')[0]
        data.sort(key=lambda x:x.get('loc')[0][1])
        text = ''.join([x.get('text') for x in data])
        datas_fixed.append({'text':text,'loc':loc})
        return datas_fixed
    def choose_gift(self):
        time.sleep(0.3)
        self.monitor.refresh()
        top_left = (200,440)
        datas = self.monitor.ocr(range=(top_left,(1500,540)))
        datas = self.concat_ocr(datas)
        for x in datas:
            text = x.get('text')
            if '经费' in text and '概率' in text:
                x['info'] = '经费ego'
            elif '随机' in text and '饰品' in text:
                x['info'] = 'ego'
            elif '经费' in text:
                x['info'] = '经费'
            elif '碎片' in text:
                x['info'] = '罪孽碎片'

        for info in self.gift_priority:
            for x in datas:
                if x['info'] == info:
                    r_loc = x['loc']
                    print(info)
                    break
            else:
                continue
            break
    
        loc = Loc(r_loc) + Loc(self.monitor.window_loc) + Loc(top_left) + Loc(0,self.monitor.title_height)
        move_and_click(loc.to_tuple())
        _,loc,_ = self.monitor.find('gift_confirm')
        move_and_click(loc)
        time.sleep(3)
    def reconnect(self):
        _,loc,_ = self.monitor.find('net_error')
        move_and_click(loc)
        super().move_free()
        time.sleep(5)
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'ego':
                self.confirm_ego()
            elif status == 'ego1':
                self.confirm_ego1()
            elif status == 'gift':
                self.choose_gift()
            elif status == 'net_error':
                self.reconnect()
            elif status == 'not_result':
                return True
            elif status in('error_process','dead'):
                return False

class ResultChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_ego(self):
        return self.monitor.find('get_ego')[0]
    def is_ego1(self):
        return self.monitor.find('get_ego1')[0]
    def is_gift(self):
        return self.monitor.find('chose_gift')[0]
    def net_error(self):
        return self.monitor.find('net_error')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_ego1():
                    return 'ego1'
                elif self.is_gift():
                    return 'gift'
                elif self.is_ego():
                    return 'ego'
                elif self.net_error():
                    return 'net_error'
                else:
                    return 'not_result'
            else:
                return 'dead'
        return 'error_process'

class CardChooseSolver(Solver):
    """
    卡包选择
    """
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = CardChooseChecker(self.monitor)
        self.bad_cards = self.get_bad_cards()
    def get_bad_cards(self):
        return BADCARDS
    def choose_card(self):
        super().move_free()
        self.monitor.refresh()
        top_left = (240,550)
        datas = self.monitor.ocr(range=(top_left,(1540,670)))
        print([x.get('text') for x in datas])
        filtered = [x for x in datas if all(y not in x.get('text') for y in self.bad_cards)]
        print(filtered)
        if filtered:
            choice = random.choice(filtered)
        else:
            choice = random.choice(datas)
        loc = Loc(choice.get('loc')[0]) + Loc(self.monitor.window_loc) + Loc(60,self.monitor.title_height) + Loc(top_left)
        mouse_drag([loc.to_tuple(),(loc+Loc(0,300)).to_tuple()])
        time.sleep(4)
        found,_,_ = self.monitor.new_find('choosing_card')
        if found:
            return False
        else:
            return True
        
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'choosing_card':
                r = self.choose_card()
                if r:
                    return True
            elif status in('error_process','dead'):
                return False

class CardChooseChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_in(self):
        return self.monitor.find('choosing_card')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_in():
                    return 'choosing_card'
                else:
                    time.sleep(2)
            else:
                return 'dead'
        return 'error_process'


class IntoMirrorChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_in(self):
        return self.monitor.find('in_main')[0]
    def into_mirror(self):
        return self.monitor.find('into_mirror')[0]
    def is_enter(self):
        return self.monitor.find('enter_mirror')[0]
    def is_confirm(self):
        return self.monitor.find('into_mirror_confirm')[0]
    def is_sinner_select(self):
        return self.monitor.find('start_sinner_choose',threshold=0.9)[0] and self.monitor.find('sinner_choose_found2')[0]
    def is_select_star_buff(self):
        return self.monitor.find('star_buff_select')[0]
    def is_confirm_star_buff(self):
        return self.monitor.find('star_buff_confirm')[0]
    def is_choose_ego(self):
        return self.monitor.find('choose_start_ego')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.into_mirror():
                    return 'into_page'
                elif self.is_enter():
                    return 'enter_mirror'
                elif self.is_in():
                    return 'in_main'
                elif self.is_confirm():
                    return 'in_confirm'
                elif self.is_sinner_select():
                    return 'select_sinner'
                elif self.is_confirm_star_buff():
                    return 'star_buff_confirm'
                elif self.is_select_star_buff():
                    return 'select_star_buff'
                elif self.is_choose_ego():
                    return 'choose_ego'
                else:
                    time.sleep(2)
            else:
                return 'dead'
        return 'error_process'


class IntoMirrorSolver(Solver):
    """
    主界面进入镜牢，选取星之恩惠和初始ego
    """
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = IntoMirrorChecker(self.monitor)
        self.buff_selected = self.get_buff_list()
        self.start_ego = self.get_start_ego()
    def get_buff_list(self):
        return STAR_buff_list
    def get_start_ego(self):
        return START_ego
    def into_select(self):
        _,loc,_ = self.monitor.find('in_main')
        move_and_click(loc)
        time.sleep(2)
    def into_mirror(self):
        _,loc,_ = self.monitor.find('into_mirror')
        move_and_click(loc)
    def enter_mirror(self):
        _,loc,_ = self.monitor.find('enter_mirror')
        move_and_click(loc)
        time.sleep(0.5)
    def confirm_into(self):
        _,loc,_ = self.monitor.find('into_mirror_confirm')
        move_and_click(loc)
        time.sleep(1.5)
    def sinner_selected(self):
        _,loc,_ = self.monitor.find('selected_confirm')
        move_and_click(loc)
        time.sleep(1.5)
    def select_star_buff(self):
        locs = []
        for x in self.buff_selected:
            loc = Loc(350,400) + self.monitor.window_loc
            if x > 5:
                x -= 5
                loc = loc + Loc(0,250)
            loc += Loc(233*(x-1),0)
            locs.append(loc)
        for loc in locs:
            move_and_click(loc.to_tuple())
        _,loc,_ = self.monitor.find('star_buff_selected')
        move_and_click(loc)
        time.sleep(1)
    def confirm_star_buff(self):
        _,loc,_ = self.monitor.find('start_buff_confirm')
        move_and_click(loc)
        time.sleep(1)
    def choose_ego(self):
        top_left = (180,180)
        datas = self.monitor.ocr(range=(top_left,(900,700)))
        key_word = self.start_ego[0]
        r = [x for x in datas if key_word in x.get('text')]
        if r:
            loc = Loc(r[0].get('loc')[0]) + Loc(top_left) + Loc(self.monitor.window_loc) + Loc(0,self.monitor.title_height)
            move_and_click(loc.to_tuple())
            for x in self.start_ego[1]:
                loc = Loc(1040,360) + Loc(0,135)*(x-1) + Loc(self.monitor.window_loc)
                move_and_click(loc.to_tuple())
                
            _,loc,_ = self.monitor.find('start_ego_selected')
            move_and_click(loc)
            return True
        else:
            return False
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'in_main':
                self.into_select()
            elif status == 'into_page':
                self.into_mirror()
            elif status == 'enter_mirror':
                self.enter_mirror()
            elif status == 'in_confirm':
                self.confirm_into()
            elif status == 'select_sinner':
                self.sinner_selected()
            elif status == 'select_star_buff':
                self.select_star_buff()
            elif status == 'star_buff_confirm':
                self.confirm_star_buff()
            elif status == 'choose_ego':
                self.choose_ego()
                return True
            elif status in('error_process','dead'):
                return False

class MainChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def in_main(self):
        return self.monitor.find('main_screen')[0]
    def in_route(self):
        return self.monitor.find('out_fight')[0] and self.monitor.find('on_way')[0]
    def in_card_choose(self):
        return self.monitor.find('choosing_card')[0]
    def in_shop(self):
        return self.monitor.find('in_shop')[0]
    def in_event(self):
        return self.monitor.find('in_event')[0]
    def in_fight(self):
        return self.monitor.find('start_fight')[0]
    def in_sinner_choose(self):
        return self.monitor.find('sinner_choose_found2')[0]
    def in_end(self):
        return self.monitor.find('mirror_win')[0] or self.monitor.find('fight_lose')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.in_main():
                    return 'in_main'
                elif self.in_route():
                    return 'in_route'
                elif self.in_card_choose():
                    return 'in_card_choose'
                elif self.in_shop():
                    return 'in_shop'
                elif self.in_event():
                    return 'in_event'
                elif self.in_fight():
                    return 'in_fight'
                elif self.in_sinner_choose():
                    return 'in_sinner_choose'
                elif self.in_end():
                    return 'in_end'
                else:
                    return 'wait'
            else:
                time.sleep(2)
        return 'dead'
class MainSolver(Solver):
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = MainChecker(self.monitor)
        self.need_rechoose = True
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'in_main':
                s = IntoMirrorSolver(self.monitor)
            elif status == 'in_route':
                s = RouteSolver(self.monitor)
            elif status == 'in_card_choose':
                s = CardChooseSolver(self.monitor)
                self.need_rechoose = True
            elif status == 'in_shop':
                s = ShopSolver(self.monitor)
            elif status == 'in_event':
                s = EventSolver(self.monitor)
            elif status == 'in_fight':
                s = FreeFightSolver(self.monitor)
            elif status == 'in_sinner_choose':
                s = SinnerChooseSolver(self.monitor,self.need_rechoose)
                self.need_rechoose = False
            elif status == 'in_end':
                s = EndSolver(self.monitor)
            elif status == 'wait':
                time.sleep(2)
                continue
            else:
                return False
            s.run()
            time.sleep(1)
            ResultSolver(self.monitor).run()



class EndSolver(Solver):
    """
    确认战斗结果
    """
    def __init__(self,monitor):
        super().__init__(monitor)
        self.retry = 0
        self.checker = EndChecker(self.monitor)
        self.lowest_layers = self.get_lowest_layers()
    def get_lowest_layers(self):
        return 6
    def check_layers(self):
        data = self.monitor.ocr(range=((425,515),(500,550)))
        for x in data:
            if (found := re.search(r'(\d)层',x.get('text')).group(1)):
                return int(found)
        return 0
    def win_confirm(self):
        _,loc,_ = self.monitor.find('mirror_win_confirm')
        move_and_click(loc)
        super().move_free()
        time.sleep(0.5)
        _,loc,_ = self.monitor.new_find('end_mirror')
        move_and_click(loc)
        super().move_free()
        _,loc,_ = self.monitor.new_find('end_mirror2')
        move_and_click(loc)
        super().move_free()
        _,loc,_ = self.monitor.new_find('end_mirror3')
        move_and_click(loc)
        super().move_free()
        time.sleep(2)
        _,loc,_ = self.monitor.new_find('end_mirror4')
        move_and_click(loc)
        super().move_free()
        time.sleep(4)
        return True
    def run(self):
        while True:
            if self.retry > MAX_RETRY:
                return False
            status = self.checker.check_status()
            print(status)
            if status == 'win':
                self.win_confirm()
                return True
            elif status == 'lose':
                pass
            elif status in('error_process','dead'):
                return False

class EndChecker(Checker):
    def __init__(self, monitor):
        super().__init__(monitor)
        self.status = 'start'
    def is_win(self):
        return self.monitor.find('mirror_win')[0]
    def is_lose(self):
        return self.monitor.find('fight_lose')[0]
    def is_gift(self):
        return self.monitor.find('chose_gift')[0]
    def check_status(self):
        for _ in range(8):
            super().check_screen()
            if self.window_status != 'dead':
                if self.is_win():
                    return 'win'
                elif self.is_lose():
                    return 'lose'
                else:
                    return 'end'
            else:
                return 'dead'
        return 'error_process'
    
    
if __name__ == '__main__':
    m = WindowMonitor()
    s = MainSolver(m)
    s.run()
    # m = WindowMonitor()
    # s = ShopSolver(m)
    # s.run()
    