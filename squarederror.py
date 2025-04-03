import numpy as np
from nexcsi import decoder
import matplotlib.pyplot as plt

# デバイス設定
device = 'raspberrypi'

# pcapファイルの読み込みとCSIデータの取得
judge = decoder(device).read_pcap('pcaps/008.pcap')  # ファイル名は適宜変更
judge_csi = decoder(device).unpack(judge['csi'])
judge_amp = np.abs(judge_csi)

sample = decoder(device).read_pcap('pcaps/009.pcap')
data = decoder(device).unpack(sample['csi'])
data_amp = np.abs(data)

judge_ave = np.average(judge_amp, axis=0)

def get_squared_error(data, judge_ave=judge_ave):
    error = []
    for i in range(len(data)):
        error.append(np.sum((data[i] - judge_ave)**2))

    return error

error = get_squared_error(data_amp, judge_ave=judge_ave)
error1 = get_squared_error(judge_amp, judge_ave=judge_ave)
print(error)
print(error1)

plt.figure(figsize=(10, 5))

# 008.pcap（judge_amp）と009.pcap（data_amp）の誤差のヒストグラムを描画
plt.hist(error, bins=30, alpha=0.5, label="009.pcap (sample)", color="red")
plt.hist(error1, bins=30, alpha=0.5, label="008.pcap (judge)", color="blue")

# ラベルとタイトルを設定
plt.xlabel("Squared Error")
plt.ylabel("Frequency")
plt.title("Histogram of Squared Errors")
plt.legend()
plt.grid()

# ヒストグラムを表示
plt.show()
