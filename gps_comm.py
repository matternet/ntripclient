import os
import serial
import signal
import atexit
import subprocess

ntripclient = ['./ntripclient', '-s', 'ntrip.polaris.pointonenav.com', '-m', 'polaris', '-r', '2101', '-u', 'TESTRPI', '-p', '9224c400a9ffaa89', '-n', '$GNGGA,232725.00,3728.75130,N,12213.69507,W,1,12,0.93,-5.1,M,-30.0,M,,*5D', '-D', '/dev/ttyACM0']
# Start ./test in the background
process = subprocess.Popen(ntripclient)

print("Background process started with PID", process.pid)

# Register a function to kill the background process when Python quits
def cleanup():
    print("Terminating background process...")
    process.terminate()  # Gracefully terminate
    try:
        process.wait(timeout=5)  # Wait for the process to terminate
    except subprocess.TimeoutExpired:
        print("Force killing the background process...")
        os.kill(process.pid, signal.SIGKILL)  # Force kill if it doesn't terminate

def parse_gga(line):
    parts = line.split(',')
    message_id = parts[0]
    time = parts[1]
    latitude = parts[2]
    lat_direction = parts[3]
    longitude = parts[4]
    lon_direction = parts[5]
    fix_quality = parts[6]
    num_satellites = parts[7]
    hdop = parts[8]
    altitude = parts[9]
    altitude_units = parts[10]
    geoid_seperation = parts[11]
    diff_correction_age = parts[12]
    diff_station_id = parts[13]
    checksum = parts[14]
    if fix_quality == '0':
        fix_quality = 'No Fix'
    elif fix_quality == '1':
        fix_quality = 'Autonomous'
    elif fix_quality == '2':
        fix_quality = 'Differential'
    elif fix_quality == '4':
        fix_quality = 'RTK Fixed'
    elif fix_quality == '5':
        fix_quality = 'RTK Float'
    else:
        fix_quality = 'Unknown'

    gga = {
        'message_id': message_id,
        'time': time,
        'latitude': latitude,
        'lat_direction': lat_direction,
        'longitude': longitude,
        'lon_direction': lon_direction,
        'fix_quality': fix_quality,
        'num_satellites': num_satellites,
        'hdop': hdop,
        'altitude': altitude,
        'altitude_units': altitude_units,
        'geoid_seperation': geoid_seperation,
        'diff_correction_age': diff_correction_age,
        'diff_station_id': diff_station_id,
        'checksum': checksum
    }

    return gga



def read_gngga_lines(port, baudrate=9600, timeout=1):
    """
    Reads data from the specified serial port and prints lines that start with $GNGGA.

    Args:
        port (str): The name of the serial port (e.g., '/dev/ttyUSB0' or 'COM3' on Windows).
        baudrate (int): The baud rate for the serial communication (default is 9600).
        timeout (float): The timeout for reading from the serial port (default is 1 second).
    """

# Different messages
# {'$GNGLL', '$GQGSV', '$GLGSV', '$GNGSA', '$GPGSV', '$GNVTG', '$GBGSV', '$GNGGA', '$GAGSV', '$GNRMC'}
# RTK Fix: 4, RTK Float: 5, RTK None: 0

    try:
        # Open the serial port
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Listening on {port} at {baudrate} baud...")
            unique_starts = set()
            while True:
                # Read a line from the serial port
                line = ser.readline().decode('ascii', errors='ignore').strip()
                # Print the line if it starts with $GNGGA
                if line.startswith('$GNGGA') or line.startswith('$GPGGA') or line.startswith('$GAGGA'):
                    gga = parse_gga(line)
                    print(gga['latitude'], gga['longitude'], gga['altitude'])
    except serial.SerialException as e:
        print(f"Error: {e}")


# Register cleanup to be called on exit
atexit.register(cleanup)

try:
    while True:
        read_gngga_lines(port='/dev/ttyACM0')
except KeyboardInterrupt:
    print("Exiting program...")



