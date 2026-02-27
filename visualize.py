import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from simulation import run_simulation
from network_setup import create_network
from adaptive_routing import AdaptiveRouter


def visualize(duration=100):
    results, monitors = run_simulation(duration=duration)
    network = create_network()
    router = AdaptiveRouter(network, monitors)
    best_path = router.find_best_path(1, 6)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Early Congestion Prediction & Adaptive Routing', fontsize=16, fontweight='bold')

    # ── Plot 1: Network Topology ──────────────────────────────────────────
    ax1 = axes[0, 0]
    pos = {1: (0, 1), 2: (1, 2), 3: (1, 0), 4: (2, 1), 5: (3, 2), 6: (3, 0)}

    # 3 colors: green=OK, yellow=predicted, red=congested
    node_colors = []
    for node in network.nodes():
        m = monitors[node]
        if m.congested:
            node_colors.append('tomato')
        elif m.predicted:
            node_colors.append('gold')
        else:
            node_colors.append('lightgreen')

    best_path_edges = [(best_path[i], best_path[i+1]) for i in range(len(best_path)-1)] if best_path else []
    edge_colors = ['blue' if (u,v) in best_path_edges or (v,u) in best_path_edges
                   else 'gray' for u,v in network.edges()]
    edge_widths = [3 if (u,v) in best_path_edges or (v,u) in best_path_edges
                   else 1 for u,v in network.edges()]

    nx.draw(network, pos, ax=ax1, with_labels=True, node_color=node_colors,
            node_size=900, font_size=13, font_weight='bold',
            edge_color=edge_colors, width=edge_widths)

    red_patch    = mpatches.Patch(color='tomato',     label='Congested Node')
    yellow_patch = mpatches.Patch(color='gold',       label='Predicted (early warning)')
    green_patch  = mpatches.Patch(color='lightgreen', label='OK Node')
    blue_patch   = mpatches.Patch(color='blue',       label='Best Path (chosen early)')
    ax1.legend(handles=[green_patch, yellow_patch, red_patch, blue_patch], loc='lower right', fontsize=8)
    ax1.set_title('Network Topology\n(Yellow = Early Prediction, Route Already Switched)', fontsize=11)

    # ── Plot 2: Queue Length with prediction threshold line ───────────────
    ax2 = axes[0, 1]
    for node_id in [2, 4]:
        times  = [r['time']  for r in results if r['node'] == node_id]
        queues = [r['queue'] for r in results if r['node'] == node_id]
        ax2.plot(times, queues, label=f'Node {node_id}')

    ax2.axhline(y=6,  color='gold',   linestyle='--', linewidth=1.5, label='Prediction Threshold (Q=6)')
    ax2.axhline(y=10, color='tomato', linestyle='--', linewidth=1.5, label='Congestion Threshold (Q=10)')
    ax2.set_xlabel('Simulation Time')
    ax2.set_ylabel('Queue Length (packets)')
    ax2.set_title('Queue Length — Rerouting at Yellow Line, Not Red', fontsize=11)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ── Plot 3: Delay with both threshold lines ───────────────────────────
    ax3 = axes[1, 0]
    for node_id in [2, 4]:
        times  = [r['time']  for r in results if r['node'] == node_id]
        delays = [r['delay'] for r in results if r['node'] == node_id]
        ax3.plot(times, delays, label=f'Node {node_id}')

    ax3.axhline(y=0.03, color='gold',   linestyle='--', linewidth=1.5, label='Prediction Threshold (30ms)')
    ax3.axhline(y=0.05, color='tomato', linestyle='--', linewidth=1.5, label='Congestion Threshold (50ms)')
    ax3.set_xlabel('Simulation Time')
    ax3.set_ylabel('Delay (seconds)')
    ax3.set_title('Delay Over Time — Early vs Late Detection', fontsize=11)
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # ── Plot 4: Predicted vs Congested event counts ───────────────────────
    ax4 = axes[1, 1]
    node_ids = sorted(monitors.keys())

    predicted_counts = [sum(1 for r in results if r['node']==n and r['predicted']) for n in node_ids]
    congested_counts = [sum(1 for r in results if r['node']==n and r['congested']) for n in node_ids]

    x = range(len(node_ids))
    w = 0.35
    bars1 = ax4.bar([i - w/2 for i in x], predicted_counts, w, label='Early Prediction Events', color='gold',       edgecolor='black')
    bars2 = ax4.bar([i + w/2 for i in x], congested_counts, w, label='Actual Congestion Events', color='tomato', edgecolor='black')

    ax4.set_xticks(list(x))
    ax4.set_xticklabels([f'Node {n}' for n in node_ids])
    ax4.set_ylabel('Number of Events')
    ax4.set_title('Early Prediction vs Actual Congestion Events\n(Gold bars = rerouted before congestion hit)', fontsize=11)
    ax4.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig('results.png', dpi=150, bbox_inches='tight')
    print("\nChart saved as results.png")
    plt.show()


if __name__ == '__main__':
    visualize(duration=100)
    