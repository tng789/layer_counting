import base64
import io
from typing import List, Dict
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import numpy as np
from ultralytics import YOLO

from val6 import manipulate

# 初始化 FastAPI 应用
app = FastAPI(title="Image Prediction API")

# 预先加载模型，避免每次预测时都加载
print("正在加载自定义YOLOv8 nano模型...")
model = YOLO('layer_counting.pt')  # 加载自定义训练的模型
model.conf = 0.5  # 设置置信度阈值
model.iou = 0.45  # 设置IOU阈值
print("自定义YOLO模型加载完成!")

# --- 数据模型定义 ---

class ImageRequest(BaseModel):
    """
    接收客户端请求的模型
    假设客户端发送的 JSON 格式为: {"image_base64": "...."}
    """
    image_base64: str

# --- 模拟耗时预测函数 ---

async def predict(image: Image.Image) -> List[Dict[str, any]]:
    """
    使用预加载的YOLO模型进行预测
    """
    try:
        # 使用预加载的YOLOv8模型进行预测
        # YOLOv8 可以直接接受 PIL Image 对象
        results = model(image)
        
        # 获取第一个结果的检测框
        # results[0] 对应输入的一张图片
        boxes = results[0].boxes
        
        # 转换为所需的输出格式 [[class, x, y, w, h], ...]
        detection_list = []
        if boxes is not None:
            # xywhn 返回归一化的 x, y, w, h
            # boxes.xywhn 形状为 (N, 4)
            # boxes.cls 形状为 (N, 1)
            
            # 确保有检测结果
            if boxes.shape[0] > 0:
                # 获取归一化的 xywh
                xywhn = boxes.xywhn.cpu().numpy()
                # 获取类别
                cls = boxes.cls.cpu().numpy()
                
                for i in range(len(boxes)):
                    class_idx = int(cls[i])
                    x_norm, y_norm, w_norm, h_norm = xywhn[i]
                    detection_list.append([class_idx, float(x_norm), float(y_norm), float(w_norm), float(h_norm)])
         
        result = manipulate(detection_list, image.height, image.width) 
        # 构建返回结果
#        result = [
#            {
#                "cross_section": "A1",
#                "profile": "Type_X",
#                "layers": [1, 2, 3],
#                "detections": detection_list
#            }
#        ]
        
#        print(f"检测到 {len(detection_list)} 个物体")
        print(f"检测结果：{result}")
        return result
    except Exception as e:
        print(f"预测过程中发生错误: {str(e)}")
        raise e

# --- API 接口 ---

@app.post("/predict")
async def predict_endpoint(request: ImageRequest):
    """
    接收 base64 图片，转换格式，调用 predict，返回结果
    """
    try:
        # 1. 解码 Base64
        # 处理可能存在的 data:image/png;base64, 前缀
        image_data = request.image_base64
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        image_bytes = base64.b64decode(image_data)
        
        # 2. 使用 Pillow 打开图片并转换格式
        # 这一步会自动识别原图格式，并加载到内存中
        img = Image.open(io.BytesIO(image_bytes))
        
        # 如果需要强制转换为 RGB (去除透明通道等)，可以取消下面这行的注释
        # img = img.convert('RGB')
        
        # 此时 img 对象已经是 JPG/PNG 等标准格式的对象，可以直接传给 predict
        # 无论原图是什么，Pillow 都能处理，除非文件损坏
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片解码或转换失败: {str(e)}")

    # 3. 调用预测函数
    try:
        results = await predict(img)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测过程出错: {str(e)}")

# --- 启动服务 ---

if __name__ == "__main__":
    # 使用 uvicorn 启动服务
    # host="0.0.0.0" 允许外部访问
    uvicorn.run(app, host="0.0.0.0", port=8000)