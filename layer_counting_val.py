import numpy as np
from sklearn.cluster import DBSCAN

def count_layers_from_yolo(yolo_coords, y_threshold=0.02):
    """
    根据 YOLO 坐标计算层数
    
    参数:
    - yolo_coords: 列表，每一项是一个框 [class, x, y, w, h] (归一化坐标 0-1)
    - y_threshold: 垂直方向的聚类阈值。
                   如果是归一化坐标(0-1)，默认 0.02 代表高度差的 2%。
                   如果是像素坐标，请根据图片高度设置，例如 20 (像素)。
    """
    if not yolo_coords:
        return 0, []

    # 1. 提取中心点 Y 坐标
    # YOLO 的 y 是中心点，所以直接用 yolo_coords[i][2]
    # 如果不确定 y 是中心还是左上角，可以用 y + h/2 计算中心
    centers_y = np.array([box[2] for box in yolo_coords]).reshape(-1, 1)
    
    # 2. DBSCAN 聚类
    # eps=y_threshold: 垂直距离小于这个值的框会被归为一类
    # min_samples=1: 哪怕只有一个框也算一层
    clustering = DBSCAN(eps=y_threshold, min_samples=1).fit(centers_y)
    labels = clustering.labels_
    
    # 3. 整理每一层的信息
    layers = {}
    for i, label in enumerate(labels):
        if label not in layers:
            layers[label] = []
        layers[label].append(yolo_coords[i]) # 保存原始坐标以便核对
    
    # 4. 对层进行排序 (从上到下)
    # 计算每个聚类簇的平均 Y 坐标，然后排序
    sorted_layer_keys = sorted(layers.keys(), key=lambda k: np.mean([box[2] for box in layers[k]]))
    
    # 5. 打印结果
    print(f"🔍 检测到总层数: {len(sorted_layer_keys)} 层")
    print("-" * 30)
    
    for idx, layer_key in enumerate(sorted_layer_keys):
        layer_boxes = layers[layer_key]
        avg_y = np.mean([box[2] for box in layer_boxes])
        print(f"第 {idx+1} 层 (中心Y≈{avg_y:.4f}): 共 {len(layer_boxes)} 个目标")
        # 如果需要看具体坐标，可以取消下面这行的注释
        # print(f"   -> 坐标详情: {layer_boxes}")
        
    return len(sorted_layer_keys), layers

# ==============================================================================
# 🧪 测试数据 (模拟 YOLO 格式: class, x, y, w, h)
# 假设这是一张归一化坐标 (0-1) 的图片
# ==============================================================================

# 模拟数据：
# 第1层 (y≈0.1): 2个物体
# 第2层 (y≈0.3): 2个物体
# 第3层 (y≈0.5): 1个物体
# 第4层 (y≈0.9): 1个物体
my_yolo_data = [
    "0 0.497559 0.529502 0.024414 0.051136",
    "0 0.521851 0.536058 0.024658 0.053759",
    "0 0.451050 0.632212 0.026123 0.057255",
    "0 0.529785 0.656031 0.030273 0.062063",
    "0 0.503052 0.646416 0.028076 0.058566",
    "0 0.476440 0.639860 0.027588 0.057692",
    "0 0.623047 0.563811 0.028320 0.055944",
    "0 0.597656 0.555944 0.027344 0.059441",
    "0 0.572144 0.547421 0.026123 0.053759",
    "0 0.546265 0.542395 0.024170 0.055944",
    "0 0.623535 0.611451 0.027832 0.049825",
    "0 0.595947 0.605769 0.029297 0.056818"]
yolo_data = []
for line in my_yolo_data:
    coords = [float(x) for x in line.split()]
    yolo_data.append(coords)

# 运行计算
# 注意：如果是归一化坐标，y_threshold 设为 0.02 (即 2% 的高度) 通常比较合适
# 如果是像素坐标（比如图片高640），y_threshold 可以设为 20 左右
count_layers_from_yolo(yolo_data, y_threshold=0.02)