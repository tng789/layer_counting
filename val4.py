import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from collections import Counter

from pathlib import Path
from process_cylinders import process_cylinders
from process_rectangulars import process_rectangulars
def analyze_truck_layers(yolo_coords, img_width=1000, img_height=1000, 
                         x_threshold=80, y_threshold=20):
    """
    分析多辆卡车的堆叠层数
    1. 先按X坐标聚类，区分不同车辆
    2. 对每辆车单独计算层数
    3. 剔除非顶层的单点层, 这个不再有效
    
    参数:
    - yolo_coords: 列表，包含所有检测到的柱子 [class, x, y, w, h] (归一化坐标 0-1)
    - img_width/height: 图片尺寸，用于转换坐标
    - x_threshold: 区分不同车辆的X轴距离阈值 (像素)                 100->80
    - y_threshold: 同一层内Y轴距离阈值 (像素)                       20
    """
    
    if not yolo_coords:
        return
    
    # 转换为像素坐标并提取中心点
    centers = []
    for box in yolo_coords:
        class_id, x, y, w, h = box
        px = x * img_width
        py = y * img_height
        centers.append([px, py])
    
    centers = np.array(centers)
    
    # 1. 按X坐标聚类，区分不同车辆
    # eps=x_threshold: X轴距离小于这个值的视为同一辆车
    vehicle_clustering = DBSCAN(eps=x_threshold, min_samples=1).fit(centers[:, 0].reshape(-1, 1))
    vehicle_labels = vehicle_clustering.labels_
    unique_vehicles = np.unique(vehicle_labels)
    
    print(f"检测到 {len(unique_vehicles)} 辆车")
    
    # 2. 对每辆车单独处理
    for vehicle_id in unique_vehicles:
        vehicle_indices = np.where(vehicle_labels == vehicle_id)[0]
        vehicle_centers = centers[vehicle_indices]
        
        # 按Y坐标排序
        sorted_indices = np.argsort(vehicle_centers[:, 1])
        sorted_centers = vehicle_centers[sorted_indices]
        
        # 3. 按Y坐标聚类，计算层数
        y_coords = sorted_centers[:, 1].reshape(-1, 1)
        layer_clustering = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords)
        layer_labels = layer_clustering.labels_
        
        # 4. 剔除非顶层的单点层
        # 统计每层的物体数量
        layer_counts = {}
        for label in layer_labels:
            layer_counts[label] = layer_counts.get(label, 0) + 1
        
        # 找到顶层（Y坐标最小的层）
        top_layer_label = layer_labels[0]  # 排序后第一个是顶层
        
        # 检查每一层，剔除非顶层的单点层
        final_labels = layer_labels.copy()
#        for label, count in layer_counts.items():
#            if count == 1 and label != top_layer_label:
#                # 找到最近的层进行合并
#                current_y = y_coords[np.where(layer_labels == label)[0][0]]
#                other_layers = [l for l in layer_counts.keys() if l != label and layer_counts[l] > 1]
#                if other_layers:
#                    # 计算距离，合并到最近的层
#                    distances = [abs(current_y - y_coords[np.where(layer_labels == l)[0][0]]) for l in other_layers]
#                    closest_layer = other_layers[np.argmin(distances)]
#                    final_labels[final_labels == label] = closest_layer
        
        # 统计最终层数
        final_unique_layers = np.unique(final_labels)
        num_layers = len(final_unique_layers)
        
        print(f"车辆 {vehicle_id} 分析结果:")
        print(f"  - 初始检测层数: {len(np.unique(layer_labels))}")
        print(f"  - 最终有效层数: {num_layers}")
        print(f"  - 各层物体数量: {[layer_counts.get(l, 0) for l in final_unique_layers]}")

        pillars =  [layer_counts.get(l, 0) for l in final_unique_layers]
        result, length = process_rectangulars(pillars)
#        
        print(f"输出: {result}, 层数: {length}")
        # 可视化
