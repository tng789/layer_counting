import numpy as np
from sklearn.cluster import DBSCAN
import cv2

def robust_layer_counting(detections, img_height, min_samples=2, eps_ratio=0.03):
    """
    鲁棒的分层计数算法
    :param detections: YOLO 检测结果 (results[0].boxes)
    :param img_height: 图片高度 (用于将 eps 从像素比例转为绝对像素)
    :param min_samples: DBSCAN 最小样本数 (防止孤立噪点形成一层)
    :param eps_ratio: 邻域半径比例 (相对于图片高度的比例，适应不同分辨率)
    :return: layer_count, layer_details (每层的中心Y坐标和包含的检测框)
    """
    
    if len(detections) == 0:
        return 0, []

    # 1. 提取数据：只取中心点 Y 坐标，同时保留原始 box 以便后续分析
    # 格式: [y_center, box_index]
    data_points = []
    for i, box in enumerate(detections):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cy = (y1 + y2) / 2
        # 过滤掉置信度极低的框 (可选，YOLO推理时通常已过滤)
        if box.conf[0] > 0.4: 
            data_points.append([cy, i])
    
    if len(data_points) < min_samples:
        return 0, [] # 点数太少，无法判断

    data_points = np.array(data_points)
    y_coords = data_points[:, 0].reshape(-1, 1)
    
    # 2. 动态计算 DBSCAN 的 eps (邻域半径)
    # 逻辑：柱子直径通常在图片高度的 3%~8% 之间。
    # 层内间距应该小于柱子直径，层间间距应该大于柱子直径。
    # 我们设定 eps 为图片高度的 eps_ratio (默认3%)，这通常能覆盖同一层的波动
    eps_pixels = img_height * eps_ratio
    
    # 使用 DBSCAN 进行一维聚类
    # DBSCAN 优势：不需要预设层数(K)，能自动识别噪点(离群点)
    db = DBSCAN(eps=eps_pixels, min_samples=min_samples).fit(y_coords)
    
    labels = db.labels_
    unique_labels = set(labels)
    
    # -1 代表噪点 (Outliers)，不计入层数
    real_layers = [l for l in unique_labels if l != -1]
    layer_count = len(real_layers)
    
    if layer_count == 0:
        # 如果没有形成任何簇，但有检测框，可能所有点都很散
        # 降级策略：如果点数>2，强制按最大间隙切分一次
        if len(data_points) >= 2:
             sorted_y = sorted(y_coords.flatten())
             gaps = [sorted_y[i+1] - sorted_y[i] for i in range(len(sorted_y)-1)]
             max_gap_idx = np.argmax(gaps)
             # 如果最大间隙显著大于其他间隙，算2层，否则算1层
             if gaps[max_gap_idx] > np.mean(gaps) * 2.5:
                 return 2, []
             else:
                 return 1, []
        return 0, []

    # 3. (可选) 后处理验证：检查每层的“合理性”
    # 如果某一层只有1个点，而其他层有5个点，这一层可能是误检或极端遮挡
    # 这里我们选择信任 DBSCAN 的结果，但可以输出警告
    layer_details = []
    for label in real_layers:
        class_member_mask = (labels == label)
        layer_points = data_points[class_member_mask]
        layer_y_mean = np.mean(layer_points[:, 0])
        layer_count_in_group = len(layer_points)
        
        layer_details.append({
            "layer_id": label,
            "center_y": layer_y_mean,
            "count": layer_count_in_group,
            "box_indices": layer_points[:, 1].astype(int)
        })
    
    # 按 Y 坐标从上到下排序 (Y越小越靠上)
    layer_details.sort(key=lambda x: x['center_y'])
    
    return layer_count, layer_details
def main():
    path = "/mnt/d/workspace/pillar_yolo/P00000.txt"
    detections = []
    with open(path, 'rt') as f:
        detection = [line.strip().split() for line in f]
        if detection[0][0] in ('0','2'):
            detections.append(detection[0])
    counts, details = robust_layer_counting(detections, img_height=2288)
    print(f"{counts=}, {details=}")

if __name__ == "__main__":
    main()

# ==========================================
# 集成到你的 YOLO 推理流程中
# ==========================================
def process_yolo_results(results, img_path):
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    boxes = results[0].boxes
    
    count, details = robust_layer_counting(boxes, h)
    
    print(f"📷 图片: {img_path}")
    print(f"   -> 检测到总端面数: {len(boxes)}")
    print(f"   -> 🎯 最终判定层数: {count}")
    
    if count > 0:
        for i, layer in enumerate(details):
            print(f"      [第{i+1}层] 中心Y: {layer['center_y']:.1f}, 该层可见柱子数: {layer['count']}")
            
            # 可视化：给不同层画不同颜色的框
            color = (0, 255, 0) if i % 2 == 0 else (0, 0, 255) # 绿红交替
            for idx in layer['box_indices']:
                x1, y1, x2, y2 = map(int, boxes[idx].xyxy[0])
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                # 标注层号
                cv2.putText(img, f"L{i+1}", (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # 画分层分割线
        for i in range(len(details)-1):
            y1 = details[i]['center_y']
            y2 = details[i+1]['center_y']
            line_y = int((y1 + y2) / 2)
            cv2.line(img, (0, line_y), (w, line_y), (0, 255, 255), 2) # 黄色分割线

    cv2.imwrite(f"result_processed_{img_path}", img)
    return count