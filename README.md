# Early Congestion Prediction & Adaptive Routing

> A Computer Networks simulation that predicts traffic jams in a network *before* they happen — and automatically reroutes data to avoid them.

---

## Table of Contents

1. [What Is This Project?](#what-is-this-project)
2. [The Problem It Solves](#the-problem-it-solves)
3. [How It Works](#how-it-works)
4. [Project Structure](#project-structure)
5. [How to Run](#how-to-run)
6. [Expected Output](#expected-output)
7. [CN Concepts Used](#cn-concepts-used)
8. [Outcomes & Results](#outcomes--results)
9. [Advantages](#advantages)
10. [Limitations](#limitations)
11. [Tools & Technologies](#tools--technologies)

---

## What Is This Project?

Think of a computer network like a city's road system. Data packets are the cars, routers are the intersections, and bandwidth is the road capacity. When too many cars pile up at one intersection, you get a traffic jam — in networking terms, that's **congestion**.

Traditional networks deal with congestion the way most drivers do: they notice the jam only after they're already stuck in it. By the time the system reacts, packets have already been delayed or dropped.

**This project does something different.** It monitors network traffic continuously — watching queue lengths, delays, and traffic rates — and predicts when a node is *heading toward* congestion, not just when it's already there. Once a prediction is made, traffic is automatically rerouted through a less loaded path — before any packet loss occurs.

The analogy: it's the difference between Google Maps rerouting you *around* a forming traffic jam versus telling you about it after you're stuck bumper-to-bumper.

---

## The Problem It Solves

In standard network congestion control (like TCP's approach), the system relies on **packet loss** as the signal that congestion has occurred. This is reactive by design — the damage is already done before the system responds.

| Traditional Approach | This Project |
|---|---|
| Detects congestion after packet loss | Predicts congestion before packet loss |
| Reacts when queue is already full | Acts when queue is 60–70% full |
| Single threshold for detection | Two-stage threshold system |
| Reroutes after performance degrades | Reroutes while performance is still good |
| Congestion = certain delay | Congestion often prevented entirely |

The core insight is simple: **if you can see congestion coming, you don't have to experience it.**

---

## How It Works

### The Two-Stage Detection System

The heart of this project is a two-stage threshold system in `congestion_monitor.py`:

**Stage 1 — Early Prediction (Soft Thresholds)**

These thresholds are set at 60–70% of the danger zone. When a node crosses these, it is flagged as `PREDICTED` — meaning congestion is trending in that direction.

| Metric | Prediction Threshold | What It Means |
|---|---|---|
| Queue Length | > 6 packets | Queue is filling up faster than it drains |
| Delay | > 30ms | Packets waiting noticeably longer than normal |
| Traffic Rate | > 55 pkts/sec | Arrivals outpacing service capacity |

A node is flagged `PREDICTED` when **2 or more** of these soft thresholds are crossed simultaneously. This prevents false alarms from a single metric spiking briefly.

**Stage 2 — Actual Congestion (Hard Thresholds)**

| Metric | Congestion Threshold |
|---|---|
| Queue Length | > 10 packets |
| Delay | > 50ms |
| Traffic Rate | > 80 pkts/sec |

A node is flagged `CONGESTED` when **2 or more** hard thresholds are crossed.

### The Routing Decision

The adaptive router (`adaptive_routing.py`) assigns a cost to each possible path based on the state of nodes along it:

- **Normal node** → cost 0 (free to use)
- **Predicted node** → cost 1 (avoid if a better option exists)
- **Congested node** → cost 3 (strongly avoid)

It then evaluates all paths from source to destination and picks the one with the lowest total cost. The key detail: **rerouting is triggered at cost 1 (prediction stage)**, not cost 3 (congestion stage). By the time a node would have turned red, traffic has already been moved away.

### Node States at a Glance

```
🟢 OK         — Normal operation, no issues
🟡 PREDICTED  — Congestion trending, route already switched
🔴 CONGESTED  — Hard threshold breached (rare, since we predicted it)
```

---

## Project Structure

```
CN_Project/
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

### The Network Topology

```
    [1] ──── [2] ────┐
     │               [4] ──── [5]
    [1] ──── [3] ────┘         │
                     [4] ──── [6]
                               │
                     [5] ──── [6]
```

6 nodes representing routers. 7 edges representing physical links with defined capacities. Node 2 and Node 4 are given higher traffic rates in the simulation to demonstrate prediction and rerouting.

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

That's it. This single command runs all 5 files in the correct order:

```
Step 1/5 — network_setup.py       Builds and verifies the network
Step 2/5 — congestion_monitor.py  Tests prediction logic on sample nodes
Step 3/5 — adaptive_routing.py    Tests routing with predicted/congested nodes
Step 4/5 — simulation.py          Runs full SimPy simulation
Step 5/5 — visualize.py           Generates charts and saves results.png
```

If any step fails, the runner stops and tells you which file to check.

### Step 3 — View Results

After running, open `results.png` in your project folder. It contains 4 charts:

- Network topology with node states color-coded
- Queue length over time with both threshold lines
- Delay over time with both threshold lines
- Predicted vs congested event counts per node

### Running the Live Demo (Optional)

Open `demo.html` in any browser — no installation required. Use the sliders to control traffic rates per node in real time and watch the routing adapt live.

---

## Expected Output

When you run `python run.py`, here is roughly what you'll see in the terminal:

```
-------------------------------------------------------
  CN PROJECT — Full Pipeline Runner
-------------------------------------------------------

-------------------------------------------------------
  Step 4/5 — Running Simulation
-------------------------------------------------------
  Early Congestion Prediction & Adaptive Routing Sim

Node 2: Queue=7, Delay=0.035s, Rate=60 pkt/s, Status=PREDICTED (early warning — rerouting triggered)
Node 4: Queue=12, Delay=0.062s, Rate=85 pkt/s, Status=CONGESTED

All paths from Node 1 to Node 6:
  N1[OK] -> N2[PREDICTED] -> N4[CONGESTED] -> N6[OK]  |  Cost=4
  N1[OK] -> N3[OK] -> N4[CONGESTED] -> N6[OK]          |  Cost=3  <-- BEST PATH

--- Simulation Summary ---
Total events recorded : 847
Early prediction hits : 312  (rerouted before congestion)
Actual congestion hits: 89   (threshold breached)
Packets saved by early prediction: ~312
```

The key number to look at is **"Early prediction hits"** — these are the packets that were rerouted while the node was still in the yellow (predicted) zone, before congestion ever hit.

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

## Outcomes & Results

After running the simulation, the following improvements are observed compared to a system with no early prediction:

**Reduced Packet Loss**
Since rerouting happens before queues overflow, fewer packets are dropped. In the simulation, nodes that would have hit the hard congestion threshold are avoided by the time they reach the soft threshold.

**Lower End-to-End Delay**
Packets travel through less loaded nodes, spending less time in queues. The delay chart clearly shows nodes that hit the prediction stage but never reached the congestion stage due to early rerouting.

**Better Throughput**
More packets complete their journey successfully per unit of simulation time, because the network avoids bottlenecks proactively.

**Cleaner QoS**
Traffic is distributed more evenly across the network, preventing any single node from becoming a permanent bottleneck.

---

## Advantages

**Early action, not late reaction**
The defining strength of this project. Traditional congestion control (like TCP's AIMD — Additive Increase Multiplicative Decrease) only responds after packet loss. This system acts at 60–70% capacity, while there's still room to manoeuvre.

**Lightweight and simple**
No machine learning. No deep packet inspection. No complex probabilistic models. Just three metrics, two thresholds, and a cost function. This makes it fast to compute and easy to understand, deploy, and debug.

**Graceful degradation**
Even if a prediction is wrong (false positive), the cost of rerouting unnecessarily is small — a slightly longer path. The cost of not predicting correctly (false negative) is much higher — dropped packets and degraded performance.

**Scalable logic**
The threshold-based scoring system scales naturally. Adding more nodes means adding more monitors — the core logic doesn't change.

**Path diversity awareness**
The router evaluates all available paths, not just the shortest one. A longer path with no congestion is preferred over a shorter one with a predicted node. This reflects real-world traffic engineering principles.

---

## Limitations

**Simulated environment**
This runs in a discrete-event simulation (SimPy), not on a real network. Real network traffic is far more complex, bursty, and unpredictable. Results here demonstrate the concept, not production performance.

**Static threshold values**
The prediction thresholds (Q > 6, delay > 30ms, rate > 55) are fixed. In a real network, optimal thresholds vary based on link capacity, application type, and traffic patterns. Adaptive thresholds (possibly learned over time) would be significantly more robust.

**No feedback mechanism**
Once a packet is rerouted, the simulation doesn't model the effect of that rerouting on the new path's congestion. In reality, sending more traffic to an alternate path can eventually congest that path too.

**Queue does not fully drain**
The simulation uses a simplified drain model (random packets drained per tick). Real routers use service rates determined by hardware and protocol specifics — the behaviour here is an approximation.

**Global view assumption**
The router assumes it knows the state of all nodes at all times. In a distributed real-world network, this level of visibility would require a centralised SDN (Software Defined Networking) controller or a gossip-based monitoring protocol, neither of which is implemented here.

**No packet prioritisation**
All packets are treated equally. Real networks often implement QoS with priority queues — high-priority traffic (voice, video) gets served before bulk data. This project does not model that distinction.

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

## Authors

CN Project — Computer Networks Course

---

*This project was built as part of a Computer Networks course to demonstrate early congestion prediction using traffic trend analysis — without relying on packet loss as the primary congestion signal.*