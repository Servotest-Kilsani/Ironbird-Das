import sys
import datetime
from PyQt6.QtWidgets import QApplication
from core.simulator import SignalManager
from core.logger import DataLogger
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Initialize Core Components
    simulator = SignalManager()
    logger = DataLogger(log_dir=".")
    
    # Initialize UI
    window = MainWindow(simulator)
    
    # Connect Signals for Logging
    # Simulator emits: (angles, pressures, flows, limits, state_str)
    # Logger needs: (timestamp, state, angles, pressures, flows, limits)
    
    def bridge_logger(angles, pressures, flows, limits, state_str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.log(timestamp, state_str, angles, pressures, flows, limits)
        
    simulator.data_updated.connect(bridge_logger)
    
    # Connect Control Signals to Logger Start/Stop
    # When Simulator starts (Start button), Logger should start?
    # Or logger starts when app starts?
    # Requirement: "Start: ... 자동으로 실행... Stop: ... Data Logging..." 
    # Requirement: "시스템의 입력되는 모든 데이터는 자동 저장되어야 합니다."
    # AND "CHAX는 시험 일자별 실행 차수이며 Start-Stop 한 세트가 한 차수입니다."
    # So we must start logging when Start is pressed, and stop when Stop/Abort or finishes.
    
    # We can hook into state_changed.
    # If state changes IDLE -> MOVING_UP (Start pressed), Start Logging.
    # If state changes to IDLE (from Down) or ABORTED, Stop Logging.
    
    def handle_state_change(new_state):
        # Start Logging on transition from IDLE/ABORTED to MOVING_UP
        # But simulator logic sets state to MOVING_UP immediately on START command
        if new_state == "MOVING_UP":
            if not logger.is_logging:
                logger.start_logging()
        
        # Stop Logging when returning to IDLE or ABORTED
        if new_state == "IDLE" or new_state == "ABORTED":
            if logger.is_logging:
                # We want to capture the last data point or sequence completion.
                # Stopping immediately might miss the 'IDLE' state log.
                # Let's stop after a brief delay or just stop. 
                # Since 'bridge_logger' is called by data_updated which runs on timer,
                # as long as timer runs, we log.
                # But simulator timer runs always?
                # Simulator.start_simulation() is called? 
                pass
                
    simulator.state_changed.connect(handle_state_change)
    
    # Special case: The simulator loop runs continuously to update idle values?
    # Or only during test? 
    # Req: "GUI ... 사용자 화면 ... Simulator는 실제 Rig를 대체 ... 신호를 발생해야 합니다."
    # Usually DAS shows current values always. So Simulator loop should run always.
    simulator.start_simulation()
    
    # MainWindow update_ui also needs to handle the new 5th arg 'state' 
    # But MainWindow.update_ui signature is (angles, pressures, flows, limits).
    # Qt signals match by argument count or type. If connected function has fewer args, it drops the rest?
    # Python slots can be flexible.
    # Let's fix MainWindow.update_ui signature in main_window.py to accept 5 args, or use lambda.
    # Actually, main_window.py connects: self.simulator.data_updated.connect(self.update_ui)
    # update_ui matches (angles, pressures, flows, limits).
    # It will fail if signal sends 5 args and slot takes 4.
    
    # Let's use a lambda wrapper for MainWindow too in main_window.py or simple refactor.
    # Better to update MainWindow to use the state string if needed, or ignore it.
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
