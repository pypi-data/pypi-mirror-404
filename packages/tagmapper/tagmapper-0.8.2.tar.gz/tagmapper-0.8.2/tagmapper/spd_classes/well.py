from typing import List
import pandas as pd

from tagmapper.connector_api import get_api_client
from commonlib_reader import Facility
from tagmapper.generic_model import Attribute
from tagmapper.mapping import Timeseries
from tagmapper.spd_classes.base_model import Base


class Well(Base):
    """
    Well class
    """

    _well_attributes = pd.DataFrame()
    _well_header = pd.DataFrame()

    def __init__(self, uwi):

        if isinstance(uwi, str):
            # assume data is UWI
            data = Well.get_attributes(uwi)
        elif isinstance(uwi, pd.DataFrame):
            data = uwi

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a dataframe")

        if data.empty:
            raise ValueError("Input data can not be empty")
        super().__init__(data["unique_well_identifier"].iloc[0])

        for _, r in data.iterrows():
            self._attributes.append(r.to_dict())

    @property
    def uwi(self):
        return self._ui

    @property
    def ioc_name(self) -> str:
        # Placeholder implementation, to be deleted when header table is in place
        return self.uwi

    @property
    def functional_location(self) -> str:
        # Placeholder implementation, to be deleted when header table is in place
        raise NotImplementedError("No header table exist for wells yet")

    @property
    def tag_no(self) -> str:
        # Placeholder implementation, to be deleted when header table is in place
        raise NotImplementedError("No header table exist for wells yet")

    @property
    def attribute(self) -> list[Timeseries]:
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
    def get_wells(cls, facility: str = "") -> List["Well"]:
        return Well.get_objects(facility=facility)

    @classmethod
    def get_object_names(cls, facility: str = "") -> List[str]:
        return cls.get_uwis(facility=facility)

    @classmethod
    def get_uwis(cls, facility: str = "") -> List[str]:
        df_attributes = cls.get_attributes()
        if facility != "":
            fac = Facility(facility)
            ind = df_attributes["gov_fcty_name"] == fac.resolve_gov_facility_name()
            if any(ind):
                return sorted(set(df_attributes["unique_well_identifier"][ind]))
            else:
                return []
        return sorted(set(df_attributes["unique_well_identifier"]))

    @classmethod
    def get_attributes(cls, upi: str = ""):
        if cls._well_attributes.empty:
            data = get_api_client().get_json(
                url="/well-attributes-mapped-to-timeseries-all",
                params={"limit": 100000},
            )
            if isinstance(data, dict) and "data" in data.keys():
                cls._well_attributes = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for well attributes")

        if upi:
            ind = cls._well_attributes["unique_well_identifier"] == upi
            return cls._well_attributes[ind]

        return cls._well_attributes

    @classmethod
    def get_header(cls, upi: str = ""):
        raise NotImplementedError("No header table exist for wells yet")

        if cls._well_header.empty:
            param = {"limit": 100000}
            data = get_api_client().get_json(url="/well-header", params=param)
            if isinstance(data, dict) and "data" in data.keys():
                cls._well_header = pd.DataFrame(data=data["data"])
            else:
                raise ValueError("No data found from API for well header")

        if upi:
            ind = cls._well_header["unique_well_identifier"] == upi
            return cls._well_header[ind]

        return cls._well_header
