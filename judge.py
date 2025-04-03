import numpy as np
from nexcsi import decoder
import matplotlib.pyplot as plt

# デバイス設定
device = 'raspberrypi'

# pcapファイルの読み込みとCSIデータの取得
judge = decoder(device).read_pcap('pcaps/009.pcap')  # ファイル名は適宜変更
judge_csi = decoder(device).unpack(judge['csi'])
judge_amp = np.abs(judge_csi)

sample = decoder(device).read_pcap('pcaps/008.pcap')
data = decoder(device).unpack(sample['csi'])
data_amp = np.abs(data)

judge_ave = np.average(judge_amp, axis=0)
print(judge_ave.shape)

def get_corr(data, judge_amp=judge_ave):
    r = []
    for i in range(len(data)):
        print(data[i].shape, judge_amp.shape)
        corr = np.corrcoef(np.array([data[i], judge_amp]))
        r.append(corr[0][1])
    
    return r

r = np.array([get_corr(data_amp, judge_amp=judge_ave)])
print(r)
