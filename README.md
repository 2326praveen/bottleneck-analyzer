# OS Performance Bottleneck Analyzer - Real-Time Prototype

A real-time system performance monitoring tool that analyzes CPU, memory, and disk I/O to identify performance bottlenecks on your Windows system.

## Features

### Real-Time Monitoring Mode
- **Live CPU Monitoring**: Track current CPU usage percentage
- **Memory Analysis**: Monitor RAM usage, available memory, and identify memory bottlenecks
- **Disk I/O Tracking**: Measure read/write speeds and disk usage
- **Auto-Refresh**: Continuously monitor system performance every 2 seconds
- **Visual Alerts**: Color-coded status indicators and bottleneck detection

### Simulation Mode
- Educational mode using synthetic workloads
- Page replacement algorithm simulation (FIFO, LRU, Optimal)
- Disk scheduling algorithm comparison (FCFS, SSTF)
- Ideal for learning OS concepts

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows OS (tested on Windows 10/11)

### Quick Setup

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```powershell
   python main.py
   ```

## Usage

### Real-Time Monitoring

1. Launch the application
2. Select **"Real-Time"** mode from the top panel
3. Click **"Analyze Now"** to check current system performance
4. Enable **"Auto-Refresh (2s)"** for continuous monitoring
5. View results:
   - **Analysis Results**: Detected bottleneck and recommendations
   - **System Metrics**: CPU, memory, disk usage details
   - **Performance Visualization**: Graphical comparison

### Simulation Mode

1. Select **"Simulation"** mode
2. **Option A - Random Generation**: Click "Analyze Now" for random workload
3. **Option B - Custom Input**: 
   - Check "Use Custom Values"
   - Enter your own parameters:
     - **Processes**: Number of simulated processes (1-20)
     - **Physical Frames**: Available RAM pages (3-64)
     - **Memory Load**: Memory pressure 0-100% (> 85% triggers bottleneck)
     - **Disk I/O Load**: Disk activity 50-1000 (> 500 triggers bottleneck)
   - Click "Analyze Now" to test your scenario
4. Compare different page replacement and disk scheduling algorithms

**Try these scenarios:**
- Balanced: Memory 50%, Disk 300 → No bottleneck
- RAM stressed: Memory 90%, Disk 250 → RAM Bottleneck
- Disk stressed: Memory 60%, Disk 750 → Disk I/O Bottleneck

See [SIMULATION_GUIDE.md](SIMULATION_GUIDE.md) for detailed testing scenarios.

## Understanding the Results

### Bottleneck Types

- **RAM Bottleneck**: Memory usage exceeds 85%
  - *Recommendation*: Close unused applications, upgrade RAM
  
- **Disk I/O Bottleneck**: High disk activity detected
  - *Recommendation*: Consider SSD upgrade, close disk-intensive programs
  
- **Balanced System**: No bottlenecks detected
  - System is operating normally

### Metrics Explained

**Real-Time Mode:**
- **CPU Usage**: Percentage of CPU resources being used
- **Memory Usage**: RAM consumption vs total available
- **Disk Read/Write**: Data transfer rates in MB/s
- **Disk I/O Operations**: Number of read/write operations per second
- **Active Processes**: Total number of running processes

**Simulation Mode:**
- **Page Fault Rate**: How often requested pages aren't in memory
- **FIFO/LRU/Optimal Faults**: Page faults for different algorithms
- **Disk Seek Time**: Time to access disk locations (FCFS vs SSTF)

## Tips for Best Results

1. **For Accurate Monitoring**: Run the tool while using your system normally
2. **Identify Bottlenecks**: Use auto-refresh and observe patterns over time
3. **Before Major Tasks**: Check system status before gaming, video editing, etc.
4. **System Optimization**: Use recommendations to improve performance

## Troubleshooting

### "Real-time monitoring unavailable" message
- Install psutil: `pip install psutil`
- Restart the application

### High CPU usage from the tool itself
- Disable auto-refresh when not needed
- Use longer refresh intervals for monitoring

### Audio not working
- Install pyttsx3: `pip install pyttsx3`
- Check system audio settings

## Technical Details

### Dependencies
- **psutil**: System and process monitoring
- **matplotlib**: Data visualization
- **tkinter**: GUI framework (built-in)
- **pyttsx3**: Text-to-speech for audio reports (optional)

### System Requirements
- Windows 7 or higher
- 2GB RAM minimum
- Python 3.7+

## Project Structure

```
bottleneck-analyzer/
├── main.py              # Entry point
├── gui.py               # Main GUI interface
├── system_monitor.py    # Real-time system monitoring (NEW!)
├── analyzer.py          # Bottleneck detection logic
├── memory_manager.py    # Page replacement simulation
├── disk_scheduler.py    # Disk scheduling simulation
├── workload.py          # Synthetic workload generation
├── graphs.py            # Performance visualization
├── audio_report.py      # Audio feedback
├── suggestion.py        # Optimization recommendations
└── requirements.txt     # Python dependencies
```

## Educational Value

This tool demonstrates key OS concepts:
- Memory management and page replacement
- Disk scheduling algorithms
- Process and resource monitoring
- Performance analysis and optimization

## Future Enhancements

- Historical data tracking and graphs
- Network I/O monitoring
- Process-level analysis
- Custom alert thresholds
- Export reports to PDF/CSV

## License

Educational project for OS course - 4th Semester

## Support

For issues or questions, refer to your course materials or contact your instructor.

---

**Made with Python** | **Real-Time System Monitoring** | **Educational Tool**
