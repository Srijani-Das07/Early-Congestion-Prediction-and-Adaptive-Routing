"""
compare.py — Baseline vs Early Prediction Comparison

Runs the simulation TWICE with identical traffic and random seed:
  Run 1: No early prediction (traditional reactive routing)
  Run 2: With early prediction (this project)

Then produces a side-by-side comparison chart showing exactly
what early prediction improves and by how much.
"""

import random
import simpy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from network_setup import create_network
from adaptive_routing import AdaptiveRouter


# ══════════════════════════════════════════════════════════════
#  SHARED CONSTANTS
# ══════════════════════════════════════════════════════════════
RANDOM_SEED    = 42       # same seed = same traffic both runs
SIM_DURATION   = 80
TRAFFIC_RATES  = {1: 5, 2: 15, 3: 5, 4: 12, 5: 5, 6: 5}
SERVICE_RATE   = 6        # packets drained per tick at each node

# Hard thresholds (both modes use these)
QUEUE_HARD  = 10
DELAY_HARD  = 0.05
RATE_HARD   = 80

# Soft thresholds (only early prediction mode uses these)
QUEUE_SOFT  = 6
DELAY_SOFT  = 0.03
RATE_SOFT   = 55


# ══════════════════════════════════════════════════════════════
#  NODE MONITOR — supports both modes
# ══════════════════════════════════════════════════════════════
class NodeMonitor:
    def __init__(self, node_id, early_prediction=True):
        self.node_id          = node_id
        self.early_prediction = early_prediction
        self.queue_length     = 0
        self.delay            = 0.0
        self.traffic_rate     = 0
        self.congestion_score = 0
        self.predicted        = False
        self.congested        = False
        self.packets_dropped  = 0   # dropped when queue overflows

    def update_and_check(self, rate):
        """Update stats and return routing score for path cost calculation."""
        # Hard score
        hard = 0
        if self.queue_length > QUEUE_HARD:  hard += 1
        if self.delay        > DELAY_HARD:  hard += 1
        if self.traffic_rate > RATE_HARD:   hard += 1
        self.congestion_score = hard
        self.congested        = hard >= 2

        if self.early_prediction:
            # Soft score — fires before hard
            soft = 0
            if self.queue_length > QUEUE_SOFT:  soft += 1
            if self.delay        > DELAY_SOFT:  soft += 1
            if self.traffic_rate > RATE_SOFT:   soft += 1
            self.predicted = (soft >= 2) and not self.congested
        else:
            self.predicted = False

    def get_routing_score(self):
        if self.congested:  return 3
        if self.predicted:  return 1
        return 0


# ══════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════
import networkx as nx

class Router:
    def __init__(self, network, monitors):
        self.network  = network
        self.monitors = monitors

    def path_cost(self, path):
        return sum(self.monitors[n].get_routing_score() for n in path if n in self.monitors)

    def best_path(self, src, dst):
        paths = list(nx.all_simple_paths(self.network, src, dst))
        if not paths: return [src, dst]
        return min(paths, key=self.path_cost)


# ══════════════════════════════════════════════════════════════
#  SIMULATION ENGINE
# ══════════════════════════════════════════════════════════════
def run_sim(early_prediction, seed):
    """
    Run simulation in one of two modes:
      early_prediction=False → traditional reactive routing
      early_prediction=True  → this project's early prediction
    """
    random.seed(seed)
    env      = simpy.Environment()
    network  = create_network()
    monitors = {n: NodeMonitor(n, early_prediction) for n in network.nodes()}
    router   = Router(network, monitors)

    results = {
        'queue_history':    {n: [] for n in network.nodes()},
        'delay_history':    {n: [] for n in network.nodes()},
        'time_labels':      [],
        'dropped_total':    0,
        'predicted_events': 0,
        'congested_events': 0,
        'reroutes':         0,
        'reroute_times':    [],
    }

    prev_path = [None]

    def packet_generator(node_id, monitor, rate):
        while True:
            yield env.timeout(random.expovariate(rate))
            monitor.queue_length  += 1
            monitor.traffic_rate   = int(rate * 10) + random.randint(-5, 5)
            monitor.delay          = monitor.queue_length * 0.005

            # Drop packet if queue is over hard limit (simulates buffer overflow)
            if monitor.queue_length > QUEUE_HARD + 5:
                monitor.packets_dropped += 1
                results['dropped_total'] += 1
                monitor.queue_length -= 1   # packet lost, queue doesn't grow

            monitor.update_and_check(rate)

    def drain_and_record():
        while True:
            yield env.timeout(1.0)

            for n, monitor in monitors.items():
                drain = random.randint(4, SERVICE_RATE + 2)
                monitor.queue_length = max(0, monitor.queue_length - drain)
                monitor.update_and_check(TRAFFIC_RATES[n])

                results['queue_history'][n].append(monitor.queue_length)
                results['delay_history'][n].append(monitor.delay)

                if monitor.predicted:  results['predicted_events'] += 1
                if monitor.congested:  results['congested_events'] += 1

            results['time_labels'].append(round(env.now, 1))

            # Check if best path changed (reroute event)
            current_path = router.best_path(1, 6)
            if current_path != prev_path[0]:
                results['reroutes'] += 1
                results['reroute_times'].append(env.now)
                prev_path[0] = current_path

    for node_id, rate in TRAFFIC_RATES.items():
        env.process(packet_generator(node_id, monitors[node_id], rate))
    env.process(drain_and_record())
    env.run(until=SIM_DURATION)

    results['monitors']      = monitors
    results['final_path']    = router.best_path(1, 6)
    results['avg_queue_n2']  = np.mean(results['queue_history'][2])
    results['avg_queue_n4']  = np.mean(results['queue_history'][4])
    results['avg_delay_n2']  = np.mean(results['delay_history'][2])
    results['avg_delay_n4']  = np.mean(results['delay_history'][4])
    results['peak_queue_n2'] = max(results['queue_history'][2]) if results['queue_history'][2] else 0
    results['peak_queue_n4'] = max(results['queue_history'][4]) if results['queue_history'][4] else 0

    return results


