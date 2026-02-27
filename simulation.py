import simpy
import random
from network_setup import create_network
from congestion_monitor import NodeMonitor
from adaptive_routing import AdaptiveRouter


def packet_generator(env, node_id, monitor, rate, results):
    """Simulates packets arriving at a node over time."""
    while True:
        # Wait for next packet arrival (random interval based on rate)
        yield env.timeout(random.expovariate(rate))

        # Update node stats as packets arrive
        monitor.queue_length += 1
        monitor.traffic_rate = int(rate * 10)
        monitor.delay = monitor.queue_length * 0.005
        monitor.predict_congestion()

        # Record the event
        results.append({
            'time': round(env.now, 3),
            'node': node_id,
            'queue': monitor.queue_length,
            'delay': round(monitor.delay, 4),
            'rate': monitor.traffic_rate,
            'congested': monitor.predict_congestion()
        })


def run_simulation(duration=50):
    """Run the full network simulation."""
    print("=" * 50)
    print("  Early Congestion Prediction Simulation")
    print("=" * 50)

    env = simpy.Environment()
    network = create_network()
    monitors = {n: NodeMonitor(n) for n in network.nodes()}
    router = AdaptiveRouter(network, monitors)
    results = []

    # Traffic rates per node — higher = more packets arriving = more likely to congest
    traffic_rates = {
        1: 5,
        2: 15,   # Node 2 gets heavy traffic — will congest
        3: 5,
        4: 12,   # Node 4 gets moderate-heavy traffic
        5: 5,
        6: 5
    }

    print(f"\nStarting simulation for {duration} time units...")
    print(f"Heavy traffic nodes: 2 (rate=15), 4 (rate=12)\n")

    # Start packet generators for all nodes
    for node_id, rate in traffic_rates.items():
        env.process(packet_generator(env, node_id, monitors[node_id], rate, results))

    # Run the simulation
    env.run(until=duration)

    # Print final node statuses
    print("\n--- Node Status After Simulation ---")
    for node_id, monitor in monitors.items():
        monitor.report()

    # Show routing decision
    print("\n--- Adaptive Routing Decision (Node 1 → Node 6) ---")
    router.find_best_path(1, 6)

    print(f"\nTotal events recorded: {len(results)}")
    return results, monitors


if __name__ == '__main__':
    results, monitors = run_simulation(duration=50)
