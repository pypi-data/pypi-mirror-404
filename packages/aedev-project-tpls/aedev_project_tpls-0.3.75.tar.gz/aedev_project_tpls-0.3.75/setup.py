# THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.project_tpls v0.3.74
""" setup of aedev namespace package portion project_tpls: managed Python project files templates. """
import sys
# noinspection PyUnresolvedReferences
import pathlib
# noinspection PyUnresolvedReferences
import setuptools


print("SetUp " + __name__ + ": " + sys.executable + str(sys.argv) + f" {sys.path=}")

setup_kwargs = {
    'author': 'AndiEcker',
    'author_email': 'aecker2@gmail.com',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
    'description': 'aedev namespace package portion project_tpls: managed Python project files templates',
    'extras_require': {
        'dev': [
            'aedev_project_tpls',
            'aedev_aedev',
            'anybadge',
            'coverage-badge',
            'flake8',
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'typing',
            'types-setuptools',
        ],
        'docs': [],
        'tests': [
            'anybadge',
            'coverage-badge',
            'flake8',
            'mypy',
            'pylint',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'typing',
            'types-setuptools',
        ],
    },
    'install_requires': [],
    'keywords': [
        'configuration',
        'development',
        'environment',
        'productivity',
    ],
    'license': 'GPL-3.0-or-later',
    'long_description': (pathlib.Path(__file__).parent / 'README.md').read_text(encoding='utf-8'),
    'long_description_content_type': 'text/markdown',
    'name': 'aedev_project_tpls',
    'package_data': {
        '': [
            'templates/de_tpl_README.md',
            'templates/de_sfp_de_otf_de_tpl_.readthedocs.yaml',
            'templates/de_otf_pyproject.toml',
            'templates/de_otf_de_tpl_dev_requirements.txt',
            'templates/de_otf_de_tpl_.gitlab-ci.yml',
            'templates/de_otf_de_tpl_setup.py',
            'templates/de_otf_de_tpl_.gitignore',
            'templates/de_otf_SECURITY.md',
            'templates/de_otf_LICENSE.md',
            'templates/de_otf_de_tpl_CONTRIBUTING.rst',
            'templates/tests/de_otf_de_tpl_requirements.txt',
            'templates/tests/de_otf_conftest.py',
            'templates/tests/de_tpl_test_{portion_name or project_name}.py',
            'templates/de_sfp_docs/de_otf_Makefile',
            'templates/de_sfp_docs/de_otf_de_tpl_requirements.txt',
            'templates/de_sfp_docs/de_otf_de_tpl_index.rst',
            'templates/de_sfp_docs/features_and_examples.rst',
            'templates/de_sfp_docs/de_otf_de_tpl_conf.py',
        ],
    },
    'packages': [
        'aedev.project_tpls',
        'aedev.project_tpls.templates',
        'aedev.project_tpls.templates.tests',
        'aedev.project_tpls.templates.de_sfp_docs',
    ],
    'project_urls': {
        'Bug Tracker': 'https://gitlab.com/aedev-group/aedev_project_tpls/-/issues',
        'Documentation': 'https://aedev.readthedocs.io/en/latest/_autosummary/aedev.project_tpls.html',
        'Repository': 'https://gitlab.com/aedev-group/aedev_project_tpls',
        'Source': 'https://aedev.readthedocs.io/en/latest/_modules/aedev/project_tpls.html',
    },
    'python_requires': '>=3.12',
    'url': 'https://gitlab.com/aedev-group/aedev_project_tpls',
    'version': '0.3.75',
    'zip_safe': False,
}

if __name__ == "__main__":
    setuptools.setup(**setup_kwargs)
    pass
