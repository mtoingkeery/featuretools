import os
import subprocess

import pytest

from featuretools.primitives.base import PrimitiveBase
from featuretools.primitives.install import (
    get_installation_dir,
    install_primitives,
    list_primitive_files,
    load_primitive_from_file,
    get_featuretools_root
)


@pytest.fixture(scope='module')
def primitives_to_install_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, "primitives_to_install")


@pytest.fixture(scope='module')
def bad_primitives_files_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, "bad_primitive_files")


@pytest.fixture(scope='module')
def primitives_to_install_archive():
    # command to make this file: tar -zcvf primitives_to_install.tar.gz primitives_to_install/*.py
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, "primitives_to_install.tar.gz")


def setup_installation():
    installation_dir = get_installation_dir()
    custom_max_file = os.path.join(installation_dir, "custom_max.py")
    custom_mean_file = os.path.join(installation_dir, "custom_mean.py")
    custom_sum_file = os.path.join(installation_dir, "custom_sum.py")

    # make sure primitive files aren't there e.g from a failed run
    for p in [custom_max_file, custom_mean_file, custom_sum_file]:
        try:
            os.unlink(p)
        except Exception:
            pass


def cleanup_installation():
    installation_dir = get_installation_dir()
    files = list_primitive_files(installation_dir)
    # then delete to clean up
    for f in files:
        os.unlink(f)


def do_installation(install_path):
    install_primitives(install_path, prompt=False)

    # due to how python modules are loaded/reloaded check for installed
    # primitives in subprocesses
    print(str(subprocess.check_output(['featuretools', "info"])))
    result = str(subprocess.check_output(['featuretools', "list-primitives"]))
    print(result)
    print("Featuretools installation directory: %s" % get_featuretools_root())

    # make sure the custom primitives are there
    assert "custommax" in result
    assert "custommean" in result
    assert "customsum" in result

    installation_dir = get_installation_dir()
    files = list_primitive_files(installation_dir)
    custom_max_file = os.path.join(installation_dir, "custom_max.py")
    custom_mean_file = os.path.join(installation_dir, "custom_mean.py")
    custom_sum_file = os.path.join(installation_dir, "custom_sum.py")
    assert set(files) == {custom_max_file, custom_mean_file, custom_sum_file}


def test_install_primitives_directory(primitives_to_install_dir):
    setup_installation()
    do_installation(primitives_to_install_dir)
    cleanup_installation()


def test_install_primitives_archive(primitives_to_install_archive):
    setup_installation()
    do_installation(primitives_to_install_archive)
    cleanup_installation()


def test_install_primitives_s3(primitives_to_install_dir, primitives_to_install_archive):
    setup_installation()
    s3_archive = "s3://featuretools-static/primitives_to_install.tar.gz"
    do_installation(s3_archive)
    cleanup_installation()


def test_install_primitives_https(primitives_to_install_dir, primitives_to_install_archive):
    setup_installation()
    https_archive = "https://s3.amazonaws.com/featuretools-static/primitives_to_install.tar.gz"
    do_installation(https_archive)
    cleanup_installation()


def test_list_primitive_files(primitives_to_install_dir):
    files = list_primitive_files(primitives_to_install_dir)
    custom_max_file = os.path.join(primitives_to_install_dir, "custom_max.py")
    custom_mean_file = os.path.join(primitives_to_install_dir, "custom_mean.py")
    custom_sum_file = os.path.join(primitives_to_install_dir, "custom_sum.py")
    assert set(files) == {custom_max_file, custom_mean_file, custom_sum_file}


def test_load_primitive_from_file(primitives_to_install_dir):
    primitve_file = os.path.join(primitives_to_install_dir, "custom_max.py")
    primitive_name, primitive_obj = load_primitive_from_file(primitve_file)
    assert issubclass(primitive_obj, PrimitiveBase)


def test_errors_more_than_one_primitive_in_file(bad_primitives_files_dir):
    primitive_file = os.path.join(bad_primitives_files_dir, "multiple_primitives.py")
    error_text = 'More than one primitive defined in file'
    with pytest.raises(RuntimeError, match=error_text):
        load_primitive_from_file(primitive_file)


def test_errors_no_primitive_in_file(bad_primitives_files_dir):
    primitive_file = os.path.join(bad_primitives_files_dir, "no_primitives.py")
    error_text = 'No primitive defined in file'
    with pytest.raises(RuntimeError, match=error_text):
        load_primitive_from_file(primitive_file)