#        plt.figure(figsize=(10, 6))
#        for label in final_unique_layers:
#            mask = final_labels == label
#            plt.scatter(sorted_centers[mask, 0], sorted_centers[mask, 1], label=f'层 {label}')
#        plt.title(f'车辆 {vehicle_id} 层级分布')
#        plt.xlabel('X 坐标 (像素)')
#        plt.ylabel('Y 坐标 (像素)')
#        plt.legend()
#        plt.grid(True)
#        plt.show()
def analyze_truck_layers_with_type(yolo_coords, img_width=1000, img_height=1000, 
                                   x_threshold=300, y_threshold=22,
                                   class_names={0: "方形", 2: "圆形"}):
    """
    分析多辆卡车的堆叠层数，并识别每辆车装载的柱子类型
    
    参数:
    - yolo_coords: 列表，包含所有检测到的柱子 [class, x, y, w, h] (归一化坐标 0-1)
    - class_names: 类别ID到名称的映射字典
    """
    
    anlyze_results =[]
    if not yolo_coords:
        return anlyze_results
    
    # 1. 数据预处理：转换为像素坐标，并保留类别信息
    data_points = [] # 每个元素是 [class_id, px, py]
    for box in yolo_coords:
        class_id, x, y, w, h = box
        px = x * img_width
        py = y * img_height
        data_points.append([class_id, px, py])
    
    data_points = np.array(data_points)
    centers = data_points[:, 1:]  # 只取坐标用于聚类
    class_ids = data_points[:, 0].astype(int) # 提取类别ID

    # 2. 按X坐标聚类，区分不同车辆
    vehicle_clustering = DBSCAN(eps=x_threshold, min_samples=1).fit(centers[:, 0].reshape(-1, 1))
    vehicle_labels = vehicle_clustering.labels_
    
    # 检查是否有需要合并的小簇
    unique_labels, label_counts = np.unique(vehicle_labels, return_counts=True)
    label_to_count = dict(zip(unique_labels, label_counts))
    
    # 查找小于等于3个点的簇
    small_clusters = [label for label, count in label_to_count.items() if count <= 3]
    
    if small_clusters and len(unique_labels) > 1:
        # 将小簇合并到最大的簇中
        max_cluster_label = unique_labels[np.argmax(label_counts)]
        
        # 创建新的标签数组
        new_vehicle_labels = vehicle_labels.copy()
        
        # 将小簇中的点重新分配到最大簇
        for small_cluster in small_clusters:
            new_vehicle_labels[vehicle_labels == small_cluster] = max_cluster_label
            
        # 更新标签
        vehicle_labels = new_vehicle_labels
        unique_vehicles = np.unique(vehicle_labels)
    else:
        unique_vehicles = unique_labels
    
    print(f"检测到 {len(unique_vehicles)} 辆车\n")
    
    
    # 3. 对每辆车单独处理
    for vehicle_id in unique_vehicles:
        # 找到属于当前车的所有索引
        vehicle_mask = (vehicle_labels == vehicle_id)
        vehicle_indices = np.where(vehicle_mask)[0]
        
        # 提取该车的坐标和类别
        vehicle_centers = centers[vehicle_mask]
        vehicle_class_ids = class_ids[vehicle_mask]
        
        # --- 新增：识别车辆装载类型 ---
        # 统计该车上所有柱子的类别
        class_counter = Counter(vehicle_class_ids)
        # 多数投票：选择出现次数最多的类别
        dominant_class_id = class_counter.most_common(1)[0][0]
        dominant_class_name = class_names.get(dominant_class_id, f"未知类型({dominant_class_id})")
        confidence = class_counter[dominant_class_id] / len(vehicle_class_ids)
        # -----------------------------
        
        # 4. 按Y坐标排序和聚类（计算层数）
        sorted_order = np.argsort(vehicle_centers[:, 1])
        sorted_centers = vehicle_centers[sorted_order]
        sorted_class_ids = vehicle_class_ids[sorted_order] # 也对类别排序，保持对应
        
        y_coords = sorted_centers[:, 1].reshape(-1, 1)
        layer_clustering = DBSCAN(eps=y_threshold, min_samples=1).fit(y_coords)
        layer_labels = layer_clustering.labels_
        
        # 5. 剔除非顶层的单点层  , 这项功能不用
        layer_counts = {}
        for label in layer_labels:
            layer_counts[label] = layer_counts.get(label, 0) + 1
        
        top_layer_label = layer_labels[0]
        final_labels = layer_labels.copy()
        
