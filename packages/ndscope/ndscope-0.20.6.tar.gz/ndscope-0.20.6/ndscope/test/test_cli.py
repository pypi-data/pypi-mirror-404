from pytest_console_scripts import ScriptRunner


def test_run_version(script_runner):
    script_runner.run(
        "ndscope --version",
        shell=True,
        check=True,
    )


def test_run_usage(script_runner):
    script_runner.run(
        "ndscope --usage",
        shell=True,
        check=True,
    )


def test_run_gen_template(script_runner):
    cmd = [
        "ndscope",
        "--gen-template",
    ]
    result = script_runner.run(cmd)
    assert result.returncode == 0
    assert (
        result.stdout
        == """
color-mode: dark
font-size: 10
grid-alpha: 0.2
plots:
- channels: []
  col: 0
  colspan: 1
  row: 0
  title: null
  yrange: auto
t0: null
time-window:
- -2
- 0
trend: null
trend-auto-raw-sec: 120
trend-auto-sec-min: 3600
window-title: ''

""".lstrip()
    )
    assert result.stderr == ""


def test_run_gen_template_args(script_runner):
    cmd = [
        "ndscope",
        "--grid",
        "--title",
        "My Plot",
        "--light",
        "--font-size",
        "12",
        "--line-width",
        "2",
        "--size",
        "600",
        "400",
        "FOO",
        "BAR",
        "BAZ",
        "--time",
        "1374515988",
        "--window",
        "10",
        "--gen-template",
    ]
    result = script_runner.run(cmd)
    assert result.returncode == 0
    assert (
        result.stdout
        == """
color-mode: light
font-size: 12
grid-alpha: 0.2
line-width: 2
plots:
- channels:
  - FOO:
      color: '#1f77b4'
      label: null
      offset: 0.0
      scale: 1.0
      unit: null
      width: 1
  col: 0
  colspan: 1
  row: 0
  title: null
  yrange: auto
- channels:
  - BAR:
      color: '#ff7f0e'
      label: null
      offset: 0.0
      scale: 1.0
      unit: null
      width: 1
  col: 1
  colspan: 1
  row: 0
  title: null
  yrange: auto
- channels:
  - BAZ:
      color: '#2ca02c'
      label: null
      offset: 0.0
      scale: 1.0
      unit: null
      width: 1
  col: 0
  colspan: 1
  row: 1
  title: null
  yrange: auto
t0: 1374515988.0
time-window:
- -5.0
- 5.0
trend: null
trend-auto-raw-sec: 120
trend-auto-sec-min: 3600
window-title: My Plot

""".lstrip()
    )
    assert result.stderr == ""
