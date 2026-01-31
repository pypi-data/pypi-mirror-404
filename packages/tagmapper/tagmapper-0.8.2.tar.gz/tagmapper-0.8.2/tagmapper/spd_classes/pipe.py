from commonlib_reader import Facility
import pandas as pd

from tagmapper.generic_model import Attribute
from tagmapper.mapping import Timeseries
from .base_model import Base
from tagmapper.connector_api import get_api_client


class Pipe(Base):
    """
    Pipe class
    """

    _pipe_attributes = pd.DataFrame()
    _pipe_header = pd.DataFrame()

    def __init__(self, upi):

        if isinstance(upi, pd.DataFrame):
            if upi.empty:
                raise ValueError("Input dataframe is empty")

            attributes = upi
            if "unique_pipe_identifier" not in attributes.columns:
                raise ValueError(
                    "Invalid dataframe input, must contain 'unique_pipe_identifier' column"
                )
            upi = attributes["unique_pipe_identifier"].values[0]
            if not all(attributes["unique_pipe_identifier"] == upi):
                raise ValueError(
                    "DataFrame contains multiple unique_pipe_identifier values"
                )
        elif isinstance(upi, str):
            attributes = Pipe.get_attributes(upi)

        super().__init__(upi)

        for _, r in attributes.iterrows():
            self._attributes.append(r.to_dict())

    @property
    def upi(self) -> str:
        return self._ui

    @property
    def attribute(self) -> list[Attribute]:
        attributes = []
        for attr in self._attributes:
            attr["identifier"] = getattr(attr, "attribute_identifier", "")
            attr["alias"] = getattr(attr, "attribute_alias", "")
            attr["description"] = getattr(attr, "attribute_description", "")

            # attribute name is not included in api data
            att = Attribute(
                name=getattr(
                    attr, "attribute_name", getattr(attr, "attribute_identifier", "")
                ),
                data=attr,
            )
            att.add_mapping(Timeseries(data=attr))
            attributes.append(att)

        return attributes

    @classmethod
    def get_pipes(cls, facility: str = ""):
        return Pipe.get_objects(facility=facility)

    @classmethod
    def get_object_names(cls, facility: str = "") -> list[str]:
        return cls.get_mapped_upi_list(facility=facility)

    @classmethod
    def get_upi(cls, facility: str = "") -> list[str]:
        df_attributes = cls.get_attributes()
        if facility != "":
            fac = Facility(facility)
            ind = df_attributes["gov_fcty_name"] == fac.resolve_gov_facility_name()
            if any(ind):
                return sorted(set(df_attributes["unique_pipe_identifier"][ind]))
            else:
                return []
        return sorted(set(df_attributes["unique_pipe_identifier"]))

    @classmethod
    def get_upi_list(cls):
        df_pipe_header = cls.get_header()
        return sorted(set(df_pipe_header["unique_pipe_identifier"]))

    @classmethod
    def get_mapped_upi_list(cls, facility: str = ""):
        return cls.get_upi(facility=facility)

    @classmethod
    def get_attributes(cls, upi: str = ""):
        if cls._pipe_attributes.empty:
            data = get_api_client().get_json(
                url="/pipe-attributes-mapped-to-timeseries-all",
                params={"limit": 100000},
            )
            if isinstance(data, dict) and "data" in data.keys():
                cls._pipe_attributes = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for pipe attributes")

        if upi:
            ind = cls._pipe_attributes["unique_pipe_identifier"] == upi
            return cls._pipe_attributes[ind]

        return cls._pipe_attributes

    @classmethod
    def get_header(cls, upi: str = ""):
        if cls._pipe_header.empty:
            param = {"limit": 100000}
            data = get_api_client().get_json(url="/pipe-header", params=param)
            if isinstance(data, dict) and "data" in data.keys():
                cls._pipe_header = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for pipe header")

        if upi:
            ind = cls._pipe_header["unique_pipe_identifier"] == upi
            return cls._pipe_header[ind]

        return cls._pipe_header
