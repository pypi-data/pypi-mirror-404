"""Analysis module initialization"""

from appxploit.analysis.manifest import ManifestAnalyzer
from appxploit.analysis.components import ComponentAnalyzer
from appxploit.analysis.permissions import PermissionAnalyzer
from appxploit.analysis.security_flags import SecurityFlagsAnalyzer
from appxploit.analysis.deeplink_analyzer import DeepLinkAnalyzer

__all__ = ["ManifestAnalyzer", "ComponentAnalyzer", "PermissionAnalyzer", "SecurityFlagsAnalyzer", "DeepLinkAnalyzer"]