# ══════════════════════════════════════════════════════════════
#  PRINT SUMMARY
# ══════════════════════════════════════════════════════════════
def print_summary(label, r):
    print(f"\n{'─'*50}")
    print(f"  {label}")
    print(f"{'─'*50}")
    print(f"  Packets dropped        : {r['dropped_total']}")
    print(f"  Avg queue length (N2)  : {r['avg_queue_n2']:.2f}")
    print(f"  Avg queue length (N4)  : {r['avg_queue_n4']:.2f}")
    print(f"  Peak queue (N2)        : {r['peak_queue_n2']}")
    print(f"  Peak queue (N4)        : {r['peak_queue_n4']}")
    print(f"  Avg delay (N2)         : {r['avg_delay_n2']*1000:.1f} ms")
    print(f"  Avg delay (N4)         : {r['avg_delay_n4']*1000:.1f} ms")
    print(f"  Congestion events      : {r['congested_events']}")
    print(f"  Early prediction hits  : {r['predicted_events']}")
    print(f"  Rerouting events       : {r['reroutes']}")
    if r['reroute_times']:
        print(f"  First reroute at       : t={r['reroute_times'][0]:.1f}s")


# ══════════════════════════════════════════════════════════════
#  COMPARISON CHART
# ══════════════════════════════════════════════════════════════
def plot_comparison(baseline, predicted):
    fig = plt.figure(figsize=(16, 12))
    fig.patch.set_facecolor('#0a0e1a')

    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.3)

    C_BASE  = '#ff4e6a'   # red   — baseline (no prediction)
    C_PRED  = '#00d4ff'   # blue  — with early prediction
    C_SOFT  = '#ffd93d'   # gold  — prediction threshold line
    C_HARD  = '#ff4e6a'   # red   — congestion threshold line
    BG      = '#0f1624'
    GRID    = '#1e2d45'
    TEXT    = '#c8e0f4'

    def style_ax(ax, title):
        ax.set_facecolor(BG)
        ax.tick_params(colors=TEXT, labelsize=9)
        ax.xaxis.label.set_color(TEXT)
        ax.yaxis.label.set_color(TEXT)
        ax.set_title(title, color=TEXT, fontsize=11, fontweight='bold', pad=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        ax.grid(True, color=GRID, linewidth=0.6, alpha=0.7)

    fig.suptitle(
        'Early Congestion Prediction vs Traditional Reactive Routing\n'
        'Same network · Same traffic · Same random seed',
        color='white', fontsize=14, fontweight='bold', y=0.98
    )

    t = baseline['time_labels']

    # ── 1. Queue Length — Node 2 ─────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t, baseline['queue_history'][2],  color=C_BASE, lw=1.5, label='No Prediction')
    ax1.plot(t, predicted['queue_history'][2], color=C_PRED, lw=1.5, label='Early Prediction')
    ax1.axhline(QUEUE_SOFT, color=C_SOFT,  lw=1.2, ls='--', label=f'Predict Threshold ({QUEUE_SOFT})')
    ax1.axhline(QUEUE_HARD, color=C_HARD,  lw=1.2, ls=':',  label=f'Congest Threshold ({QUEUE_HARD})')
    # Mark first reroute time for prediction run
    if predicted['reroute_times']:
        ax1.axvline(predicted['reroute_times'][0], color=C_SOFT, lw=1.5, ls='-.',
                    label=f'Early reroute @ t={predicted["reroute_times"][0]:.0f}s')
    ax1.set_ylabel('Queue Length (pkts)', color=TEXT)
    ax1.set_xlabel('Simulation Time (s)', color=TEXT)
    ax1.legend(fontsize=7, facecolor='#0f1624', labelcolor=TEXT, loc='upper left')
    style_ax(ax1, 'Queue Length — Node 2')

    # ── 2. Queue Length — Node 4 ─────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t, baseline['queue_history'][4],  color=C_BASE, lw=1.5, label='No Prediction')
    ax2.plot(t, predicted['queue_history'][4], color=C_PRED, lw=1.5, label='Early Prediction')
    ax2.axhline(QUEUE_SOFT, color=C_SOFT, lw=1.2, ls='--')
    ax2.axhline(QUEUE_HARD, color=C_HARD, lw=1.2, ls=':')
    ax2.set_ylabel('Queue Length (pkts)', color=TEXT)
    ax2.set_xlabel('Simulation Time (s)', color=TEXT)
    ax2.legend(fontsize=7, facecolor='#0f1624', labelcolor=TEXT)
    style_ax(ax2, 'Queue Length — Node 4')

    # ── 3. Delay — Node 2 ────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(t, [d*1000 for d in baseline['delay_history'][2]],  color=C_BASE, lw=1.5, label='No Prediction')
    ax3.plot(t, [d*1000 for d in predicted['delay_history'][2]], color=C_PRED, lw=1.5, label='Early Prediction')
    ax3.axhline(DELAY_SOFT*1000, color=C_SOFT, lw=1.2, ls='--', label=f'Predict Threshold ({DELAY_SOFT*1000:.0f}ms)')
    ax3.axhline(DELAY_HARD*1000, color=C_HARD, lw=1.2, ls=':',  label=f'Congest Threshold ({DELAY_HARD*1000:.0f}ms)')
    ax3.set_ylabel('Delay (ms)', color=TEXT)
    ax3.set_xlabel('Simulation Time (s)', color=TEXT)
    ax3.legend(fontsize=7, facecolor='#0f1624', labelcolor=TEXT)
    style_ax(ax3, 'Delay Over Time — Node 2')

    # ── 4. Delay — Node 4 ────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(t, [d*1000 for d in baseline['delay_history'][4]],  color=C_BASE, lw=1.5, label='No Prediction')
    ax4.plot(t, [d*1000 for d in predicted['delay_history'][4]], color=C_PRED, lw=1.5, label='Early Prediction')
    ax4.axhline(DELAY_SOFT*1000, color=C_SOFT, lw=1.2, ls='--')
    ax4.axhline(DELAY_HARD*1000, color=C_HARD, lw=1.2, ls=':')
    ax4.set_ylabel('Delay (ms)', color=TEXT)
    ax4.set_xlabel('Simulation Time (s)', color=TEXT)
    ax4.legend(fontsize=7, facecolor='#0f1624', labelcolor=TEXT)
    style_ax(ax4, 'Delay Over Time — Node 4')

    # ── 5. Side-by-side metric comparison bar chart ───────────
    ax5 = fig.add_subplot(gs[2, 0])
    metrics      = ['Packets\nDropped', 'Avg Queue\nNode 2', 'Avg Queue\nNode 4',
                    'Avg Delay\nNode 2 (ms)', 'Avg Delay\nNode 4 (ms)', 'Congestion\nEvents']
    base_vals    = [
        baseline['dropped_total'],
        round(baseline['avg_queue_n2'], 1),
        round(baseline['avg_queue_n4'], 1),
        round(baseline['avg_delay_n2']*1000, 1),
        round(baseline['avg_delay_n4']*1000, 1),
        baseline['congested_events'],
    ]
    pred_vals    = [
        predicted['dropped_total'],
        round(predicted['avg_queue_n2'], 1),
        round(predicted['avg_queue_n4'], 1),
        round(predicted['avg_delay_n2']*1000, 1),
        round(predicted['avg_delay_n4']*1000, 1),
        predicted['congested_events'],
    ]
    x  = np.arange(len(metrics))
    w  = 0.35
    b1 = ax5.bar(x - w/2, base_vals, w, color=C_BASE,  alpha=0.85, label='No Prediction',    edgecolor='white', lw=0.5)
    b2 = ax5.bar(x + w/2, pred_vals, w, color=C_PRED, alpha=0.85, label='Early Prediction', edgecolor='white', lw=0.5)
    ax5.set_xticks(x)
    ax5.set_xticklabels(metrics, color=TEXT, fontsize=8)
    ax5.legend(fontsize=8, facecolor='#0f1624', labelcolor=TEXT)
    for bar in b1:
        h = bar.get_height()
        ax5.text(bar.get_x()+bar.get_width()/2, h+0.3, f'{h:.1f}', ha='center', color=TEXT, fontsize=7)
    for bar in b2:
        h = bar.get_height()
        ax5.text(bar.get_x()+bar.get_width()/2, h+0.3, f'{h:.1f}', ha='center', color=TEXT, fontsize=7)
    style_ax(ax5, 'Head-to-Head Metric Comparison\n(Lower = Better)')

    # ── 6. Improvement % summary ──────────────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.set_facecolor(BG)
    ax6.axis('off')

    def pct(base, pred):
        if base == 0: return 0.0
        return round((base - pred) / base * 100, 1)

    improvements = [
        ('Packets Dropped',        pct(baseline['dropped_total'],       predicted['dropped_total'])),
        ('Avg Queue — Node 2',     pct(baseline['avg_queue_n2'],        predicted['avg_queue_n2'])),
        ('Avg Queue — Node 4',     pct(baseline['avg_queue_n4'],        predicted['avg_queue_n4'])),
        ('Avg Delay — Node 2',     pct(baseline['avg_delay_n2'],        predicted['avg_delay_n2'])),
        ('Avg Delay — Node 4',     pct(baseline['avg_delay_n4'],        predicted['avg_delay_n4'])),
        ('Congestion Events',      pct(baseline['congested_events'],    predicted['congested_events'])),
    ]

    ax6.text(0.5, 0.97, 'Improvement with Early Prediction',
             ha='center', va='top', color='white', fontsize=11, fontweight='bold',
             transform=ax6.transAxes)
    ax6.text(0.5, 0.88, 'vs Traditional Reactive Routing',
             ha='center', va='top', color=TEXT, fontsize=9,
             transform=ax6.transAxes)

    y_pos = 0.75
    for label, val in improvements:
        color  = '#00ff9d' if val > 0 else ('#ff4e6a' if val < 0 else TEXT)
        symbol = '▼' if val > 0 else ('▲' if val < 0 else '—')
        ax6.text(0.08, y_pos, label,         color=TEXT,  fontsize=9,  transform=ax6.transAxes)
        ax6.text(0.78, y_pos, f'{symbol} {abs(val):.1f}%', color=color, fontsize=10,
                 fontweight='bold', transform=ax6.transAxes)
        ax6.axhline(0, color=GRID)
        y_pos -= 0.115

    ax6.text(0.5, 0.02,
             f'First reroute: t={predicted["reroute_times"][0]:.1f}s (early prediction)'
             if predicted['reroute_times'] else '',
             ha='center', color=C_SOFT, fontsize=8, transform=ax6.transAxes)

    plt.savefig('comparison.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print('\nComparison chart saved as comparison.png')
    plt.show()


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('=' * 55)
    print('  Baseline vs Early Prediction — Comparison Run')
    print('=' * 55)
    print(f'\nRandom seed     : {RANDOM_SEED}  (identical for both runs)')
    print(f'Simulation time : {SIM_DURATION}s')
    print(f'Traffic rates   : Node 2 = {TRAFFIC_RATES[2]}, Node 4 = {TRAFFIC_RATES[4]} (heavy)')

    print('\n[1/2] Running WITHOUT early prediction (baseline)...')
    baseline = run_sim(early_prediction=False, seed=RANDOM_SEED)

    print('[2/2] Running WITH early prediction...')
    predicted = run_sim(early_prediction=True, seed=RANDOM_SEED)

    print_summary('WITHOUT Early Prediction (Baseline)', baseline)
    print_summary('WITH Early Prediction (This Project)', predicted)

    # Calculate and print key improvements
    print(f'\n{"="*55}')
    print('  KEY IMPROVEMENTS')
    print(f'{"="*55}')

    def show(label, bval, pval, unit=''):
        diff = bval - pval
        pct  = (diff/bval*100) if bval != 0 else 0
        arrow = '✅' if diff > 0 else ('⚠️ ' if diff < 0 else '➖')
        print(f'  {arrow}  {label}: {bval:.1f}{unit} → {pval:.1f}{unit}  ({pct:.1f}% reduction)')

    show('Packets Dropped',       baseline['dropped_total'],     predicted['dropped_total'])
    show('Avg Queue Node 2',      baseline['avg_queue_n2'],      predicted['avg_queue_n2'],  ' pkts')
    show('Avg Delay  Node 2',     baseline['avg_delay_n2']*1000, predicted['avg_delay_n2']*1000, ' ms')
    show('Congestion Events',     baseline['congested_events'],  predicted['congested_events'])
    print(f'\n  ⚡  First reroute triggered at: t={predicted["reroute_times"][0]:.1f}s (early prediction)')

    print(f'\n  Generating comparison chart...')
    plot_comparison(baseline, predicted)