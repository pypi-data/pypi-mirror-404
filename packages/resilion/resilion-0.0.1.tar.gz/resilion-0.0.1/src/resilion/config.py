from dataclasses import dataclass

@dataclass
class ResilionConfig:
    """
    Configuration container for RESILION runs.
    """
    mission_name: str = "default"
    domain: str = "space"
    enable_uncertainty: bool = True
