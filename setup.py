from setuptools import setup

setup(
	name='fossil-tools',
	version='0.5.0',
    package_dir={
        "fossil_tools": "tools"
    },
    entry_points={
        'console_scripts': [
            'fossil_image=fossil_tools.fossil_image:main'
        ]
    },
    install_requires=[
        "Pillow",
        "crc32c"
    ],
)
