import os
import io
from collections import OrderedDict
from typing import Optional, Tuple
import xml.etree.ElementTree as ET

import dttlib
import yaml
import numpy as np
from qtpy import QtCore
from pyqtgraph import exporters
import h5py

# cairosvg needs to be handled specially because
# MacOS arm pypi package doesn't include the
# cairo library needed by the module.
# so we catch that case here and disallow
# pdf creation
try:
    import cairosvg
except:
    cairosvg = None

from scipy.io import savemat
import matplotlib.pyplot as plt

from .data import DataBufferDict
from .template import get_channel_color

##################################################

EXPORT_FILTERS = [
    ("scene to Portable Network Graphic (*.png)", [".png"]),
    ("scene to Scalable Vector Graphic (*.svg)", [".svg"]),
    ("scene to Portable Document Format (*.pdf)", [".pdf"]),
    ("data to Hierarchical Data Format (*.hdf5 *.h5)", [".hdf5", ".h5"]),
    ("data to MATLAB Binary Format (*.mat)", [".mat"]),
    ("template to YAML (*.yaml *.yml)", [".yaml", ".yml"]),
]


def _export_filter_spec():
    return ";;".join([f[0] for f in EXPORT_FILTERS])


def _ext2filt(ext):
    for f, e in EXPORT_FILTERS:
        if ext in e:
            return f


def _filt2ext(filt):
    try:
        return dict(EXPORT_FILTERS).get(filt)[0]
    except IndexError:
        pass


def export_dialog(dialog_func, parent, path):
    """Open an dialog to choose export path

    Returns chosen path.

    """
    if path:
        base, ext = os.path.splitext(path)
        initialFilter = _ext2filt(ext)
    else:
        path = ""
        initialFilter = EXPORT_FILTERS[0][0]
    path, selectedFilter = dialog_func(
        parent=parent,
        directory=path,
        caption="Export scene, data, or template to file",
        filter=_export_filter_spec(),
        initialFilter=initialFilter,
    )
    if not path:
        return
    base, ext = os.path.splitext(path)
    if ext == "":
        path = base + _filt2ext(selectedFilter)
    return path


def _write_file(data, path):
    with open(path, "wb") as f:
        f.write(data)


##################################################
# EXPORT SCENE


def export_scene_png(scene, path=None):
    """Export scene to PNG bytes object"""
    image = exporters.ImageExporter(scene).export(toBytes=True)
    ba = QtCore.QByteArray()
    buff = QtCore.QBuffer(ba)
    buff.open(QtCore.QIODevice.WriteOnly)  # type: ignore
    if image is not None and type(image) != bool:
        ok = image.save(buff, "PNG")
        assert ok
        if path:
            _write_file(ba.data(), path)
        else:
            return ba.data()


def _scene_to_svg(scene):
    exporter = exporters.SVGExporter(scene)
    svg: bytes = exporter.export(toBytes=True)  # type: ignore
    # HACK: FIXME: this is HACK to set the SVG viewBox, since
    # the pyqtgraph SVGExporter (technically generateSvg) is
    # for some reason not setting it.

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(svg)
    size = scene.parent().size()
    width = size.width()
    height = size.height()
    root.attrib["viewBox"] = f"0 0 {width} {height}"
    # FIXME: in 3.9 we can just do this:
    # out = ET.tostring(root, encoding='UTF-8', xml_declaration=True)
    with io.BytesIO() as bout:
        ET.ElementTree(root).write(bout, encoding="UTF-8", xml_declaration=True)
        svg = bout.getvalue()
    # END HACK
    return svg


def export_scene_svg(scene, path):
    """Export scene to SVG bytes object"""
    svg = _scene_to_svg(scene)
    _write_file(svg, path)


def export_scene_pdf(scene, path):
    """Export scene to PDF bytes object"""
    if cairosvg is None:
        raise Exception("Cannot create PDF: `cairosvg` could not be imported")
    svg = _scene_to_svg(scene)
    # FIXME: this is known to be not working on buster
    # (python3-cairosvg 1.0*):
    # lxml.etree.XMLSyntaxError: internal error: Huge input lookup, line 122, column 9996358
    # return cairosvg.svg2pdf(svg)
    pdf = cairosvg.svg2pdf(svg)
    _write_file(pdf, path)


IMAGE_EXPORT_FUNCTIONS = {
    ".png": export_scene_png,
    ".svg": export_scene_svg,
    ".pdf": export_scene_pdf,
}


##################################################
# EXPORT DATA


class ExportData:
    def __init__(self, datad, start, end):
        self.sample_rate = datad.sample_rate
        self.unit = datad.unit
        ind = np.where(
            (start <= datad.tarray) & (datad.tarray <= end),
            True,
            False,
        )
        self.data = {}
        for mod, data in datad.items():
            self.data[mod] = data[ind]
        self.gps_start = start
        self.span = end - start

    def items(self):
        return self.data.items()


