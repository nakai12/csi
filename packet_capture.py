import subprocess
import time

class NetworkInterface:
    def __init__(self, interface='wlan0', pcap_filename='output.pcap', packet_num = 500):
        self.interface = interface
        self.running = False
        self.capture_filter = "dst port 5500"
        self.device = 'raspberrypi'
        self.pcap_filename = pcap_filename
        self.packet_num = packet_num
    
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

    def run_setup(self):
        """
        インターフェースの設定を行い、その後指定されたコマンドを実行します。
        """
        if self.setup_interface():
            print("インターフェースが正常に設定されました。次のコマンドを実行します。")
            
            # 実行するコマンド
            cmd = f"sudo tcpdump -i {self.interface} {self.capture_filter} -vv -w {self.pcap_filename} -c {self.packet_num}"
            
            try:
                print(f"コマンド: {cmd} を実行しています...")
                # コマンドを実行
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"コマンド実行中にエラーが発生しました: {e}")
        else:
            print("インターフェースの設定に失敗しました。")
            
if __name__ == "__main__":
    # インターフェースを設定するクラスのインスタンス作成
    network_interface = NetworkInterface()

    # 設定を行い、その後コマンドを実行
    network_interface.run_setup()
