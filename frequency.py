import numpy as np
from nexcsi import decoder
from scipy.fft import fft

device = "raspberrypi"

samples = decoder(device).read_pcap('pcaps/205.pcap')  # ファイル名は適宜変更
csi_data = decoder(device).unpack(samples['csi'])

amplitude = np.abs(csi_data)

def ispresent(csi_amp, sample_rate=10, freq_band = (0.1,2.0), threshold=10000):
    fft_result = np.abs(fft(csi_amp, axis=0))
    freq_axis = np.fft.fftfreq(csi_amp.shape[0], 1/sample_rate)

    energy = 0
    for i, freq in enumerate(freq_axis):
        if freq_band[0] <= abs(freq) <= freq_band[1]:
            energy += np.mean(fft_result[i])

    print(energy)
    return energy > threshold

energy = ispresent(amplitude, sample_rate=10, freq_band=(0.1, 2.0), threshold=10000)
print(energy)