from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# デバイス設定
device = 'raspberrypi'

# pcapファイルの読み込みとCSIデータの取得
samples = decoder(device).read_pcap('pcaps/001.pcap')  # ファイル名は適宜変更
csi_data = decoder(device).unpack(samples['csi'])

# 位相データの抽出
phase = np.angle(csi_data)

# 全体の行数を取得して4分割するインデックスを計算
total_rows = phase.shape[1]  # サブキャリアのインデックス
split_index = total_rows // 4

# グラフの描画
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for i, ax in enumerate(axes.flat):
    start_idx = i * split_index
    end_idx = (i + 1) * split_index if i < 3 else total_rows
    sns.heatmap(phase[:, start_idx:end_idx].T, cmap="viridis", cbar=True, ax=ax)
    ax.set_title(f"Subcarrier Index {start_idx} to {end_idx}")
    ax.set_ylabel("Subcarrier Index")
    ax.set_xlabel("Antenna")

plt.tight_layout()
plt.show()
