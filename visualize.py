import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from simulation import run_simulation
from network_setup import create_network
from adaptive_routing import AdaptiveRouter


def visualize(duration=100):
    # Run simulation
    results, monitors = run_simulation(duration=duration)
    network = create_network()
    router = AdaptiveRouter(network, monitors)
    best_path = router.find_best_path(1, 6)

    # ── Figure layout: 2 rows, 2 columns ──────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Early Congestion Prediction & Adaptive Routing', fontsize=16, fontweight='bold')

    # ── Plot 1: Network Topology ───────────────────────────────────────────
    ax1 = axes[0, 0]
    pos = {1: (0, 1), 2: (1, 2), 3: (1, 0), 4: (2, 1), 5: (3, 2), 6: (3, 0)}

    # Color nodes: red if congested, green if OK
    node_colors = []
    for node in network.nodes():
        if monitors[node].predict_congestion():
            node_colors.append('tomato')
        else:
            node_colors.append('lightgreen')

    # Highlight best path edges
    best_path_edges = [(best_path[i], best_path[i+1]) for i in range(len(best_path)-1)] if best_path else []
    edge_colors = ['blue' if (u, v) in best_path_edges or (v, u) in best_path_edges
                   else 'gray' for u, v in network.edges()]
    edge_widths = [3 if (u, v) in best_path_edges or (v, u) in best_path_edges
                   else 1 for u, v in network.edges()]

    nx.draw(network, pos, ax=ax1, with_labels=True, node_color=node_colors,
            node_size=900, font_size=13, font_weight='bold',
            edge_color=edge_colors, width=edge_widths)

    red_patch = mpatches.Patch(color='tomato', label='Congested Node')
    green_patch = mpatches.Patch(color='lightgreen', label='OK Node')
    blue_patch = mpatches.Patch(color='blue', label='Best Path')
    ax1.legend(handles=[red_patch, green_patch, blue_patch], loc='lower right', fontsize=8)
    ax1.set_title('Network Topology\n(Blue = Best Path, Red = Congested)', fontsize=11)

    # ── Plot 2: Queue Length Over Time for Node 2 ─────────────────────────
    ax2 = axes[0, 1]
    for node_id in [2, 4]:
        times = [r['time'] for r in results if r['node'] == node_id]
        queues = [r['queue'] for r in results if r['node'] == node_id]
        ax2.plot(times, queues, label=f'Node {node_id}')

    ax2.axhline(y=10, color='orange', linestyle='--', linewidth=1.5, label='Congestion Threshold')
    ax2.set_xlabel('Simulation Time')
    ax2.set_ylabel('Queue Length (packets)')
    ax2.set_title('Queue Length Over Time', fontsize=11)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # ── Plot 3: Delay Over Time ────────────────────────────────────────────
    ax3 = axes[1, 0]
    for node_id in [2, 4]:
        times = [r['time'] for r in results if r['node'] == node_id]
        delays = [r['delay'] for r in results if r['node'] == node_id]
        ax3.plot(times, delays, label=f'Node {node_id}')

    ax3.axhline(y=0.05, color='orange', linestyle='--', linewidth=1.5, label='Delay Threshold (50ms)')
    ax3.set_xlabel('Simulation Time')
    ax3.set_ylabel('Delay (seconds)')
    ax3.set_title('Delay Over Time', fontsize=11)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # ── Plot 4: Congestion Score Bar Chart ────────────────────────────────
    ax4 = axes[1, 1]
    node_ids = sorted(monitors.keys())
    scores = [monitors[n].congestion_score for n in node_ids]
    bar_colors = ['tomato' if s >= 2 else 'lightgreen' for s in scores]

    bars = ax4.bar([f'Node {n}' for n in node_ids], scores, color=bar_colors, edgecolor='black')
    ax4.axhline(y=2, color='orange', linestyle='--', linewidth=1.5, label='Congestion Threshold (score=2)')
    ax4.set_ylabel('Congestion Score (0-3)')
    ax4.set_title('Final Congestion Score per Node', fontsize=11)
    ax4.set_ylim(0, 3.5)
    ax4.legend()

    for bar, score in zip(bars, scores):
        ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 str(score), ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig('results.png', dpi=150, bbox_inches='tight')
    print("\nChart saved as results.png")
    plt.show()


if __name__ == '__main__':
    visualize(duration=100)
