"""Layout read-back must tolerate row ordering noise, never missing transforms."""

import json

import fdm_cad.build as builder
import numpy as np
import pytest

from fdm_cad.geometry import load_mesh_instances


def bounds(x=0.0, y=0.0):
    return np.array([[x, y, 0.0], [x+10.0, y+5.0, 2.0]])


def test_layout_bounds_matches_observed_row_sort_regression():
    # Real revision012 bounds: CAD epsilon puts the slider before the bracket;
    # tessellation rounds both X minima to zero and instead orders them by Y.
    expected = [
        [[-8.881784197001252e-16, 196.0, -1.0164568432923028e-15],
         [35.75, 210.5, 21.0]],
        [[0.0, 103.20000000000002, -2.755455298081545e-16],
         [114.3, 188.0, 32.20000000000002]],
    ]
    actual = [
        [[0.0, 103.2, 0.0], [114.3, 188.0, 32.2]],
        [[0.0, 196.000944, 0.0], [35.75, 210.5, 21.0]],
    ]
    assert not np.allclose(sorted(actual, key=lambda b: b[0]),
                           sorted(expected, key=lambda b: b[0]), atol=0.05, rtol=0)
    assert builder.match_layout_bounds(expected, actual) == [1, 0]


def test_layout_bounds_reassigns_an_ambiguous_first_match():
    # The first actual bound could match either expected bound; the second
    # actual bound can only match the first. Greedy matching cannot resolve it.
    expected = [bounds(0.0), bounds(0.08)]
    actual = [bounds(0.04), bounds(0.0)]
    assert builder.match_layout_bounds(expected, actual) == [1, 0]


def test_layout_bounds_rejects_duplicate_instances_with_missing_counterpart():
    # Every bound has at least one candidate, in both directions, but the counts
    # at the two positions differ. One mesh must never satisfy two CAD parts.
    expected = [bounds(0.0), bounds(0.0), bounds(20.0)]
    actual = [bounds(0.0), bounds(20.0), bounds(20.0)]
    with pytest.raises(ValueError, match="no one-to-one bounds match"):
        builder.match_layout_bounds(expected, actual)


@pytest.mark.parametrize("change", ["position", "extent", "large_position"])
def test_layout_bounds_rejects_actual_errors_beyond_absolute_tolerance(change):
    expected = bounds(1_000_000 if change == "large_position" else 0.0)
    actual = expected.copy()
    if change == "extent":
        actual[1, 2] += 0.051
    else:
        actual[:, 0] += 0.051
    with pytest.raises(ValueError, match="no one-to-one bounds match"):
        builder.match_layout_bounds([expected], [actual])


@pytest.mark.parametrize("shift,valid", [(-1e-12, True), (-0.051, False)])
def test_build_roundtrip_row_noise_and_bad_transform(tmp_path, monkeypatch, shift, valid):
    model = tmp_path / "rows.py"
    model.write_text('''from build123d import Align, Box, Pos

def build(p):
    block = Box(150, 20, 2, align=(Align.MIN, Align.MIN, Align.MIN))
    parts = {name: block for name in ("first", "second", "third")}
    assembly = {name: Pos(index*200, 0, 0)*part
                for index, (name, part) in enumerate(parts.items())}
    return {"parts": parts, "assembly": assembly}
''')
    parameters = tmp_path / "parameters.json"
    parameters.write_text('{}')

    def reordered_instances(path):
        instances = load_mesh_instances(path)
        last_row = max(instances, key=lambda entry: entry[1].bounds[0, 1])[1]
        last_row.apply_translation([shift, 0, 0])
        return list(reversed(instances))

    # Exercise the builder's actual final-layout validation. Individual meshes
    # and layout count inspection still use the real independent mesh loader.
    monkeypatch.setattr(builder, "load_mesh_instances", reordered_instances)
    output = tmp_path / "built"
    if valid:
        report = builder.build_project(model, parameters, output, previews=False)
        comparison = report["print_layout"]["bounds_comparison"]
        assert report["status"] == "passed"
        assert comparison["absolute_tolerance_mm"] == 0.05
        assert comparison["relative_tolerance"] == 0.0
        assert len({match["mesh_instance"] for match in comparison["matches"]}) == 3
        assert {match["part"] for match in comparison["matches"]} == {"first", "second", "third"}
        assert json.loads((output / "validation.json").read_text())["status"] == "passed"
    else:
        with pytest.raises(ValueError, match="no one-to-one bounds match"):
            builder.build_project(model, parameters, output, previews=False)
        assert not output.exists()
