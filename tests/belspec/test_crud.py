# Local
import bel.belspec.crud


def test_check_version():

    versions = {
        "doc_type": "belspec_versions",
        "latest": "2.1.2",
        "default": "latest",
        "versions": ["latest", "2.1.2", "2.0.1"],
    }

    version_start = "latest"
    expected = "2.1.2"

    version = bel.belspec.crud.check_version(version=version_start, versions=versions)

    print("Version Start", version_start, "End:", version)

    assert version == expected

    version_start = "2.0.0"
    expected = "2.0.1"

    version = bel.belspec.crud.check_version(version=version_start, versions=versions)

    print("Version Start", version_start, "End:", version)

    assert version == expected
