主程序 main.py 启动一个http server, 端口在8000。它会接收base64的图片，返回一个列表，列表中的每个元素是一个字典（相当于json）。列表中有多少个元素就表示多少辆车。
当前只接收单张图片，不支持批量处理。

server段地址：http://ip:8000/predict

具体格式如下：

```json
[
  {
    "dominant_class_name": "圆形空心",
    "final_layers": 4
  },
  {
    "dominant_class_name": "方形空心",
    "final_layers": 4
  }
]
```

利用client_test.py可以进行测试。

模型是以yolov8s为基础训练的，数据集另存在阿里云盘。请向我索要。