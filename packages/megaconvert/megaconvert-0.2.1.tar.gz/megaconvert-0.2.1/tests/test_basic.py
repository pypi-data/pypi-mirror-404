from megaconvert import list_converters, supports

def test_registry_loads():
    names = list_converters()
    assert isinstance(names, list)
    assert len(names) >= 1

def test_supports_bool():
    assert isinstance(supports("pdf", "pdf"), bool)
