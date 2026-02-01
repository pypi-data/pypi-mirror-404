class ResilionCore:
    """
    Core entry point for the RESILION framework.

    This class is intentionally minimal for v0.0.1,
    but establishes the public API and package legitimacy.
    """

    def __init__(self, name: str = "resilion"):
        self.name = name

    def info(self) -> dict:
        """
        Return basic framework metadata.
        """
        return {
            "framework": "resilion",
            "version": "0.0.1",
            "purpose": "mission resilience modeling",
            "domains": [
                "space systems",
                "human performance (future)",
                "infrastructure (future)",
            ],
        }
