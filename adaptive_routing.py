import networkx as nx
from network_setup import create_network
from congestion_monitor import NodeMonitor


class AdaptiveRouter:
    def __init__(self, network, monitors):
        self.network = network
        self.monitors = monitors  # dict: {node_id: NodeMonitor}

    def path_cost(self, path):
        """Calculate total congestion score along a path."""
        total_score = 0
        for node in path:
            if node in self.monitors:
                total_score += self.monitors[node].congestion_score
        return total_score

    def find_best_path(self, source, destination):
        """Find the least congested path from source to destination."""
        all_paths = list(nx.all_simple_paths(self.network, source, destination))

        if not all_paths:
            print(f'No path found between {source} and {destination}!')
            return None

        best_path = min(all_paths, key=self.path_cost)
        best_cost = self.path_cost(best_path)

        print(f'\nAll paths from Node {source} to Node {destination}:')
        for path in all_paths:
            cost = self.path_cost(path)
            marker = ' <-- BEST (least congested)' if path == best_path else ''
            print(f'  Path {path}  |  Congestion Cost = {cost}{marker}')

        return best_path


if __name__ == '__main__':
    print("--- Testing Adaptive Routing ---")

    network = create_network()
    monitors = {n: NodeMonitor(n) for n in network.nodes()}

    # Simulate node 2 being congested
    monitors[2].update(queue_length=15, delay=0.09, traffic_rate=95)
    monitors[2].predict_congestion()

    # Simulate node 4 being slightly busy
    monitors[4].update(queue_length=8, delay=0.03, traffic_rate=60)
    monitors[4].predict_congestion()

    router = AdaptiveRouter(network, monitors)
    best = router.find_best_path(1, 6)
    print(f'\nChosen path: {best}')
