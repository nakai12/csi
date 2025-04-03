#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
import subprocess
import signal
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from datetime import datetime
import os

# 日本語フォントサポートを設定
def setup_japanese_fonts():
    try:
        # 日本語フォントのパスを追加
        font_dirs = ['/usr/share/fonts/']
        font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
        
        # 日本語フォントを検索
        japanese_fonts = [f for f in font_files if 'ipa' in f.lower() or 'noto' in f.lower()]
        
        if japanese_fonts:
            # 見つかった最初の日本語フォントを使用
            japanese_font = japanese_fonts[0]
            font_prop = font_manager.FontProperties(fname=japanese_font)
            plt.rcParams['font.family'] = font_prop.get_name()
            return True
        else:
            # 日本語フォントが見つからなければ代替
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
            return False
            
    except Exception as e:
        print(f"フォント設定エラー: {e}")
        # 安全な選択肢にフォールバック
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
        return False

# nexcsiライブラリをインポート
try:
    import nexcsi
except ImportError:
    print("nexcsiライブラリがインストールされていません。")
    print("pip install nexcsi でインストールしてください。")
    sys.exit(1)

# グローバル変数
running = True
data_lock = threading.Lock()
csi_buffer = []
buffer_max_size = 100

# 設定
SUBCARRIER_NUM = 64  # サブキャリア数
PLOT_LEN = 100       # プロット表示するサンプル数

class CSICapture(threading.Thread):
    def __init__(self, interface, mac_address=None, buffer=None):
        threading.Thread.__init__(self)
        self.interface = interface
        self.mac_address = mac_address
        self.buffer = buffer if buffer is not None else []
        self.process = None
        self.daemon = True
        
    def run(self):
        # tcpdumpコマンドを構築
        cmd = ['sudo', 'tcpdump', '-i', self.interface, '-U', '-w', '-']
        if self.mac_address:
            cmd.extend(['ether', 'host', self.mac_address])
            
        print(f"実行コマンド: {' '.join(cmd)}")
        
        # tcpdumpプロセスを開始
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        
        # CSIデータの取得ループ
        try:
            while running:
                # パケットデータを読み取る（サイズは調整可能）
                packet_data = self.process.stdout.read(2048)
                
                if not packet_data:
                    time.sleep(0.001)
                    continue
                
                # nexcsi.decoderでCSIデータを抽出
                try:
                    csi_data = nexcsi.decoder(packet_data)
                    if csi_data is not None:
                        # CSIデータが取得できた場合、バッファに追加
                        with data_lock:
                            self.buffer.append({
                                'timestamp': time.time(),
                                'csi': csi_data
                            })
                            # バッファサイズ制限
                            if len(self.buffer) > buffer_max_size:
                                self.buffer.pop(0)
                except Exception as e:
                    # デコードエラーは無視
                    pass
                
        except Exception as e:
            print(f"CSIキャプチャエラー: {e}")
        finally:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except:
                    self.process.kill()

