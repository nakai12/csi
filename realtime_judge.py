import numpy as np
import subprocess
import threading
import time
from datetime import datetime
from nexcsi import decoder

class NexmonCSIMotionDetector:
    def __init__(self, interface='wlan0', window_size=3, threshold=0.12, k=2.0, pcap_filename='hoge.pcap'):
        self.interface = interface
        self.window_size = window_size
        self.threshold = threshold
        self.csi_buffer = []
        self.last_detection_time = 0
        self.cooldown_period = 1  # 検出後のクールダウン（秒）
        self.running = False
        self.capture_filter = "dst port 5500"
        self.device = 'raspberrypi'
        self.pcap_filename = pcap_filename
        self.k = k
        self.standing_ave = None
        self.sitting_ave = None
        self.load_reference_data()

    def load_reference_data(self):
        """
        座っている状態と立っている状態の参照データを読み込む
        """
        try:
            # 座っている状態のPCAPファイル
            sitting = decoder(self.device).read_pcap('pcaps/014.pcap')
            sitting_csi = decoder(self.device).unpack(sitting['csi'])
            self.sitting_ave = np.average(np.abs(sitting_csi), axis=0)
            self.th_sitting = np.sum((np.abs(sitting_csi) - self.sitting_ave)**2)

            # 立っている状態のPCAPファイル
            standing = decoder(self.device).read_pcap('pcaps/013.pcap')
            standing_csi = decoder(self.device).unpack(standing['csi'])
            self.standing_ave = np.average(np.abs(standing_csi), axis=0)
            self.th_standing = np.sum((np.abs(standing_csi) - self.standing_ave)**2)
            
            print("参照データの読み込みが完了しました。")
        except Exception as e:
            print(f"参照データの読み込みエラー: {e}")

    def _parse_csi_data(self, raw_line):
        try:
            samples = decoder(self.device).read_pcap(self.pcap_filename)
            csi_data = decoder(self.device).unpack(samples['csi'])
            return np.array(csi_data)
        
        except ValueError:
            return np.array([])
    def setup_interface(self):
        """
        インターフェースをモニターモードに設定し、チャンネルを設定
        """
        try:
            # 既存のmon0インターフェースを削除
            try:
                subprocess.run(f"sudo iw dev mon0 del", shell=True, check=True)
                print("既存のmon0インターフェースを削除しました")
            except subprocess.CalledProcessError:
                pass  # mon0が存在しない場合はエラーを無視
            
            # インターフェースの設定
            subprocess.run(f"sudo ifconfig {self.interface} up", shell=True, check=True)
            print(f"インターフェース {self.interface} が有効化されました")
            
            subprocess.run(f"sudo iw dev {self.interface} interface add mon0 type monitor", shell=True, check=True)
            print("モニターモードに設定されました")
            
            subprocess.run(f"sudo ip link set mon0 up", shell=True, check=True)
            print("セットアップ完了")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"インターフェースのセットアップ中にエラーが発生しました: {e}")
            return False

    def start_capture(self):
        if not self.setup_interface():
            return
        self.running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        print(f"Nexmon CSI キャプチャを {self.interface} で開始")
    
    def _capture_loop(self):
        """
        `tcpdump` の出力をリアルタイムに取得して表示
        """
        print("CSIデータキャプチャ中...")
        try:
            i = 0
            while self.running:
                capture_cmd = f"sudo tcpdump -i {self.interface} {self.capture_filter} -vv -w {self.pcap_filename} -c 1"
                capture_process = subprocess.Popen(capture_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = capture_process.communicate()
                print(i)
                i += 1
                if capture_process.returncode == 0:
                    self._parse_and_process_packet(stdout)
                else:
                    print(f"エラー: {stderr}")

                if i == 100:
                    break

        except Exception as e:
            print(f"キャプチャループ中にエラー: {e}")

    def _parse_and_process_packet(self, packet_data):
        try:
            # ここでキャプチャしたパケットデータを処理する
            csi_data = self._parse_csi_data(packet_data)
            if csi_data.size > 0:
                self.detect_motion(csi_data)
        except Exception as e:
            print(f"パケット処理中にエラー: {e}")
    
    def detect_motion(self, csi_frame):
        if len(csi_frame) == 0:
            return
        current_time = time.time()
        amplitude = np.abs(csi_frame)
        amplitude = np.clip(amplitude, 0, 3000)

        # 座っているか立っているかを判定する
        is_standing = self.is_standing_or_sitting(amplitude)
        if is_standing == 1:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 立っている状態が検出されました")
        elif is_standing == 2:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 座っている状態が検出されました")

    def compute_average_error(self, pcap_filename):
        """
        指定されたPCAPファイルに基づいて平均誤差和を計算
        """
        # pcapファイルを読み込む
        sample = decoder(self.device).read_pcap(pcap_filename)
        csi_data = decoder(self.device).unpack(sample['csi'])
        csi_amp = np.abs(csi_data)
        
        # 平均振幅を計算
        ave_amp = np.mean(csi_amp, axis=0)
        return ave_amp

    def is_standing_or_sitting(self, data):
        """
        立っている状態と座っている状態を判定する関数
        """
        # 立っている状態と座っている状態の平均を計算
        if self.standing_ave is None or self.sitting_ave is None:
            self.standing_ave = self.compute_average_error('pcaps/013.pcap')
            self.sitting_ave = self.compute_average_error('pcaps/014.pcap')

        # 立っている状態と座っている状態の誤差を計算
        standing_error = np.sum((data - self.standing_ave) ** 2)
        sitting_error = np.sum((data - self.sitting_ave) ** 2)

        # 閾値を動的に計算
        stand_threshold = 2.5
        sit_threshold = 8
        
        # 判定処理
        if standing_error > stand_threshold * self.th_standing:
            return 1  # 立っている状態
        elif sitting_error < sit_threshold * self.th_standing:
            return 2  # 座っている状態
        else:
            return 0  # 判定できない（例えば、両方とも閾値より大きい場合）


if __name__ == "__main__":
    detector = NexmonCSIMotionDetector()
    detector.start_capture()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.running = False
        print("終了します")
