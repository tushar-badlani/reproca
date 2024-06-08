from pymemcache import serde
from pymemcache.client.base import Client


class Memcache(Client):
    def __init__(self, address: tuple[str, int] | str) -> None:
        super().__init__(address, serde=serde.pickle_serde)

    def rate_limit(self, accessor: str, resource: str, rate: int) -> bool:
        """Rate limit an accessor for a resource.

        Returns True if the accessor is NOT allowed to access the resource.

        Args:
        ----
            accessor: The accessor to rate limit.
            resource: The resource to rate limit.
            rate: The rate limit in seconds.

        """
        lock = self.get(f"accessor={accessor};resource={resource}")
        if lock:
            return True
        self.set(f"accessor={accessor};resource={resource}", True, expire=rate)
        return False
