import cv2
import time
from config import OCR_ENGINE
import numpy as np
import logging


print(f"{OCR_ENGINE=}")
if OCR_ENGINE == 'PaddleOCR':
    from paddleocr import PaddleOCR, draw_ocr
    logging.getLogger('ppocr').setLevel(logging.ERROR)
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    def img_ocr(img):
        t1 = time.time()
        result = ocr.ocr(img)
        data_list = []
        for data in result:
            if data:
                for line in data:
                    if line:
                        loc = [[int(y) for y in x] for x in line[0]]
                        text = line[1][0]
                        confidence = line[1][1]
                        data_list.append({'loc':loc,'text':text,'confidence':confidence})
        t2 = time.time()
        print('ocr耗时:{}s'.format(t2-t1))
        return data_list


if OCR_ENGINE == 'PP_OCR_V3':
    import paddlehub as hub
    ocr = hub.Module(name="ch_pp-ocrv3", enable_mkldnn=True)
    def img_ocr(img):
        img0 = np.stack((img, img, img), axis=-1)
        result = ocr.recognize_text(images=[img0])
        result = result[0].get('data')
        result = [{'loc' if k == 'text_box_position' else k:v for k,v in dict0.items()} for dict0 in result]
        return result


if OCR_ENGINE == 'EASYOCR':
    import easyocr
    reader = easyocr.Reader(['ch_sim', 'en'])
    def img_ocr(img):
        result = reader.readtext(img)
        data_list = []
        for line in result:
            loc = line[0]
            text = line[1]
            confidence = line[2]
            data_list.append({'loc':loc,'text':text,'confidence':confidence})
        return data_list



if __name__ == "__main__":
    for _ in range(10):
        s_time = time.time()
        img = cv2.imread('test0000.png',cv2.IMREAD_GRAYSCALE)
        print(img_ocr(img))
        print('耗时:{}'.format(time.time()-s_time))