class CSIRealTimePlot:
    def __init__(self, csi_buffer, save_dir=None, mode='amplitude'):
        self.csi_buffer = csi_buffer
        self.save_dir = save_dir
        self.mode = mode  # 'amplitude' または 'phase'
        self.ani = None  # アニメーションオブジェクトを初期化
        
        # データ保存用ディレクトリの作成
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.csv_file = open(f"{save_dir}/csi_data_{timestamp}.csv", 'w')
            self.csv_file.write("timestamp,")
            for i in range(SUBCARRIER_NUM):
                self.csv_file.write(f"subcarrier{i},")
            self.csv_file.write("\n")
        else:
            self.csv_file = None
        
        # プロット用のデータ配列を初期化
        self.amplitude_history = np.zeros((PLOT_LEN, SUBCARRIER_NUM))
        self.timestamp_history = np.zeros(PLOT_LEN)
        
        # プロット設定
        plt.style.use('ggplot')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.fig.tight_layout(pad=3.0)
        
        # 上段グラフ: 時系列でのCSI振幅（または位相）
        self.ax1.set_xlim(0, PLOT_LEN)
        if self.mode == 'amplitude':
            self.ax1.set_ylim(0, 1)  # 振幅の場合
            self.ax1.set_title('CSI振幅 - 時系列')
            self.ax1.set_ylabel('振幅')
        else:
            self.ax1.set_ylim(-np.pi, np.pi)  # 位相の場合
            self.ax1.set_title('CSI位相 - 時系列')
            self.ax1.set_ylabel('位相 (rad)')
        self.ax1.set_xlabel('サンプル')
        self.ax1.grid(True)
        
        # サブキャリアごとの線をプロット
        self.lines = []
        for i in range(SUBCARRIER_NUM):
            line, = self.ax1.plot([], [], lw=1, label=f'SC {i}' if i % 16 == 0 else "")
            self.lines.append(line)
        
        # 凡例
        legend_elements = [Line2D([0], [0], color='black', lw=1, label='サブキャリア')]
        self.ax1.legend(handles=legend_elements, loc='upper right')
        
        # 下段グラフ: ヒートマップ
        self.heatmap = self.ax2.imshow(
            self.amplitude_history.T,  # 転置して表示
            aspect='auto',
            cmap='viridis',
            interpolation='nearest',
            origin='lower',
            vmin=0 if self.mode == 'amplitude' else -np.pi,
            vmax=1 if self.mode == 'amplitude' else np.pi
        )
        
        if self.mode == 'amplitude':
            self.ax2.set_title('CSI振幅 - ヒートマップ')
            self.cbar_label = '振幅'
        else:
            self.ax2.set_title('CSI位相 - ヒートマップ')
            self.cbar_label = '位相 (rad)'
        
        self.ax2.set_xlabel('サンプル')
        self.ax2.set_ylabel('サブキャリア')
        
        # カラーバー
        self.cbar = self.fig.colorbar(self.heatmap, ax=self.ax2)
        self.cbar.set_label(self.cbar_label)
        
        # パケット情報表示用のテキスト
        self.info_text = self.fig.text(0.5, 0.01, '', ha='center')
    
    def start_animation(self):
        # アニメーションの作成と保持
        self.ani = FuncAnimation(
            self.fig, 
            self.update_plot, 
            interval=100, 
            cache_frame_data=False,
            blit=True
        )
        return self.ani
    
    def update_plot(self, frame):
        global running
        
        # バッファからデータを取得
        with data_lock:
            buffer_data = list(self.csi_buffer)
        
        if not buffer_data:
            return self.lines + [self.heatmap]
        
        # 最新のCSIデータを処理
        latest_data = buffer_data[-1]
        csi_complex = latest_data['csi']
        
        # CSIデータの振幅または位相を計算
        if self.mode == 'amplitude':
            csi_values = np.abs(csi_complex)
            # 0-1に正規化
            max_val = np.max(csi_values) if np.max(csi_values) > 0 else 1
            csi_values = csi_values / max_val
        else:
            csi_values = np.angle(csi_complex)
        
        # 履歴データを更新
        self.amplitude_history = np.roll(self.amplitude_history, -1, axis=0)
        self.amplitude_history[-1, :] = csi_values[:SUBCARRIER_NUM]
        
        self.timestamp_history = np.roll(self.timestamp_history, -1)
        self.timestamp_history[-1] = latest_data['timestamp']
        
        # プロットを更新
        x = np.arange(PLOT_LEN)
        for i, line in enumerate(self.lines):
            if i < SUBCARRIER_NUM:
                line.set_data(x, self.amplitude_history[:, i])
        
        # ヒートマップを更新
        self.heatmap.set_array(self.amplitude_history.T)
        
        # 情報テキストを更新
        self.info_text.set_text(f'取得パケット数: {len(buffer_data)}')
        
        # データを保存
        if self.csv_file:
            timestamp_str = datetime.fromtimestamp(latest_data['timestamp']).strftime("%Y-%m-%d %H:%M:%S.%f")
            self.csv_file.write(f"{timestamp_str},")
            for val in csi_values[:SUBCARRIER_NUM]:
                self.csv_file.write(f"{val},")
            self.csv_file.write("\n")
            self.csv_file.flush()
        
        return self.lines + [self.heatmap]
    
    def close(self):
        plt.close(self.fig)
        if self.csv_file:
            self.csv_file.close()

def signal_handler(sig, frame):
    global running
    print('終了します...')
    running = False
    plt.close('all')

def main():
    # 日本語フォントの設定
    has_japanese_font = setup_japanese_fonts()
    if not has_japanese_font:
        print("警告: 日本語フォントが見つかりません。日本語の表示が正しく行われない可能性があります。")
        print("日本語フォントをインストールするには次のコマンドを実行してください:")
        print("sudo apt-get update && sudo apt-get install fonts-ipafont-gothic fonts-ipafont-mincho")
    
    # コマンドライン引数
    parser = argparse.ArgumentParser(description='nexcsiを使用したリアルタイムCSIプロットツール')
    parser.add_argument('-i', '--interface', type=str, required=True,
                        help='CSIデータを取得するネットワークインターフェース名 (例: wlan0)')
    parser.add_argument('-m', '--mac', type=str, default=None,
                        help='CSIデータを取得する対象のMACアドレス (例: 00:11:22:33:44:55)')
    parser.add_argument('-s', '--save-dir', type=str, default=None,
                        help='CSIデータを保存するディレクトリ')
    parser.add_argument('-p', '--phase', action='store_true',
                        help='振幅の代わりに位相をプロットする')
    
    args = parser.parse_args()
    
    # 信号ハンドラ設定
    signal.signal(signal.SIGINT, signal_handler)
    
    # CSIキャプチャスレッドの開始
    csi_thread = CSICapture(args.interface, args.mac, csi_buffer)
    csi_thread.start()
    
    # プロットの設定と開始
    try:
        mode = 'phase' if args.phase else 'amplitude'
        plot = CSIRealTimePlot(csi_buffer, args.save_dir, mode)
        
        # アニメーションを開始し、グローバル変数に保持して参照を保つ
        global animation
        animation = plot.start_animation()
        
        plt.show(block=True)
    except Exception as e:
        print(f"プロットエラー: {e}")
    finally:
        global running
        running = False
        if csi_thread.is_alive():
            csi_thread.join(timeout=2)

if __name__ == "__main__":
    # グローバル変数として参照を保持するためにanimationを定義
    animation = None
    main()