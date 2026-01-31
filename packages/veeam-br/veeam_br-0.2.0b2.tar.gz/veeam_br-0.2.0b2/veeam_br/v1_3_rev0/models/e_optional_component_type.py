from enum import Enum


class EOptionalComponentType(str, Enum):
    CATALYSTSDK = "CatalystSdk"
    CIFSGATEWAY = "CifsGateway"
    DDBOOSTSDK = "DDBoostSdk"
    GUESTINTERACTIONPROXY = "GuestInteractionProxy"
    MOUNTTARGET = "MountTarget"
    NFSGATEWAY = "NfsGateway"
    SNAPDIFFV3 = "SnapDiffV3"

    def __str__(self) -> str:
        return str(self.value)
