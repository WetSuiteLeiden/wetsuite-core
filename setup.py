from setuptools import setup

setup(
    name='wetsuite',
    version='0.1.0',
    classifiers=['Development Status :: 3 - Alpha',   'Programming Language :: Python :: 3',   'Topic :: Text Processing :: Linguistic'],
    url='https://github.com/knobs-dials/wetsuite-dev.git',
    author='Wetsuite team',
    author_email='scarfboy@gmail.com',
    description='Wetsuite',
    packages=['wetsuite.datasets', 'wetsuite.helpers', 'wetsuite.datacollect', 'wetsuite.extras'],
    package_dir={"": "src"},
    python_requires=">=3",
    install_requires=[
        'lxml',                # BSD
        'bs4',                 # MIT
        'msgpack',             # Apache2
        'requests',            # Apache2
        'python-dateutil',     # Apache2
        'numpy >= 1.11.1',     # BSD
        'matplotlib >= 1.5.1', # BSD
        'spacy',               # MIT
        'pillow',              # HPND, which is permissive, and GPL-compatible
        'PyMuPDF',             # AGPL (or commercial)
    ],
    extras_require={
        #'spacy-transformers',  # MIT
        'spacy-cpu':'spacy',
        'spacy-cuda80':'spacy[cuda80]',
        'spacy-cuda90':'spacy[cuda90]','spacy-cuda91':'spacy[cuda91]','spacy-cuda92':'spacy[cuda92]',
        'spacy-cuda100':'spacy[cuda100]','spacy-cuda101':'spacy[cuda101]','spacy-cuda102':'spacy[cuda102]','spacy-cuda110':'spacy[cuda110]',
        'spacy-cuda111':'spacy[cuda111]','spacy-cuda112':'spacy[cuda112]','spacy-cuda113':'spacy[cuda113]','spacy-cuda114':'spacy[cuda114]','spacy-cuda115':'spacy[cuda115]','spacy-cuda116':'spacy[cuda116]','spacy-cuda117':'spacy[cuda117]',
        'fastlang':[
            'spacy_fastlang',    # MIT
            'fasttext'           # MIT
        ],
        'ocr':'easyocr',         # Apache2
        'extras':['wordcloud',], # MIT
        # all?
    },
)
