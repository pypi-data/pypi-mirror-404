"""Module for making highly-custom DL-NIRSP movies."""

import logging
import warnings
from datetime import datetime
from datetime import timedelta
from functools import cached_property
from functools import partial
from itertools import repeat
from logging import getLogger
from pathlib import Path

import astropy.units as u
import imageio_ffmpeg
import numpy as np
from astropy.convolution import interpolate_replace_nans
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning
from astropy.visualization.wcsaxes import WCSAxes
from astropy.wcs import WCS
from astropy.wcs.utils import wcs_to_celestial_frame
from dkist_processing_common.codecs.fits import fits_hdu_decoder
from dkist_processing_common.codecs.json import json_decoder
from dkist_processing_common.models.dkist_location import location_of_dkist
from dkist_processing_common.tasks import WriteL1Frame
from dkist_service_configuration.logging import logger
from dkist_spectral_lines import get_closest_spectral_line
from matplotlib import animation
from matplotlib import pyplot as plt
from matplotlib import rcdefaults
from matplotlib import rcParams
from matplotlib.axes import Axes
from matplotlib.patches import Polygon
from matplotlib.text import Text
from reproject import reproject_interp
from reproject.mosaicking import find_optimal_celestial_wcs
from reproject.mosaicking import reproject_and_coadd
from sunpy.coordinates import HeliocentricInertial
from sunpy.coordinates import Helioprojective
from sunpy.coordinates import SphericalScreen

from dkist_processing_dlnirsp.models.tags import DlnirspTag
from dkist_processing_dlnirsp.parsers.dlnirsp_l0_fits_access import DlnirspL0FitsAccess
from dkist_processing_dlnirsp.tasks.dlnirsp_base import DlnirspTaskBase

__all__ = ["MakeDlnirspMovie"]

reproject_logger = getLogger("reproject.mosaicking.coadd")
reproject_logger.setLevel(logging.WARNING)
warnings.simplefilter("ignore", category=AstropyWarning)
warnings.simplefilter("ignore", category=RuntimeWarning)


