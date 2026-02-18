# Simulation Mode - Custom Input Guide

## How to Use Custom Values in Simulation

The simulation mode now lets you enter **your own values** to test different bottleneck scenarios! This is perfect for learning and experimentation.

## Step-by-Step Instructions

### 1. Select Simulation Mode
- Click the "Simulation" radio button at the top

### 2. Enable Custom Input
- Check the box: "Use Custom Values" in the Simulation Parameters panel
- Input fields will become active (enabled)

### 3. Enter Your Values

#### **Number of Processes** (1-20)
- How many simulated processes to run
- More processes = more resource demand

#### **Physical Frames** (3-64)
- Amount of RAM available (in page frames)
- Fewer frames = more page faults

#### **Memory Load (%)** (0-100%)
- Simulates memory pressure
- **> 85%** = RAM Bottleneck detected
- **< 85%** = Normal memory usage

#### **Disk I/O Load** (50-1000)
- Simulates disk activity (seek time)
- **> 500** = Disk I/O Bottleneck detected
- **< 500** = Normal disk performance

### 4. Click "Analyze Now"
- The system will analyze your custom values
- Results show detected bottleneck and recommendations

## Testing Scenarios

### ✅ Test a Balanced System
```
Processes: 5
Physical Frames: 12
Memory Load: 50%
Disk I/O Load: 300
```
**Expected**: "Balanced System"

### ⚠️ Test RAM Bottleneck
```
Processes: 10
Physical Frames: 8
Memory Load: 90%
Disk I/O Load: 250
```
**Expected**: "RAM Bottleneck"
**Recommendation**: Increase RAM or use LRU paging

### ⚠️ Test Disk I/O Bottleneck
```
Processes: 8
Physical Frames: 12
Memory Load: 60%
Disk I/O Load: 750
```
**Expected**: "Disk I/O Bottleneck"
**Recommendation**: Use SSTF scheduling or upgrade to SSD

### ⚠️ Test Combined Stress
```
Processes: 15
Physical Frames: 6
Memory Load: 95%
Disk I/O Load: 850
```
**Expected**: "RAM Bottleneck" (highest priority)

## Understanding the Results

### Metrics Display
When using custom values, you'll see:

**Input Values:**
- Your entered parameters

**Analysis Results:**
- Page Fault Rate (calculated from memory load)
- FIFO/LRU/Optimal Page Faults (simulated)
- Disk Seek Times (FCFS vs SSTF)
- Total Disk Requests

### Bottleneck Priority
The analyzer prioritizes bottlenecks in this order:
1. **RAM Bottleneck** (Memory Load > 85%)
2. **Disk I/O Bottleneck** (Disk Load > 500)
3. **Inefficient Page Replacement** (FIFO >> LRU)
4. **Balanced System** (no issues)

## Educational Tips

### Learn About Memory Management
- Try different frame counts with the same memory load
- See how page replacement algorithms compare (FIFO vs LRU vs Optimal)
- Understand when adding RAM helps

### Learn About Disk Scheduling
- Compare FCFS vs SSTF seek times
- Observe how high I/O affects overall performance
- See why SSDs (lower seek times) improve performance

### Experiment!
- What happens with very few physical frames?
- Can you create a worst-case scenario?
- What's the optimal balance for 10 processes?

## Quick Tips

💡 **Hints appear below the sliders** showing bottleneck thresholds

🎯 **Use the sliders** for quick value adjustments

🔄 **Random Mode**: Uncheck "Use Custom Values" to generate random workloads

📊 **Graphs**: View visual comparisons of different algorithms

---

**Happy Testing!** Use this tool to understand OS performance concepts better.
