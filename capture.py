from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# デバイス設定
device = 'raspberrypi'

# 最初のpcapファイルの読み込みと処理
samples_1 = decoder(device).read_pcap('pcaps/08.pcap')
csi_data_1 = decoder(device).unpack(samples_1['csi'])

# 2つ目のpcapファイルの読み込みと処理
samples_2 = decoder(device).read_pcap('pcaps/05.pcap')
csi_data_2 = decoder(device).unpack(samples_2['csi'])

# CSIデータの振幅（Amplitude）の取得
amplitude_1 = np.abs(csi_data_1)
amplitude_2 = np.abs(csi_data_2)

# 振幅の転置を計算
amplitude_1_T = np.transpose(amplitude_1)
amplitude_2_T = np.transpose(amplitude_2)

# vmax を3000に固定
vmax = 2000

# 振幅の転置をプロット
plt.figure(figsize=(12, 6))

# 01.pcapの振幅（転置）
plt.subplot(1, 2, 1)
sns.heatmap(amplitude_1_T, cmap='viridis', cbar_kws={'label': 'Amplitude'}, vmin=0, vmax=vmax)
plt.title('Amplitude of 01.pcap (Transposed)')
plt.xlabel('Antenna Index')
plt.ylabel('Subcarrier Index')

# 02.pcapの振幅（転置）
plt.subplot(1, 2, 2)
sns.heatmap(amplitude_2_T, cmap='viridis', cbar_kws={'label': 'Amplitude'}, vmin=0, vmax=vmax)
plt.title('Amplitude of 02.pcap (Transposed)')
plt.xlabel('Antenna Index')
plt.ylabel('Subcarrier Index')

plt.tight_layout()
plt.show()
