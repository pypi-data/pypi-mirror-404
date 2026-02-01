from datetime import datetime
from pip_setuptools import setup, clean, find_packages, requirements
from setuptools.command.develop import develop

desc = '\n'.join(reversed(('Универсальная библиотека python для большинства задач', 'A universal python library for most tasks')))


class Develop(develop):
    def run(self):
        # Устанавливаем специальную версию для develop
        self.distribution.metadata.version = self.get_dev_version()
        super().run()

    def get_dev_version(self):
        return str(self.distribution.metadata.version) + f'-build-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'


BASE_REQUIREMENTS = requirements('requirements/requirements.txt')
IMAGE_REQUIREMENTS = requirements('requirements/image_requirements.txt')
FLASK_REQUIREMENTS = requirements('requirements/flask_requirements.txt')
FILETYPE_REQUIREMENTS = requirements('requirements/filetype_requirements.txt')
DEV_REQUIREMENTS = requirements('requirements/dev_requirements.txt')
BASE_DEV_REQUIREMENTS = BASE_REQUIREMENTS + BASE_REQUIREMENTS
FULL_DEV_REQUIREMENTS = BASE_DEV_REQUIREMENTS + IMAGE_REQUIREMENTS + FLASK_REQUIREMENTS + FILETYPE_REQUIREMENTS

REQUIREMENTS = dict(
    base=BASE_REQUIREMENTS,
    image=BASE_REQUIREMENTS + IMAGE_REQUIREMENTS,
    flask=BASE_REQUIREMENTS + FLASK_REQUIREMENTS,
    filetype=BASE_REQUIREMENTS + FILETYPE_REQUIREMENTS,
    dev=BASE_DEV_REQUIREMENTS,
    dev_base=BASE_DEV_REQUIREMENTS,
    dev_image=BASE_DEV_REQUIREMENTS + IMAGE_REQUIREMENTS,
    dev_flask=BASE_DEV_REQUIREMENTS + FLASK_REQUIREMENTS,
    dev_filetype=BASE_DEV_REQUIREMENTS + FILETYPE_REQUIREMENTS,
    all=BASE_REQUIREMENTS + FLASK_REQUIREMENTS + IMAGE_REQUIREMENTS + FILETYPE_REQUIREMENTS,
    dev_all=FULL_DEV_REQUIREMENTS,
    dev_full=FULL_DEV_REQUIREMENTS,
)

clean()
setup(
    name='hrenpack',
    version='2.5.4',
    author_email='magilyas.doma.09@list.ru',
    author='Маг Ильяс DOMA (MagIlyasDOMA)',
    description=desc,
    license='MIT',
    url='https://github.com/MagIlyasDOMA/hrenpack',
    packages=find_packages(),
    setup_requires=DEV_REQUIREMENTS,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 11',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Framework :: Django',
        'Framework :: Django :: 5.2',
        'Natural Language :: English',
        'Natural Language :: Russian',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security :: Cryptography',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    platforms=[
        'Windows',
        'Windows 10',
        'Windows 11',
        'Windows Server 2019+',
        'Linux'
    ],
    project_urls=dict(
        Source='https://github.com/MagIlyasDOMA/hrenpack',
        Documentation='https://magilyasdoma.github.io/hrenpack/documentation.html',
        Changelog='https://github.com/MagIlyasDOMA/hrenpack/blob/main/CHANGELOG.md'
    ),
    python_requires='>=3.10',
    install_requires=BASE_REQUIREMENTS,
    extras_require=REQUIREMENTS,
    include_package_data=True,
    cmdclass=dict(
        develop=Develop,
    ),
)
