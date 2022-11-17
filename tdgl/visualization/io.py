from typing import Optional, Sequence, Tuple

import h5py
import numpy as np

from ..enums import Observable
from ..finite_volume.matrices import build_gradient
from ..finite_volume.mesh import Mesh
from ..solution.data import TDGLData, get_edge_observable_data, load_state_data


def get_alpha(h5file: h5py.File) -> Optional[np.ndarray]:
    if "disorder" in h5file:
        return np.asarray(h5file["disorder"]["alpha"])
    return None


def get_plot_data(
    h5file: h5py.File, mesh: Mesh, observable: Observable, frame: int
) -> Tuple[np.ndarray, np.ndarray, Sequence[float]]:
    """Get data to plot.

    Args:
        h5file: The data file.
        mesh: The mesh used in the simulation.
        observable: The observable to return.
        frame: The current frame.

    Returns:
        A tuple of the values for the color plot, the directions for the
        quiver plot and the limits for the color plot.
    """
    tdgl_data = TDGLData.from_hdf5(h5file, frame)
    psi = tdgl_data.psi
    mu = tdgl_data.mu
    a_applied = tdgl_data.applied_vector_potential
    a_induced = tdgl_data.induced_vector_potential
    supercurrent = tdgl_data.supercurrent
    normal_current = tdgl_data.normal_current

    if observable is Observable.COMPLEX_FIELD and psi is not None:
        return np.abs(psi), np.zeros((len(mesh.x), 2)), [0, 1]

    elif observable is Observable.PHASE and psi is not None:
        return np.angle(psi) / np.pi, np.zeros((len(mesh.x), 2)), [-1, 1]

    elif observable is Observable.SUPERCURRENT and supercurrent is not None:
        return get_edge_observable_data(supercurrent, mesh)

    elif observable is Observable.NORMAL_CURRENT and normal_current is not None:
        return get_edge_observable_data(normal_current, mesh)

    elif observable is Observable.SCALAR_POTENTIAL and mu is not None:
        mu = mu - np.nanmin(mu)
        return mu, np.zeros((len(mesh.x), 2)), [np.min(mu), np.max(mu)]

    elif observable is Observable.APPLIED_VECTOR_POTENTIAL and a_applied is not None:
        return get_edge_observable_data(
            (a_applied * mesh.edge_mesh.directions).sum(axis=1), mesh
        )

    elif observable is Observable.INDUCED_VECTOR_POTENTIAL and a_induced is not None:
        return get_edge_observable_data(
            (a_induced * mesh.edge_mesh.directions).sum(axis=1), mesh
        )

    elif (
        observable is Observable.TOTAL_VECTOR_POTENTIAL
        and a_applied is not None
        and a_induced is not None
    ):
        return get_edge_observable_data(
            ((a_applied + a_induced) * mesh.edge_mesh.directions).sum(axis=1), mesh
        )

    elif observable is Observable.ALPHA:
        alpha = get_alpha(h5file)

        if alpha is None:
            alpha = np.ones_like(mu)

        return alpha, np.zeros((len(mesh.x), 2)), [np.min(alpha), np.max(alpha)]

    elif (
        observable is Observable.VORTICITY
        and supercurrent is not None
        and normal_current is not None
    ):
        j_sc_site = mesh.get_observable_on_site(supercurrent)
        j_nm_site = mesh.get_observable_on_site(normal_current)
        j_site = j_sc_site + j_nm_site
        gradient = build_gradient(mesh)
        normalized_directions = (
            mesh.edge_mesh.directions
            / np.linalg.norm(mesh.edge_mesh.directions, axis=1)[:, np.newaxis]
        )
        grad_jx = gradient @ j_site[:, 0]
        grad_jy = gradient @ j_site[:, 1]
        djy_dx = grad_jy * normalized_directions[:, 0]
        djx_dy = grad_jx * normalized_directions[:, 1]
        vorticity_on_edges = djy_dx - djx_dy
        vorticity = mesh.get_observable_on_site(vorticity_on_edges, vector=False)
        vmax = max(np.abs(np.max(vorticity)), np.abs(np.min(vorticity)))
        return vorticity, np.zeros((len(mesh.x), 2)), [-vmax, vmax]

    return np.zeros_like(mesh.x), np.zeros((len(mesh.x), 2)), [0, 0]


def get_state_string(h5file: h5py.File, frame: int, max_frame: int) -> str:
    state = load_state_data(h5file, frame)

    state_string = f"Frame {frame} of {max_frame}"
    i = 1
    for key, value in state.items():
        if key == "timestamp":
            continue
        state_string += ", "
        if i % 3 == 0:
            state_string += "\n"
        if type(value) is np.float64:
            state_string += f"{key}: {value:.2e}"
        else:
            state_string += f"{key}: {value}"

        i += 1

    return state_string[:-1]