"""ViSP modulator state parser."""

from dkist_processing_common.models.constants import BudName
from dkist_processing_common.models.tags import StemName
from dkist_processing_common.parsers.single_value_single_key_flower import (
    SingleValueSingleKeyFlower,
)
from dkist_processing_common.parsers.unique_bud import UniqueBud

from dkist_processing_visp.models.fits_access import VispMetadataKey
from dkist_processing_visp.parsers.visp_l0_fits_access import VispL0FitsAccess


class ObserveFrameError(BaseException):
    """Error raised when no observe frames are identified by polarization mode."""

    pass


class NumberModulatorStatesBud(UniqueBud):
    """Bud to check the number of modulator states."""

    def __init__(self):
        super().__init__(
            constant_name=BudName.num_modstates.value,
            metadata_key=VispMetadataKey.number_of_modulator_states,
        )
        self.polarimeter_mode_set = set()

    def setter(self, fits_obj: VispL0FitsAccess) -> int:
        """
        Set the value of the bud.

        Parameters
        ----------
        fits_obj:
            A single FitsAccess object
        """
        pol_mode = getattr(fits_obj, VispMetadataKey.polarimeter_mode.name)
        self.polarimeter_mode_set.add(pol_mode)
        return super().setter(fits_obj)

    def getter(self):
        """Get the value of the bud, checking for restrictions on polarimetric observe data."""
        if "observe_intensity" in self.polarimeter_mode_set:
            return 1

        # Polarimetric data must have the same number of modulator states in all frames
        if "observe_polarimetric" in self.polarimeter_mode_set:
            return super().getter()

        raise ObserveFrameError(
            "No valid observe frames types were found in the headers of the data. Check the input data."
        )


class ModulatorStateFlower(SingleValueSingleKeyFlower):
    """Flower to find the ip task type."""

    def __init__(self):
        super().__init__(
            tag_stem_name=StemName.modstate.value, metadata_key=VispMetadataKey.modulator_state
        )
        self.polarimeter_mode_set = set()

    def setter(self, fits_obj: VispL0FitsAccess) -> int:
        """
        Set value of the flower.

        Parameters
        ----------
        fits_obj:
            A single FitsAccess object
        """
        pol_mode = getattr(fits_obj, VispMetadataKey.polarimeter_mode.name)
        self.polarimeter_mode_set.add(pol_mode)
        return super().setter(fits_obj)

    def getter(self, key: str) -> int:
        """Return the modulator state given in the header of each file unless it is in intensity mode - then return modulator state = 1 for everything."""
        if "observe_intensity" in self.polarimeter_mode_set:
            return 1
        return super().getter(key)
