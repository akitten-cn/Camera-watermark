# Camera-watermark

使用python实现当前流行的添加相机机型和拍摄参数的水印效果

可以在不改变原始照片的情况下，将照片的重要信息（如相机参数和拍摄信息）添加到照片上，以便于查看和分享。

需要用到的包：

- pillow==9.3.0
- pyyaml==6.0
- piexif

```bash
#!/bin/bash
pip install -r requirements.txt
```

文件夹说明：

- input:存放需要批量处理的照片
- output:处理完的图片输出位置
- logos:相机厂商logo存放位置
- fonts:需要使用的字体存放位置

功能：

- 显示厂商 logo
- 显示相机机型
- 根据设置显示摄影作者名
- 显示拍摄参数（等效焦距、光圈、快门速度）
- 支持复制 exif 信息到输出的文件中
- 如果EXIF信息中缺少关键数据，元信息图片将不会添加到原始图片中。

效果展示：

![输出图片](./output/P1040227.jpg)
![输出图片](./output/testimg_cat.jpg)