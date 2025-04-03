import numpy as np
import subprocess
import threading
import time
from scipy import signal
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

    def get_dynamic_threshold(self):
        if len(self.csi_buffer) < 2:
            return 0
        avg_amplitude = np.mean(self.csi_buffer, axis=0)
        std_amplitude = np.std(self.csi_buffer, axis=0)

        threshold = self.threshold + self.k * np.mean(std_amplitude)
        return threshold
    
    def setup_interface(self):
        """
        インターフェースをモニターモードに設定し、チャンネルを設定
        """
        try:
            # まず既存のmon0インターフェースを確認・削除
            try:
                subprocess.run(f"sudo iw dev mon0 del", shell=True, check=True)
                print("既存のmon0インターフェースを削除しました")
            except subprocess.CalledProcessError:
                # mon0が存在しない場合はエラーになるが無視
                pass
                
            subprocess.run("mcp -C 1 -N 1 -c 36/80 -m dc:a6:32:72:02:8a", shell=True, check=True)
            # インターフェースがupかチェック
            subprocess.run(f"sudo ifconfig {self.interface} up", shell=True, check=True)
            print(f"インターフェース {self.interface} が有効化されました")
            
            subprocess.run("nexutil -Iwlan0 -s500 -b -l34 -vKuABEQAAAQDcpjJyAooAAAAAAAAAAAAAAAAAAAAAAAAAAA==", shell=True, check=True)

            # モニターモードに設定
            subprocess.run(f"sudo iw dev {self.interface} interface add mon0 type monitor", shell=True, check=True)
            print("モニターモードに設定されました")
            
            # チャンネルを設定
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
            # ここでtcpdumpを開始、パケットを逐次的にキャプチャ
            i=0
            while self.running:
                capture_cmd = f"sudo tcpdump -i {self.interface} {self.capture_filter} -vv -w {self.pcap_filename} -c 1"
                capture_process = subprocess.Popen(capture_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = capture_process.communicate()
                print(i)
                i+=1
                if capture_process.returncode == 0:
                    self._parse_and_process_packet(stdout)
                else:
                    print(f"エラー: {stderr}")
                
                if i == 100:
                    break

                #time.sleep(0.1)  # 少し待機し、次のパケットキャプチャに備える

            # self.capture_process = subprocess.Popen(
            #     ["sudo", "tcpdump", "-i", self.interface, self.capture_filter, "-l"],
            #     stdout=subprocess.PIPE,
            #     stderr=subprocess.STDOUT,
            #     universal_newlines=True
            # )

            # # リアルタイムで出力を取得して表示
            # for line in iter(self.capture_process.stdout.readline, ''):
            #     if not self.running:
            #         break
            #     csi_data = self._parse_csi_data(line)
            # if self.csi_data.size > 0:
            #     self.detect_motion(self.csi_data)

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

    def process_pcap_file(self):
        try:
            sample = decoder(self.device).read_pcap(self.pcap_filename)
            self.csi_data = decoder(self.device).unpack(sample['csi'])
        except Exception as e:
            print(f"pcap解析中にエラー:{e}")
    def _parse_csi_data(self, raw_line):
        try:
            samples = decoder(self.device).read_pcap(self.pcap_filename)
            csi_data = decoder(self.device).unpack(samples['csi'])
            return np.array(csi_data)
        
        except ValueError:
            return np.array([])
    
    def detect_motion(self, csi_frame):
        if len(csi_frame) == 0:
            return
        current_time = time.time()
        amplitude = np.abs(csi_frame)
        amplitude = np.clip(amplitude, 0, 3000)
        dynamic_threshold = self.get_dynamic_threshold()
        normalized_amplitude = (amplitude - np.mean(amplitude)) / np.std(amplitude)
        self.csi_buffer.append(normalized_amplitude)
        if len(self.csi_buffer) > self.window_size:
            self.csi_buffer.pop(0)
        if len(self.csi_buffer) < 2:
            return
        avg_diff = np.mean([np.mean(np.abs(self.csi_buffer[i] - self.csi_buffer[i-1])) for i in range(1, len(self.csi_buffer))])
        print(avg_diff)
        if avg_diff > self.threshold and current_time - self.last_detection_time > self.cooldown_period:
            self.last_detection_time = current_time
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 動きを検出しました")

if __name__ == "__main__":
    detector = NexmonCSIMotionDetector()
    detector.start_capture()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.running = False
        print("終了します")