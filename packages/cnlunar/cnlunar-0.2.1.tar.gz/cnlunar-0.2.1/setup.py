from setuptools import setup

setup(
    name='cnlunar',
    version='0.2.1',
    packages=['cnlunar'],
    url='https://github.com/OPN48/cnLunar',
    author='cuba3',
    author_email='cuba3@163.com',
    description="农历，中国农历历法项目，无需数据库环境，以《钦定协纪辨方书》为核心的python3 农历、黄历、二十四节气、节假日、星次、每日凶煞、每日值神、农历建除十二神、农历每日宜忌、彭祖百忌、每日五行、二十八星宿、天干地支、农历生辰八字、时辰凶吉等开源项目。",
    long_description=open("README.rst", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown"
)
# python3 setup.py sdist bdist_wheel
# python3 -m twine upload dist/*
# [pypi]
# name = '__token__'
# value = 'pypi-AgEIcHlwaS5vcmcCJDFkMmY2ZTdhLTExMWEtNDc3Ny04NDgzLTA2OWY2N2QzODY2YQACKlszLCJjZDU1NGM2OC03Y2Q1LTRlNTUtOTE0Mi1hNDJjM2I1NGFiMDQiXQAABiAnI0l3G3dr3D6_pB6W_4bQ9njJcjhpSYc2o22j3P0Y0Q'