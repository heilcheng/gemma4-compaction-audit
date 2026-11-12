from gpaper.memory import Memory, fingerprint, mask_observations


def test_fingerprint_tracks_edit_and_new_file(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    s0 = fingerprint(tmp_path)
    assert fingerprint(tmp_path) == s0
    (tmp_path / "a.py").write_text("x=2")
    s1 = fingerprint(tmp_path)
    assert s1 != s0
    (tmp_path / "b.py").write_text("")
    assert fingerprint(tmp_path) != s1


def test_flat_and_fresh_share_evidence_body():
    m = Memory()
    m.add("test", "2 failed", "S0")
    m.add("edit", "patched f()", "S0")
    m.add("read", "def f(): ...", "S1")
    strip = lambda s: [l.split("] ", 1)[1] for l in s.splitlines()]
    assert strip(m.render_flat()) == strip(m.render_fresh("S1")) == strip(m.render_control("S1"))
    assert "older code state" in m.render_fresh("S1").splitlines()[0]
    assert "current" in m.render_fresh("S1").splitlines()[2]
    assert "validated" not in m.render_flat() and "older" not in m.render_control("S1")


def test_masking_keeps_actions():
    h = [("a1", "o1"), ("a2", "o2"), ("a3", "o3")]
    out = mask_observations(h, 1)
    assert [a for a, _ in out] == ["a1", "a2", "a3"] and out[2][1] == "o3" and out[0][1] != "o1"
