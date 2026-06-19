// Lenia 连续 CA 的 TS-CPU 忠实移植(对应 ca/lenia.py)。
//
// Orbium 配方:环形高斯核(R≈13)+ 高斯生长函数(mu≈0.15, sigma≈0.015)+
// dt≈0.1 + 环面(wrap)边界。单浮点场 ∈[0,1]。Bert Chan《Lenia》原始参数。
//
// 无 LLM、无 FFT、无 WebGL:Float32Array + 直接(naive)卷积。
// Python 后端用 FFT 做循环卷积;这里在 64² 网格上用直接循环卷积,二者数学等价
// (同一环面循环卷积),只是实现不同。核居中、环面 wrap、和归一化为 1,与 Python 对齐。

export interface LeniaParams {
  R: number; // 核半径
  mu: number; // 生长函数中心
  sigma: number; // 生长函数宽度
  dt: number; // 时间步
  kernelMu: number; // 核内环高斯壳中心(相对归一化半径)
  kernelSigma: number; // 核内环高斯壳宽度
}

// Orbium 已知良好参数(Bert Chan, Lenia),与 lenia.py 的 LeniaParams 默认值一致。
export const DEFAULT_LENIA_PARAMS: LeniaParams = {
  R: 13,
  mu: 0.15,
  sigma: 0.015,
  dt: 0.1,
  kernelMu: 0.5,
  kernelSigma: 0.15,
};

// 高斯钟形 exp(-((x-mu)/sigma)^2 / 2)。对应 lenia.py 的 _bell。
function bell(x: number, mu: number, sigma: number): number {
  const z = (x - mu) / sigma;
  return Math.exp(-(z * z) / 2.0);
}

export interface Kernel {
  size: number; // 边长 = 2R+1
  R: number;
  data: Float32Array; // size*size 行优先, 已归一化(和为 1)
}

// 环形高斯核,已归一化(和为 1)。对应 lenia.py 的 make_kernel。
// 在 [-R, R]² 网格上按到中心的归一化半径取壳值,半径>1 截断为 0。
export function makeKernel(params: LeniaParams): Kernel {
  const R = params.R;
  const size = 2 * R + 1;
  const data = new Float32Array(size * size);
  let total = 0;
  for (let j = 0; j < size; j++) {
    const dy = j - R; // 对应 np.arange(-R, R+1)
    for (let i = 0; i < size; i++) {
      const dx = i - R;
      const radius = Math.sqrt(dx * dx + dy * dy) / R; // 归一化半径
      let v = bell(radius, params.kernelMu, params.kernelSigma);
      if (radius > 1.0) v = 0.0; // 截断在单位半径外
      data[j * size + i] = v;
      total += v;
    }
  }
  if (total > 0) {
    for (let k = 0; k < data.length; k++) data[k] /= total;
  }
  return { size, R, data };
}

// 生长函数:双侧高斯映到 [-1, 1]。G(u) = 2*bell(u) - 1。对应 lenia.py 的 growth。
function growth(u: number, params: LeniaParams): number {
  return 2.0 * bell(u, params.mu, params.sigma) - 1.0;
}

export interface Grid {
  width: number;
  height: number;
  data: Float32Array; // height*width 行优先, ∈[0,1]
}

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

// 环面(toroidal)边界下的直接卷积:对每个输出格累加 kernel 覆盖范围内的环绕样本。
// potential[y,x] = Σ_{ky,kx} grid[(y+ky-R) mod H][(x+kx-R) mod W] * kernel[ky,kx]
// 与 lenia.py 的 _fft_convolve_wrap(居中、循环卷积)数学等价。
function convolveWrap(grid: Grid, kernel: Kernel): Float32Array {
  const { width: W, height: H, data: A } = grid;
  const { size, R, data: K } = kernel;
  const out = new Float32Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let acc = 0;
      for (let ky = 0; ky < size; ky++) {
        // 行偏移(环面 wrap),+H 保证非负后取模
        const sy = (((y + ky - R) % H) + H) % H;
        const rowA = sy * W;
        const rowK = ky * size;
        for (let kx = 0; kx < size; kx++) {
          const sx = (((x + kx - R) % W) + W) % W;
          acc += A[rowA + sx] * K[rowK + kx];
        }
      }
      out[y * W + x] = acc;
    }
  }
  return out;
}

// Lenia 单步更新:A' = clip(A + dt * G(K * A), 0, 1)。对应 lenia.py 的 lenia_step。
// 返回新 Grid(不就地修改入参),环面边界,场 ∈[0,1]。
export function leniaStep(
  grid: Grid,
  params: LeniaParams = DEFAULT_LENIA_PARAMS,
  kernel?: Kernel,
): Grid {
  const k = kernel ?? makeKernel(params);
  const potential = convolveWrap(grid, k);
  const next = new Float32Array(grid.data.length);
  for (let i = 0; i < next.length; i++) {
    const delta = growth(potential[i], params);
    next[i] = clamp01(grid.data[i] + params.dt * delta);
  }
  return { width: grid.width, height: grid.height, data: next };
}

// Orbium 初始 "生物" 图案(Bert Chan 原始 20x20 cell array),与 lenia.py 的 _ORBIUM 逐值一致。
// 放进足够大的场里、用上面的参数迭代即会滑行。
const ORBIUM: number[][] = [
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
];

// 在 (width,height) 的零场里放一只 Orbium。对应 lenia.py 的 seed_orbium。
// 默认放在偏左上(width/4, height/4)以便观察滑行;环面 wrap 放置。
export function seedOrbium(
  width: number,
  height: number,
  cx?: number,
  cy?: number,
): Grid {
  const data = new Float32Array(width * height);
  const oh = ORBIUM.length;
  const ow = ORBIUM[0].length;
  const centerX = cx ?? Math.floor(width / 4);
  const centerY = cy ?? Math.floor(height / 4);
  const y0 = centerY - Math.floor(oh / 2);
  const x0 = centerX - Math.floor(ow / 2);
  for (let j = 0; j < oh; j++) {
    for (let i = 0; i < ow; i++) {
      const yy = (((y0 + j) % height) + height) % height;
      const xx = (((x0 + i) % width) + width) % width;
      data[yy * width + xx] = ORBIUM[j][i];
    }
  }
  return { width, height, data };
}
