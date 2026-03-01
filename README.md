# Early Congestion Prediction & Adaptive Routing

> A Computer Networks simulation that **predicts congestion before it happens** and reroutes traffic proactively to prevent packet loss and delay.

Traditional congestion control reacts after packet loss. This system predicts congestion at 60–70% utilization and reroutes traffic before performance degrades.

---

## Overview

In a computer network, data packets compete for limited bandwidth. When queues fill up, congestion occurs, leading to delay and packet drops.

This project implements:

- A **two-stage congestion detection model**
- A **cost-based adaptive routing algorithm**
- A **SimPy discrete-event network simulation**
- Visualization of congestion trends and routing behavior

The system reroutes traffic at the *prediction stage*, not the failure stage.

---

## Problem Statement

Most congestion control mechanisms (e.g., TCP AIMD) use packet loss as the signal for congestion. This is reactive and the performance degradation has already occurred.

This project improves upon that by:

| Traditional Approach | This Project |
|----------------------|-------------|
| Detects after packet loss | Predicts before packet loss |
| Acts when queue is full | Acts at 60–70% capacity |
| Single detection threshold | Two-stage threshold system |
| Reroutes after degradation | Reroutes while performance is stable |

Core insight: **If congestion can be predicted, it can be avoided.**

---

## Architecture

### 1. Two-Stage Congestion Detection

Implemented in `congestion_monitor.py`.

#### Stage 1 — Early Prediction (Soft Thresholds)

A node is marked **PREDICTED** if any 2 of the following occur:

- Queue length > 6 packets  
- Delay > 30 ms  
- Traffic rate > 55 packets/sec  

These represent ~60–70% of danger capacity.

#### Stage 2 — Hard Congestion (Hard Thresholds)

A node is marked **CONGESTED** if any 2 of the following occur:

- Queue length > 10 packets  
- Delay > 50 ms  
- Traffic rate > 80 packets/sec  

This two-metric requirement prevents false positives from single metric spikes.

---

### 2. Adaptive Routing Logic

Implemented in `adaptive_routing.py`.

Each node contributes cost to a path:

- OK → cost 0  
- PREDICTED → cost 1  
- CONGESTED → cost 3  

All simple paths from source to destination are evaluated using NetworkX.

The path with **minimum total cost** is selected.

Rerouting is triggered at cost 1 (prediction stage), not cost 3 (congestion stage).

---

## Network Topology

- 6 nodes (routers)
- 7 bidirectional edges (links with capacity)
- Node 2 and Node 4 receive higher simulated traffic to demonstrate prediction and rerouting

---

## Project Structure

```
root/
│
├── network_setup.py       # Builds the network graph (6 nodes, 7 edges)
├── congestion_monitor.py  # Two-stage prediction logic per node
├── adaptive_routing.py    # Finds least-cost path using prediction scores
├── simulation.py          # SimPy-based discrete event simulation
├── visualize.py           # 4-panel matplotlib output chart
├── run.py                 # Single command to run everything in order
├── demo.html              # Live interactive browser demo (no install needed)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```
---

## How to Run

### Prerequisites

Make sure you have Python 3.8 or higher installed. You can check by running:

```bash
python --version
```

### Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: `networkx`, `simpy`, `matplotlib`.

### Step 2 — Run Everything

```bash
python run.py
```
### Running the Live Demo (Optional)

Open `demo.html` in any browser. No installation required. Use the sliders to control traffic rates per node in real time and watch the routing adapt live.

---

## CN Concepts Used

| Concept | Where It's Applied |
|---|---|
| **Congestion Control** | Two-stage threshold system in `congestion_monitor.py` |
| **Routing Algorithms** | Shortest/least-cost path in `adaptive_routing.py` using all-simple-paths |
| **Quality of Service (QoS)** | Prioritising low-congestion paths to maintain throughput and reduce delay |
| **Network Monitoring** | Continuous per-node tracking of queue length, delay, and traffic rate |
| **Discrete Event Simulation** | SimPy environment simulating packet arrivals using exponential distribution |
| **Graph Theory** | NetworkX graph with weighted edges representing link capacity |

---

## Tools & Technologies

| Tool | Purpose |
|---|---|
| **Python 3.8+** | Core programming language |
| **NetworkX** | Network graph creation and path enumeration |
| **SimPy** | Discrete-event simulation engine for modelling time and packet arrivals |
| **Matplotlib** | Chart generation and result visualisation |
| **HTML/CSS/JavaScript** | Live interactive browser demo (`demo.html`) |
| **Chart.js** | Real-time charts inside the browser demo |

---

## Results

Compared to no early prediction:

- Reduced packet loss (queues avoided before overflow)
- Lower end-to-end delay
- Improved throughput
- Better traffic distribution across nodes
- Fewer nodes reaching hard congestion state

---

## Advantages

- Predictive rather than reactive
- Lightweight (no ML, no DPI)
- Two-metric validation reduces false positives
- Scalable threshold model
- Path diversity awareness (longer clean path preferred over shorter congested one)

---

## Limitations

- Simulated environment (SimPy model)
- Static threshold values
- No feedback loop for rerouted traffic load
- Simplified queue drain model
- Assumes global state visibility (SDN-like control)
- No packet prioritization

---

## Authors

- [Hana Maria Philip](https://github.com/hana-20092006)
- [Leela Chandana Apilagunta](https://github.com/leelachandana45-a11y)
- [Poojitha Sudalagunta](https://github.com/poojithasudalagunta-source)
- [Srijani Das](https://github.com/Srijani-Das07)

---

*This project was built as part of a Computer Networks course to demonstrate early congestion prediction using traffic trend analysis, without relying on packet loss as the primary congestion signal.*
