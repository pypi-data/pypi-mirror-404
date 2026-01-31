from enum import Enum


class EApplicationPluginType(str, Enum):
    MSSQL = "MSSQL"
    ORACLERMAN = "OracleRMAN"
    SAPHANA = "SAPHANA"
    SAPONORACLE = "SAPOnOracle"

    def __str__(self) -> str:
        return str(self.value)
