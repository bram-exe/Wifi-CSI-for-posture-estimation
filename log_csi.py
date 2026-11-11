import serial
import csv
import json
import time
import argparse

#port settings
PORT = '/dev/cu.usbmodem1101'
BAUDRATE = 921600  
TIMEOUT = 1     

parser = argparse.ArgumentParser()
parser.add_argument("--label", type=str, required=True, help= "sitting, standing, waving")
parser.add_argument("--subject", type=str, choices=["Bram", "Sarah"])
parser.add_argument("--session", type=int)
parser.add_argument("--duration", type = int, default=60, help= "enter number of seconds to record")
parser.add_argument("--port", default='/dev/cu.usbmodem1101', type=str)
args = parser.parse_args() 

try:
    # Open the serial port
    with serial.Serial(args.port, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Connected to {args.port}. Recoring '{args.label}' for {args.duration}s")
        
        #Clear the buffer of old data before reading
        ser.reset_input_buffer() 

        good = 0
        bad = 0
        missed = 0
        last_seq = None
        start = time.time()
        last_report = start
        

        while True:
            # Read a line up to the newline character (\n)
            line_bytes = ser.readline()
            if time.time() - start >= args.duration:
                break
            
            # Check if we actually received data (pyserial returns empty bytes on timeout)
            if line_bytes:
                # Decode bytes to a string and strip whitespace/newlines (\r\n)
                line_string = line_bytes.decode('utf-8', errors='ignore').strip()
                if line_string.startswith('CSI_DATA'):
                    #print(line_string)
                    #fields = next(csv.reader([line_string]))
                    #print(len(fields))
                    #print(fields[:10])
                    try:
                        fields = next(csv.reader([line_string]))
                        if len(fields) != 25:
                            raise ValueError("wrong field count")
                        seq = int(fields[1])
                        rssi = int(fields[3])
                        csi = json.loads(fields[24])
                        if len(csi) != 384:
                            raise ValueError("wrong CSI length")
                    except (ValueError, json.JSONDecodeError):
                        bad +=1
                        continue 
                    good+=1
                    if last_seq is not None and seq > last_seq + 1:
                        missed += seq - last_seq -1 
                    last_seq = seq
                    if time.time() - last_report >= 5:
                        rate = (good/ (time.time() - start))
                        print(f"good={good}, bad={bad}, missed={missed}, rate:{rate:.2f} Hz")
                        last_report = time.time()

                    #print(seq, rssi, len(csi))
                
except serial.SerialException as e:
    print(f"Error opening or communicating on port {PORT}: {e}")
except KeyboardInterrupt:
    print("\nProgram stopped by user.")