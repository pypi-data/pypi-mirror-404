def test_versions():
    """Check we have the defined version info"""
    from dpps import VERSION_INFO, __version__

    assert __version__ != "0.0.0dev0"
    assert "wms" in VERSION_INFO
    assert "bdms" in VERSION_INFO
    assert "rucio" in VERSION_INFO
