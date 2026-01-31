from pkg_resources import resource_filename

from .. import template


def test_load_template():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test.yaml")
    t, _ = template.load_template(path)
    assert t["time-window"] == -100


def test_create_template_chans0():
    template._CHANNEL_COLORS = {}
    chans = ["A", "B", "C"]
    t0, l0 = template.template_from_chans(chans)
    template.convert_layout(t0, "grid")
    path = resource_filename(__name__, "templates/test0.yaml")
    t1, l1 = template.load_template(path)
    assert t0 == t1


def test_create_template_chans1():
    template._CHANNEL_COLORS = {}
    chans = ["A", ".", "B", "C", ".", "D"]
    t0, l0 = template.template_from_chans(chans)
    path = resource_filename(__name__, "templates/test1.yaml")
    t1, l1 = template.load_template(path)
    assert t0 == t1


def test_template_convert_grid():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test1.yaml")
    t0, l0 = template.load_template(path)
    template.convert_layout(t0, "grid")
    path = resource_filename(__name__, "templates/test1-1.yaml")
    t1, l1 = template.load_template(path)
    assert t0 == t1


def test_template_convert_stack():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test1.yaml")
    t0, l0 = template.load_template(path)
    template.convert_layout(t0, "stack")
    path = resource_filename(__name__, "templates/test1-2.yaml")
    t1, l1 = template.load_template(path)
    assert t0 == t1


def test_template_convert_single():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test1.yaml")
    t0, l0 = template.load_template(path)
    template.convert_layout(t0, "single")
    path = resource_filename(__name__, "templates/test1-3.yaml")
    t1, l1 = template.load_template(path)
    assert t0 == t1


def test_load_template_stp():
    path = resource_filename(__name__, "templates/test2.stp")
    t0, l0 = template.load_template(path)
    assert l0 == "single"
    path = resource_filename(__name__, "templates/test2.yaml")
    t1, l1 = template.load_template(path)
    assert l1 == "table"
    assert t0 == t1


def test_load_template_txt():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test3.txt")
    t0, l0 = template.load_template(path)
    assert l0 == "grid"
    path = resource_filename(__name__, "templates/test3.yaml")
    t1, l1 = template.load_template(path)
    assert l1 == "table"
    assert t0 == t1


def test_load_template_xml():
    template._CHANNEL_COLORS = {}
    path = resource_filename(__name__, "templates/test4.xml")
    t0, l0 = template.load_template(path)
    assert l0 == "grid"
    path = resource_filename(__name__, "templates/test4.yaml")
    t1, l1 = template.load_template(path)
    assert l1 == "table"
    assert t0["plots"] == t1["plots"]
