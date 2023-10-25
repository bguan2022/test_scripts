# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import argparse
import logging
import sys
import time

import streamer_demo_hal


class FPGA_tx_Streamer:
    def __init__(self):
        self.buf = streamer_demo_hal.TxBufInterface(streamer_demo_hal.EgressBufOffset)

    def __del__(self):
        self.buf.disable_buffer()

    def transmit_text(self, tx_string):
        size = len(tx_string)
        for i in range(0, size):
            self.buf.bufU8[self.buf.current_data_pointer_u8 + i] = ord(tx_string[i])

        self.buf.send_packet(size)

    def transmit_file(self, filename):
        target_packet_size = 512
        with open(filename, "rb") as f:
            chunk = f.read(target_packet_size)
            size = len(chunk)
            while size > 0:
                start = self.buf.current_data_pointer_u8
                stop = self.buf.current_data_pointer_u8 + size
                if stop > self.buf.bufSize:
                    stop = stop - self.buf.bufSize
                    self.buf.bufU8[start : self.buf.bufSize] = chunk[
                        0 : (self.buf.bufSize - start)
                    ]
                    self.buf.bufU8[0:stop] = chunk[(self.buf.bufSize - start) : size]
                else:
                    self.buf.bufU8[start:stop] = chunk

                self.buf.send_packet(size)
                chunk = f.read(target_packet_size)
                size = len(chunk)

        self.buf.flush_tx_buffer()
        print("########################################################")
        print("Current Egress HW Address = ", hex(self.buf.read_local_reg(5)))
        print("Remaining Egress Credit = ", self.buf.read_local_reg(6))
        print("Number of Egress Packets = ", self.buf.read_local_reg(16))
        print("Header Mismatch count = ", self.buf.read_local_reg(17))
        print("########################################################")


class FPGA_rx_Streamer:
    def __init__(self):
        self.buf = streamer_demo_hal.RxBufInterface(streamer_demo_hal.IngressBufOffset)

    def __del__(self):
        self.buf.disable_buffer()

    def receive_text(self, timeout, size):
        self.done = 0
        received_bytes = 0
        passed_time = 0
        time_of_last_packet = time.time()
        while self.done == 0:
            rx_bytes = self.buf.check_for_received_packet()
            if rx_bytes > 0:
                my_string = ""
                for i in range(0, rx_bytes):
                    my_string = my_string + chr(
                        self.buf.bufU8[self.buf.current_data_pointer_u8 + i]
                    )

                print("Packet #", self.buf.packet_id, " received text: ", my_string)
                self.buf.dequeue_packet()
                time_of_last_packet = time.time()

            passed_time = time.time() - time_of_last_packet
            received_bytes = received_bytes + rx_bytes
            if (timeout > 0) & (passed_time > timeout):
                self.done = 1
                print("reached timout")
            if (size > 0) & (received_bytes >= size):
                self.done = 1
                print("reached target size")

        self.buf.flush_tx_buffer()
        print("########################################################")
        print("Current Ingress Address = ", self.buf.read_local_reg(5))
        print("Remaining Ingress Credit = ", self.buf.read_local_reg(6))
        print("Number of Ingress Packets = ", self.buf.read_local_reg(16))
        print("########################################################")

    def receive_file(self, timeout, size, filename):
        with open(filename, "wb") as f:
            self.done = 0
            received_bytes = 0
            passed_time = 0
            time_of_last_packet = time.time()
            while self.done == 0:
                rx_bytes = self.buf.check_for_received_packet()
                if rx_bytes > 0:
                    start = self.buf.current_data_pointer_u8
                    end = self.buf.current_data_pointer_u8 + rx_bytes
                    if end > self.buf.bufSize:
                        end = end - self.buf.bufSize
                        # handle the data wraps around the end of buffer
                        f.write(bytes(self.buf.bufU8[start : self.buf.bufSize]))
                        f.write(bytes(self.buf.bufU8[0:end]))
                    else:
                        f.write(bytes(self.buf.bufU8[start:end]))

                    self.buf.dequeue_packet()
                    time_of_last_packet = time.time()

                passed_time = time.time() - time_of_last_packet
                received_bytes = received_bytes + rx_bytes
                if (timeout > 0) & (passed_time > timeout):
                    self.done = 1
                    print("reached timout")
                if (size > 0) & (received_bytes >= size):
                    self.done = 1
                    print("reached target size")

            print("########################################################")
            print("Current Ingress Address = ", self.buf.read_local_reg(5))
            print("Remaining Ingress Credit = ", self.buf.read_local_reg(6))
            print("Number of Ingress Packets = ", self.buf.read_local_reg(16))
            print("########################################################")

def main():
    num_byte = 20
    latency_test(num_byte)

def latency_test(num_byte):
    print("start latency test for loopback test")
    some_junks = num_byte*"AB"
    tx_obj = FPGA_tx_Streamer()
    rx_obj = FPGA_rx_Streamer()
    target_timeout = 60

    start_time = time.time()
    tx_obj.transmit_text(some_junks)
    rx_obj.receive_text(target_timeout, num_byte)
    time_diff = time.time() - start_timei # in ns
    tp = num_byte*8 / (time_diff/1E9)   
    print("latency for loopback test: ", time_diff, "total byte sent: " num_byte, "throuhgput (Gb/s): " , tp)

    


if __name__ == "__main__":
    main()
