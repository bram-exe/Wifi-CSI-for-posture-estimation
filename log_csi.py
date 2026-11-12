import serial
import csv
import json
import time
import argparse
import os

#port settings
#PORT = '/dev/cu.usbmodem1101'
BAUDRATE = 921600  
TIMEOUT = 1     

parser = argparse.ArgumentParser()
parser.add_argument("--label", type=str, required=True, help= "sitting, standing, waving")
parser.add_argument("--subject", type=str, required=True, choices=["Bram", "Sarah"])
parser.add_argument("--session", required = True, type=int)
parser.add_argument("--duration", type = int, default=60, help= "enter number of seconds to record")
parser.add_argument("--port", default='/dev/cu.usbmodem1101', type=str)
args = parser.parse_args() 

os.makedirs("data", exist_ok=True)
filename = f"data/s{args.session}_{args.subject}_{args.label}_{time.strftime('%Y%m%d_%H%M%S')}.csv"

try:
    # Open the serial port
    with serial.Serial(args.port, BAUDRATE, timeout=TIMEOUT) as ser, open(filename, 'w', newline='') as f:
        print(f"Connected to {args.port}. Recording '{args.label}' for {args.duration}s")

        writer = csv.writer(f)
        writer.writerow(["time", "seq", "rssi", "label", "subject", "session", "csi"])
        #Clear the buffer of old data before reading
        ser.reset_input_buffer() 

        good = 0
        bad = 0
        missed = 0
        last_seq = None
        start = time.time()
        last_report = start
        
        buf = b""   
        while True:
            # Read a line up to the newline character (\n)
            #line_bytes = ser.readline()
            if time.time() - start >= args.duration:
                break
            buf += ser.read(ser.in_waiting or 1)
            *lines, buf = buf.split(b"\n")
            
            
            # Check if we actually received data (pyserial returns empty bytes on timeout)
            for line_bytes in lines:
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

                    writer.writerow([time.time(), seq, rssi, args.label, args.subject, args.session, fields[24]])

                    if last_seq is not None and seq > last_seq + 1:
                        missed += seq - last_seq -1 
                    last_seq = seq
                    if time.time() - last_report >= 5:
                        rate = (good/ (time.time() - start))
                        print(f"good={good}, bad={bad}, missed={missed}, rate:{rate:.2f} Hz")
                        last_report = time.time()

                    #print(seq, rssi, len(csi))
        elapsed = time.time() - start
        print(f"DONE. good={good}, bad={bad}, missed={missed}, rate:{good/elapsed:.2f} Hz -> {filename}")
                
except serial.SerialException as e:
    print(f"Error opening or communicating on port {args.port}: {e}")
except KeyboardInterrupt:
    #os.remove(filename)
    if os.path.exists(filename):
        os.remove(filename)
    print("\nProgram stopped by user.")