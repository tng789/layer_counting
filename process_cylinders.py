
def has_duplicates(lst):
    '''检查列表中是否有重复元素, 返回True或False，和重复元素的个数'''
    len_list = len(lst)
    len_set  = len(set(lst))
    return len_list != len_set 


def process_cylinders(lst):
    """
    处理列表，按照指定规则合并元素：
    1. 如果列表长度为2或者以下，则不处理，返回该列表和长度，退出
    2. 判断第0个元素与第1个元素的大小
    3. 如果第0个元素小于第1个元素，则判断第1个元素与第2个元素之间的大小，以此类推。
    4. 如果第0个元素大于或者等于第1个元素，则第1个元素与后面的第2个元素、第3个元素甚至第4个元素相加，直到相加之和大于第0个元素，成为第1个元素，也就是这几个元素以相加方式合并，列表长度相应缩减
    5. 重复以上步骤，从已经固定的数值开始计算，直至列表长度为2，或者最后一个元素小于倒数第二个元素，注意：最后一个元素小于倒数第二个元素这个条件必须是在程序走到列表末尾时才判断，而不是一开始就判断。
    6. 特殊情况：若是最后得到的列表形成一个公差为2的等差数列，则输出该列表，说明其是特殊情况，并输出长度为实际列表长度减一，即长度为2。
    """
    # 复制列表以避免修改原始列表
    result = lst[:]

    # 规则1：如果列表长度为2或者以下，则不处理，返回该列表和长度，退出
    if any([x >= 10 for x in result]):
        print("列表中有10根以上的管桩在同一层中，应是误判")
        layers = len(result) + max(result)//7                     # 不做详细拆分，毛估估加点儿
        return result, layers
    
    if len(lst) <= 2:
        return lst, len(lst)
    
    fixed_index = 0  # 表示已固定的索引位置
    
    while len(result) > 2:
        # 检查是否达到终止条件：最后一个元素小于倒数第二个元素
        # if result[-1] < result[-2]:
            # break
            
        # 检查当前固定索引及其下一个元素
        if fixed_index + 1 >= len(result):
            break
            
        # 如果第fixed_index个元素大于或等于第fixed_index+1个元素
        if result[fixed_index] >= result[fixed_index + 1]:
            # 将第fixed_index+1个元素与后续元素相加，直到总和大于第fixed_index个元素
            if fixed_index + 2 < len(result):
                # 从第fixed_index+1个元素开始累加后续元素
                current_sum = result[fixed_index + 1]
                elements_to_merge = 1  # 至少包含第fixed_index+1个元素
                
                # 累加后续元素，直到和大于第fixed_index个元素
                idx = fixed_index + 2
                while idx < len(result) and current_sum <= result[fixed_index]:
                    current_sum += result[idx]
                    elements_to_merge += 1
                    idx += 1
                
                # 将累加和赋值给第fixed_index+1个位置
                result[fixed_index + 1] = current_sum
                
                # 删除被合并的元素
                for _ in range(elements_to_merge - 1):
                    if fixed_index + 2 < len(result):
                        del result[fixed_index + 2]
                
                # 固定索引前进一位
                fixed_index += 1
            else:
                # 如果没有更多元素可以合并，则结束
                break
                
            # 如果新列表长度不大于2，则输出新列表和长度，退出
            if len(result) <= 2:
                return result, len(result)
                
            # 如果新列表长度为3且最后一个元素小于倒数第二个，则不再继续
            if len(result) == 3 and result[-1] < result[-2]:
                break
        else:
            # 如果第fixed_index个元素小于第fixed_index+1个元素，固定索引前进一位
            fixed_index += 1
            
            # 如果固定索引超出了可能的范围，则退出
            if fixed_index >= len(result) - 1:
                break
    
    # 检查特殊情况：公差为2的等差数列
    if len(result) >= 3:
        is_arithmetic = True
        for i in range(1, len(result)):
            if result[i] - result[i-1] != 2:
                is_arithmetic = False
                break
        
        if is_arithmetic:
            print("这是一个公差为2的等差数列的特殊情况")
            return result, len(result)-1  # 长度为实际列表长度减一
    
    layers = len(result)
    # if has_duplicates(result):
        # print("列表中有重复元素")
        # layers = layers - 1
    if layers >=3 and result[-1] < result[-2]: # elif result[-1] == 1:
        print("最底层管桩数量小于倒数第二层，应是误判")
        layers = layers - 1
    elif layers >= 3 and result[-1] >= sum(result[:-1]) + 1:
        print("最底层管桩数量过多，而上层管桩数量过少，不合常理，应是误判")
        layers = layers - 1
    else:
        pass

    return result, layers