class MakeDlnirspMovie(DlnirspTaskBase):
    """
    Task class for DL-NIRSP quicklook movie generation from CALIBRATED frames.

    Parameters
    ----------
    recipe_run_id : int
        id of the recipe run used to identify the workflow run this task is part of
    workflow_name : str
        name of the workflow to which this instance of the task belongs
    workflow_version : str
        version of the workflow to which this instance of the task belongs
    """

    def setup_look_and_feel(self) -> None:
        """Initialize figure and movie parameters that affect the overall look of the movie."""
        rcdefaults()

        # Use the cross-platform ffmpeg binary provided by `imageio_ffmpeg`
        rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"mpl ffmpeg path set to {rcParams['animation.ffmpeg_path']}")

        width_pixels = 1920
        height_pixels = 1080
        self.dpi = 300
        self.fig_width_inches = width_pixels / self.dpi
        self.fig_height_inches = height_pixels / self.dpi

        # Define the location of the mosaic axes
        self.mosaic_left = 0.3
        self.mosaic_bottom = 0.06
        self.mosaic_width = 0.33
        self.mosaic_height = 0.36
        self.mosaic_h_padding = 0.02
        self.mosaic_v_padding = 0.05

        # Fraction of full axis size to pad limits
        self.fractional_mosaic_axis_limit_pad = 0.01

        self.spec_left = 0.02
        self.spec_bottom = 0.06
        self.spec_width = 0.1
        self.spec_height = 0.11
        self.spec_h_padding = 0.01
        self.spec_v_padding = 0.03
        self.stack_height = 0.65

        self.arrow_x = 0.92
        self.arrow_y = 0.88
        self.arrow_length = 0.08

        axis_frame_linewidth = 0.5

        maximum_duration_ms = 3 * 60.0 * 1000
        maximum_interval_ms = 300.0

        # We don't care about dithers here, because they will be stitched into the same mosaic
        self.num_movie_frames = (
            self.constants.num_mosaic_repeats
            * self.constants.num_mosaic_tiles_x
            * self.constants.num_mosaic_tiles_y
        )

        # Ensures we won't be longer than the max duration or slower than the maximum interval
        duration_ms = min(maximum_duration_ms, self.num_movie_frames * maximum_interval_ms)
        self.frame_interval = duration_ms / self.num_movie_frames
        logger.info(
            f"With {self.num_movie_frames} frames the frame interval will be {self.frame_interval} ms"
        )

        plt.rcParams.update(
            {
                "figure.dpi": self.dpi,
                "font.size": 9,  # Default font size for all text
                "font.family": "DejaVu Sans",
                "image.origin": "lower",
                "image.cmap": "gray",
                "image.interpolation": "nearest",
                "axes.labelsize": 9,  # Font size for x and y labels
                "xtick.labelsize": 5,  # Font size for x-axis ticks
                "ytick.labelsize": 5,  # Font size for y-axis ticks
                "lines.linewidth": 0.7,
                "axes.linewidth": axis_frame_linewidth,
                "xtick.major.width": axis_frame_linewidth,
                "xtick.minor.width": axis_frame_linewidth,
                "ytick.major.width": axis_frame_linewidth,
                "ytick.minor.width": axis_frame_linewidth,
            }
        )

    def run(self):
        """
        Build a movie showing mosaic images, stacked spectra, and single spectral plots.

        Each mosaic step is a single "frame" in the movie. If the data are polarimetric then a core and continuum
        image/spectrum are shown for both Stokes I and V. For intensity mode data the Stokes V images are replaced with
        text stating the dataset is intensity mode.

        The steps of this method are:

        #. Setup/compute movie metadata (spectral line, wavelength indices for core and continuum, etc.)
        #. Read all Stokes I and (if available) Stokes V CALIBRATED frames and order by DATE-BEG
        #. Using all Stokes I frames, compute a reference WCS that will be the canvas for all mosaic images
        #. Set up the plotting canvas. This involves places axes, filling them with data from the first step, and setting instance variables that will be updated for each movie frame
        #. Animate the plot for each scan step and save the resultant movie file
        """
        with self.telemetry_span("Set up movie variables"):
            self.setup_look_and_feel()
            obs_part_id = self.metadata_store_input_dataset_observe_frames.inputDatasetPartId
            self.product_id = WriteL1Frame.compute_product_id(obs_part_id, "L1")

            any_header = self.add_L1_header_values(self.get_any_calibrated_header())
            single_step_spatial_shape = (any_header["NAXIS2"], any_header["NAXIS1"])
            self.num_wave = any_header["NAXIS3"]
            self.num_spec = np.prod(single_step_spatial_shape)
            logger.info(
                f"Each step has spatial shape {single_step_spatial_shape} => {self.num_spec} total spectra"
            )
            logger.info(f"There are {self.num_wave} wavelength pixels")

            self.wave_abscissa = self.compute_wavelength_abscissa(any_header)
            self.core_wave_idx = np.argmin(
                np.abs(self.wave_abscissa - self.parameters.movie_core_wave_value_nm)
            )
            self.cont_wave_idx = np.argmin(
                np.abs(self.wave_abscissa - self.parameters.movie_cont_wave_value_nm)
            )
            central_wave = np.nanmean(self.wave_abscissa)
            self.spectral_line_name = get_closest_spectral_line(central_wave * u.nm).name
            logger.info(
                f"With center wavelength {central_wave:.3f} nm the spectral line is {self.spectral_line_name}"
            )

        with self.telemetry_span("Read CALIBRATED files"):
            logger.info("Reading CALIBRATED files")
            self.I_file_list = sorted(
                self.read(
                    tags=[DlnirspTag.calibrated(), DlnirspTag.frame(), DlnirspTag.stokes("I")]
                ),
                key=lambda fo: fits.getheader(fo)["DATE-OBS"],
            )
            self.V_file_list = sorted(
                self.read(
                    tags=[DlnirspTag.calibrated(), DlnirspTag.frame(), DlnirspTag.stokes("V")]
                ),
                key=lambda fo: fits.getheader(fo)["DATE-OBS"],
            )

        with self.telemetry_span("Compute reference WCS"):
            self.reference_wcs, self.full_mosaic_shape = self.compute_reference_wcs(
                self.I_file_list, single_step_spatial_shape
            )
            self.reference_coord_frame = wcs_to_celestial_frame(self.reference_wcs)
            reference_observer = self.reference_coord_frame.observer
            self.spherical_screen = SphericalScreen(center=reference_observer, only_off_disk=True)

        with self.telemetry_span("Initialize plot"):
            logger.info("Setting up plot")
            self.currently_shown_mosaic = 0
            self.fig = self.init_plot()

        with self.telemetry_span("Render movie"):
            logger.info("Rendering movie")
            relative_movie_path = f"{self.constants.dataset_id}_browse_movie.mp4"
            absolute_movie_path = str(self.scratch.absolute_path(relative_movie_path))
            update_func = partial(
                update_plot, task_obj=self, is_polarimetric=self.constants.correct_for_polarization
            )
            ani = animation.FuncAnimation(
                fig=self.fig,
                func=update_func,
                frames=self.num_movie_frames,
                interval=self.frame_interval,
            )
            ani.save(filename=absolute_movie_path, writer="ffmpeg", dpi=self.dpi)
            self.tag(path=absolute_movie_path, tags=[DlnirspTag.output(), DlnirspTag.movie()])

    @cached_property
    def wavelength_solution(self) -> dict[str, str | int | float]:
        """Load the wavelength solution from disk."""
        return next(
            self.read(
                tags=[DlnirspTag.intermediate(), DlnirspTag.task_wavelength_solution()],
                decoder=json_decoder,
            )
        )

    def get_any_calibrated_header(self) -> fits.Header:
        """Return *any* calibrated header."""
        tags = [DlnirspTag.calibrated(), DlnirspTag.frame()]
        return next(self.read(tags=tags, decoder=fits_hdu_decoder)).header

    def compute_wavelength_abscissa(self, header: fits.Header) -> np.ndarray:
        """
        Compute a wavelength vector from the WCS in a header.

        The header passed in should have a spectral WCS axis.
        """
        wcs = WCS(header)
        abscissa = wcs.spectral.pixel_to_world(np.arange(self.num_wave)).to_value(u.nm)
        return abscissa

    def compute_reference_wcs(
        self, file_list: list[Path], spatial_shape: tuple[int, int]
    ) -> tuple[WCS, tuple[int, int]]:
        """Examine the spatial extents of *all* calibrated files and compute an optimal WCS region that covers all mosaics."""
        logger.info("Parsing headers")
        wcs_list = []
        for f in file_list:
            hdul = fits.open(f)
            header = self.add_L1_header_values(hdul[0].header)
            wcs_list.append(WCS(header).dropaxis(2))
            del hdul

        logger.info("Computing reference WCS")
        reference_wcs, shape_out = find_optimal_celestial_wcs(
            tuple(zip(repeat(spatial_shape), wcs_list)),
            auto_rotate=False,
            negative_lon_cdelt="auto",
        )

        return reference_wcs, shape_out

    def init_plot(self):
        """
        Initialize the full plotting canvas and fill with data from the first mosaic step.

        This function lays out the axes for each individual plot and defines instance properties for the parts of the
        figure that will change when the plot is updated. This properties can then be referenced and modified in
        `update_plot`.
        """
        logger.info("Computing initial mosaics")
        I_mosaic_data, I_mosaic_WCS, I_mosaic_dates = self.read_mosaic_frames(
            mosaic_num=0, stokes="I"
        )
        I_mosaic_list = self.build_mosaic_images(data_list=I_mosaic_data, wcs_list=I_mosaic_WCS)

        core_iscales = np.nanpercentile(I_mosaic_list[0], [5, 95]) + np.array([-0.1, 0.1])
        cont_iscales = np.nanpercentile(I_mosaic_list[1], [5, 95]) + np.array([-0.1, 0.1])

        if self.constants.correct_for_polarization:
            V_mosaic_data, V_mosaic_WCS, _ = self.read_mosaic_frames(mosaic_num=0, stokes="V")
            V_mosaic_list = self.build_mosaic_images(data_list=V_mosaic_data, wcs_list=V_mosaic_WCS)

            V_core_ratio = V_mosaic_list[0] / I_mosaic_list[0]
            V_cont_ratio = V_mosaic_list[1] / I_mosaic_list[1]
            core_vscale = np.nanpercentile(np.abs(V_core_ratio), 95)
            cont_vscale = np.nanpercentile(np.abs(V_cont_ratio), 95)
            self.vscale = np.nanmax([core_vscale, cont_vscale])
        else:
            V_core_ratio = np.empty_like(I_mosaic_list[0]) * np.nan
            V_cont_ratio = np.empty_like(I_mosaic_list[0]) * np.nan
            core_vscale = 1.0
            cont_vscale = 1.0
            self.vscale = 1.0

        fig = plt.figure(figsize=(self.fig_width_inches, self.fig_height_inches))

        logger.info("Building mosaic plots")
        self._init_mosaic_plots(
            fig=fig,
            I_core_mosaic=I_mosaic_list[0],
            I_cont_mosaic=I_mosaic_list[1],
            V_core_ratio=V_core_ratio,
            V_cont_ratio=V_cont_ratio,
            core_iscales=core_iscales,
            cont_iscales=cont_iscales,
            core_vscale=core_vscale,
            cont_vscale=cont_vscale,
        )

        logger.info("Building stack plots")

        I_stack = self.get_stacked_spectra(self.I_file_list[0])
        if self.constants.correct_for_polarization:
            V_stack = self.get_stacked_spectra(self.V_file_list[0])
            V_ratio = V_stack / I_stack
        else:
            V_ratio = np.empty_like(I_stack) * np.nan

        I_stack_axis = self._init_stack_plots(fig=fig, I_stack=I_stack, V_ratio=V_ratio)

        logger.info("Building spectral plots")
        self._init_spectral_plots(
            fig=fig, I_stack_axis=I_stack_axis, I_stack=I_stack, V_ratio=V_ratio
        )

        fig.text(
            0.3,
            0.98,
            f"DKIST/DLNIRSP Level 1 Quicklook -- Dataset {self.constants.dataset_id}",
            ha="left",
            fontsize=8,
            color="green",
            va="top",
            fontweight="bold",
        )
        mosaic_start_time, mosaic_duration = self.compute_mosaic_timing(I_mosaic_dates)
        self.mosaic_info_title = fig.text(
            0.3,
            0.95,
            self.format_title_text(mosaic_start_time, mosaic_duration),
            ha="left",
            fontsize=5.0,
            va="top",
        )
        first_header = fits.getheader(self.I_file_list[0])
        first_date_beg = first_header["DATE-BEG"]
        first_mindex1 = first_header["MINDEX1"]
        first_mindex2 = first_header["MINDEX2"]
        self.step_info_title = fig.text(
            0.25 / 2.0,
            0.98,
            self.format_step_info_text(
                date_beg=first_date_beg, mindex1=first_mindex1, mindex2=first_mindex2
            ),
            ha="center",
            fontsize=6,
            va="top",
            color="k",
        )
        fig.text(
            0.25 / 2.0, 0.89, "Stacked IFU Spectra", ha="center", fontsize=6, color="tab:orange"
        )
        return fig

    def _init_mosaic_plots(
        self,
        *,
        fig: plt.Figure,
        I_core_mosaic: np.ndarray,
        I_cont_mosaic: np.ndarray,
        V_core_ratio: np.ndarray,
        V_cont_ratio: np.ndarray,
        core_iscales: np.ndarray,
        cont_iscales: np.ndarray,
        core_vscale: float,
        cont_vscale: float,
    ):
        """Initialize four plots of the full mosaic image: line core and continuum for Stokes I and V."""
        I_mosaic_core_axis: WCSAxes = fig.add_axes(
            (
                self.mosaic_left,
                self.mosaic_bottom + self.mosaic_height + self.mosaic_v_padding,
                self.mosaic_width,
                self.mosaic_height,
            ),
            projection=self.reference_wcs,
        )
        V_mosaic_core_axis: WCSAxes = fig.add_axes(
            (
                self.mosaic_left + self.mosaic_width + self.mosaic_h_padding,
                self.mosaic_bottom + self.mosaic_height + self.mosaic_v_padding,
                self.mosaic_width,
                self.mosaic_height,
            ),
            projection=self.reference_wcs,
        )
        I_mosaic_cont_axis: WCSAxes = fig.add_axes(
            (self.mosaic_left, self.mosaic_bottom, self.mosaic_width, self.mosaic_height),
            projection=self.reference_wcs,
        )
        V_mosaic_cont_axis: WCSAxes = fig.add_axes(
            (
                self.mosaic_left + self.mosaic_width + self.mosaic_h_padding,
                self.mosaic_bottom,
                self.mosaic_width,
                self.mosaic_height,
            ),
            projection=self.reference_wcs,
        )

        if not self.constants.correct_for_polarization:
            for ax in [V_mosaic_core_axis, V_mosaic_cont_axis]:
                ax.set_facecolor("paleturquoise")
                ax.text(
                    0.5,
                    0.5,
                    "Intensity\nmode",
                    transform=ax.transAxes,
                    fontsize=7,
                    ha="center",
                    va="center",
                    color="k",
                )

        self.I_mosaic_core_im = I_mosaic_core_axis.imshow(
            I_core_mosaic,
            vmin=core_iscales[0],
            vmax=core_iscales[1],
            zorder=2,
        )
        self.I_mosaic_cont_im = I_mosaic_cont_axis.imshow(
            I_cont_mosaic,
            vmin=cont_iscales[0],
            vmax=cont_iscales[1],
            zorder=2,
        )
        self.V_mosaic_core_im = V_mosaic_core_axis.imshow(
            V_core_ratio,
            vmin=-core_vscale,
            vmax=core_vscale,
            zorder=2,
        )
        self.V_mosaic_cont_im = V_mosaic_cont_axis.imshow(
            V_cont_ratio,
            vmin=-cont_vscale,
            vmax=cont_vscale,
            zorder=2,
        )

        corners = self.compute_step_wcs_box(self.I_file_list[0])

        self.I_core_patch = self._add_patch_to_axis(
            ax=I_mosaic_core_axis, corners=corners, color="blue"
        )
        self.I_cont_patch = self._add_patch_to_axis(
            ax=I_mosaic_cont_axis, corners=corners, color="orange"
        )

        self._add_ax_top_text(
            ax=I_mosaic_core_axis,
            text=rf"Stokes I [$\lambda = ${self.parameters.movie_core_wave_value_nm:.2f} nm]",
            fontsize=5,
            fontweight="bold",
        )
        self._add_ax_top_text(
            ax=I_mosaic_cont_axis,
            text=rf"Stokes I [$\lambda = ${self.parameters.movie_cont_wave_value_nm:.2f} nm]",
            fontsize=5,
            fontweight="bold",
        )

        for ax in [I_mosaic_core_axis, I_mosaic_cont_axis, V_mosaic_core_axis, V_mosaic_cont_axis]:
            ax.set_ylabel("")
            ax.set_xlabel("")
            self.maximize_mosaic_axis_area(ax)
            self.pad_mosaic_axis(ax)

            if (
                ax in [I_mosaic_core_axis, I_mosaic_cont_axis]
                or self.constants.correct_for_polarization
            ):
                ax.coords.grid(color="grey", linestyle="dashed", alpha=0.7, linewidth=0.3, zorder=1)

        self.clean_axis_spines(I_mosaic_core_axis, show_xtick_labels=False, show_ytick_labels=True)
        self.clean_axis_spines(I_mosaic_cont_axis, show_xtick_labels=True, show_ytick_labels=True)
        self.clean_axis_spines(V_mosaic_core_axis, show_xtick_labels=False, show_ytick_labels=False)
        self.clean_axis_spines(V_mosaic_cont_axis, show_xtick_labels=True, show_ytick_labels=False)

        if self.constants.correct_for_polarization:
            V_mosaic_core_axis.coords.grid(
                color="grey", linestyle=":", alpha=0.7, linewidth=0.3, zorder=1
            )
            V_mosaic_cont_axis.coords.grid(
                color="grey", linestyle=":", alpha=0.7, linewidth=0.3, zorder=1
            )

            self.V_core_patch = self._add_patch_to_axis(
                ax=V_mosaic_core_axis, corners=corners, color="blue"
            )
            self.V_cont_patch = self._add_patch_to_axis(
                ax=V_mosaic_cont_axis, corners=corners, color="orange"
            )
            self.V_mosaic_core_info_text = self._add_ax_top_text(
                ax=V_mosaic_core_axis,
                text=self.format_V_mosaic_info_text(
                    wavelength=self.parameters.movie_core_wave_value_nm, vscale=core_vscale
                ),
                fontsize=5,
                fontweight="bold",
            )
            self.V_mosaic_cont_info_text = self._add_ax_top_text(
                ax=V_mosaic_cont_axis,
                text=self.format_V_mosaic_info_text(
                    wavelength=self.parameters.movie_cont_wave_value_nm, vscale=cont_vscale
                ),
                fontsize=5,
                fontweight="bold",
            )

        V_mosaic_core_axis.annotate(
            "N",
            (self.arrow_x, self.arrow_y),
            xytext=(self.arrow_x, self.arrow_y + self.arrow_length),
            arrowprops=dict(arrowstyle="<-", shrinkA=0, shrinkB=0, lw=0.5),
            xycoords="figure fraction",
            textcoords="figure fraction",
            fontsize=6,
            ha="center",
            va="center",
        )
        V_mosaic_core_axis.annotate(
            "E",
            (self.arrow_x, self.arrow_y),
            xytext=(
                self.arrow_x - self.arrow_length / self.fig_width_inches * self.fig_height_inches,
                self.arrow_y,
            ),
            arrowprops=dict(arrowstyle="<-", shrinkA=0, shrinkB=0, lw=0.5),
            xycoords="figure fraction",
            textcoords="figure fraction",
            fontsize=6,
            va="center",
            ha="center",
        )

    def _init_stack_plots(
        self, *, fig: plt.Figure, I_stack: np.ndarray, V_ratio: np.ndarray
    ) -> plt.Axes:
        """Initialize two plots of stacked, 2D spectra; one for Stokes I and V."""
        I_stack_axis = fig.add_axes(
            (
                self.spec_left,
                self.spec_bottom + self.spec_height + self.spec_v_padding,
                self.spec_width,
                self.stack_height,
            )
        )
        V_stack_axis = fig.add_axes(
            (
                self.spec_left + self.spec_width + self.spec_h_padding,
                self.spec_bottom + self.spec_height + self.spec_v_padding,
                self.spec_width,
                self.stack_height,
            ),
            sharex=I_stack_axis,
            sharey=I_stack_axis,
        )

        I_stack_axis.set_facecolor("linen")
        V_stack_axis.set_facecolor("black")

        if not self.constants.correct_for_polarization:
            V_stack_axis.set_facecolor("paleturquoise")
            V_stack_axis.text(
                0.5,
                0.5,
                "Intensity\nmode",
                transform=V_stack_axis.transAxes,
                fontsize=7,
                ha="center",
                va="center",
                color="k",
            )

        for ax in [I_stack_axis, V_stack_axis]:
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)

        V_ratio -= np.nanmedian(V_ratio, axis=1)[:, None]

        self.I_stack_im = I_stack_axis.imshow(
            I_stack,
            extent=(self.wave_abscissa[0], self.wave_abscissa[-1], 0, I_stack.shape[1]),
            aspect="auto",
        )
        self.I_stack_im.set_clim(np.nanpercentile(I_stack, [1, 99]))
        self.V_stack_im = V_stack_axis.imshow(
            V_ratio,
            extent=(self.wave_abscissa[0], self.wave_abscissa[-1], 0, V_ratio.shape[1]),
            aspect="auto",
        )
        self.V_stack_im.set_clim(np.nanpercentile(V_ratio, [1, 99]))

        self._add_ax_top_text(
            ax=I_stack_axis,
            text="Stokes I",
            fontsize=6,
            color="tab:orange",
        )
        self._add_ax_top_text(
            ax=V_stack_axis,
            text="Stokes V/I",
            fontsize=6,
            color="tab:orange",
        )
        return I_stack_axis

    def _init_spectral_plots(
        self, *, fig: plt.Figure, I_stack_axis: plt.Axes, I_stack: np.ndarray, V_ratio: np.ndarray
    ):
        """Initialize two plots showing the spatial median spectrum for Stokes I and V."""
        I_spec_axis = fig.add_axes(
            (self.spec_left, self.spec_bottom, self.spec_width, self.spec_height),
            sharex=I_stack_axis,
        )

        I_spec_axis.yaxis.set_visible(False)
        I_spec_axis.spines[["top", "left", "right"]].set_visible(False)
        I_spec_axis.tick_params(axis="x", labelsize=4)

        self.I_spec_line = I_spec_axis.plot(self.wave_abscissa, np.nanmedian(I_stack, axis=0))[0]
        I_spec_axis.axvline(
            self.parameters.movie_core_wave_value_nm, ls="dashed", color="blue", lw=0.6
        )
        I_spec_axis.axvline(
            self.parameters.movie_cont_wave_value_nm, ls="dashed", color="orange", lw=0.6
        )
        I_spec_axis.set_ylim(0, 1.2)
        I_spec_axis.text(
            0.02,
            1.14,
            f"Median I",
            ha="left",
            va="top",
            transform=I_spec_axis.transAxes,
            color="tab:blue",
            fontsize=5,
        )
        spec_plus_minus_wave_limit = np.round(
            0.45 * (self.wave_abscissa.max() - self.wave_abscissa.min()), 1
        )
        I_spec_axis.set_xticks(
            np.round(
                np.mean(self.wave_abscissa)
                + np.array([-spec_plus_minus_wave_limit, 0, spec_plus_minus_wave_limit]),
                2,
            )
        )
        I_spec_axis.set_xticklabels(
            [
                f"-{spec_plus_minus_wave_limit}",
                f"{np.mean(self.wave_abscissa):.2f}nm",
                f"+{spec_plus_minus_wave_limit}",
            ]
        )

        if self.constants.correct_for_polarization:
            V_spec_axis = fig.add_axes(
                (
                    self.spec_left + self.spec_width + self.spec_h_padding,
                    self.spec_bottom,
                    self.spec_width,
                    self.spec_height,
                ),
                sharex=I_stack_axis,
            )
            V_spec_axis.yaxis.set_visible(False)
            V_spec_axis.spines[["top", "left", "right"]].set_visible(False)
            V_spec_axis.tick_params(axis="x", labelsize=4)

            self.V_spec_line = V_spec_axis.plot(self.wave_abscissa, np.nanmedian(V_ratio, axis=0))[
                0
            ]
            V_spec_axis.axvline(
                self.parameters.movie_core_wave_value_nm, ls="dashed", color="blue", lw=0.6
            )
            V_spec_axis.axvline(
                self.parameters.movie_cont_wave_value_nm, ls="dashed", color="orange", lw=0.6
            )
            V_spec_axis.set_ylim(-self.vscale, self.vscale)
            self.V_spec_title = V_spec_axis.text(
                0.02,
                1.14,
                self.spec_V_info_text,
                ha="left",
                va="top",
                transform=V_spec_axis.transAxes,
                color="tab:blue",
                fontsize=5,
            )
            self.V_spec_axis = V_spec_axis

    @staticmethod
    def _add_patch_to_axis(ax: WCSAxes, corners: np.ndarray, color: str) -> Polygon:
        """Add a IFU footprint patch to a given axis."""
        patch = ax.fill(
            corners[:, 0],
            corners[:, 1],
            facecolor="none",
            edgecolor=color,
            linewidth=0.75,
            alpha=0.7,
            transform=ax.get_transform("world"),
            zorder=2.5,
        )[0]
        return patch

    @staticmethod
    def _add_ax_top_text(
        ax: Axes, text: str, fontsize: int, color: str = "k", fontweight: str = "normal"
    ) -> Text:
        """
        Add text at the top center of an axis.

        This lets us be a little tighter than `ax.set_title`
        """
        text = ax.text(
            0.5,
            1.01,
            text,
            fontsize=fontsize,
            ha="center",
            va="bottom",
            color=color,
            fontweight=fontweight,
            transform=ax.transAxes,
        )
        return text

    def build_mosaic_images(
        self, data_list: list[list[np.ndarray]], wcs_list: list[WCS]
    ) -> list[np.ndarray]:
        """
        Build mosaic images for a given set of data and WCS values.

        Parameters
        ----------
        data_list
            A list of lists containing `np.ndarray` objects. A separate mosaic image will be created for each list of
            data in the top-level list.

        wcs_list
            A list of `astropy.wcs.WCS` objects. Should have the same length as the inner lists in ``data_list``.

        Returns
        -------
        mosaic_list
            A single mosaic array for each level in the outer list of ``data_list``.
        """
        logger.info("Stitching mosaics")
        mosaic_list = []
        with self.spherical_screen:
            for i, dl in enumerate(data_list):
                mosaic, _ = reproject_and_coadd(
                    tuple(zip(dl, wcs_list)),
                    self.reference_wcs,
                    reproject_function=reproject_interp,
                    shape_out=self.full_mosaic_shape,
                    blank_pixel_value=np.nan,
                    roundtrip_coords=False,
                )
                cleaned = interpolate_replace_nans(
                    mosaic,
                    np.ones(self.parameters.movie_nan_replacement_kernel_shape),
                    boundary="fill",
                    fill_value=np.nan,
                )
                mosaic_list.append(cleaned)

        return mosaic_list

    def read_mosaic_frames(
        self, mosaic_num: int, stokes: str
    ) -> tuple[list[list[np.ndarray]], list[WCS], list[str]]:
        """
        Read data and header info from all files for a given mosaic and Stokes parameter.

        This function returns all data needed by other mosaic functions. In this way we only need to read the set of files
        once.

        Returns
        -------
        data_list
            A list of lists containing `np.ndarray` objects. A separate mosaic image will be created for each list of
            data in the top-level list.

        wcs_list
            A list of `astropy.wcs.WCS` objects. Should have the same length as the inner lists in ``data_list``.

        date_beg_list
            A list of DATE-BEG values from each mosaic file.
        """
        tags = [
            DlnirspTag.calibrated(),
            DlnirspTag.frame(),
            DlnirspTag.mosaic_num(mosaic_num),
            DlnirspTag.stokes(stokes),
        ]
        file_paths = self.read(tags=tags)
        logger.info(f"Found {self.count(tags)} files for {mosaic_num = } and {stokes = }")
        wcs_list = []
        date_beg_list = []
        data_list = [[], []]
        for fo in file_paths:
            hdul = fits.open(fo)
            header = self.add_L1_header_values(hdul[0].header)
            wcs_list.append(WCS(header).dropaxis(2))
            date_beg_list.append(header["DATE-BEG"])

            for i, s in enumerate([self.core_wave_idx, self.cont_wave_idx]):
                data = hdul[0].data[s, :, :]
                for vs in self.parameters.movie_vertical_nan_slices:
                    data[vs, :] = np.nan
                data_list[i].append(data)

            del hdul

        return data_list, wcs_list, date_beg_list

    def compute_mosaic_timing(self, date_beg_list: list[str]) -> tuple[datetime, timedelta]:
        """
        Compute the start time and duration of a mosaic from a list of DATE-BEG values for frames in the mosaic.

        Returns
        -------
        start_time
            The start `datetime` of the mosaic

        duration
            Duration of the mosaic
        """
        datetime_list = [datetime.fromisoformat(i) for i in date_beg_list]
        start_time = min(datetime_list)
        end_time = max(datetime_list)
        duration = end_time - start_time

        return start_time, duration

    def compute_step_wcs_box(self, file_path: Path) -> np.ndarray:
        """
        Compute the spatial "box" representing a single mosaic step given a header from that step.

        The WCS footprint is read directly from the FITS header and then converted to the coordinate frame of the
        reference WCS.

        Returns
        -------
        corners
            Array of shape (4, 2) containing (x, y) locations of 4 corners of the box representing the pointing of the
            particular mosaic step. The values are in WCS coordinates.
        """
        header = self.add_L1_header_values(fits.getheader(file_path))
        wcs = WCS(header).dropaxis(2)
        local_corners = wcs.calc_footprint()
        footprint_in_local_wcs = SkyCoord(
            *local_corners.T, unit=u.deg, frame=wcs_to_celestial_frame(wcs)
        )
        with self.spherical_screen:
            footprint_in_ref_wcs = footprint_in_local_wcs.transform_to(self.reference_coord_frame)
            ref_corners = (
                u.Quantity([footprint_in_ref_wcs.Tx, footprint_in_ref_wcs.Ty]).to_value(u.deg).T
            )

        return ref_corners

    def get_stacked_spectra(self, file_path: Path) -> np.ndarray:
        """Read a file for a single mosaic step and flatten the 3D cube into a stacked, 2D spectral array."""
        data = fits.getdata(file_path)
        stack = data.reshape(self.num_wave, self.num_spec).T
        return stack

    @staticmethod
    def clean_axis_spines(axis: WCSAxes, show_xtick_labels: bool, show_ytick_labels: bool) -> None:
        """
        Clean extra ticks and (optionally) tick labels from a given axis.

        The top and right ticks are always turned off. The ``show_[xy]tick_labels`` flags optionally turn off the value
        labels of the bottom and left axes.
        """
        lon, lat = axis.coords
        lon.set_ticks_position("b")
        lat.set_ticks_position("l")
        if not show_xtick_labels:
            lon.set_ticklabel_visible(False)
        if not show_ytick_labels:
            lat.set_ticklabel_visible(False)

    def maximize_mosaic_axis_area(self, axis: WCSAxes) -> None:
        """
        Expand axis limits to ensure the axis always fills its "box".

        `imshow` will auto-tighten the limits to the image area, but we want the mosaic axes to always take up the same
        space in the figure, regardless of the mosaic aspect ratio.
        """
        full_ax_aspect = (
            self.fig_width_inches / self.fig_height_inches * self.mosaic_width / self.mosaic_height
        )
        x_min, x_max = axis.get_xlim()
        y_min, y_max = axis.get_ylim()
        img_aspect = (x_max - x_min) / (y_max - y_min)

        if img_aspect > full_ax_aspect:
            # Image is wider → expand ylim
            y_center = 0.5 * (y_min + y_max)
            y_span = (x_max - x_min) / full_ax_aspect
            axis.set_ylim(y_center - y_span / 2, y_center + y_span / 2)
        else:
            # Image is taller → expand xlim
            x_center = 0.5 * (x_min + x_max)
            x_span = (y_max - y_min) * full_ax_aspect
            axis.set_xlim(x_center - x_span / 2, x_center + x_span / 2)

    def pad_mosaic_axis(self, axis: WCSAxes) -> None:
        """
        Expand axis limits by a small amount so the mosaic image doesn't touch the axis lines.

        Because of how matplotlib animation works, the image can end up looking "on top" of the axis frame if the limits
        are super tight.
        """
        xrange = np.abs(np.diff(axis.get_xlim()))[0]
        padded_xlim = (
            np.array(axis.get_xlim())
            + np.array([-xrange, xrange]) * self.fractional_mosaic_axis_limit_pad
        )
        axis.set_xlim(*padded_xlim)

        yrange = np.abs(np.diff(axis.get_ylim()))[0]
        padded_ylim = (
            np.array(axis.get_ylim())
            + np.array([-yrange, yrange]) * self.fractional_mosaic_axis_limit_pad
        )
        axis.set_ylim(*padded_ylim)

    def format_title_text(self, mosaic_start_time: datetime, mosaic_duration: timedelta) -> str:
        """Return the top-level figure title text."""
        pol_str = (
            "Full Stokes Polarimetry (Q&U not shown)"
            if self.constants.correct_for_polarization
            else "Stokes I Only"
        )
        title = (
            f"ArmID: {self.constants.arm_id} -- {self.spectral_line_name} -- {pol_str}"
            f"\nProduct ID: {self.product_id} --- Experiment ID: {self.constants.experiment_id}"
            f"\nStart Time: {self.constants.obs_ip_start_time} --- End Time: {self.constants.obs_ip_end_time}"
            f"\nMosaic {self.currently_shown_mosaic + 1} of {self.constants.num_mosaic_repeats} -> start time: {mosaic_start_time.isoformat("T")} - Duration: {mosaic_duration.total_seconds():.2f} sec"
        )
        return title

    def format_V_mosaic_info_text(self, wavelength: float, vscale: float) -> str:
        """
        Format the info text for V mosaic images given the current mosaic's vscale parameter.

        Wavelength is a parameter so this can be used for both core and continuum images.
        """
        return rf"Stokes V/I [$\lambda = ${wavelength:.2f} nm]  Saturation @ ± {vscale * 100.:.2f}%"

    def format_step_info_text(self, date_beg: str, mindex1: int, mindex2: int) -> str:
        """
        Format the info text for a single mosaic step.

        Shows the DATE-BEG and mosaic index position.
        """
        return f"Mosaic index ({mindex1}, {mindex2})\n{date_beg}"

    @property
    def spec_V_info_text(self) -> str:
        """Return the title of the V median spectrum plot with the appropriate vscale."""
        return f"Median V/I [±{self.vscale * 100:.2f}%]"

    def add_L1_header_values(self, header) -> fits.Header:
        """Add the L1 header values that are needed to compute accurate WCSs."""
        header["DATEREF"] = header["DATE-BEG"]
        header["OBSGEO-X"] = location_of_dkist.x.to_value(u.m)
        header["OBSGEO-Y"] = location_of_dkist.y.to_value(u.m)
        header["OBSGEO-Z"] = location_of_dkist.z.to_value(u.m)
        obstime = Time(header["DATE-BEG"])
        header["OBS_VR"] = (
            location_of_dkist.get_gcrs(obstime=obstime)
            .transform_to(HeliocentricInertial(obstime=obstime))
            .d_distance.to_value(u.m / u.s)
        )

        dkist_at_date_beg = location_of_dkist.get_itrs(obstime=obstime)
        sun_coordinate = Helioprojective(
            Tx=0 * u.arcsec, Ty=0 * u.arcsec, observer=dkist_at_date_beg
        )
        header["SOLARRAD"] = round(sun_coordinate.angular_radius.value, 2)

        header["SPECSYS"] = "TOPOCENT"
        header["VELOSYS"] = 0.0

        header.update(self.wavelength_solution)

        return header


