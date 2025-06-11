from dataclasses import dataclass, field
from datetime import datetime
from pprint import pprint
from typing import List


@dataclass
class Subscription:
    """訂閱資料類別"""
    user_id: str
    difficulty_id: str
    difficulty_name: str
    count: int
    time: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SubscriptionManager:
    def __init__(self):
        self.subscriptions: List[Subscription] = []

    def add_subscription(self, subscription: Subscription):
        """新增訂閱"""
        self.subscriptions.append(subscription)

    def get_user_subscriptions(self, user_id: str) -> List[Subscription]:
        """獲取使用者的訂閱"""
        return [s for s in self.subscriptions if s.user_id == user_id]

    def remove_user_subscriptions(self, user_id: str):
        """移除使用者的所有訂閱"""
        self.subscriptions = [s for s in self.subscriptions if s.user_id != user_id]

    def get_all_subscriptions(self) -> List[Subscription]:
        """獲取所有訂閱"""
        return self.subscriptions

    def get_subscriptions_by_time(self, time: str) -> List[Subscription]:
        """獲取指定時段的所有訂閱"""
        return [s for s in self.subscriptions if s.time == time]


# 使用範例資料初始化
if __name__ == "__main__":
    manager = SubscriptionManager()

    data = [
        {
            "user_id": "user_123",
            "difficulty_id": "diff_001",
            "difficulty_name": "中等",
            "count": 3,
            "time": "08:00",
            "created_at": "2025-06-11T15:30:00.000000"
        },
        {
            "user_id": "user_123",
            "difficulty_id": "diff_002",
            "difficulty_name": "困難",
            "count": 2,
            "time": "09:00",
            "created_at": "2025-06-11T15:35:00.000000"
        },
        {
            "user_id": "user_456",
            "difficulty_id": "diff_001",
            "difficulty_name": "中等",
            "count": 1,
            "time": "08:00",
            "created_at": "2025-06-11T15:40:00.000000"
        }
    ]

    for item in data:
        manager.add_subscription(Subscription(**item))

    # 示範呼叫
    print("user_123 的訂閱：")
    pprint(manager.get_user_subscriptions("user_123"))

    print("\n所有訂閱：")
    pprint(manager.get_all_subscriptions())

    print("\n08:00 的訂閱：")
    pprint(manager.get_subscriptions_by_time("08:00"))

    manager.remove_user_subscriptions("user_123")

    print("\n移除 user_123 後的訂閱：")
    pprint(manager.get_all_subscriptions())
