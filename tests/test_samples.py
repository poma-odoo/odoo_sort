import pathlib

from osort import osort


def pytest_generate_tests(metafunc):
    samples_dir = pathlib.Path("test_data/samples")

    samples = []
    for input_path in samples_dir.glob("*_input.py"):
        samples.append(input_path.name[: -len("_input.py")])
    samples.sort()
    assert samples

    metafunc.parametrize("sample", samples)


# def test_samples(sample):
#     samples_dir = pathlib.Path("test_data/samples")
#     input_path = samples_dir / f"{sample}_input.py"
#     output_path = samples_dir / f"{sample}_output.py"
#     input_text = input_path.read_bytes()
#
#     actual_text = osort(
#         input_text,
#         filename=str(input_path),
#         on_wildcard_import=lambda **kwargs: None,
#     )
#
#     # XXX Uncomment to update samples. XXX
#     # output_path.write_bytes(actual_text)
#     # XXX Don't forget to restore re-comment after. XXX
#
#     expected_text = output_path.read_bytes()
#
#     assert actual_text == expected_text


def test_idempotent(sample):
    samples_dir = pathlib.Path("test_data/samples")
    input_path = samples_dir / f"{sample}_input.py"
    input_text = input_path.read_bytes()

    sorted_text = osort(
        input_text,
        filename=str(input_path),
        on_wildcard_import=lambda **kwargs: None,
    )
    resorted_text = osort(
        sorted_text,
        filename=str(input_path),
        on_wildcard_import=lambda **kwargs: None,
    )

    assert resorted_text == sorted_text
