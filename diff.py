from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.ndimage import gaussian_filter1d

# デバイス設定
device = 'raspberrypi'

# 最初のpcapファイルの読み込みと処理
samples_1 = decoder(device).read_pcap('pcaps/106.pcap')
csi_data_1 = decoder(device).unpack(samples_1['csi'])

# 2つ目のpcapファイルの読み込みと処理
samples_2 = decoder(device).read_pcap('pcaps/107.pcap')
csi_data_2 = decoder(device).unpack(samples_2['csi'])

def moving_average_filter(csi_amplitude, window_size=5):
    """
    各サブキャリアごとに移動平均フィルタを適用する関数
    
    Parameters:
        csi_amplitude (numpy.ndarray): CSI の振幅データ (num_packets, num_subcarriers)
        window_size (int): 移動平均のウィンドウサイズ
    
    Returns:
        numpy.ndarray: フィルタ適用後の CSI 振幅データ
    """
    num_packets, num_subcarriers = csi_amplitude.shape  # データのサイズ取得
    filtered_csi = np.zeros_like(csi_amplitude)  # 結果を保存する配列
    
    for subcarrier in range(num_subcarriers):
        filtered_csi[:, subcarrier] = np.convolve(
            csi_amplitude[:, subcarrier], 
            np.ones(window_size) / window_size, 
            mode='same'  # 端のデータが消えないようにする
        )
    
    return filtered_csi
def gauss(amp, sigma=1.0):
    return gaussian_filter1d(amp,sigma=sigma)

# CSIデータの振幅（Amplitude）の取得
# amplitude_1 = moving_average_filter(np.abs(csi_data_1))
# amplitude_2 = gauss(np.abs(csi_data_2))
amplitude_1 = np.abs(csi_data_1)
amplitude_2 = np.abs(csi_data_2)

# 振幅の差分の絶対値を計算
amplitude_diff = (amplitude_2 - amplitude_1)

# ヒートマップで可視化
plt.figure(figsize=(10, 6))
sns.heatmap(amplitude_diff.T, cmap="viridis", cbar=True)
plt.xlabel("Packet Index")
plt.ylabel("Subcarrier Index")
plt.title("Absolute Amplitude Difference (107.pcap - 106.pcap)")
plt.show()
