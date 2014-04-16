import os.path
import sys

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import find_packages, setup
from setuptools.command.test import test
from earthreader.web.version import VERSION


def readme():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
            return f.read()
    except (IOError, OSError):
        return ''


class pytest(test):

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        from pytest import main
        errno = main(self.test_args)
        raise SystemExit(errno)


setup_requires = [
    'libsass >= 0.3.0'
]

install_requires = [
    'Flask >= 0.10',
    'libearth >= 0.1.1',
    'waitress'
]
if sys.version_info < (2, 7):
    install_requires.append('argparse >= 1.1')
install_requires.extend(setup_requires)


setup(
    name='EarthReader-Web',
    version=VERSION,
    description='Earth Reader for Web',
    long_description=readme(),
    url='http://earthreader.org/',
    author='Earth Reader team',
    author_email='earthreader' '@' 'librelist.com',
    entry_points={
        'console_scripts': [
            'earthreader = earthreader.web.command:main'
        ]
    },
    app=['app.py'],
    license='AGPLv3 or later',
    packages=find_packages(exclude=['tests']),
    package_data={
        'earthreader.web': ['templates/*.*', 'templates/*/*.*',
                            'static/*.*', 'static/*/*.*']
    },
    sass_manifests={
        'earthreader.web': ('static/scss/', 'static/css/')
    },
    setup_requires=setup_requires,
    install_requires=install_requires,
    dependency_links=[
        'https://github.com/earthreader/libearth/releases'
    ],
    download_url='https://github.com/earthreader/web/releases',
    tests_require=['pytest >= 2.5.0'],
    cmdclass={'test': pytest},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved ::'
        ' GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Communications',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Text Processing :: Markup :: XML'
    ]
)
