"""Discovery module initialization"""

from appxploit.discovery.secrets import SecretsDiscovery
from appxploit.discovery.endpoints import EndpointExtractor

__all__ = ["SecretsDiscovery", "EndpointExtractor"]