def update_plot(frame_index: int, task_obj: MakeDlnirspMovie, is_polarimetric: bool):
    """
    Update the movie figure with data from the current mosaic step.

    The stack and spectral axis are always updated, as are the boxes that show the location of the current step.
    If the current step is the first in a new mosaic then the mosaic images are also updated.
    """
    I_path = task_obj.I_file_list[frame_index]

    I_obj = DlnirspL0FitsAccess.from_path(I_path)
    current_mosaic = I_obj.mosaic_num

    logger.info(
        f"Plotting step {frame_index} / {task_obj.num_movie_frames}. Mosaic {current_mosaic} / {task_obj.constants.num_mosaic_repeats}"
    )
    if current_mosaic != task_obj.currently_shown_mosaic:
        logger.info(f"Creating mosaic number {current_mosaic}")
        I_mosaic_data, I_mosaic_WCS, I_mosaic_dates = task_obj.read_mosaic_frames(
            mosaic_num=current_mosaic, stokes="I"
        )
        I_mosaic_list = task_obj.build_mosaic_images(data_list=I_mosaic_data, wcs_list=I_mosaic_WCS)

        core_iscales = np.nanpercentile(I_mosaic_list[0], [5, 95]) + np.array([-0.1, 0.1])
        cont_iscales = np.nanpercentile(I_mosaic_list[1], [5, 95]) + np.array([-0.1, 0.1])

        task_obj.I_mosaic_core_im.set_data(I_mosaic_list[0])
        task_obj.I_mosaic_cont_im.set_data(I_mosaic_list[1])
        task_obj.I_mosaic_core_im.set_clim(*core_iscales)
        task_obj.I_mosaic_cont_im.set_clim(*cont_iscales)

        if is_polarimetric:
            V_mosaic_data, V_mosaic_WCS, _ = task_obj.read_mosaic_frames(
                mosaic_num=current_mosaic, stokes="V"
            )
            V_mosaic_list = task_obj.build_mosaic_images(
                data_list=V_mosaic_data, wcs_list=V_mosaic_WCS
            )

            V_core_ratio = V_mosaic_list[0] / I_mosaic_list[0]
            V_cont_ratio = V_mosaic_list[1] / I_mosaic_list[1]

            core_vscale = np.nanpercentile(np.abs(V_core_ratio), 95)
            cont_vscale = np.nanpercentile(np.abs(V_cont_ratio), 95)
            task_obj.vscale = max([core_vscale, cont_vscale])

            task_obj.V_mosaic_core_im.set_data(V_core_ratio)
            task_obj.V_mosaic_cont_im.set_data(V_cont_ratio)
            task_obj.V_mosaic_core_im.set_clim(-core_vscale, core_vscale)
            task_obj.V_mosaic_cont_im.set_clim(-cont_vscale, cont_vscale)

            task_obj.V_mosaic_core_info_text.set_text(
                task_obj.format_V_mosaic_info_text(
                    wavelength=task_obj.parameters.movie_core_wave_value_nm, vscale=core_vscale
                )
            )
            task_obj.V_mosaic_cont_info_text.set_text(
                task_obj.format_V_mosaic_info_text(
                    wavelength=task_obj.parameters.movie_cont_wave_value_nm, vscale=cont_vscale
                )
            )
            task_obj.V_spec_title.set_text(task_obj.spec_V_info_text)

        task_obj.currently_shown_mosaic = current_mosaic

        mosaic_start_time, mosaic_duration = task_obj.compute_mosaic_timing(I_mosaic_dates)
        task_obj.mosaic_info_title.set_text(
            task_obj.format_title_text(mosaic_start_time, mosaic_duration)
        )

    corners = task_obj.compute_step_wcs_box(I_path)

    I_stack = task_obj.get_stacked_spectra(I_path)
    task_obj.I_stack_im.set_data(I_stack)
    task_obj.I_stack_im.set_clim(np.nanpercentile(I_stack, [1, 99]))

    task_obj.I_spec_line.set_ydata(np.nanmedian(I_stack, axis=0))

    task_obj.I_core_patch.set_xy(corners)
    task_obj.I_cont_patch.set_xy(corners)

    if is_polarimetric:
        V_path = task_obj.V_file_list[frame_index]
        V_stack = task_obj.get_stacked_spectra(V_path)
        V_ratio = V_stack / I_stack
        V_ratio -= np.nanmedian(V_ratio, axis=1)[:, None]
        task_obj.V_stack_im.set_data(V_ratio)
        task_obj.V_stack_im.set_clim(np.nanpercentile(V_ratio, [1, 99]))
        task_obj.V_spec_line.set_ydata(np.nanmedian(V_ratio, axis=0))
        task_obj.V_spec_axis.set_ylim(-task_obj.vscale, task_obj.vscale)
        task_obj.V_core_patch.set_xy(corners)
        task_obj.V_cont_patch.set_xy(corners)

    # TODO: Metadata key?
    mindex1 = I_obj.header["MINDEX1"]
    mindex2 = I_obj.header["MINDEX2"]
    task_obj.step_info_title.set_text(
        task_obj.format_step_info_text(date_beg=I_obj.time_obs, mindex1=mindex1, mindex2=mindex2)
    )
