import enum
import time
import random
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class SystemState(enum.Enum):
    IDLE = 0            # Down Locked
    MOVING_UP = 1       # Going to Up
    UPLOCKED = 2        # Holding at Up
    MOVING_DOWN = 3     # Going to Down
    STOPPING = 4        # Emergency return to Down
    ABORTED = 5         # Immediate Stop

class SignalManager(QObject):
    # Signals to update GUI
    # angles: nose, main_lh, main_rh (0-90)
    # pressures: 10 channels
    # flows: 10 channels
    # limits: 6 channels
    # state: current system state string
    data_updated = pyqtSignal(list, list, list, list, str) 
    state_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.dt = 0.1  # 100ms
        self.noise_level = 0.05 # 5%
        
        # System State
        self.state = SystemState.IDLE
        self.state_timer = 0.0
        
        # Physical Values
        # Angles: 0 = Down, 90 = Up
        self.angles = [0.0, 0.0, 0.0] # Nose, MainLH, MainRH
        
        # Pressures (0-3000 psi)
        self.base_pressures = [1500.0] * 10
        self.pressures = [0.0] * 10
        
        # Flows (0-1 GPM)
        self.base_flows = [0.5] * 10
        self.flows = [0.0] * 10
        
        # Limit Switches: [Nose_Down, Nose_Up, MLH_Down, MLH_Up, MRH_Down, MRH_Up]
        self.limits = [True, False, True, False, True, False]
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        
    def start_simulation(self):
        self.timer.start(int(self.dt * 1000))
        
    def stop_simulation(self):
        self.timer.stop()
        
    def set_command(self, command):
        """
        External commands: 'START', 'STOP', 'ABORT'
        """
        if command == 'ABORT':
            self.state = SystemState.ABORTED
            self.state_changed.emit("ABORTED")
            # Immediate stop, no movement
            
        elif command == 'STOP':
            if self.state != SystemState.IDLE:
                self.state = SystemState.STOPPING
                self.state_timer = 0.0
                self.state_changed.emit("STOPPING")
                
        elif command == 'START':
            if self.state == SystemState.IDLE or self.state == SystemState.ABORTED:
                self.state = SystemState.MOVING_UP
                self.state_timer = 0.0
                self.state_changed.emit("MOVING_UP")
                # Release Down Locks
                self.limits[0] = False
                self.limits[2] = False
                self.limits[4] = False

    def update_loop(self):
        self.update_physics()
        self.update_logic()
        
        # Emit data
        self.data_updated.emit(self.angles, self.pressures, self.flows, self.limits, self.state.name)

    def update_physics(self):
        # Add noise to Pressure and Flow
        # Range: Pressure 0-3000, Flow 0-1
        # Noise is +/- 5% of range? Or current value? usually range or specific value.
        # User said: "각 물리량의 범위 내에서 ±5%의 노이즈" -> 5% of Full Scale usually.
        # Pressure FS = 3000, 5% = 150
        # Flow FS = 1, 5% = 0.05
        
        for i in range(10):
            p_noise = (random.random() - 0.5) * 2 * (3000 * self.noise_level)
            f_noise = (random.random() - 0.5) * 2 * (1.0 * self.noise_level)
            
            # Simple simulation: oscillate around base value
            self.pressures[i] = max(0, min(3000, self.base_pressures[i] + p_noise))
            self.flows[i] = max(0, min(1.0, self.base_flows[i] + f_noise))

    def update_logic(self):
        if self.state == SystemState.ABORTED:
            return

        self.state_timer += self.dt
        
        # Movement speed
        # 0 -> 90 degrees in 5 seconds = 18 deg/s
        angle_speed = 90.0 / 5.0 * self.dt 

        if self.state == SystemState.MOVING_UP:
            # Increase Angle
            finished = True
            for i in range(3):
                if self.angles[i] < 90.0:
                    self.angles[i] += angle_speed
                    if self.angles[i] >= 90.0:
                        self.angles[i] = 90.0
                    else:
                        finished = False
            
            # Check for Uplock condition (simulated 90 deg reached)
            if finished:
                self.state = SystemState.UPLOCKED
                self.state_timer = 0.0
                self.state_changed.emit("UPLOCKED")
                # Set Up Limits
                self.limits[1] = True
                self.limits[3] = True
                self.limits[5] = True
        
        elif self.state == SystemState.UPLOCKED:
            if self.state_timer >= 5.0:
                self.state = SystemState.MOVING_DOWN
                self.state_timer = 0.0
                self.state_changed.emit("MOVING_DOWN")
                # Release Up Limits
                self.limits[1] = False
                self.limits[3] = False
                self.limits[5] = False
                
        elif self.state == SystemState.MOVING_DOWN or self.state == SystemState.STOPPING:
            # Decrease Angle
            finished = True
            speed = angle_speed
            
            # If STOPPING, we might want to move faster or same speed? 
            # Req: "최대 10초 이내에 Down Lock". Normal down is 5s, so same speed is fine.
            
            for i in range(3):
                if self.angles[i] > 0.0:
                    self.angles[i] -= speed
                    if self.angles[i] <= 0.0:
                        self.angles[i] = 0.0
                    else:
                        finished = False
            
            if finished:
                self.state = SystemState.IDLE
                self.state_timer = 0.0
                self.state_changed.emit("IDLE")
                # Set Down Limits
                self.limits[0] = True
                self.limits[2] = True
                self.limits[4] = True
