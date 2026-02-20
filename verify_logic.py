import sys
import os
import datetime
import time
from PyQt6.QtCore import QCoreApplication, QTimer
from core.simulator import SignalManager
from core.logger import DataLogger

def verify():
    app = QCoreApplication(sys.argv)
    
    print(f"[{datetime.datetime.now()}] Setup...")
    
    sim = SignalManager()
    logger = DataLogger(log_dir=".")
    
    # Bridge for logging
    def bridge_logger(angles, pressures, flows, limits, state_str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.log(timestamp, state_str, angles, pressures, flows, limits)
    sim.data_updated.connect(bridge_logger)
    
    # State change handler
    def on_state_change(new_state):
        print(f"[{datetime.datetime.now()}] State Changed: {new_state}")
        if new_state == "MOVING_UP":
            if not logger.is_logging:
                logger.start_logging()
        elif new_state == "IDLE" or new_state == "ABORTED":
            if logger.is_logging:
                # Give a moment to log the last state then stop?
                # For this test, we just stop immediately as per logic
                pass
                
    sim.state_changed.connect(on_state_change)
    
    # Start Simulation Loop
    sim.start_simulation()
    
    # Test Sequence
    # 1. Wait 1s
    # 2. Trigger START
    # 3. Wait for full sequence (approx 15-20s)
    # 4. Quit
    
    QTimer.singleShot(1000, lambda: (print(f"[{datetime.datetime.now()}] COMMAND: START"), sim.set_command('START')))
    
    # Stop app after 25s
    QTimer.singleShot(25000, app.quit)
    
    print(f"[{datetime.datetime.now()}] Running verification...")
    app.exec()
    
    # After exit, stop logger to save file
    if logger.is_logging:
        logger.stop_logging()
        
    print(f"[{datetime.datetime.now()}] Verification Finished.")

if __name__ == "__main__":
    verify()
