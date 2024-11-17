from setuptools import setup

setup(
    name             = 'wetsuite',
    version          = '0.2.2',
    description      = 'A library that helps to explore dutch legal data, and to apply language processing on it',
    long_description = 'A library that helps to explore dutch legal data, and to apply language processing on it. This is the library code, you are probably more interested in some notebooks that use it, at https://github.com/WetSuiteLeiden/example-notebooks or the website that introduces it, http://wetsuite.nl',

    author           = 'Wetsuite team',
    author_email     = 'alewijnse.bart+wetsuite@gmail.com',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)',
    ],
    url          = 'https://github.com/WetSuiteLeiden/wetsuite-core.git',
    project_urls = {
        'Project home':'https://wetsuite.nl',
        'API docs':    'https://wetsuite.knobs-dials.com/apidocs/',
        'Source code': 'https://github.com/WetSuiteLeiden/wetsuite-core.git'
    },

    packages         = [
        'wetsuite.datasets',
        'wetsuite.helpers',
        'wetsuite.datacollect',
        'wetsuite.extras'],
    package_dir      = {"": "src"},
    python_requires  = ">=3",
    install_requires = [
        'lxml',                # BSD
        'bs4',                 # MIT
        'msgpack',             # Apache2
        'requests',            # Apache2
        'python-dateutil',     # Apache2
        'numpy >= 1.11.1',     # BSD
        'matplotlib >= 1.5.1', # BSD
        'ipywidgets',          # BSD
        'spacy',               # MIT
        'spacy_fastlang',      # MIT
        'wordcloud',           # MIT
        'pillow',              # HPND, which is permissive and GPL-compatible
        'PyMuPDF',             # AGPL (or commercial)
        'fasttext-wheel',      # MIT;    the non-wheel name seems to need a linker on windows; either use this or use gensim's implementation?
        # 'gensim',              # LGPL
    ],
    extras_require={
        # TODO: test install of easyOCR and spacy  as CPU-only, to avoid needing and pulling in CUDA
        'cpu':[
            # apparently torch it won't pull in CUDA like this?
            'torch',               # BSD
            'torchvision',         # BSD
            'spacy',               # MIT
            'easyocr',             # Apache2
        ],

        'gpu':[
            'torch',                  # BSD
            'torchvision',            # BSD
            'spacy[cuda-autodetect]', # MIT   and pulls in cupy and depends on CUDA?   replaces a bunch of specific package name depending on a similar list of package extras
            'easyocr',                # Apache2
        ],

        #'spacy-transformers',  # MIT,  draws in a bunch more depdendencies, so optional; could uncomment now that it's in extras

        # CONSIDER: 'all':[ ... ]
    },
)
