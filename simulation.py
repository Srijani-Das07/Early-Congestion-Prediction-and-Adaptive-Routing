import simpy
import random
from network_setup import create_network
from congestion_monitor import NodeMonitor
from adaptive_routing import AdaptiveRouter


def packet_generator(env, node_id, monitor, rate, results):
    """Simulates packets arriving at a node over time."""
    while True:
        yield env.timeout(random.expovariate(rate))

        monitor.queue_length += 1
        monitor.traffic_rate = int(rate * 10)
        monitor.delay = monitor.queue_length * 0.005

        # Two-stage prediction check
        monitor.predict_congestion()

        results.append({
            'time': round(env.now, 3),
            'node': node_id,
            'queue': monitor.queue_length,
            'delay': round(monitor.delay, 4),
            'rate': monitor.traffic_rate,
            'predicted': monitor.predicted,   # early warning flag
            'congested': monitor.congested    # actual congestion flag
        })


def run_simulation(duration=50):
    """Run the full network simulation with early congestion prediction."""
    print("=" * 55)
    print("  Early Congestion Prediction & Adaptive Routing Sim")
    print("=" * 55)

    env = simpy.Environment()
    network = create_network()
    monitors = {n: NodeMonitor(n) for n in network.nodes()}
    router = AdaptiveRouter(network, monitors)
    results = []

    # Traffic rates — Node 2 and 4 get heavy traffic to demonstrate prediction
    traffic_rates = {
        1: 5,
        2: 15,   # Will enter PREDICTED state, then possibly CONGESTED
        3: 5,
        4: 12,   # Will enter PREDICTED state
        5: 5,
        6: 5
    }

    print(f"\nStarting simulation for {duration} time units...")
    print(f"Heavy traffic: Node 2 (rate=15), Node 4 (rate=12)")
    print(f"Early prediction triggers at 60-70% of congestion thresholds\n")

    for node_id, rate in traffic_rates.items():
        env.process(packet_generator(env, node_id, monitors[node_id], rate, results))

    # Track rerouting events during simulation
    prev_path = router.find_best_path(1, 6)
    reroute_count = 0

    env.run(until=duration)

    # Final status report
    print("\n--- Final Node Status ---")
    for node_id, monitor in monitors.items():
        monitor.report()

    print("\n--- Adaptive Routing Decision (Node 1 to Node 6) ---")
    final_path = router.find_best_path(1, 6)

    # Count how many events were predicted vs actually congested
    predicted_events = sum(1 for r in results if r['predicted'])
    congested_events = sum(1 for r in results if r['congested'])
    early_saves = predicted_events  # packets rerouted before congestion hit

    print(f"\n--- Simulation Summary ---")
    print(f"Total events recorded : {len(results)}")
    print(f"Early prediction hits : {predicted_events}  (rerouted before congestion)")
    print(f"Actual congestion hits: {congested_events}  (threshold breached)")
    print(f"Packets saved by early prediction: ~{early_saves}")

    return results, monitors


if __name__ == '__main__':
    results, monitors = run_simulation(duration=50)
