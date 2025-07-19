from datetime import datetime
import sys

class Logger:
    def __init__(self, filename="app.log"):
        self.filename = filename
        self.log_file = open(self.filename, "a", buffering=1)  # line-buffered
        self.stdout = sys.stdout

    def log(self, where, what):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{timestamp} - [{where}] {what}"
        
        # Write to stdout
        print(message, file=self.stdout)
        
        # Write to log file
        self.log_file.write(message + "\n")

    def close(self):
        self.log_file.close()

    def __del__(self):
        self.close()  # Ensure file is closed if Logger is destroyed
