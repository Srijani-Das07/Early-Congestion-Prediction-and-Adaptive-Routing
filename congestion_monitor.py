# Thresholds for congestion prediction
QUEUE_THRESHOLD = 10    # More than 10 packets waiting = warning
DELAY_THRESHOLD = 0.05  # More than 50ms delay = warning
RATE_THRESHOLD = 80     # More than 80 packets/sec = warning


class NodeMonitor:
    def __init__(self, node_id):
        self.node_id = node_id
        self.queue_length = 0
        self.delay = 0.0
        self.traffic_rate = 0
        self.congestion_score = 0

    def update(self, queue_length, delay, traffic_rate):
        self.queue_length = queue_length
        self.delay = delay
        self.traffic_rate = traffic_rate

    def predict_congestion(self):
        score = 0
        if self.queue_length > QUEUE_THRESHOLD:
            score += 1
        if self.delay > DELAY_THRESHOLD:
            score += 1
        if self.traffic_rate > RATE_THRESHOLD:
            score += 1
        self.congestion_score = score
        # Congestion predicted if 2 or more metrics are high
        return score >= 2

    def report(self):
        status = 'CONGESTED' if self.predict_congestion() else 'OK'
        print(f'Node {self.node_id}: Queue={self.queue_length}, '
              f'Delay={self.delay:.3f}s, Rate={self.traffic_rate} pkt/s, Status={status}')


if __name__ == '__main__':
    print("--- Testing Congestion Monitor ---")

    # Test a normal node
    m1 = NodeMonitor(1)
    m1.update(queue_length=3, delay=0.01, traffic_rate=20)
    m1.report()

    # Test a congested node
    m2 = NodeMonitor(2)
    m2.update(queue_length=12, delay=0.06, traffic_rate=85)
    m2.report()
