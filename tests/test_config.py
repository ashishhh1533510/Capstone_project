from cnad.config import PROJECT_ROOT, load_config


def test_config_loads_locked_values():
    cfg = load_config()
    assert cfg["seed"] == 42
    assert cfg["splits"]["validation_fraction"] == 0.15
    assert cfg["splits"]["held_out_classes"] == ["DoS", "Reconnaissance", "Backdoor"]
    assert cfg["thresholds"]["percentile"] == 95


def test_paths_resolve_under_project_root():
    cfg = load_config()
    for path in cfg["paths"].values():
        assert path.is_absolute()
        assert PROJECT_ROOT in path.parents
