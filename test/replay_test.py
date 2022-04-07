import sys
import signal
import time
from timeit import default_timer as timer
import argparse
import numpy as np
import uhd
try:
    import tqdm
    HAVE_TQDM = True
except ImportError:
    HAVE_TQDM = False

time_to_exit = False

def signal_handler(sig, frame):
    global time_to_exit
    print("Exiting . . .")
    time_to_exit = True

def run_replay_loopback(graph,
                        replay,
                        ports_to_test=None,
                        num_bytes=None,
                        pkt_size_bytes=None,
                        num_tests=1,
                        use_tqdm=None):
    """
    Run a replay block loopback test.
    """
    use_tqdm = use_tqdm if use_tqdm is not None else HAVE_TQDM
    if use_tqdm:
        assert HAVE_TQDM
    ## Set up which ports to test
    num_replay_ports = replay.get_num_input_ports()
    print(f"Number of available replay ports: {num_replay_ports}")
    ports_to_test = ports_to_test or range(num_replay_ports)
    num_ports = len(ports_to_test)
    print(f"Testing ports: {','.join([str(x) for x in ports_to_test])}")
    assert all([port in range(num_replay_ports) for port in ports_to_test])
    ## Figure out how many bytes to send
    mem_size = replay.get_mem_size()
    mem_stride = mem_size // num_ports
    print(f"Total memory size: {mem_size // 1024 // 1024} MiB")
    # Set the number of bytes to test
    num_bytes = int(num_bytes or mem_stride)
    print(f"Record/playback size: {num_bytes // 1024 // 1024} MiB")
    if num_bytes > mem_size // num_ports:
        num_bytes = mem_size // num_ports
        print(f"WARNING: Exceeds allocated space per port! "
              f"Reducing to {num_bytes // 1024 // 1024} MiB")
    for port in ports_to_test:
        replay.set_play_type("sc16", 0)
        replay.set_record_type("sc16", 0)
        if pkt_size_bytes is not None:
            replay.set_max_items_per_packet(pkt_size_bytes // 4, port)
    print("Setting up graph...")
    stream_args = uhd.usrp.StreamArgs("sc16", "sc16")
    tx_streamer = graph.create_tx_streamer(num_ports, stream_args)
    rx_streamer = graph.create_rx_streamer(num_ports, stream_args)
    for stream_idx, replay_port_idx in enumerate(ports_to_test):
        graph.connect(tx_streamer, stream_idx, replay.get_unique_id(), replay_port_idx)
        graph.connect(replay.get_unique_id(), replay_port_idx, rx_streamer, stream_idx)
    graph.commit()
    pkt_size_words = pkt_size_bytes // 4 \
                     if pkt_size_bytes is not None \
                     else tx_streamer.get_max_num_samps()
    if pkt_size_words > tx_streamer.get_max_num_samps():
        print(f"WARNING: Requested packet size ({pkt_size_words}) words exceeds "
              f"maximum value of {tx_streamer.get_max_num_samps()} words. "
              "Coercing down.")
        pkt_size_words = tx_streamer.get_max_num_samps()
    print(f"Packet size: {pkt_size_words} words/packet")
    tx_md = uhd.types.TXMetadata()

    # Create array of incrementing 32-bit numbers, and a buffer for RX data
    num_words = num_bytes // 4
    input_data = np.tile(np.arange(num_words, dtype="uint32"), (num_ports, 1))
    output_data = np.zeros((num_ports, num_words), dtype=np.uint32)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to stop streaming')


    for test_idx in range(num_tests):
        if num_tests > 1:
            print("------------------------------------------------------")
            print(f"Running test {test_idx}... ")
            print("------------------------------------------------------")
        for port in ports_to_test:
            # Start recording in the replay block
            replay.record(port * mem_stride, num_bytes, port)
        # Stream the data to record
        print("Recording data . . .")
        if use_tqdm:
            num_tx = 0
            start_word = 0
            end_word = pkt_size_words
            num_pkts = int(np.ceil(num_words / pkt_size_words))
            with tqdm.tqdm(total=num_bytes*num_ports,
                           unit_scale=True, unit="byte") as pbar:
                for _ in range(num_pkts):
                    num_tx += tx_streamer.send(
                        input_data[:, start_word:end_word], tx_md, 2.0)
                    start_word += pkt_size_words
                    end_word = min(end_word + pkt_size_words, num_words)
                    pbar.update(pkt_size_words * 4 * num_ports)
        else:
            num_tx = tx_streamer.send(input_data, tx_md, 10.0)
        if num_tx != num_words:
            print(f"ERROR: Only sent 0x{num_tx:X} words instead of 0x{num_words:X}")
            return False
        # Wait until all the data is received
        while any((replay.get_record_fullness(port) < num_bytes
                   for port in ports_to_test)):
            time.sleep(0.100)
            if time_to_exit:
                return True

        #input("Press Enter to start playback:")
        print("Starting playback . . .")
        for port in ports_to_test:
            replay.play(
                port * mem_stride, num_bytes, port, uhd.types.TimeSpec(0.0), False)

        # Receive the data
        rx_md = uhd.types.RXMetadata()
        start = timer()
        if use_tqdm:
            num_rx = 0
            output_buf = np.zeros((num_ports, pkt_size_words), dtype=np.uint32)
            with tqdm.tqdm(total=num_bytes*num_ports,
                           unit_scale=True, unit="byte") as pbar:
                while num_rx < num_words:
                    end_word = min(num_rx + pkt_size_words, num_words)
                    num_rx_i = rx_streamer.recv(output_buf, rx_md, 1.0)
                    if rx_md.error_code != uhd.types.RXMetadataErrorCode.none:
                        print(rx_md.strerror())
                        break
                    pbar.update(num_rx_i * 4 * num_ports)
                    output_data[:, num_rx:end_word] = output_buf[:, 0:num_rx_i]
                    num_rx += num_rx_i
        else:
            num_rx = rx_streamer.recv(output_data, rx_md, 15.0)
        elapsed = timer() - start

        # Report the results of playback
        print("{:0.0f} MS/s, {:0.1f} MB/s, {:0.1f} Gbps".format(
            num_rx * num_ports / elapsed / 1.0e6,
            num_rx*4.0 * num_ports / elapsed / 1e6,
            num_rx*32 * num_ports / elapsed / 1.0e9))
        if num_rx != num_words:
            print(f"\nERROR: Only received 0x{num_rx*4:X} out of 0x{num_bytes:X} bytes "
                  f"({num_rx*4.0 / num_bytes * 100.0:0.1f}%)")
            if num_rx:
                print(f"Last value received was (32-bit): 0x{output_data[num_rx-1]:08X}")
            return False

        # Check the data for errors
        passed = np.array_equal(input_data, output_data)
        if passed:
            print("Result: PASSED")
        else:
            print("Result: * * * * FAILED * * * * ")
            error_count = 0
            for chan in range(num_ports):
                for i in range(num_words):
                    if input_data[chan][i] != output_data[chan][i]:
                        error_count += 1
                        print(f"Found error on sample {i}, chan {chan}. "
                              f"Expected 0x{input_data[chan][i]:X}, "
                              f"received 0x{output_data[chan][i]:X}")
                        if error_count > 10:
                            break
            return False
        if time_to_exit:
            break
    return True

def parse_args():
    """
    Return parsed command line args
    """
    parser = argparse.ArgumentParser(
        description="Tests the Replay block by recording to the USRP's memory and "
                    "playing it back to verify it.")

    parser.add_argument("--args", "-a", type=str, default="",
                        help="Device args to use when connecting to the USRP.")
    parser.add_argument("--ports", "-p", type=int, nargs='+',
                        help="List of ports to test. Defaults to all ports.")
    parser.add_argument("--size", "-s", type=float,
                        help="Size in bytes of the buffer to replay. "
                             "Defaults to the size of the device's memory.")
    parser.add_argument("--block", "-b", type=str, default="0/Replay#0",
                        help="Replay block to test. Defaults to \"0/Replay#0\".")
    parser.add_argument("--count", "-c", type=int, default=1,
                        help="Number of times to run the test for each port. "
                             "Defaults to 1. Use 0 to run until stopped by Ctrl+C.")
    parser.add_argument("--pkt-size", "-k", type=int, default=None,
                        help="Playback packet size in bytes. "
                             "Defaults to maximum packet size for this transport")
    args = parser.parse_args()
    return args

def main():
    """
    Run loopback test.
    """
    args = parse_args()
    graph = uhd.rfnoc.RfnocGraph(args.args)
    replay = uhd.rfnoc.ReplayBlockControl(graph.get_block(args.block))
    run_replay_loopback(
        graph, replay,
        args.ports, args.size, args.pkt_size, args.count,
        use_tqdm=True)

if __name__ == "__main__":
    sys.exit(not main())
