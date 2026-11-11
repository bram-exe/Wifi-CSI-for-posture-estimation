import serial

#port settings
PORT = '/dev/cu.usbmodem1101'
BAUDRATE = 921600  
TIMEOUT = 1     

try:
    # Open the serial port
    with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        print(f"Connected to {PORT} successfully.")
        
        #Clear the buffer of old data before reading
        ser.reset_input_buffer() 
        
        while True:
            # Read a line up to the newline character (\n)
            line_bytes = ser.readline()
            
            # Check if we actually received data (pyserial returns empty bytes on timeout)
            if line_bytes:
                # Decode bytes to a string and strip whitespace/newlines (\r\n)
                line_string = line_bytes.decode('utf-8', errors='ignore').strip()
                if line_string.startswith('CSI_DATA'):
                    print(line_string)
                
except serial.SerialException as e:
    print(f"Error opening or communicating on port {PORT}: {e}")
except KeyboardInterrupt:
    print("\nProgram stopped by user.")