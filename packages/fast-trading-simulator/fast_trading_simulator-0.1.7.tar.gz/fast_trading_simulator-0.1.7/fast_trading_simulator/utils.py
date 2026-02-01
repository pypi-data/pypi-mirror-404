from typing import Callable, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import talib as ta
from crypto_data_downloader.utils import load_pkl
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from scipy.stats import binned_statistic
from trading_models.utils import D2_TYPE, D_TYPE, plot_general

from fast_trading_simulator.sim import ACT_HIGH, ACT_LOW, ACT_NAMES


class ActMap:
    @staticmethod
    def from_tanh(tanh, low, high):
        return (tanh + 1) / 2 * (high - low) + low

    @staticmethod
    def to_tanh(x, low, high):
        return (x - low) / (high - low) * 2 - 1


def volatility(price: np.ndarray):
    dp = np.diff(price) / price[:-1]
    return np.sqrt(np.mean(dp**2))


def make_market_n_obs(
    path,
    vol_range=[0, 1],
    ref_sym="BTCUSDT",
    price_idx=1,
    # obs:
    MA=ta.KAMA,
    periods=[10, 100],
    add_ref_obs=True,
):
    data: D_TYPE = load_pkl(path, gz=True)
    T = len(data[ref_sym])
    temp: D2_TYPE = {}
    skip = max(periods)
    for sym, v in data.items():
        if len(v) != T:
            continue
        p = v[:, price_idx]
        obs = np.array([p / MA(p, P) - 1 for P in periods]).T
        obs = obs.clip(-1, 1)
        vol = volatility(p)
        ok = vol > vol_range[0] and vol < vol_range[1]
        temp[sym] = {"raw": v[skip:], "obs": obs[skip:], "ok": ok, "vol": vol}
    if add_ref_obs:
        ref_obs = temp[ref_sym]["obs"]
        for sym, d in temp.items():
            d["obs"] = np.concat([d["obs"], ref_obs], axis=1)
    get = lambda key: np.array([d[key] for d in temp.values() if d["ok"]])
    # plt.hist(get("vol"), bins=100)
    # plt.savefig("volatility_hist")
    return get("raw"), get("obs")


def rand_period(arrays: List[np.ndarray], dt=1024):
    T = arrays[0].shape[1]
    t1 = np.random.randint(0, T - dt)
    return [x[:, t1 : t1 + dt] for x in arrays]


def slice_period(arrays: List[np.ndarray], r1, r2):
    T = arrays[0].shape[1]
    t1, t2 = int(T * r1), int(T * r2)
    return [x[:, t1:t2] for x in arrays]


def rand_action(obs: np.ndarray):
    SYM, TIME, _ = obs.shape
    tanh_act = np.random.uniform(-1, 1, (SYM, TIME, 5))
    tanh_act[:, :, 0] = np.where(tanh_act[:, :, 0] > 0, 1, -1)
    return ActMap.from_tanh(tanh_act, ACT_LOW, ACT_HIGH)


def plot_act_hist(action: np.ndarray):
    plots = {f"{ACT_NAMES[i]}_hist": action[..., i] for i in range(5)}
    plot_general(plots, "act_hist")


def bin_stat(X: np.ndarray, Y: np.ndarray, stat, y_lim=None, bins=100):
    nx, ny = X.shape[-1], Y.shape[-1]
    plt.figure(figsize=(4 * ny, 3 * nx))
    cnt = 0
    for i in range(nx):
        for j in range(ny):
            cnt += 1
            plt.subplot(nx, ny, cnt)
            plt.title(f"X{i}, Y{j}")
            x, y = X[:, i], Y[:, j]
            y2, edges, _ = binned_statistic(x, y, stat, bins)
            x2 = (edges[:-1] + edges[1:]) / 2
            plt.scatter(x, y, s=3, c="y", label="raw")
            plt.plot(x2, y2, c="b", label="bin_stat")
            if y_lim is not None:
                plt.ylim(y_lim)
            plt.legend()
    plt.tight_layout()
    plt.savefig("bin_stat")
    plt.close()


# ======================================


def round_dx(x, dx):
    return round(round(x / dx) * dx, 10)


def pymoo_minimize(func: Callable, conf: Dict, algo=GA()):
    xl = [v[0] for v in conf.values()]
    xu = [v[1] for v in conf.values()]
    dx = [v[2] for v in conf.values()]
    best = np.inf

    class Prob(ElementwiseProblem):
        def __init__(s):
            super().__init__(n_var=len(xl), n_obj=1, xl=xl, xu=xu)

        def _evaluate(s, X: np.ndarray, out, *args, **kwargs):
            X = [round_dx(xi, dxi) for xi, dxi in zip(X, dx)]
            P = dict(zip(conf.keys(), X))
            loss = func(P)
            nonlocal best
            if loss < best:
                best = loss
                print(f"best: {best} {P}")
            out["F"] = loss

    minimize(Prob(), algo, seed=42)
