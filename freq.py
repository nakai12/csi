from scipy.fft import fft, fftfreq
from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

# デバイス設定
device = 'raspberrypi'
# pcapファイルの読み込みとCSIデータの取得
samples = decoder(device).read_pcap('pcaps/19.pcap')  # ファイル名は適宜変更
csi_data = decoder(device).unpack(samples['csi'])

amplitude = np.abs(csi_data)
# 位相データの抽出
phase = np.angle(csi_data)

# サンプル数の設定
n = len(csi_data)  # CSIデータのサンプル数

# サンプリング周波数（例: 1 MHz）
sampling_rate = 1e6  

# 周波数軸の作成
freqs = fftfreq(n, d=1/sampling_rate)

# フーリエ変換
fft_amplitude = fft(amplitude)

# 振幅スペクトルのプロット
plt.figure(figsize=(10, 6))
plt.plot(freqs[:n//2], np.sum(np.abs(fft_amplitude)[:n//2],axis=1))  # 正の周波数のみ
plt.title("Amplitude Spectrum of CSI Data")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()