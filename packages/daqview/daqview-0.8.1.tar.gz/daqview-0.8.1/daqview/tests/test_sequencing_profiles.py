# pytest standard usage means these warnings are not required:
# pylint: disable=no-self-use, missing-docstring, redefined-outer-name
# pylint: disable=unused-argument

from daqview.models.sequencing import Config


def test_load_config(sequence_template):
    cfg = Config(sequence_template)
    for box in ("Box1", "Box2", "Box3"):
        assert box in cfg.cfg_daus
    for role in ("V1", "V2", "V3", "V4", "VA", "VB"):
        assert role in cfg.cfg_roles
    assert len(cfg.cfg_templates) == 2


def test_template(sequence_template):
    cfg = Config(sequence_template)
    tpl = cfg.templates[0]
    assert tpl.name == "Test Template"
    assert tpl.description == "Test template for automated tests"
    assert tpl.tzero_offset == -10.0
    assert tpl.variables[0] == {
        "id": "duration",
        "name": "Duration",
        "description": "Test duration",
        "units": "s",
        "default": 10.0,
        "type": "float",
        "step": 0.1,
        "decimals": 1,
        "minimum": 0.0,
        "maximum": 100.0,
    }

    variables = {
        "duration": 5.0,
        "mdot": 1.5,
    }
    rendered = tpl.render(variables)

    for profile in rendered.profiles:
        profile.to_display()
    for sequence in rendered.sequences:
        sequence.to_display()
