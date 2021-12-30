import os
import pickle

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms

from metrics import *
from utils_torch import *
from utils_plot import visualize_att

from PIL import ImageFont, ImageDraw, Image

import numpy as np
import argparse, cv2

from config.test_config import *

def test(img_path, save_path=None, save=True, model='lstm',name=None):
    print(name, "in test.py")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    #임베딩 불러오기
    embedder = CaptionEmbedder.load(EMBED_PATH)
    VOCAB_SIZE = len(embedder.w2i)
    
    #모델 불러오기
    model = EncodertoDecoder(VECTOR_DIM, VECTOR_DIM, VOCAB_SIZE, num_layers=2, model=model, embedder=embedder)
    model_data = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(model_data['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    if os.path.isdir(img_path):
        
        folder_img_path_list = []
        possible_img_extension = ['.jpg', '.jpeg', '.JPG', '.bmp', '.png']
        
        for (root, dirs, files) in os.walk(img_path):
            if files:
                for file_name in files:
                    if os.path.splitext(file_name)[1] in possible_img_extension:
                        img_path = root + '/' + file_name
                        
                        # 경로에서 \를 모두 /로 바꿔줘야함
                        img_path = img_path.replace('\\', '/') # \는 \\로 나타내야함         
                        folder_img_path_list.append(img_path)
                        
        for f_img_path in folder_img_path_list:
                #하나씩 이미지를 불러와서 캡션 달아주기
            image = read_image(f_img_path)
            
            _image = image.clone()
            _image = image.type(torch.FloatTensor)
            _image = _image.to(device)
            transform = transforms.Compose(
                [
                transforms.Resize((299,299)),
                # transforms.ToTensor(),
                transforms.Normalize((127.5, 127.5, 127.5), (255., 255., 255.))
                ]
            )

            _image = transform(_image)
          
            #모델에 사진 넣기
            caption = ''.join(model.caption_image(_image, embedder, max_length=FIXED_LENGTH))
            caption = name+','+caption
            print(caption)    

    else:
        image = read_image(img_path)
        
        _image = image.clone().to(device)
        _image = image.type(torch.FloatTensor)
        _image = _image.to(device)
        
        transform = transforms.Compose(
            [
            transforms.Resize((299,299)),
            # transforms.ToTensor(),
            transforms.Normalize((127.5, 127.5, 127.5), (255., 255., 255.))
            ]
        )

        _image = transform(_image)
        
        #모델에 사진 넣기
        caption = ''.join(model.caption_image(_image, embedder, max_length=FIXED_LENGTH))
        caption = name+','+caption
        print(caption)
    
        # 사진에 캡션 추가
        img = torch.permute(image, (1,2,0))
        img = img.numpy()

        # 캡션 글자 크기 계산
        size_img = min(img.shape[0],img.shape[1])
        ft_size = int(size_img / 14)


        img = Image.fromarray(img)
        
        draw = ImageDraw.Draw(img) 

        ### 캡션 폰트 사이즈 수정
        font=ImageFont.truetype('font/RixYeoljeongdo Regular.ttf',ft_size)
        
        w, h = draw.textsize(caption, font=font, spacing=5)
        img_W = img.size[0]
        img_H = img.size[1]
        
        org=((img_W-w)/2, img_H-(img_H*0.1)) 
        draw.text(org,caption,font=font,fill=(225,225,225))

        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        if save:
            cv2.imwrite(save_path, img)
        else:
            cv2.imshow('imgwithcaption', img)
            cv2.waitKey(0) 

def add_caption(img, caption):
    from PIL import ImageFont, ImageDraw
    
    # 캡션 글자 크기 계산
    size_img = min(img.shape[0],img.shape[1])
    ft_size = int(size_img / 14)
    
    ### 캡션 폰트 사이즈 수정
    font=ImageFont.truetype('font/RixYeoljeongdo Regular.ttf',ft_size)
    
    draw = ImageDraw.Draw(img) 
    w, h = draw.textsize(caption, font=font, spacing=5)
    img_W = img.size[0]
    img_H = img.size[1]
    
    org=((img_W-w)/2, img_H-(img_H*0.1)) 
    draw.text(org,caption,font=font,fill=(225,225,225))
    
    return np.array(img)

def get_args():
    parser = argparse.ArgumentParser(description = '각종 옵션')
    parser.add_argument('-p', '--image_path', default=r"data\debug\img\bluedragon\bluedragon1.jpg",
                        type=str, help='입력 이미지 경로')
    parser.add_argument('-m', '--model', default='lstm',
                        type=str, help='모델명')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    
    test(args.image_path, save=False, model=args.model)