#        for label, count in layer_counts.items():
#            if count == 1 and label != top_layer_label:
#                current_y = y_coords[np.where(layer_labels == label)[0][0]]
#                other_layers = [l for l in layer_counts.keys() if l != label and layer_counts[l] > 1]
#                if other_layers:
#                    distances = [abs(current_y - y_coords[np.where(layer_labels == l)[0][0]]) for l in other_layers]
#                    closest_layer = other_layers[np.argmin(distances)]
#                    final_labels[final_labels == label] = closest_layer
#        
        final_unique_layers = np.unique(final_labels)
        num_layers = len(final_unique_layers)
        
        # 6. 输出结果
        print(f"--- 车辆 {vehicle_id+1} 分析结果 ---")
        print(f"  - 装载类型: {dominant_class_name} (置信度: {confidence:.2%})")
        # print(f"  - 初始检测层数: {len(np.unique(layer_labels))}")
        # print(f"  - 最终有效层数: {num_layers}")
        print(f"  - 各层物体数量: {[list(final_labels).count(l) for l in final_unique_layers]}")
        # print(f"  - 详细类别分布: {dict(class_counter)}\n")
        
        labels_per_layer = [list(final_labels).count(l) for l in final_unique_layers]
        if dominant_class_name == "圆形":
            results, final_layers = process_cylinders(labels_per_layer)
        elif dominant_class_name == "方形":
            results, final_layers = process_rectangulars(labels_per_layer)
        else:
            print("无法识别装载类型")
            results = []
            final_layers = 0
        
        print(f"*******\n调整后各层管桩数量{results}\n最终层数: {final_layers}\n*******")

        anlyze_results.append({"dominant_class_name": dominant_class_name, "final_layers": final_layers, "results": results})
    
    return anlyze_results 

        # 7. 可视化（用颜色区分层，用形状或大小暗示类别）
#        plt.figure(figsize=(10, 6))
#        for label in final_unique_layers:
#            mask = (final_labels == label)
#            # 为了可视化类别，我们可以用不同 marker，但这里简化用颜色
#            plt.scatter(sorted_centers[mask, 0], sorted_centers[mask, 1], label=f'层 {label}', s=80)
#        
        # 在图上标注车辆类型
#        plt.title(f'车辆 {vehicle_id} | 装载: {dominant_class_name}')
#        plt.xlabel('X 坐标 (像素)')
#        plt.ylabel('Y 坐标 (像素)')
#        plt.legend()
#        plt.grid(True)
#        plt.show()

def main():
    yolo_dir = Path("d:\\workspace\\tmp\\train8\\labels")
    for yolo_file in yolo_dir.glob("P0*.txt"):
        # if yolo_file.stem.startswith("class"): continue

        print(f"处理 {yolo_file}:")
        
        h = 2288                    #这些地方都要修改，每张图的分辨率需要从图片中获取
        # w = 4096
        hollow = False
        yolos = []
        with open(yolo_file,"rt") as f:
            for line in f:
                yolo = [float(d) for d in line.split()]
                if yolo[0] == 0 or yolo[0] == 2:
                    yolos.append(yolo) 
                    # rectangulars.append(yolo)
                # elif yolo[0] == 2: 
                    # cylinders.append(yolo)
                elif yolo[0] == 1:
                    hollow = True
                else:
                    continue
        if len(yolos):
            heights = sum([ coord[-1] for coord in yolos])/len(yolos)*h/2.75  
            results = analyze_truck_layers_with_type(yolos, img_width=4096, img_height=2288,
                                           x_threshold=280, y_threshold=heights)        
            print("空心管桩") if hollow else print("实心管桩")
        else:
            print("没有检测到管桩")
        # if len(rectangulars):
            # analyze_truck_layers(rectangulars)
        # if len(cylinders):
            # analyze_truck_layers(cylinders)    
        
            
        #最终要返回的是层数layers、装载类型class_name和是否空心hollow

if __name__ == "__main__":
    main()
    