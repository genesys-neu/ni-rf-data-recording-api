#/bin/bash

# Set the MTU size of all Eth ports connected to USRPs to 9000 to get maximum sampling rate
# ifconfig enp5s0 mtu 9000 up
# ifconfig enp3s0 mtu 9000 up
# ifconfig enp10s0f1 mtu 9000 up

# resize the buffer to be more efficient. Use max buffer size provided by the system
sysctl -w net.core.rmem_max=24912805
sysctl -w net.core.wmem_max=24912805

# run some benchmarks (NOTE: change IPs accordingly"
#python3 /usr/local/lib/uhd/examples/python/benchmark_rate.py --args="type=x300,addr=192.168.50.2,num_recv_frames=1000" --rx_rate 100e6 --channels 0 --rx_channels 0
#python3 /usr/local/lib/uhd/examples/python/benchmark_rate.py --args="type=x300,addr=192.168.60.2,num_recv_frames=1000" --rx_rate 100e6 --channels 0 --rx_channels 0
