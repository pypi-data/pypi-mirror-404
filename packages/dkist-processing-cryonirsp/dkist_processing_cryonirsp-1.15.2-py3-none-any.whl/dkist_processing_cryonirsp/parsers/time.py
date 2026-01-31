"""Buds to parse exposure time."""

from dkist_processing_common.models.flower_pot import SetStem

from dkist_processing_cryonirsp.models.constants import CryonirspBudName
from dkist_processing_cryonirsp.parsers.cryonirsp_l0_fits_access import CryonirspRampFitsAccess


class CryonirspTimeObsBud(SetStem):
    """
    Produce a tuple of all time_obs values present in the dataset.

    The time_obs is a unique identifier for all raw frames in a single ramp. Hence, this list identifies all
    the ramps that must be processed in a data set.
    """

    def __init__(self):
        super().__init__(stem_name=CryonirspBudName.time_obs_list.value)

    def setter(self, fits_obj: CryonirspRampFitsAccess) -> str:
        """
        Set the time_obs for this fits object.

        Parameters
        ----------
        fits_obj
            The input fits object
        Returns
        -------
        The time_obs value associated with this fits object
        """
        return fits_obj.time_obs

    def getter(self) -> tuple:
        """
        Get the sorted tuple of time_obs values.

        Returns
        -------
        A tuple of exposure times
        """
        time_obs_tup = tuple(sorted(self.value_set))
        return time_obs_tup
