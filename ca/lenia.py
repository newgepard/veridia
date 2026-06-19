"""Lenia 连续 CA —— 复杂科学基底(作战图 §搜索族:连续态非线性 CA)。

用已发表、已知会"滑行"的 **Orbium** 配方,把涌现去风险化:
环形高斯核(R≈13) + 高斯生长函数(mu≈0.15, sigma≈0.015) + dt≈0.1 +
环面(wrap)边界。单浮点场 ∈[0,1]。Bert Chan《Lenia》原始参数。

**无 LLM**:纯 numpy 卷积。这是复杂科学层,不是平均/扩散——核是环形的,
生长函数是双侧高斯钟形,故能长出持续移动的"生物"结构,而非抹平。
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np


@dataclass
class LeniaParams:
    """Orbium 已知良好参数(Bert Chan, Lenia)。"""
    R: int = 13            # 核半径
    mu: float = 0.15       # 生长函数中心
    sigma: float = 0.015   # 生长函数宽度
    dt: float = 0.1        # 时间步
    # 核内环的高斯壳参数(相对半径的中心与宽度)
    kernel_mu: float = 0.5
    kernel_sigma: float = 0.15


def _bell(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """高斯钟形 exp(-((x-mu)/sigma)^2 / 2)。"""
    return np.exp(-(((x - mu) / sigma) ** 2) / 2.0)


def make_kernel(params: LeniaParams) -> np.ndarray:
    """环形高斯核,已归一化(和为 1)。Orbium 经典单环核。"""
    R = params.R
    # 在 [-R, R] 网格上按到中心的归一化半径取壳值
    ax = np.arange(-R, R + 1)
    xx, yy = np.meshgrid(ax, ax)
    radius = np.sqrt(xx ** 2 + yy ** 2) / R  # 归一化半径 ∈[0, ~1.41]
    kernel = _bell(radius, params.kernel_mu, params.kernel_sigma)
    kernel[radius > 1.0] = 0.0  # 截断在单位半径外
    total = kernel.sum()
    if total > 0:
        kernel = kernel / total
    return kernel


def growth(u: np.ndarray, params: LeniaParams) -> np.ndarray:
    """生长函数:双侧高斯映到 [-1, 1]。G(u) = 2*bell(u) - 1。"""
    return 2.0 * _bell(u, params.mu, params.sigma) - 1.0


def _fft_convolve_wrap(grid: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """环面(toroidal)边界下的卷积,用 FFT。kernel 居中放进 grid 大小后做循环卷积。"""
    H, W = grid.shape
    kh, kw = kernel.shape
    # 把核放进与 grid 同尺寸的画布,核中心对齐到 (0,0) 以得到正确的循环卷积相位
    k_full = np.zeros((H, W), dtype=np.float64)
    k_full[:kh, :kw] = kernel
    # 把核中心移到原点(roll 半个核大小),使卷积是中心对称的
    k_full = np.roll(k_full, -(kh // 2), axis=0)
    k_full = np.roll(k_full, -(kw // 2), axis=1)
    conv = np.fft.irfft2(np.fft.rfft2(grid) * np.fft.rfft2(k_full), s=(H, W))
    return conv


def lenia_step(grid: np.ndarray, params: LeniaParams | None = None,
               kernel: np.ndarray | None = None) -> np.ndarray:
    """Lenia 单步更新。grid ∈[0,1] 浮点场,环面边界,返回新场 ∈[0,1]。

    A' = clip(A + dt * G(K * A), 0, 1)
    """
    if params is None:
        params = LeniaParams()
    if kernel is None:
        kernel = make_kernel(params)
    grid = np.asarray(grid, dtype=np.float64)
    potential = _fft_convolve_wrap(grid, kernel)
    delta = growth(potential, params)
    new = grid + params.dt * delta
    return np.clip(new, 0.0, 1.0)


# Orbium 初始 "生物" 图案(Bert Chan 原始 20x20 cell array)。
# 放进足够大的场里、用上面的参数迭代即会滑行。
_ORBIUM = np.array([
    [0, 0, 0, 0, 0, 0, 0.1, 0.14, 0.1, 0, 0, 0.03, 0.03, 0, 0, 0.3, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0.08, 0.24, 0.3, 0.3, 0.18, 0.14, 0.15, 0.16, 0.15, 0.09, 0.2, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0.15, 0.34, 0.44, 0.46, 0.38, 0.18, 0.14, 0.11, 0.13, 0.19, 0.18, 0.45, 0, 0, 0],
    [0, 0, 0, 0, 0.06, 0.13, 0.39, 0.5, 0.5, 0.37, 0.06, 0, 0, 0, 0.02, 0.16, 0.68, 0, 0, 0],
    [0, 0, 0, 0.11, 0.17, 0.17, 0.33, 0.4, 0.38, 0.28, 0.14, 0, 0, 0, 0, 0, 0.18, 0.42, 0, 0],
    [0, 0, 0.09, 0.18, 0.13, 0.06, 0.08, 0.26, 0.32, 0.32, 0.27, 0, 0, 0, 0, 0, 0, 0.82, 0, 0],
    [0.27, 0, 0.16, 0.12, 0, 0, 0, 0.25, 0.38, 0.44, 0.45, 0.34, 0, 0, 0, 0, 0, 0.22, 0.17, 0],
    [0, 0.07, 0.2, 0.02, 0, 0, 0, 0.31, 0.48, 0.57, 0.6, 0.57, 0, 0, 0, 0, 0, 0, 0.49, 0],
    [0, 0.59, 0.19, 0, 0, 0, 0, 0.2, 0.57, 0.69, 0.76, 0.76, 0.49, 0, 0, 0, 0, 0, 0.36, 0],
    [0, 0.58, 0.19, 0, 0, 0, 0, 0, 0.67, 0.83, 0.9, 0.92, 0.87, 0.12, 0, 0, 0, 0, 0.22, 0.07],
    [0, 0, 0.46, 0, 0, 0, 0, 0, 0.7, 0.93, 1, 1, 1, 0.61, 0, 0, 0, 0, 0.18, 0.11],
    [0, 0, 0.82, 0, 0, 0, 0, 0, 0.47, 1, 1, 0.98, 1, 0.96, 0.27, 0, 0, 0, 0.19, 0.1],
    [0, 0, 0.46, 0, 0, 0, 0, 0, 0.25, 1, 1, 0.84, 0.92, 0.97, 0.54, 0.14, 0.04, 0.1, 0.21, 0.05],
    [0, 0, 0, 0.4, 0, 0, 0, 0, 0.09, 0.8, 1, 0.82, 0.8, 0.85, 0.63, 0.31, 0.18, 0.19, 0.2, 0.01],
    [0, 0, 0, 0.36, 0.1, 0, 0, 0, 0.05, 0.54, 0.86, 0.79, 0.74, 0.72, 0.6, 0.39, 0.28, 0.24, 0.13, 0],
    [0, 0, 0, 0.01, 0.3, 0.07, 0, 0, 0.08, 0.36, 0.64, 0.7, 0.64, 0.6, 0.51, 0.39, 0.29, 0.19, 0.04, 0],
    [0, 0, 0, 0, 0.1, 0.24, 0.14, 0.1, 0.15, 0.29, 0.45, 0.53, 0.52, 0.46, 0.4, 0.31, 0.21, 0.08, 0, 0],
    [0, 0, 0, 0, 0, 0.08, 0.21, 0.21, 0.22, 0.29, 0.36, 0.39, 0.37, 0.33, 0.26, 0.18, 0.09, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0.03, 0.13, 0.19, 0.22, 0.24, 0.24, 0.23, 0.18, 0.13, 0.05, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0.02, 0.06, 0.08, 0.09, 0.07, 0.05, 0.01, 0, 0, 0, 0, 0],
], dtype=np.float64)


def seed_orbium(width: int, height: int, cx: int | None = None,
                cy: int | None = None) -> np.ndarray:
    """在 (width,height) 的零场里放一只 Orbium。默认放在偏左上以便观察滑行。"""
    grid = np.zeros((height, width), dtype=np.float64)
    oh, ow = _ORBIUM.shape
    if cx is None:
        cx = width // 4
    if cy is None:
        cy = height // 4
    y0 = cy - oh // 2
    x0 = cx - ow // 2
    for j in range(oh):
        for i in range(ow):
            yy = (y0 + j) % height
            xx = (x0 + i) % width
            grid[yy, xx] = _ORBIUM[j, i]
    return grid
