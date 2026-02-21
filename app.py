import streamlit as st
import time
import os
from PIL import Image
from core.simulator import SignalManager, SystemState

st.set_page_config(page_title="Ironbird DAS Simulator", layout="wide")

# Initialize simulator in session state
if 'simulator' not in st.session_state:
    st.session_state.simulator = SignalManager()
    st.session_state.simulator.start_simulation()
    
simulator = st.session_state.simulator

# --- UI Layout ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    logo_path = os.path.join("gui", "resources", "Windas Logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

with col_title:
    st.title("Ironbird DAS Simulator Web Dashboard")

col_control, col_cycles, col_status = st.columns([1, 1, 1])

with col_control:
    st.subheader("Controls")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("START", use_container_width=True, type="primary"):
        simulator.set_command('START')
    if c2.button("STOP", use_container_width=True):
        simulator.set_command('STOP')
    if c3.button("RESET", use_container_width=True):
        simulator.set_command('RESET')
    if c4.button("ABORT", use_container_width=True):
        simulator.set_command('ABORT')

with col_cycles:
    st.subheader("Cycles")
    c1, c2 = st.columns(2)
    target = c1.number_input("Target Cycles", min_value=1, max_value=100, value=simulator.target_count)
    if target != simulator.target_count:
        simulator.set_target_count(int(target))
    
    c2.metric("Current Cycle", simulator.current_count)

with col_status:
    st.subheader("System Status")
    color = "black"
    state_str = simulator.state.name
    if state_str == "ABORTED":
        color = "red"
    elif state_str in ("STOPPING", "STOPPED"):
        color = "orange"
    elif state_str in ("MOVING_UP", "MOVING_DOWN"):
        color = "blue"
    elif state_str == "DOWNLOCKED":
        color = "green"
    
    st.markdown(f"<div style='text-align: center; border: 2px solid {color}; padding: 10px; border-radius: 5px;'><strong style='color:{color}; font-size: 24px;'>{state_str}</strong></div>", unsafe_allow_html=True)

st.divider()

# Visualization & Sensors
# Give the gear column more weight (e.g. 2:1 ratio) so the icons render about twice as large
col_gear, col_sensors = st.columns([2, 1])

with col_gear:
    st.subheader("Landing Gears Angle")
    c_n, c_lh, c_rh = st.columns(3)
    
    # helper function to display gear
    @st.cache_data
    def load_base_image(img_name):
        path = os.path.join("gui", "resources", img_name)
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        return None
        
    @st.cache_data(max_entries=1000)
    def dict_rotated_image(img_name, rounded_angle, rot_dir):
        base_img = load_base_image(img_name)
        if base_img:
            w, h = base_img.size
            
            # To rotate the image around its top-center, we place it in a canvas 
            # where the center of the canvas aligns with the top-center of the image.
            # Thus, the canvas needs to be at least twice the height of the image.
            # We'll make it a square of size max(w, h) * 2.2 to be safe from clipping.
            max_dim = int(max(w, h) * 2.2)
            
            canvas = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
            
            # Paste the original image so its top edge is at the vertical center of the canvas.
            # For horizontal, center it.
            # That means paste_x = center_x - w/2
            # paste_y = center_y (so the top is exactly at the center pivot)
            center_x = max_dim // 2
            center_y = max_dim // 2
            
            # PyQt used cy+30 as pivot. 
            # Let's adjust paste_y slightly if we need the pivot to be exactly cy+30.
            # For now, placing the top of the image at the center of the canvas makes the top the pivot.
            paste_x = center_x - (w // 2)
            # Offset pivot down by 30 pixels (so rotation happens 30 pixels below the top edge) 
            # If the pivot is 30px below the top edge, we should place the image such that 
            # the pivot point falls exactly on center_y.
            # So the image's "pivot" Y (which is 0 + 30) should be at center_y.
            # Therefore, paste_y + 30 = center_y => paste_y = center_y - 30.
            paste_y = center_y - 30
            
            canvas.paste(base_img, (paste_x, paste_y))
            
            # Rotate the fixed-size canvas without expanding
            pil_angle = -(rot_dir * rounded_angle)
            rotated = canvas.rotate(pil_angle, resample=Image.Resampling.BILINEAR, expand=False)
            
            # Optional: Crop the blank space to maximize display size in Streamlit
            # We know the pivot is at the center. 
            # Streamlit displays the bounding box. If we leave it huge, it spans too much vertical space.
            # Let's crop it centrally.
            crop_margin = max(w, h)
            cropped = rotated.crop((center_x - crop_margin, center_y - crop_margin, center_x + crop_margin, center_y + crop_margin))
            
            return cropped
        return None

    def render_gear(col, name, angle, img_name, rot_dir):
        col.metric(name, f"{angle:.1f}°")
        rotated = dict_rotated_image(img_name, round(angle, 1), rot_dir)
        if rotated:
            col.image(rotated, use_container_width=True)
        else:
            col.warning("No Image")

    render_gear(c_n, "Nose", simulator.angles[0], "nose_gear.png", -1)
    render_gear(c_lh, "Main LH", simulator.angles[1], "main_lh_gear.png", -1)
    render_gear(c_rh, "Main RH", simulator.angles[2], "main_rh_gear.png", 1)
    
with col_sensors:
    st.subheader("Pressures (psi)")
    cols_p = st.columns(5)
    for i in range(10):
        cols_p[i % 5].metric(f"CH {i+1}", f"{simulator.pressures[i]:.0f}")
        
    st.subheader("Flows (GPM)")
    cols_f = st.columns(5)
    for i in range(10):
        cols_f[i % 5].metric(f"CH {i+1}", f"{simulator.flows[i]:.2f}")

st.divider()

st.subheader("Limit Switches")
cols_l = st.columns(6)
limit_names = ["Nose Down", "Nose Up", "MLH Down", "MLH Up", "MRH Down", "MRH Up"]
for i, name in enumerate(limit_names):
    state = "🟢 ON" if simulator.limits[i] else "⚪ OFF"
    cols_l[i].markdown(f"**{name}**: {state}")

# --- Simulation Loop Trigger ---
# Calculate elapsed time to ensure simulation physics stays real-time
# while lowering the Streamlit UI refresh rate to improve browser performance.
if 'last_time' not in st.session_state:
    st.session_state.last_time = time.time()
    st.session_state.accumulated_time = 0.0

current_time = time.time()
elapsed = current_time - st.session_state.last_time
st.session_state.last_time = current_time

st.session_state.accumulated_time += elapsed

# Catch up the physics engine
steps = int(st.session_state.accumulated_time / simulator.dt)
for _ in range(steps):
    simulator.update_loop()
    st.session_state.accumulated_time -= simulator.dt

# Lower UI refresh rate (e.g. 5 FPS maximum = 0.2s pause)
time.sleep(0.2)
st.rerun()
