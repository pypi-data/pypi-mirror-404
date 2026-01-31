import shutil

import numpy as np
import pytest
from dkist_processing_common._util.scratch import WorkflowFileSystem
from dkist_processing_common.codecs.json import json_encoder

from dkist_processing_dlnirsp.models.tags import DlnirspTag
from dkist_processing_dlnirsp.tasks.movie import MakeDlnirspMovie
from dkist_processing_dlnirsp.tests.conftest import CalibratedHeaders
from dkist_processing_dlnirsp.tests.conftest import DlnirspTestingConstants
from dkist_processing_dlnirsp.tests.conftest import DlnirspTestingParameters
from dkist_processing_dlnirsp.tests.conftest import write_calibrated_frames_to_task


@pytest.fixture
def movie_task(recipe_run_id, tmp_path, link_constants_db, assign_input_dataset_doc_to_task):
    link_constants_db(
        recipe_run_id=recipe_run_id,
        constants_obj=DlnirspTestingConstants(),
    )
    with MakeDlnirspMovie(
        recipe_run_id=recipe_run_id,
        workflow_name="workflow_name",
        workflow_version="workflow_version",
    ) as task:
        assign_input_dataset_doc_to_task(
            task,
            DlnirspTestingParameters(),
            arm_id="VIS",
        )
        task.scratch = WorkflowFileSystem(scratch_base_path=tmp_path, recipe_run_id=recipe_run_id)

        yield task
        task._purge()


@pytest.fixture(scope="session")
def num_spectral_pix() -> int:
    return 396


@pytest.fixture(scope="session")
def valid_wavelength_solution_header(num_spectral_pix) -> dict[str, str | int | float]:
    """A valid wavelength solution header that depends on `arm_id='vis'` in `movie_task`."""
    return {
        "CTYPE3": "AWAV-GRA",
        "CUNIT3": "nm",
        "CRPIX3": num_spectral_pix // 2,
        "CRVAL3": 854.17,
        "CDELT3": 0.00229,
        "PV3_0": 23000,
        "PV3_1": 90,
        "PV3_2": 65.69,
    }


def mindices_data_func(frame: CalibratedHeaders) -> np.ndarray:
    shape = frame.array_shape

    return np.ones(shape) * (1000 * frame.current_MINDEX1_value + 100 * frame.current_MINDEX2_value)


@pytest.mark.parametrize(
    "has_multiple_mosaics",
    [pytest.param(True, id="multi_mosaic"), pytest.param(False, id="single_mosaic")],
)
@pytest.mark.parametrize(
    "is_polarimetric",
    [pytest.param(True, id="polarimetric"), pytest.param(False, id="spectrographic")],
)
@pytest.mark.parametrize(
    "is_mosaiced", [pytest.param(True, id="mosaiced"), pytest.param(False, id="no_mosaic")]
)
def test_movie_task(
    movie_task,
    has_multiple_mosaics,
    is_polarimetric,
    is_mosaiced,
    num_spectral_pix,
    valid_wavelength_solution_header,
    link_constants_db,
    mocker,
    fake_gql_client,
):
    """
    Given: A `MakeDlnirspMovie` task with CALIBRATED frames
    When: Running the task
    Then: The dang thing runs and produces the expected movie file
    """
    mocker.patch(
        "dkist_processing_common.tasks.mixin.metadata_store.GraphQLClient", new=fake_gql_client
    )

    num_dither = 1
    num_mosaics = 2 if has_multiple_mosaics else 1
    num_X_tiles = 2 if is_mosaiced else 1
    num_Y_tiles = 2 if is_mosaiced else 1
    stokes_params = ["I"]
    if is_polarimetric:
        stokes_params += ["Q", "U", "V"]
        num_modstates = 8
        pol_mode = "Full Stokes"
    else:
        num_modstates = 1
        pol_mode = "Stokes I"

    task = movie_task

    constants_db = DlnirspTestingConstants(
        POLARIMETER_MODE=pol_mode,
        NUM_DITHER_STEPS=num_dither,
        NUM_MOSAIC_REPEATS=num_mosaics,
        NUM_MOSAIC_TILES_X=num_X_tiles,
        NUM_MOSAIC_TILES_Y=num_Y_tiles,
        NUM_MODSTATES=num_modstates,
    )
    link_constants_db(task.recipe_run_id, constants_db)

    write_calibrated_frames_to_task(
        task,
        num_mosaics=num_mosaics,
        num_X_tiles=num_X_tiles,
        num_Y_tiles=num_Y_tiles,
        dither_mode_on=False,
        is_polarimetric=is_polarimetric,
        array_shape=(num_spectral_pix, 20, 30),
        data_func=mindices_data_func,
    )

    task.write(
        data=valid_wavelength_solution_header,
        tags=[DlnirspTag.intermediate(), DlnirspTag.task_wavelength_solution()],
        encoder=json_encoder,
    )

    task()

    movie_file_list = list(task.read(tags=[DlnirspTag.output(), DlnirspTag.movie()]))

    assert len(movie_file_list) == 1
