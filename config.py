# 配置文件
# 选择调用的ocr引擎，推荐PaddleOCR
OCR_ENGINE = 'PaddleOCR' # choose in "PaddleOCR","PP_OCR_V3","EASYOCR"

# 事件优先级，EVENT_priority0是第一顺序，EVENT_priority1是第二顺序
# 'judge' 是判定，'fight'是战斗，'normal'是其他类型
# 'level'是等级提升，'ego'是获取ego
EVENT_priority0 = ['judge','normal','fight']
EVENT_priority1 = ['level','ego']

# 罪人选择，按游戏里的顺序来填入对应序号，需要填满 
SINNERLIST = [1,11,3,9,6,12,10,2,4,5,7,8]

# 商店里需要购买的ego的属性（拼音）
BUYEGOATTR = ['liuxue']

# 店铺里需要更换技能的罪人和更换方式(1是1换2，2是2换3，3是3换1)
SKILLCHANGE = [('李箱',1),('堂吉诃德',3),('罗佳',1),('格里高尔',3),('奥提斯',1)]

# 店铺操作优先级:'skill'更换技能，'ego' 购买饰品，'firm' 强化饰品(难度过大，暂时不做支持)
SHOP_priority = ['skill','ego','firm']

# 店铺刷新次数
SHOP_refresh = 2

# 遭遇战奖励优先级，'经费ego'对应获取经费并概率获取ego，'ego'对应获取ego饰品，'经费'对应获取经费，'罪孽碎片'对应获取罪孽碎片
GIFT_priority = ['经费ego','ego','经费','罪孽碎片']

# 选择卡包时需要避开的卡包(避免翻车，目前脚本翻车会停掉),不一定是全名（因为ocr有时候会识别错误，遇到选错的情况用能够识别出来的部分就行）
BADCARDS = ['斩切者们','紫罗兰的正午','徒劳的怠','快车谋杀','肉斩骨断','压抑的暴怒','号线','空转的','于情感沉','落花']

# 选择的星之恩惠 
STAR_buff_list = [1,2,7]

# 选择的初始ego
START_ego = ('流血',[1])

# 屏幕检测的次数，如果没有检测到就会停下
MAX_RETRY = 3