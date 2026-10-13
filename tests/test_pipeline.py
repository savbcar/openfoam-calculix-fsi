from fsi.config import load_config
from fsi.pipeline import run_synthetic_demo


def test_end_to_end_demo(tmp_path):
    cfg = load_config("config/baseline.yaml")
    payload = run_synthetic_demo(cfg, tmp_path)
    assert payload["acceptance"]["force_pass"]
    assert payload["acceptance"]["moment_pass"]
    assert (tmp_path / "calculix" / "panel.inp").exists()
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "figures" / "pressure_mapping.png").exists()
