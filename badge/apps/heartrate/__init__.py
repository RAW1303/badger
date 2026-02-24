from badgeware import screen, io, brushes, shapes, run, PixelFont
import math
import struct

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except Exception:
    BLUETOOTH_AVAILABLE = False

# Colors
BACKGROUND = brushes.color(20, 20, 40)
FOREGROUND = brushes.color(255, 255, 255)
HIGHLIGHT = brushes.color(255, 100, 100)
CONNECTING = brushes.color(255, 200, 0)

# State
state = {
    "heart_rate": 0,
    "is_connected": False,
    "is_scanning": False,
    "scan_start": 0,
    "scan_duration": 3000,  # 3 seconds
    "hr_update_time": 0,
    "devices_found": [],
}

# Bluetooth UUIDs (as 128-bit or 16-bit)
HEART_RATE_SERVICE_UUID = "180d"
HEART_RATE_CHAR_UUID = "2a37"


def _start_scan():
    """Begin BLE scan for heart rate devices."""
    if not BLUETOOTH_AVAILABLE:
        return
    state["is_scanning"] = True
    state["scan_start"] = io.ticks
    state["devices_found"] = []


def _process_ble_event(event):
    """Handle BLE scan results (stub for MicroPython BLE integration)."""
    pass


def _parse_heart_rate(data):
    """Parse heart rate from BLE characteristic value."""
    if not data or len(data) < 2:
        return None
    flags = data[0]
    if flags & 0x01 == 0:  # 8-bit format
        return data[1]
    else:  # 16-bit format
        if len(data) >= 3:
            return (data[2] << 8) | data[1]
    return None


def _simulate_hr_reading():
    """Provide simulated heart rate for testing (when actual BLE unavailable)."""
    now = io.ticks
    if now - state.get("hr_update_time", 0) >= 500:
        # Generate realistic vary between 60-100 BPM
        base_hr = 72
        variation = int(math.sin(now / 1000.0) * 8)
        state["heart_rate"] = base_hr + variation
        state["hr_update_time"] = now


def draw_heart_icon(x, y, size, pulse):
    """Draw animated heart icon."""
    scale = 1.0 + (pulse * 0.3)
    cx, cy = x, y
    r = size
    # simple scaled drawing
    r_scaled = max(1, int(r * scale))
    ox = int(r_scaled // 2)
    screen.brush = HIGHLIGHT
    screen.draw(shapes.circle(cx - ox, cy - ox, r_scaled))
    screen.draw(shapes.circle(cx + ox, cy - ox, r_scaled))
    # crude triangle/point for bottom of heart
    screen.draw(shapes.regular_polygon(cx, cy + r_scaled//2, r_scaled, 3))


def update():
    """Main app update loop."""
    # Clear screen
    screen.brush = BACKGROUND
    screen.clear()
    
    # Set font
    screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")
    
    # Handle buttons
    if io.BUTTON_A in io.pressed:
        if not state["is_connected"] and not state["is_scanning"]:
            # Start scanning for devices
            _start_scan()
        elif state["is_connected"]:
            # Disconnect
            state["is_connected"] = False
            state["heart_rate"] = 0
    
    if io.BUTTON_HOME in io.pressed:
        return False  # Exit app
    
    # Draw title
    screen.brush = FOREGROUND
    screen.text("Heart Rate Monitor", 10, 10)
    
    now = io.ticks
    
    # Handle scanning timeout and simulate connection
    if state["is_scanning"]:
        elapsed = now - state["scan_start"]
        if elapsed >= state["scan_duration"]:
            # Scan complete, simulate connection
            state["is_scanning"] = False
            state["is_connected"] = True
            state["hr_update_time"] = now
    
    # Update heart rate if connected (or simulate)
    if state["is_connected"]:
        _simulate_hr_reading()
        
        # Draw heart animation
        pulse = abs(math.sin(now / 300.0))
        draw_heart_icon(80, 50, 15, pulse)
        
        # Draw heart rate value
        screen.brush = HIGHLIGHT
        hr_text = f"{state['heart_rate']} BPM"
        text_width, _ = screen.measure_text(hr_text)
        screen.text(hr_text, 80 - text_width // 2, 75)
        
        screen.brush = FOREGROUND
        screen.text("Connected", 10, 90)
        screen.text("Press A: disconnect", 10, 105)
        
    elif state["is_scanning"]:
        screen.brush = CONNECTING
        elapsed = (now - state["scan_start"]) // 500
        dots = "." * ((elapsed % 4) + 1)
        screen.text(f"Scanning{dots}", 10, 50)
        progress = (now - state["scan_start"]) / state["scan_duration"]
        progress_bar_w = int(140 * progress)
        screen.brush = HIGHLIGHT
        screen.draw(shapes.rectangle(10, 70, progress_bar_w, 5))
        
    else:
        screen.brush = FOREGROUND
        screen.text("Press A to scan", 10, 50)
        screen.text("for BLE device", 10, 65)
    
    return True


def init():
    """Initialize app."""
    pass


def on_exit():
    """Clean up on exit."""
    # Reset state
    state["is_connected"] = False
    state["is_scanning"] = False
    state["heart_rate"] = 0