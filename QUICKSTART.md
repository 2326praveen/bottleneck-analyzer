# Quick Start Guide - Real-Time System Monitor

## Installation (First Time Only)

1. **Open PowerShell in this folder**
   - Right-click on the folder and select "Open in Terminal"

2. **Run the setup script:**
   ```powershell
   .\setup.bat
   ```
   OR manually install:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Double-click
- Double-click `run.bat` file

### Option 2: Command line
```powershell
python main.py
```

## Using the Real-Time Monitor

### First Launch (Without psutil)
The application will start in **Simulation Mode** only.
- You'll see: "⚠️ Real-time monitoring unavailable"
- Run `setup.bat` to install psutil

### Simulation Mode - Custom Input (New!)

You can now enter your own values to test bottleneck detection:

1. **Enable Custom Input**
   - Check "Use Custom Values" in the Simulation Parameters panel

2. **Enter Test Values**
   - **Memory Load**: Set > 85% to trigger RAM bottleneck
   - **Disk I/O Load**: Set > 500 to trigger Disk bottleneck
   
3. **Click "Analyze Now"** to see results

**Quick Tests:**
- Try Memory 90%, Disk 300 → Should detect RAM bottleneck
- Try Memory 50%, Disk 750 → Should detect Disk bottleneck
- Try Memory 50%, Disk 300 → Should show balanced system

See [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md) for detailed scenarios!

### After Installing psutil

1. **Switch to Real-Time Mode**
   - Select the "Real-Time" radio button at the top
   
2. **Run a Single Analysis**
   - Click "Analyze Now"
   - View your system's current performance

3. **Enable Continuous Monitoring**
   - Check "Auto-Refresh (2s)"
   - The system will update every 2 seconds
   - Perfect for monitoring during gaming, video editing, etc.

## What to Watch For

### ✅ Balanced System (Green)
- Everything is running smoothly
- No action needed

### ⚠️ RAM Bottleneck
- Memory usage > 85%
- **Fix**: Close unused programs, browsers, or upgrade RAM

### ⚠️ Disk I/O Bottleneck
- High disk activity detected
- **Fix**: Close disk-intensive programs, consider SSD upgrade

## Tips

1. **Baseline Test**: Run once during normal usage to see your baseline
2. **Stress Test**: Open many programs and watch the bottleneck detection
3. **Before Gaming**: Check if you have enough free RAM
4. **During Work**: Monitor if your system can handle your workload

## Troubleshooting

**Problem**: "Real-time monitoring unavailable"
- **Solution**: Run `setup.bat` or `pip install psutil`

**Problem**: Application won't start
- **Solution**: Make sure Python is installed (`python --version`)

**Problem**: Errors in terminal
- **Solution**: Check if all dependencies are installed

## Need Help?

Check the full [README.md](README.md) for detailed information.

---
**Quick tip**: Press `Ctrl+C` in the terminal to stop the application.
