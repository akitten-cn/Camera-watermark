import math
import os
from datetime import datetime

import yaml
from PIL import Image, ImageDraw
from PIL import ImageFont
from PIL.ExifTags import TAGS

import piexif

# 布局，全局配置
FONT_SIZE = 240
BORDER_PIXEL = 60
UP_DOWN_MARGIN = FONT_SIZE + BORDER_PIXEL
LEFT_RIGHT_MARGIN = FONT_SIZE + BORDER_PIXEL
GAP_PIXEL = 100

# 读取配置
with open('config.yaml', 'r',encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 读取输入、输出配置
input_dir = config['base']['input_dir']
output_dir = config['base']['output_dir']
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
quality = config['base']['quality']

# 读取字体配置
font = ImageFont.truetype(config['base']['font'], FONT_SIZE)
bold_font = ImageFont.truetype(config['base']['bold_font'], FONT_SIZE)

# 读取 logo 配置
logo_enable = config['logo']['enable']
makes = config['logo']['makes']

# 读取摄影者信息配置
user = config['user']

# 读取 exif 信息，包括相机机型、相机品牌、图片尺寸、镜头焦距、光圈大小、曝光时间、ISO 和拍摄时间
def get_exif(image):
    _exif_attrs = {'Model', 'Make', 'ExifImageWidth', 'ExifImageHeight', 'FocalLength', 'FNumber', 'ExposureTime',
                   'DateTimeOriginal', 'ISOSpeedRatings', 'Orientation','FocalLengthIn35mmFilm'}
    _exif = {}
    info = image._getexif()
    exif_dict = piexif.load(img.info['exif'])  # 用于写入exif信息

    if info:
        for attr, value in info.items():
            decoded_attr = TAGS.get(attr, attr)
            if decoded_attr in _exif_attrs:
                _exif[decoded_attr] = value

    return _exif,exif_dict


# 修改日期格式
def parse_datetime(datetime_string):
    return datetime.strptime(datetime_string, '%Y:%m:%d %H:%M:%S')


# 添加 logo
def append_logo(exif_img, exif):
    logo = None
    if 'Make' in exif:
        make = exif['Make']
        for m in makes.values():
            if m['id'] in make:
                logo = Image.open(m['path'])
                print('图片的高度：',logo.height,'图片的宽度：',logo.width)
    if logo is not None:
        logo_width=math.floor(logo.width*(exif_img.height*0.7/logo.height))
        logo_height = math.floor(exif_img.height*0.7)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        return logo



# 生成元信息图片
def make_exif_image(exif):
    try:
        font_ratio = .07
        all_ratio = .13
        original_width = exif['ExifImageWidth']
        original_height = exif['ExifImageHeight']
        original_ratio = original_width / original_height
        if original_ratio > 1:
            font_ratio = .07
            all_ratio = .1

        # 型号
        model = exif['Model']
        make = exif['Make']
        model_mask = bold_font.getmask(model)
        user_mask = font.getmask(user)
        brand_img = Image.new('RGB',
                            (max(model_mask.size[0], user_mask.size[0]),
                            model_mask.size[1] + user_mask.size[1] + GAP_PIXEL * 3),
                            color='white')
        brand_draw = ImageDraw.Draw(brand_img)
        brand_draw.text((0, 0), model, font=bold_font, fill='black')
        brand_draw.text((0, model_mask.size[1] + GAP_PIXEL), user, font=font, fill='gray')

        # 参数
        focal_length_in_35mm_film = exif.get('FocalLengthIn35mmFilm', exif['FocalLength'])
        focal_length = str(int(focal_length_in_35mm_film)) + 'mm'
        f_number = 'F' + str(exif['FNumber'])
        exposure_time = str(exif['ExposureTime'].real)
        iso = 'ISO' + str(exif['ISOSpeedRatings'])
        shot_param = '  '.join((focal_length, f_number, exposure_time, iso))

        original_date_time = datetime.strftime(parse_datetime(exif['DateTimeOriginal']), '%Y-%m-%d %H:%M')
        shot_param_mask = bold_font.getmask(shot_param)
        original_date_time_mask = font.getmask(original_date_time)

        shot_param_img = Image.new('RGB',
                                (max(shot_param_mask.size[0], original_date_time_mask.size[0])+GAP_PIXEL*2,
                                    shot_param_mask.size[1] + original_date_time_mask.size[1] + GAP_PIXEL * 3),
                                color='white')

        shot_param_draw = ImageDraw.Draw(shot_param_img)
        shot_param_draw.line((0,GAP_PIXEL, 0,shot_param_mask.size[1] + original_date_time_mask.size[1] + GAP_PIXEL*2), fill='gray', width=30)
        shot_param_draw.text((GAP_PIXEL, 0), shot_param, font=bold_font, fill='black')
        shot_param_draw.text((GAP_PIXEL, shot_param_mask.size[1] + GAP_PIXEL), original_date_time, font=font, fill='gray')

        exif_img = Image.new('RGB', (original_width, math.floor(all_ratio * original_width)), color='white')
        left_margin = BORDER_PIXEL
        right_margin = BORDER_PIXEL

        brand_img = brand_img.resize(
            (math.floor(brand_img.width / brand_img.height * math.floor(original_width * font_ratio)),
            math.floor(original_width * font_ratio)), Image.Resampling.LANCZOS)
        shot_param_img = shot_param_img.resize(
            (math.floor(shot_param_img.width / shot_param_img.height * math.floor(original_width * font_ratio)),
            math.floor(original_width * font_ratio)), Image.Resampling.LANCZOS)
        if logo_enable:
            logo = append_logo(exif_img, exif)
            exif_img.paste(logo, (exif_img.width - logo.width - GAP_PIXEL//4 - shot_param_img.width - right_margin, math.floor((all_ratio - font_ratio) / 2 * original_width)))

        exif_img.paste(brand_img, (left_margin*2, math.floor((all_ratio - font_ratio) / 2 * original_width)))
        exif_img.paste(shot_param_img, (exif_img.width - shot_param_img.width - right_margin,
                                        math.floor((all_ratio - font_ratio) / 2 * original_width)))

        return exif_img.resize((original_width, math.floor(all_ratio * original_width)), Image.Resampling.LANCZOS)
    except KeyError:
        # 如果缺少任何关键信息，返回一个空的Image对象
        return Image.new('RGB', (0, 0), color='white')


# 拼接原图片和 exif 图片
def concat_image(img_x, img_y):
    img = Image.new('RGB', (img_x.width, img_x.height + img_y.height), color='white')
    img.paste(img_x, (0, 0))
    img.paste(img_y, (0, img_x.height))
    return img


# 读取文件列表
def get_file_list():
    file_list = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if 'jpg' in file or 'jpeg' in file or 'JPG' in file or 'JPEG' in file:
                file_list.append(file)
    return file_list


if __name__ == '__main__':
    file_list = get_file_list()
    for file in file_list:
        # 打开图片
        img = Image.open(os.path.join(input_dir, file))
        # 生成 exif 图片
        exif, exif_dict = get_exif(img)
        print(exif)
        if 'Orientation' in exif:
            if exif['Orientation'] == 3:
                img = img.transpose(Image.ROTATE_180)
            elif exif['Orientation'] == 6:
                img = img.transpose(Image.ROTATE_270)
            elif exif['Orientation'] == 8:
                img = img.transpose(Image.ROTATE_90)
        exif['ExifImageWidth'], exif['ExifImageHeight'] = img.width, img.height
        exif_img = make_exif_image(exif)

        # 如果exif_img不为空，才进行拼接
        if exif_img.size != (0, 0):
            img.paste(exif_img, (0, img.height - exif_img.height))

        # 写入exif信息
        output_img_bytes = img.tobytes()
        output_img = Image.frombytes('RGB', img.size, output_img_bytes)
        exif_bytes = piexif.dump(exif_dict)
        output_img.save(os.path.join(output_dir, file), 'JPEG', quality=quality, exif=exif_bytes)

