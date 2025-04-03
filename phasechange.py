import numpy as np
import matplotlib.pyplot as plt
from nexcsi import decoder

# デバイス設定
device = 'raspberrypi'

# pcapファイル1の読み込みとCSIデータの取得
samples1 = decoder(device).read_pcap('pcaps/001.pcap')  # ファイル名は適宜変更
csi_data1 = decoder(device).unpack(samples1['csi'])

# pcapファイル2の読み込みとCSIデータの取得
samples2 = decoder(device).read_pcap('pcaps/101.pcap')  # ファイル名は適宜変更
csi_data2 = decoder(device).unpack(samples2['csi'])

# それぞれのcsiデータの形を確認
print(f"CSI Data 1 shape: {csi_data1.shape}")
print(f"CSI Data 2 shape: {csi_data2.shape}")

# 位相データの抽出（ファイル1）
phase1 = np.angle(csi_data1)

# 位相データの抽出（ファイル2）
phase2 = np.angle(csi_data2)

# 位相のヒートマップをプロット
plt.figure(figsize=(14, 6))

# ファイル1の位相
plt.subplot(1, 2, 1)
plt.imshow(phase1.T, cmap='twilight', aspect='auto', origin='lower', interpolation='nearest')
plt.title("Phase Heatmap (File 1)")
plt.xlabel("Time Index")
plt.ylabel("Channel Index")
plt.colorbar(label="Phase (radians)")
plt.grid(False)

# ファイル2の位相
plt.subplot(1, 2, 2)
plt.imshow(phase2.T, cmap='twilight', aspect='auto', origin='lower', interpolation='nearest')
plt.title("Phase Heatmap (File 2)")
plt.xlabel("Time Index")
plt.ylabel("Channel Index")
plt.colorbar(label="Phase (radians)")
plt.grid(False)

# プロット表示
plt.tight_layout()
plt.show()
