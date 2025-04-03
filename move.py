from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# デバイス設定
device = 'raspberrypi'

# 2つのPCAPファイルの読み込みとCSIデータの取得
pcap_files = ['pcaps/002.pcap', 'pcaps/001.pcap']  # 2つのPCAPファイルをリストに
sum_abs_phase_diff_list = []  # 結果を保存するリスト

# 2つのPCAPファイルのデータ処理
for pcap_file in pcap_files:
    # pcapファイルの読み込みとCSIデータの取得
    samples = decoder(device).read_pcap(pcap_file)
    csi_data = decoder(device).unpack(samples['csi'])

    # 位相データの抽出
    phase = np.angle(csi_data)

    # 位相差分の計算
    phase_diff = np.diff(phase, axis=0)

    # 位相差分の絶対値を計算
    abs_phase_diff = np.abs(phase_diff)

    # 各時点での絶対位相変化の合計を計算
    sum_abs_phase_diff = np.sum(abs_phase_diff, axis=1)
    
    # 結果をリストに追加
    sum_abs_phase_diff_list.append(sum_abs_phase_diff)

# 結果をプロット（2つのデータの合計値の推移）
plt.figure(figsize=(10, 6))

# 2つのデータをそれぞれプロット
for idx, sum_abs_phase_diff in enumerate(sum_abs_phase_diff_list):
    label = f'PCAP {idx+1}'  # ラベルを付ける
    plt.plot(sum_abs_phase_diff, label=label)

plt.title('Sum of Absolute Phase Changes (Multiple PCAP Files)')
plt.xlabel('Time')
plt.ylabel('Sum of Absolute Phase Change')
plt.legend()
plt.grid(True)
plt.show()
