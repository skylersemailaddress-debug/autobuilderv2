class RetryPolicy:
    def __init__(self, max_repairs: int = 1):
        self.max_repairs = max_repairs

    def can_retry(self, repair_count: int) -> bool:
        return repair_count < self.max_repairs
