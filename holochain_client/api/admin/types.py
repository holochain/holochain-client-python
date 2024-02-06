
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

@dataclass
class WireMessageRequest:
    id: int
    data: List[int]
    type: str = "request"

@dataclass
class AdminRequest:
    type: str
    data: Dict

AppStatusFilter = Enum("AppStatusFilter", ["Enabled", "Disabled", "Running", "Stopped", "Paused"])

@dataclass
class ListApps:
    status_filter: Optional[AppStatusFilter] = None

@dataclass
class DumpNetworkStats:
    pass

@dataclass
class AppInfo:
    installed_app_id: str
    # TODO other fields
    # cell_info: Dict[str, List[CellInfo]]
    # status: AppinfoStatus
    # agent_pub_key: str
    # manifest: AppManifest
