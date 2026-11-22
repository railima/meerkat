from icons import tray_icon


def test_tray_icon_variants():
    for count, error in [(0, False), (3, False), (120, False), (0, True)]:
        img = tray_icon(count, error)
        assert img.size == (64, 64)
        assert img.mode == "RGBA"
    assert tray_icon(0, False).tobytes() != tray_icon(3, False).tobytes()
