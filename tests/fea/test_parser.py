from pathlib import Path

from cold_drawing_twin.simulation.postprocess.parser import parse_solver_outputs
from cold_drawing_twin.simulation.postprocess.quality_gate import evaluate_quality

FIXTURES = Path(__file__).parent / "fixtures"


def test_parser_reads_listing_fixture(tmp_path: Path):
    (tmp_path / "engine.out").write_text((FIXTURES / "engine.out").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "fields.json").write_text((FIXTURES / "fields.json").read_text(encoding="utf-8"), encoding="utf-8")
    parsed = parse_solver_outputs(tmp_path)
    assert parsed["placeholder"] is False
    assert parsed["termination"]["normal"] is True
    assert parsed["metrics"]["internal_energy"] == 125.0
    assert parsed["metrics"]["kinetic_energy"] == 0.41
    assert parsed["metrics"]["drawing_force_n"] == 8750.0
    assert parsed["metrics"]["peak_von_mises_pa"] == 612.0e6
    assert parsed["fields"]["source"] == "parser-fixture"


def test_parser_fixture_is_not_labeled_as_a_live_solve():
    text = (FIXTURES / "engine.out").read_text(encoding="utf-8")
    assert "not an actual openradioss solve" in text.lower()


def test_parser_reads_radioss_cycle_table(tmp_path: Path):
    listing = """
   CYCLE    TIME      TIME-STEP  ELEMENT          ERROR  I-ENERGY    K-ENERGY T  K-ENERGY R  EXT-WORK
     100  0.8227E-05  0.8227E-07 QUAD      100006   1.2%  12.50       0.4100       0.000       8.75
     NORMAL TERMINATION
"""
    (tmp_path / "engine.out").write_text(listing, encoding="utf-8")
    parsed = parse_solver_outputs(tmp_path)
    assert parsed["metrics"]["internal_energy"] == 12.5
    assert parsed["metrics"]["kinetic_energy"] == 0.41
    assert parsed["metrics"]["energy_error"] == 0.012
    assert parsed["metrics"]["external_work"] == 8.75
    assert parsed["termination"]["normal"] is True


def test_parser_reads_th_csv_reacz(tmp_path: Path):
    csv_text = (
        "time,INTERNAL ENERGY,KINETIC ENERGY,EXTERNAL WORK,CONTACT ENERGY,"
        "draw_end 81 PULL var 27,draw_end 81 PULL var 28,draw_end 81 PULL var 29\n"
        "0.0,1.0,0.1,0.5,0.0,0.0,0.01,12.0\n"
        "0.1,2.0,0.2,1.5,0.0,0.02,0.009,-8750.0\n"
    )
    (tmp_path / "runT01.csv").write_text(csv_text, encoding="utf-8")
    (tmp_path / "engine.out").write_text("NORMAL TERMINATION\n", encoding="utf-8")
    parsed = parse_solver_outputs(tmp_path)
    assert parsed["metrics"]["internal_energy"] == 2.0
    assert parsed["metrics"]["external_work"] == 1.5
    assert parsed["metrics"]["contact_energy"] == 0.0
    assert parsed["metrics"]["drawing_force_n"] == 8750.0


def test_quality_rejects_missing_termination():
    ok, reason = evaluate_quality(
        solver_status="SUCCEEDED",
        parsed={
            "termination": {"status": "MISSING", "normal": False},
            "files": [],
            "histories": {},
            "metrics": {},
        },
        mesh={"workpiece": {"element_count": 64, "node_count": 85}},
    )
    assert ok is False
    assert "termination" in reason


def test_quality_rejects_saturated_energy_error():
    ok, reason = evaluate_quality(
        solver_status="SUCCEEDED",
        parsed={
            "termination": {"status": "NORMAL_TERMINATION", "normal": True},
            "files": ["starter.stdout.log", "engine.stdout.log"],
            "histories": {"kinetic_energy": [0.2], "internal_energy": [10.0]},
            "metrics": {
                "peak_von_mises_pa": 400.0e6,
                "peak_plastic_strain": 0.2,
                "drawing_force_n": 1000.0,
                "kinetic_energy": 0.2,
                "internal_energy": 10.0,
                "energy_error": 0.999,
            },
        },
        mesh={"workpiece": {"element_count": 64, "node_count": 85}},
    )
    assert ok is False
    assert "energy error" in reason


def test_quality_accepts_unsaturated_listing_error():
    ok, reason = evaluate_quality(
        solver_status="SUCCEEDED",
        parsed={
            "termination": {"status": "NORMAL_TERMINATION", "normal": True},
            "files": ["starter.stdout.log", "engine.stdout.log"],
            "histories": {"kinetic_energy": [0.001], "internal_energy": [108.0]},
            "metrics": {
                "peak_von_mises_pa": 737.0e6,
                "peak_plastic_strain": 0.35,
                "drawing_force_n": 9100.0,
                "kinetic_energy": 0.001,
                "internal_energy": 108.0,
                "energy_error": 0.272,
            },
        },
        mesh={"workpiece": {"element_count": 64, "node_count": 85}},
    )
    assert ok is True
    assert "normal termination" in reason