def _get_data_slice(
    datad: dttlib.TimeDomainArray, start: dttlib.PipInstant, end: dttlib.PipInstant
):
    if datad.is_empty():
        data = datad.data
    else:
        start_i = datad.gps_instant_to_index(start)
        if start_i < 0:
            start_i = 0
        if start_i >= datad.len():
            start_i = datad.len() - 1
        end_i = datad.gps_instant_to_index(end)
        if end_i < 0:
            end_i = 0
        if end_i >= datad.len():
            end_i = datad.len() - 1
        if start_i > end_i:
            start_i = end_i
        data = datad.data[start_i:end_i]
    return data


def export_data_hdf5(
    ddict: DataBufferDict,
    path,
    start: dttlib.PipInstant,
    end: dttlib.PipInstant,
    **kwargs,
):
    """Save data dictionary to an HDF5 file

    Each channel key is given it's own group.  Keyword args written as
    attributes.

    """
    with h5py.File(path, "w") as f:
        groups = {}
        for id, datad in ddict.items():
            data = _get_data_slice(datad.original_struct, start, end)
            grp_name = str(id.name)
            if grp_name not in groups:
                groups[grp_name] = f.create_group(grp_name)
            grp = groups[grp_name]
            groups[grp_name] = grp
            name = id.trend_stat.data_name()
            # for name, data in datad.items():
            grp.create_dataset(name, data=data)
            # grp.create_dataset('gps', data=datad.tarray)
            grp.attrs["rate_hz"] = datad.sample_rate
            grp.attrs["gps_start"] = datad.gps_start.to_gpst_seconds()
            grp.attrs["unit"] = str(datad.unit)
        f.attrs.update(kwargs)


def export_data_mat(ddict: DataBufferDict, path, start, end, **kwargs):
    """Save data dictionary to a MAT file"""
    out = []
    groups = {}
    for id, datad in ddict.items():
        data = _get_data_slice(datad.original_struct, start, end)
        grp_name = str(id)
        if grp_name not in groups:
            span = (datad.gps_end - datad.gps_start).to_seconds()
            groups[grp_name] = OrderedDict(
                [
                    ("name", np.array(grp_name.encode("ascii"), dtype=np.str_)),
                    ("data", {}),
                    ("rate", datad.sample_rate),
                    ("start", datad.gps_start.to_gpst_seconds()),
                    ("duration", span),
                    ("unit", str(datad.unit)),
                ]
            )
        cd = groups[grp_name]
        name = id.trend_stat.data_name()
        cd["data"][name] = data.reshape(-1, 1)
        out.append(cd)
    # turn dict list into record array to conversion to struct array
    # get dtypes from first element dict
    dtypes = [(k, type(v)) for k, v in out[0].items()]
    values = [tuple(el.values()) for el in out]
    out = np.array(values, dtype=dtypes)
    recout = out.view(np.recarray)
    out = kwargs
    out["data"] = recout
    savemat(path, out)


DATA_EXPORT_FUNCS = {
    ".hdf5": export_data_hdf5,
    ".h5": export_data_hdf5,
    ".mat": export_data_mat,
}


##################################################
# TEMPLATE


def export_template_yaml(template, path):
    with open(path, "w") as f:
        yaml.safe_dump(template, f, default_style=None)


TEMPLATE_EXPORT_FUNCTIONS = {
    ".yaml": export_template_yaml,
    ".yml": export_template_yaml,
}


##################################################
# PLOT


def matplotlib_plot(ddict, t0=0.0, window: Optional[Tuple[float, float]] = None):
    for chan, data in ddict.items():
        color = get_channel_color(chan)
        kwargs = {
            "color": color,
            "label": chan,
        }

        if "raw" in data["data"]:
            y = data["data"]["raw"][:]
        else:
            y = data["data"]["mean"][:]

        t = np.arange(len(y)) / data["rate_hz"] + data["gps_start"] - t0

        plt.plot(t, y, **kwargs)
        for mm in ["min", "max"]:
            if mm not in data["data"]:
                continue
            ym = data["data"][mm][:]
            plt.fill_between(t, y, ym, color=color, alpha=0.5)

    plt.grid(True)
    plt.legend()
    if window is not None:
        plt.xlim(*window)
    if t0:
        plt.xlabel(f"GPS t0 = {t0}")
    else:
        plt.xlabel("GPS time")
    plt.show()
    # FIXME: return fig?


def matplot_h5(path):
    ddict = {}
    with h5py.File(path) as f:
        t0: float = f.attrs["t0"]  # type: ignore
        window: Optional[Tuple[float, float]] = f.attrs["window"]  # type: ignore
        for chan, grp in f.items():
            ddict[chan] = dict(grp.attrs)
            ddict[chan]["data"] = {}
            for t, d in grp.items():
                ddict[chan]["data"][t] = d[:]
    matplotlib_plot(ddict, t0=t0, window=window)
