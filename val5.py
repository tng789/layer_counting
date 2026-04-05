import numpy as np
from sklearn.cluster import DBSCAN

from pathlib import Path

def count_layers_with_outlier_merge(yolo_coords, min_layer_size=2):
    """
    针对“柱子长短不一、端面突出/缩进”场景的鲁棒层数计算
    
    核心思想：
      1. 用底部坐标 (y + h/2) 聚类得到初始层
      2. 对小尺寸层（< min_layer_size），检查是否可合并到邻近主层
    """
    if not yolo_coords:
        return 0, []

    # Step 1: 计算每个框的底部坐标 (物理堆叠的基准)
    bottoms = np.array([y + h / 2 for _, x, y, w, h in yolo_coords])
    boxes = np.array(yolo_coords)

    # Step 2: 初始聚类（使用动态 eps）
    avg_h = np.mean(boxes[:, 4])  # 平均高度
    eps = avg_h * 0.5  # 容忍半个柱子高的偏差
    clustering = DBSCAN(eps=eps, min_samples=1).fit(bottoms.reshape(-1, 1))
    labels = clustering.labels_

    # Step 3: 按层分组，并计算统计量
    layers = {}
    for i, label in enumerate(labels):
        if label not in layers:
            layers[label] = {'bottoms': [], 'indices': []}
        layers[label]['bottoms'].append(bottoms[i])
        layers[label]['indices'].append(i)

    # 转为列表并按平均底部排序（从上到下：Y 小 -> 大）
    layer_list = []
    for label, data in layers.items():
        mean_bottom = np.mean(data['bottoms'])
        std_bottom = np.std(data['bottoms']) if len(data['bottoms']) > 1 else 0.0
        layer_list.append({
            'label': label,
            'mean': mean_bottom,
            'std': std_bottom,
            'size': len(data['bottoms']),
            'indices': data['indices']
        })
    
    # 从上到下排序（Y 值小的在前）
    layer_list.sort(key=lambda x: x['mean'])

    # Step 4: 合并小层（核心逻辑！）
    final_layers = []
    to_merge = {}  # 记录哪些小层要合并到哪个主层

    for i, layer in enumerate(layer_list):
        if layer['size'] >= min_layer_size:
            # 主层，保留
            final_layers.append(layer)
        else:
            # 小层（可能是突出/缩进的孤立柱子）
            current_mean = layer['mean']
            best_target = None
            min_dist = float('inf')

            # 寻找上下最近的主层
            for j, target in enumerate(final_layers):
                dist = abs(current_mean - target['mean'])
                if dist < min_dist:
                    min_dist = dist
                    best_target = j

            # 判断是否“合理接近”：距离 < 目标层的标准差 * 2（或一个绝对阈值）
            if best_target is not None:
                target_layer = final_layers[best_target]
                merge_threshold = max(target_layer['std'] * 2.0, avg_h * 0.6)
                if min_dist < merge_threshold:
                    # 合并！
                    to_merge[layer['label']] = target_layer['label']
                    print(f"📌 合并层 {layer['label']} (size={layer['size']}) → 层 {target_layer['label']}")
                else:
                    # 距离太远，可能是真正的顶层/底层突出物，暂时保留
                    final_layers.append(layer)
            else:
                # 没有主层？说明全是小层，全部保留（极端情况）
                final_layers.append(layer)

    # Step 5: 重新分配标签
    new_labels = [-1] * len(yolo_coords)
    for layer in final_layers:
        label = layer['label']
        for idx in layer['indices']:
            # 如果这个原始 label 被合并了，就用新 label
            final_label = to_merge.get(label, label)
            new_labels[idx] = final_label

    # 去重并重新编号
    unique_final_labels = sorted(set(new_labels))
    label_map = {old: new for new, old in enumerate(unique_final_labels)}
    remapped_labels = [label_map[l] for l in new_labels]

    num_final_layers = len(unique_final_labels)
    print(f"✅ 最终层数: {num_final_layers} (初始聚类: {len(layer_list)})\n")
    return num_final_layers, remapped_labels

def main():
    yolo_dir = Path("d:\\workspace\\pillar_yolo")
    for yolo_file in yolo_dir.glob("*.txt"):
        if yolo_file.stem.startswith("class"): continue
        coords = []
        with open(yolo_file,"rt") as f:
            for line in f:
                yolo = [float(d) for d in line.split()]
                if yolo[0] == 1: continue
                coords.append(yolo)
        if len(coords):
            print(f"处理 {yolo_file}:")
            count_layers_with_outlier_merge(coords)
    

if __name__ == "__main__":
    main()
    