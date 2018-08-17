from setuptools import setup
import subprocess

def get_git_tag():
    try:
        rev = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--long']).decode('latin1').strip()
        rev = rev.split('-')
        print(len(rev), rev)
        if len(rev) < 3:
            return None
        return f"{rev[0]}.{rev[1]}+{'.'.join(rev[2:])}"
    except subprocess.CalledProcessError:
        return None

def get_git_hash():
    try:
        rev = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD']).decode('latin1').strip()
        return "0.0.0+" + rev
    except subprocess.CalledProcessError:
        return None

def get_version():
    fns = [
        get_git_tag,
        get_git_hash,
        lambda: "0.0.0"]

    version = None
    for i_fn in fns:
        version = i_fn()
        if version:
            break

    print(version)
    return version

setup(
    name='beacon',
    version=get_version(),
    packages=['beacon'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['beacon=beacon:main'],
    },
    install_requires= [
        'werkzeug>=0.14.1',
        'tensorboard>=1.8.0',
    ],
)
