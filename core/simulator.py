import enum
import time
import random
import numpy as np

class Event:
    def __init__(self):
        self._callbacks = []
    def connect(self, callback):
        self._callbacks.append(callback)
    def emit(self, *args, **kwargs):
        for cb in self._callbacks:
            cb(*args, **kwargs)

class SystemState(enum.Enum):
    IDLE = 0            # System at rest, gears are down
    MOVING_UP = 1       # Going to Up
    UPLOCKED = 2        # Holding at Up
    MOVING_DOWN = 3     # Going to Down
    DOWNLOCKED = 4      # Holding at Down
    STOPPING = 5        # Emergency return to Down
    ABORTED = 6         # Immediate Stop
    STOPPED = 7         # Paused / Freezed

class SignalManager:
    def __init__(self):
        # Events to update GUI (replaces pyqtSignal)
        # angles, pressures, flows, limits, state
        self.data_updated = Event()
        self.state_changed = Event()
        self.cycle_updated = Event()
        
        # Configuration
        self.dt = 0.1  # 100ms
        self.noise_level = 0.05 # 5%
        
        # Cycle Counters (목표/현재 런타임 카운터)
        self.target_count = 1
        self.current_count = 0
        
        # System State
        self.state = SystemState.IDLE
        self.previous_state = SystemState.IDLE
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
        
        # is_running flag for external loops
        self.is_running = False
        
    def start_simulation(self):
        self.is_running = True
        
    def stop_simulation(self):
        self.is_running = False
        
    def set_target_count(self, count):
        self.target_count = count
        self.cycle_updated.emit(self.current_count, self.target_count)
        
    def set_command(self, command):
        """
        External commands: 'START', 'STOP', 'ABORT'
        """
        if command == 'ABORT':
            self.state = SystemState.ABORTED
            self.state_changed.emit("ABORTED")
            # Immediate stop, no movement
            
        elif command == 'STOP':
            if self.state not in (SystemState.IDLE, SystemState.ABORTED, SystemState.STOPPED):
                self.previous_state = self.state
                self.state = SystemState.STOPPED
                self.state_changed.emit("STOPPED")
                
        elif command == 'START':
            # 사용자가 설정한 target 사이클 횟수가 되었을 때 무한 루핑되지 않고 완전히 멈추도록 예외 처리
            if self.current_count >= self.target_count:
                return # 시작 명령 무시 (RESET을 눌러 0으로 돌아가도록 유도)

            if self.state in (SystemState.IDLE, SystemState.ABORTED):
                # 기존처럼 START에서 카운트를 0으로 자동 리셋하지 않으므로 사용자의 명시적인 RESET 버튼 클릭이 필요합니다.
                self.state = SystemState.MOVING_UP
                self.state_timer = 0.0
                self.state_changed.emit("MOVING_UP")
                # Release Down Locks
                self.limits[0] = False
                self.limits[2] = False
                self.limits[4] = False
            elif self.state == SystemState.STOPPED:
                # 일시정지(Pause)에서 재개
                self.state = self.previous_state
                self.state_changed.emit(self.state.name)
                
        elif command == 'RESET':
            # 어떤 상태이든 리셋 명령을 강제로 수행하여 0 사이클, 0 각도로 시스템을 온전히 되돌립니다.
            self.current_count = 0
            self.cycle_updated.emit(self.current_count, self.target_count)
            
            if self.state != SystemState.ABORTED:
                self.state = SystemState.IDLE
                self.state_changed.emit("IDLE")
                self.state_timer = 0.0
                
                # 강제 영점 조절 (완전한 초기화)
                self.angles = [0.0, 0.0, 0.0]
                self.limits = [True, False, True, False, True, False]

    def update_loop(self):
        self.update_physics()
        self.update_logic()
        
        # Emit data
        self.data_updated.emit(self.angles, self.pressures, self.flows, self.limits, self.state.name)

    def update_physics(self):
        # Add noise to Pressure and Flow
        for i in range(10):
            p_noise = (random.random() - 0.5) * 2 * (3000 * self.noise_level)
            f_noise = (random.random() - 0.5) * 2 * (1.0 * self.noise_level)
            
            # Simple simulation: oscillate around base value
            self.pressures[i] = max(0, min(3000, self.base_pressures[i] + p_noise))
            self.flows[i] = max(0, min(1.0, self.base_flows[i] + f_noise))

    def update_logic(self):
        if self.state in (SystemState.ABORTED, SystemState.STOPPED):
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
                # Set Down Limits immediately when finished moving
                self.limits[0] = True
                self.limits[2] = True
                self.limits[4] = True
                
                # Transition to DOWNLOCKED state instead of immediate IDLE / MOVING_UP
                self.state = SystemState.DOWNLOCKED
                self.state_timer = 0.0
                self.state_changed.emit("DOWNLOCKED")
                
        elif self.state == SystemState.DOWNLOCKED:
            if self.state_timer >= 3.0: # Down lock stop time is 3 seconds
                # Down completed, increase count
                self.current_count += 1
                self.cycle_updated.emit(self.current_count, self.target_count)
                
                if self.current_count < self.target_count and self.state != SystemState.STOPPING:
                    # Continue to next cycle automatically
                    self.state = SystemState.MOVING_UP
                    self.state_timer = 0.0
                    self.state_changed.emit("MOVING_UP")
                    # Release Down Locks
                    self.limits[0] = False
                    self.limits[2] = False
                    self.limits[4] = False
                else:
                    # Target cycle에 도달하면 무조건 움직임을 멈추도록 STOPPED 상태로 전환
                    self.previous_state = SystemState.IDLE
                    self.state = SystemState.STOPPED
                    self.state_timer = 0.0
                    self.state_changed.emit("STOPPED")
