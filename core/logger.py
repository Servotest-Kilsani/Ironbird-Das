import os
import datetime
import pandas as pd
import glob

class DataLogger:
    def __init__(self, log_dir="."):
        self.log_dir = log_dir
        self.is_logging = False
        self.current_file = None
        self.buffer = []
        self.columns = [
            'Timestamp', 'State',
            'Angle_Nose', 'Angle_MLH', 'Angle_MRH',
        ]
        # Add Pressure columns
        self.columns.extend([f'Pressure_Ch{i+1}' for i in range(10)])
        # Add Flow columns
        self.columns.extend([f'Flow_Ch{i+1}' for i in range(10)])
        # Add Limit Switch columns
        self.columns.extend([
            'LS_Nose_Down', 'LS_Nose_Up', 
            'LS_MLH_Down', 'LS_MLH_Up', 
            'LS_MRH_Down', 'LS_MRH_Up'
        ])

    def start_logging(self):
        self.is_logging = True
        self.buffer = []
        
        # Determine filename
        today = datetime.datetime.now().strftime("%Y%m%d")
        
        # Find max Cha-su
        pattern = os.path.join(self.log_dir, f"{today}_*_DAS.csv")
        files = glob.glob(pattern)
        
        max_cha = 0
        for f in files:
            try:
                # Extract CHA part: YYYYMMDD_CHAX_DAS.csv
                basename = os.path.basename(f)
                parts = basename.split('_')
                if len(parts) >= 2:
                    cha_str = parts[1] # CHAX
                    if cha_str.startswith('CHA') and cha_str[3:].isdigit():
                        cha_num = int(cha_str[3:])
                        if cha_num > max_cha:
                            max_cha = cha_num
            except:
                continue
        
        next_cha = max_cha + 1
        filename = f"{today}_CHA{next_cha}_DAS.csv"
        self.current_file = os.path.join(self.log_dir, filename)
        print(f"Start logging to {self.current_file}")

    def log(self, timestamp, state, angles, pressures, flows, limits):
        if not self.is_logging:
            return
            
        # Transform boolean limits to int (0/1) for CSV
        limits_int = [1 if x else 0 for x in limits]
        
        row = [timestamp, state] + angles + pressures + flows + limits_int
        self.buffer.append(row)

    def stop_logging(self):
        if not self.is_logging:
            return
            
        self.is_logging = False
        if self.buffer and self.current_file:
            df = pd.DataFrame(self.buffer, columns=self.columns)
            df.to_csv(self.current_file, index=False)
            print(f"Saved {len(self.buffer)} rows to {self.current_file}")
        
        self.buffer = []
        self.current_file = None
