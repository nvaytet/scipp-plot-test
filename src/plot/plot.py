# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2020 Scipp contributors (https://github.com/scipp)
# @author Neil Vaytet

# Scipp imports
# from .._scipp import core as sc
from .sciplot import SciPlot
from .tools import make_fake_coord

from .dispatch import dispatch
from .tools import get_line_param

def plot(dict_obj,
         projection=None,
         axes=None,
         color=None,
         marker=None,
         linestyle=None,
         linewidth=None,
         bins=None,
         **kwargs):
    """
    Wrapper function to plot any kind of scipp object.
    """

    # Delayed imports
    # from .tools import get_line_param
    # from .dispatch import dispatch

    inventory = {}


    if ({"coords", "data"}.issubset(set(dict_obj.keys())) or
        {"coords", "unaligned"}.issubset(set(dict_obj.keys()))):
        # Case of a DataArray-like dict
        inventory[dict_obj["name"]] = dict_obj
    elif ({"dims", "values"}.issubset(set(dict_obj.keys())) or
          {"dims", "shape"}.issubset(set(dict_obj.keys()))):
        # Case of a Variable-like dict
        coords = {}
        for dim, size in zip(dict_obj["dims"], dict_obj["shape"]):
            coords[dim] = make_fake_coord(dim, size)
        data_array = {"data": dict_obj, "coords": coords, "masks": {},
        "attrs": {}}
        for key in dict_obj.keys():
            data_array[key] = dict_obj[key]
        # print(data_array)
        inventory["variable"] = data_array
    else:
        # Case of a Dataset-like dict
        inventory = dict_obj



    # # tp = type(dict_obj)
    # # tp = dict_obj["type"].lower()
    # if "unit" not in dict_obj:
    #     # Case of a Dataset-like dict
    #     inventory = dict_obj
    # elif "coords" in dict_obj:
    #     # Case of a DataArray-like dict
    #     inventory[dict_obj["name"]] = dict_obj
    # elif "values" in dict_obj:
    #     # Case of a Variable-like dict
    #     coords = {}
    #     for dim, size in zip(dict_obj["dims"], dict_obj["shape"]):
    #         coords[dim] = make_fake_coord(dim, size)
    #     data_array = {"data": dict_obj, "coords": coords, "masks": {},
    #     "attrs": {}}
    #     for key in dict_obj.keys():
    #         data_array[key] = dict_obj[key]
    #     # print(data_array)
    #     inventory["variable"] = data_array
    # else:
    #     raise RuntimeError("plot: Input does not contain compatible entries.")



    # if dict_obj == "dataset":
    #     for name in sorted(dict_obj.keys()):
    #         inventory[name] = dict_obj[name]
    # elif tp is sc.Variable or tp is sc.VariableView:
    #     coords = {}
    #     for dim, size in zip(dict_obj.dims, dict_obj.shape):
    #         coords[dim] = make_fake_coord(dim, size)
    #     inventory[str(tp)] = sc.DataArray(data=dict_obj, coords=coords)
    # elif tp is sc.DataArray or tp is sc.DataArrayView:
    #     inventory[dict_obj.name] = dict_obj
    # elif tp is dict:
    #     inventory = dict_obj
    # else:
    #     raise RuntimeError("plot: Unknown input type: {}. Allowed inputs are "
    #                        "a Dataset, a DataArray, a Variable (and their "
    #                        "respective proxies), and a dict of "
    #                        "DataArrays.".format(tp))

    # Prepare container for matplotlib line parameters
    line_params = {
        "color": color,
        "marker": marker,
        "linestyle": linestyle,
        "linewidth": linewidth
    }

    # Counter for 1d/event data
    line_count = -1

    # Create a list of variables which will then be dispatched to correct
    # plotting function.
    # Search through the variables and group the 1D datasets that have
    # the same coordinates and units.
    # tobeplotted is a dict that holds four items:
    # {number_of_dimensions, Dataset, axes, line_parameters}.
    tobeplotted = dict()
    for name, var in sorted(inventory.items()):

        # if sc.contains_events(var) and bins is None:
        #     raise RuntimeError("The `bins` argument must be specified when "
        #                        "plotting event data.")

        ndims = len(var["data"]["dims"])
        # if bins is not None and sc.contains_events(var):
        #     ndims += 1
        if ndims > 0:
            ax = axes
            if ndims == 1 or projection == "1d" or projection == "1D":
                # Construct a key from the dimensions
                if axes is not None:
                    # Check if we are dealing with a dict mapping dimensions to
                    # labels
                    if isinstance(axes, dict):
                        key = axes[str(var.dims[0])]
                        ax = [key]
                    else:
                        key = ".".join(axes)
                else:
                    key = ".".join([str(dim) for dim in var["data"]["dims"]])
                # Add unit to key
                key = "{}.{}".format(key, str(var["data"]["unit"]))
                line_count += 1
            else:
                key = name

            mpl_line_params = {}
            for n, p in line_params.items():
                if p is None:
                    mpl_line_params[n] = line_count
                elif isinstance(p, list):
                    mpl_line_params[n] = p[line_count]
                elif isinstance(p, dict):
                    if name in p:
                        mpl_line_params[n] = p[name]
                    else:
                        mpl_line_params[n] = line_count
                else:
                    mpl_line_params[n] = p
                if isinstance(mpl_line_params[n], int):
                    mpl_line_params[n] = get_line_param(
                        name=n, index=mpl_line_params[n])

            if key not in tobeplotted.keys():
                tobeplotted[key] = dict(ndims=ndims,
                                        data_arrays={},
                                        axes=ax,
                                        mpl_line_params={})
                for n in mpl_line_params.keys():
                    tobeplotted[key]["mpl_line_params"][n] = {}
            tobeplotted[key]["data_arrays"][name] = inventory[name]
            for n, p in mpl_line_params.items():
                tobeplotted[key]["mpl_line_params"][n][name] = p

    # Plot all the subsets
    output = SciPlot()
    for key, val in tobeplotted.items():
        output[key] = dispatch(data_arrays=val["data_arrays"],
                               name=key,
                               ndim=val["ndims"],
                               projection=projection,
                               axes=val["axes"],
                               mpl_line_params=val["mpl_line_params"],
                               bins=bins,
                               **kwargs)

    return output
