"""Tests unitaires — configuration (config/loader.py)."""

import pytest

from config.loader import load_config


# ═══════════════════════════════════════════════════════════════
# Fusion common + spécifique
# ═══════════════════════════════════════════════════════════════

class TestLoadConfig:

    def test_cone_has_physics_section(self):
        cfg = load_config("cone")
        assert "physics" in cfg

    def test_cone_has_depth(self):
        cfg = load_config("cone")
        assert "depth" in cfg["physics"]
        assert cfg["physics"]["depth"] > 0

    def test_cone_inherits_R_from_common(self):
        cfg = load_config("cone")
        assert "R" in cfg["physics"]
        assert cfg["physics"]["R"] == pytest.approx(0.4)

    def test_cone_inherits_friction(self):
        cfg = load_config("cone")
        assert "friction" in cfg["physics"]

    def test_cone_inherits_dt(self):
        cfg = load_config("cone")
        assert "dt" in cfg["physics"]
        assert cfg["physics"]["dt"] > 0

    def test_membrane_has_k(self):
        cfg = load_config("membrane")
        assert "k" in cfg["physics"]
        assert cfg["physics"]["k"] > 0

    def test_membrane_inherits_common_physics(self):
        cfg = load_config("membrane")
        phys = cfg["physics"]
        for key in ("R", "g", "friction", "dt", "n_steps", "center_radius"):
            assert key in phys, f"Clé manquante : {key}"

    def test_ml_has_paths(self):
        cfg = load_config("ml")
        assert "paths" in cfg
        assert "tracking_data" in cfg["paths"]
        assert "synth_data_dir" in cfg["paths"]
        assert "models_dir"     in cfg["paths"]

    def test_ml_has_synth_contexts(self):
        cfg = load_config("ml")
        ctx = cfg["synth"]["contexts"]
        assert "names" in ctx
        assert "fractions" in ctx
        assert len(ctx["names"]) == len(ctx["fractions"])

    def test_ml_contexts_fractions_in_range(self):
        cfg = load_config("ml")
        for frac in cfg["synth"]["contexts"]["fractions"]:
            assert 0 < frac <= 1.0

    def test_ml_has_model_section(self):
        cfg = load_config("ml")
        assert "model" in cfg
        assert "n_features" in cfg["model"]
        assert cfg["model"]["n_features"] == 9

    def test_ml_inherits_R_from_common(self):
        cfg = load_config("ml")
        assert cfg["physics"]["R"] == pytest.approx(0.4)

    def test_merge_depth1_preserves_common_keys(self):
        # cone.toml ajoute depth=0.09 sans effacer R, g, friction de common
        cfg = load_config("cone")
        phys = cfg["physics"]
        assert "R" in phys
        assert "g" in phys
        assert "friction" in phys
        assert "depth" in phys

    def test_new_physics_params_present(self):
        # Les 3 nouvelles clés ajoutées dans common.toml [physics]
        cfg = load_config("cone")
        phys = cfg["physics"]
        assert "rolling"            in phys
        assert "rolling_resistance" in phys
        assert "drag_coeff"         in phys

    def test_default_physics_levels_are_off(self):
        cfg = load_config("cone")
        phys = cfg["physics"]
        assert phys["rolling"]            == False
        assert phys["rolling_resistance"] == pytest.approx(0.0)
        assert phys["drag_coeff"]         == pytest.approx(0.0)

    def test_invalid_config_name_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("config_inexistante_xyz")

    def test_preset_default_present(self):
        cfg = load_config("cone")
        assert "preset" in cfg
        assert "default" in cfg["preset"]
        preset = cfg["preset"]["default"]
        for key in ("r0", "theta0", "v0", "direction_deg"):
            assert key in preset, f"Clé preset manquante : {key}"

    def test_ranges_present(self):
        cfg = load_config("cone")
        assert "ranges" in cfg
        ranges = cfg["ranges"]
        for key in ("r0", "theta0", "v0", "direction_deg"):
            assert key in ranges, f"Clé ranges manquante : {key}"
            assert len(ranges[key]) == 2
            assert ranges[key][0] < ranges[key][1]

    def test_ml_synth_physics_depth(self):
        cfg = load_config("ml")
        assert "synth" in cfg
        assert "depth" in cfg["synth"]["physics"]

    def test_mcu_config_has_own_presets(self):
        # mcu.toml surcharge complètement les presets de common.toml
        cfg = load_config("mcu")
        assert "preset" in cfg
        assert "default" in cfg["preset"]
