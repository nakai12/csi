from nexcsi import decoder
import numpy as np
import matplotlib.pyplot as plt
from judges_ import isStanding

device = 'raspberrypi'

sample = decoder(device).read_pcap('pcaps/009.pcap')
data = decoder(device).unpack(sample['csi'])
data_amp = np.abs(data)

ans = isStanding(data_amp, threshold_ratio=1.15)

print(ans)