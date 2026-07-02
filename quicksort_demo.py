"""
快速排序（Quick Sort）实现与基准测试
===================================
支持三种枢轴选择策略：
  - 'fixed'          : 固定选最后一个元素（简单但最坏情况 O(n²)）
  - 'random'         : 随机选一个元素与末尾交换（默认，实际中几乎避免最坏情况）
  - 'median_of_three': 三数取中，取左/中/右的中位数放到末尾（更均匀分割）
"""

import random
import time


def quicksort(arr, low=0, high=None, pivot_strategy='random'):
    """就地快速排序（递归版本）

    参数:
        arr: 待排序列表（原地修改）
        low: 当前子数组的左边界索引
        high: 当前子数组的右边界索引
        pivot_strategy: 枢轴选择策略
    """
    # --- 步骤 1：初始化右边界（首次调用时 high=None） ---
    if high is None:
        high = len(arr) - 1

    # --- 步骤 2：递归终止条件 ---
    # 当 low >= high 时，子数组长度为 0 或 1，天然有序，停止递归
    if low < high:
        # --- 步骤 3：分区操作，返回枢轴最终位置 ---
        pi = partition(arr, low, high, pivot_strategy)

        # --- 步骤 4：递归排序枢轴左侧子数组（所有元素 < 枢轴） ---
        quicksort(arr, low, pi - 1, pivot_strategy)

        # --- 步骤 5：递归排序枢轴右侧子数组（所有元素 > 枢轴） ---
        quicksort(arr, pi + 1, high, pivot_strategy)


def partition(arr, low, high, pivot_strategy):
    """
    分区函数（Lomuto 分区方案）

    核心思想：
      1. 选择一个元素作为枢轴（pivot）
      2. 将数组重新排列，使得：
         - 所有 <= pivot 的元素移到左侧
         - 所有 >  pivot 的元素留在右侧
      3. 返回 pivot 的最终下标

    参数:
        arr: 待分区的列表
        low: 左边界
        high: 右边界（枢轴最终放在此位置或与之交换）
        pivot_strategy: 枢轴选择策略

    返回:
        枢轴元素的最终索引
    """
    # =========================================================
    #  步骤 1：枢轴选择 —— 不同策略将选中的枢轴交换到 arr[high]
    # =========================================================
    if pivot_strategy == 'random':
        # 策略 A：随机选择
        # 从 [low, high] 中随机选一个索引，与 arr[high] 交换
        # 优点：任何输入都等概率，最坏情况概率极低（1/n!）
        rand_idx = random.randint(low, high)
        arr[rand_idx], arr[high] = arr[high], arr[rand_idx]

    elif pivot_strategy == 'median_of_three':
        # 策略 B：三数取中
        # 取左（low）、中（mid）、右（high）三个位置的元素
        # 将三者中的中位数交换到 arr[high] 作为枢轴
        # 优点：更接近均匀分割，避免已排序/逆序数据的退化
        mid = (low + high) // 2
        candidates = [(arr[low], low), (arr[mid], mid), (arr[high], high)]
        candidates.sort(key=lambda x: x[0])       # 按值排序，取中间值
        _, pivot_idx = candidates[1]               # 中位数所在索引
        arr[pivot_idx], arr[high] = arr[high], arr[pivot_idx]

    # 策略 C：固定选最后一个元素（pivot_strategy == 'fixed'）
    # 直接使用 arr[high] 作为枢轴，无需交换
    # 缺点：已排序数据下退化为 O(n²)

    # =========================================================
    #  步骤 2：设定枢轴值，开始分区
    # =========================================================
    pivot = arr[high]   # 枢轴值（此时已位于数组末尾）

    # i 指向"小于等于枢轴区域"的最后一个元素
    # 初始时该区域为空，i = low - 1
    i = low - 1

    # =========================================================
    #  步骤 3：遍历扫描，将元素分到枢轴两侧
    # =========================================================
    # j 从 low 遍历到 high-1（不包含枢轴本身）
    for j in range(low, high):
        # 如果当前元素 <= 枢轴，则将其交换到左侧区域
        if arr[j] <= pivot:
            i += 1                               # 扩大小于等于区域
            arr[i], arr[j] = arr[j], arr[i]       # 把 arr[j] 换到左侧

    # =========================================================
    #  步骤 4：将枢轴放到正确位置
    # =========================================================
    # 此时：
    #   arr[low..i]     全部 <= pivot
    #   arr[i+1..high-1] 全部 > pivot
    #   arr[high]        = pivot
    # 将枢轴与 arr[i+1] 交换，则枢轴落在正确位置
    arr[i + 1], arr[high] = arr[high], arr[i + 1]

    # =========================================================
    #  步骤 5：返回枢轴最终位置
    # =========================================================
    return i + 1


# ============================================================
#  测试入口 —— 直接运行即可验证
# ============================================================
if __name__ == '__main__':
    print("=" * 56)
    print("  快速排序 —— 基准测试示例")
    print("=" * 56)

    # ---- 1. 基础正确性验证 ----
    test_list = [3, 6, 8, 10, 1, 2, 1]
    print(f"\n原始列表 : {test_list}")
    expected = sorted(test_list)

    for strategy in ['random', 'median_of_three', 'fixed']:
        arr = test_list[:]
        quicksort(arr, pivot_strategy=strategy)
        ok = "✓" if arr == expected else "✗"
        print(f"  {strategy:<17} => {arr}  {ok}")

    # ---- 2. 随机数据性能对比 ----
    print("\n" + "-" * 56)
    print("性能对比（随机数据）")
    print("-" * 56)

    for size in [100, 1000, 5000, 10000]:
        data = [random.randint(0, size * 10) for _ in range(size)]

        for strategy in ['fixed', 'random', 'median_of_three']:
            arr = data[:]
            t0 = time.perf_counter()
            quicksort(arr, pivot_strategy=strategy)
            t = time.perf_counter() - t0
            correct = (arr == sorted(data))
            flag = "✓" if correct else "✗"
            print(f"  n={size:>6}  {strategy:<17}  {t:.6f}s  {flag}")

    # ---- 3. 最坏情况测试（已排序数据 + 固定枢轴） ----
    print("\n" + "-" * 56)
    print("最坏情况测试（已排序数据 n=2000）")
    print("-" * 56)

    sorted_data = list(range(2000))
    for strategy in ['fixed', 'random', 'median_of_three']:
        arr = sorted_data[:]
        t0 = time.perf_counter()
        quicksort(arr, pivot_strategy=strategy)
        t = time.perf_counter() - t0
        correct = (arr == sorted(sorted_data))
        flag = "✓" if correct else "✗"
        # fixed 策略在已排序数据上会退化为 O(n²)，耗时显著更长
        # random 和 median_of_three 则不受影响
        print(f"  {strategy:<17}  {t:.6f}s  {flag}")

    print("\n运行完毕！脚本可直接执行，无外部依赖。")
