import numpy as np
from nexcsi import decoder
import matplotlib.pyplot as plt

# デバイス設定
device = 'raspberrypi'    

#立ったかどうかを判定できればうれしい
def isStanding(data, threshold_ratio=3):
    #立った状態のエラーの平均
    standing = decoder(device).read_pcap('pcaps/013.pcap')
    standing_csi = decoder(device).unpack(standing['csi'])
    standing_amp = np.abs(standing_csi)
    #こいつは比較用のやつ
    standing_ave = np.average(standing_amp, axis=0)
    error1 = get_squared_error(standing_amp, standing_ave)
    train_error_ave = np.average(error1)
    
    error = get_squared_error(data, standing_ave)

    isStandingLabel = [0]*len(error)
    for i in range(len(error)):
        if error[i] < threshold_ratio * train_error_ave:
            isStandingLabel[i] = 1
    
    return isStandingLabel

def isSitting(data, threshold_ratio=8):
    # 座っている状態のエラーの平均
    sitting = decoder(device).read_pcap('pcaps/014.pcap')  # 座っているときのPCAPファイルを使用
    sitting_csi = decoder(device).unpack(sitting['csi'])
    sitting_amp = np.abs(sitting_csi)
    
    # 座っているときのデータの平均振幅
    sitting_ave = np.average(sitting_amp, axis=0)
    
    # 座っているときのエラーを計算
    error1 = get_squared_error(sitting_amp, sitting_ave)
    train_error_ave = np.average(error1)
    
    # 新しいデータとの比較を行う
    error = get_squared_error(data, sitting_ave)

    # 座っているラベルのリスト
    isSittingLabel = [0]*len(error)
    for i in range(len(error)):
        if error[i] > threshold_ratio * train_error_ave:
            isSittingLabel[i] = 2
    
    return isSittingLabel

#二乗誤差和を計算
def get_squared_error(data, judge_ave):
    error = []
    for i in range(len(data)):
        error.append(np.sum((data[i] - judge_ave)**2))

    return error

if __name__=="__main__":
    sample = decoder(device).read_pcap('pcaps/015.pcap')
    data = decoder(device).unpack(sample['csi'])
    data_amp = np.abs(data)

    count = 0
    # ans = isStanding(data_amp, threshold_ratio=2.5)
    ans = isSitting(data_amp, threshold_ratio=8)
    for i in range(len(ans)):
        if ans[i] == 1:
            count += 1

    print(count/100)

    print(ans)