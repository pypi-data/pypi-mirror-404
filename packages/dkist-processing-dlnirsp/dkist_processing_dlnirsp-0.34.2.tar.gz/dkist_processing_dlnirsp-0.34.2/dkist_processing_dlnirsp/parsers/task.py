"""Custom parsers to identify task sub-groupings not captured by a single header key."""

from dkist_processing_common.models.fits_access import MetadataKey
from dkist_processing_common.models.tags import StemName
from dkist_processing_common.parsers.single_value_single_key_flower import (
    SingleValueSingleKeyFlower,
)
from dkist_processing_common.parsers.task import parse_header_ip_task_with_gains

from dkist_processing_dlnirsp.parsers.dlnirsp_l0_fits_access import DlnirspL0FitsAccess


class DlnirspTaskTypeFlower(SingleValueSingleKeyFlower):
    """Flower to find the DLNIRSP task type."""

    def __init__(self):
        super().__init__(tag_stem_name=StemName.task.value, metadata_key=MetadataKey.ip_task_type)

    def setter(self, fits_obj: DlnirspL0FitsAccess):
        """
        Set value of the flower.

        Parameters
        ----------
        fits_obj:
            A single FitsAccess object
        """
        return parse_header_ip_task_with_gains(fits_obj)
