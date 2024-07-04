from EO_Floods.providers import GFM


def test_init_GFM():
    gfm = GFM(
        start_date="2022-10-01",
        end_date="2022-10-15",
        geometry=[67.740187, 27.712453, 68.104933, 28.000935],
    )
