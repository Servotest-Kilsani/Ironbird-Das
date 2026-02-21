from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGridLayout, QGroupBox, QSpinBox)
from PyQt6.QtCore import Qt
from gui.widgets import GearVisualizer, DigitalMeter, LEDIndicator, DigitalSpinBox

class MainWindow(QMainWindow):
    def __init__(self, simulator):
        super().__init__()
        self.simulator = simulator
        self.setWindowTitle("Ironbird DAS Simulator")
        self.resize(1024, 768)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Control Panel (Top)
        control_group = QGroupBox("Control Panel")
        control_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("START")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(lambda: self.simulator.set_command('START'))
        
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(lambda: self.simulator.set_command('STOP'))
        
        self.btn_abort = QPushButton("ABORT")
        self.btn_abort.setMinimumHeight(40)
        self.btn_abort.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.btn_abort.clicked.connect(lambda: self.simulator.set_command('ABORT'))
        
        self.btn_reset = QPushButton("RESET")
        self.btn_reset.setMinimumHeight(40)
        self.btn_reset.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_reset.clicked.connect(lambda: self.simulator.set_command('RESET'))
        
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-left: 20px;")
        
        # Cycle Counting UI (목표 횟수 및 현재 수행 횟수)
        cycle_layout = QHBoxLayout()
        
        self.spin_target = DigitalSpinBox("Target")
        self.spin_target.spin_box.setMinimum(1)
        self.spin_target.spin_box.setMaximum(100)
        self.spin_target.spin_box.setValue(1)
        self.spin_target.spin_box.valueChanged.connect(self.simulator.set_target_count)
        cycle_layout.addWidget(self.spin_target)
        
        self.meter_current = DigitalMeter("Current", "", is_int=True)
        cycle_layout.addWidget(self.meter_current)
        
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_abort)
        control_layout.addWidget(self.btn_reset)
        control_layout.addLayout(cycle_layout)
        control_layout.addWidget(self.status_label)
        control_group.setLayout(control_layout)
        
        main_layout.addWidget(control_group)

        # 2. Visualization (Center)
        vis_group = QGroupBox("Landing Gear Visualization")
        vis_layout = QHBoxLayout()
        
        self.gear_nose = GearVisualizer("Nose Gear", image_name="nose_gear.png", rotation_dir=-1) # 반시계 방향
        self.gear_mlh = GearVisualizer("Main LH", image_name="main_lh_gear.png", rotation_dir=-1) # 반시계 방향
        self.gear_mrh = GearVisualizer("Main RH", image_name="main_rh_gear.png", rotation_dir=1)  # 시계 방향
        
        vis_layout.addWidget(self.gear_nose)
        vis_layout.addWidget(self.gear_mlh)
        vis_layout.addWidget(self.gear_mrh)
        vis_group.setLayout(vis_layout)
        
        main_layout.addWidget(vis_group, 1) # Expandable

        # 3. Sensors & Indicators (Bottom)
        sensor_layout = QHBoxLayout()
        
        # Pressure Panel
        p_group = QGroupBox("Pressure (psi)")
        p_layout = QGridLayout()
        self.p_meters = []
        for i in range(10):
            meter = DigitalMeter(f"CH {i+1}", "psi")
            p_layout.addWidget(meter, i // 2, i % 2)
            self.p_meters.append(meter)
        p_group.setLayout(p_layout)
        
        # Flow Panel 
        f_group = QGroupBox("Flow (GPM)")
        f_layout = QGridLayout()
        self.f_meters = []
        for i in range(10):
            meter = DigitalMeter(f"CH {i+1}", "GPM")
            f_layout.addWidget(meter, i // 2, i % 2)
            self.f_meters.append(meter)
        f_group.setLayout(f_layout)
        
        # Limit Switch Panel
        l_group = QGroupBox("Limit Switches")
        l_layout = QGridLayout()
        ls_names = ["Nose Down", "Nose Up", "MLH Down", "MLH Up", "MRH Down", "MRH Up"]
        self.leds = []
        for i, name in enumerate(ls_names):
             label = QLabel(name)
             led = LEDIndicator()
             l_layout.addWidget(label, i, 0)
             l_layout.addWidget(led, i, 1)
             self.leds.append(led)
        l_group.setLayout(l_layout)
        
        sensor_layout.addWidget(p_group)
        sensor_layout.addWidget(f_group)
        sensor_layout.addWidget(l_group)
        
        main_layout.addLayout(sensor_layout)
        
        # Connect Signals
        self.simulator.data_updated.connect(self.update_ui)
        self.simulator.state_changed.connect(self.update_status)
        self.simulator.cycle_updated.connect(self.update_cycle_count)

    def update_cycle_count(self, current, target):
        self.meter_current.set_value(current)
        # Update spinbox if it has different value to keep sync
        if self.spin_target.spin_box.value() != target:
            self.spin_target.spin_box.blockSignals(True)
            self.spin_target.spin_box.setValue(target)
            self.spin_target.spin_box.blockSignals(False)

    def update_ui(self, angles, pressures, flows, limits):
        # Update Gears
        if len(angles) >= 3:
            self.gear_nose.set_angle(angles[0])
            self.gear_mlh.set_angle(angles[1])
            self.gear_mrh.set_angle(angles[2])
            
        # Update Pressures
        for i, val in enumerate(pressures):
            if i < len(self.p_meters):
                self.p_meters[i].set_value(val)
                
        # Update Flows
        for i, val in enumerate(flows):
            if i < len(self.f_meters):
                self.f_meters[i].set_value(val)
                
        # Update LEDs
        for i, val in enumerate(limits):
            if i < len(self.leds):
                self.leds[i].set_state(val)

    def update_status(self, state_str):
        self.status_label.setText(f"STATUS: {state_str}")
        
        # Style update based on state
        if state_str == "ABORTED":
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
        elif state_str in ("STOPPING", "STOPPED"):
             self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
        else:
             self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")
