from setuptools import setup, find_packages


def scm_version():
    def local_scheme(version):
        if version.tag and not version.distance:
            return version.format_with("")
        else:
            return version.format_choice("+{node}", "+{node}.dirty")
    return {
        "relative_to": __file__,
        "version_scheme": "guess-next-dev",
        "local_scheme": local_scheme
    }


setup(
    name="systemonachip",
    use_scm_version=scm_version(),
    author="Scott Shawcroft",
    author_email="scott@chickadee.tech",
    description="A framework for building system-on-a-chips with nMigen",
    #long_description="""TODO""",
    license="BSD",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "nmigen>=0.1,<0.3",
    ],
    packages=find_packages(),
    include_package_data=True,
    project_urls={
        "Source Code": "https://github.com/tannewt/systemonachip",
        "Bug Tracker": "https://github.com/tannwet/systemonachip/issues",
    },
)
