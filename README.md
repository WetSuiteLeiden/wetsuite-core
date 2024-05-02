
# Introduction - What to expect from this project

Wetsuite aims to be a toolset to make it easier for researchers to apply natural language processing and other analysis to legal text,
primarily to Dutch governmental documents (though some of it translates well, and there is some EU data collection).


Other parts of the project provides educational materials to be a gentler introduction to the topic.

This part is focused on providing, data, tools, and other infrastructure, and as such is the more technical part.

It is intended for those not scared of getting in some technical work, yet currently unsure of where to start.


The the gentler intruduction on varied topics lies in the notebooks, and arguably it is also the larger contribution in getting people started.
The code as a library, with [some API documentation here](https://wetsuite.knobs-dials.com/apidocs/), is more for the programmers ready to dive in


As a project, the core is currenty:
- datasets to work on,
- helper functions to ease some common tasks
- notebooks that 
  - introduce data sources
  - demonstrate our added helpers
  - demonstrate some common methods
  - give some examples of "if you had this question, this is how you might go about solving it"

Plans and extras
- our own searchable index of the data in the datasets, and/or a demonstration how to set up your own
- basic web versions of some common tools, e.g. extracting references
- a better trained Named Entity Recognition for more 


## What's in the repository // experiment or install?

Note that this repository is just the shared functionality that other repositories use.

If you are just poking at this to figure out what it does,
please move on to the [wetsuite-notebooks](https://github.com/knobs-dials/wetsuite-notebooks) repository.

You can load those notebooks, and if you do so in google colab each of them should do a "install wetsuite library core".


### Experiment with notebooks

Notebooks stored here are fairly easy to copy to then play around with,
so that you can do some interactive experimentation without having to worry you're editing our code.

See also [some more technical notes on that, in notebook form](notebooks/intro/technical_notebooks.ipynb).

If you want to avoid installation onto your own PCs at first, consider doing such an experiment on [google colab](https://colab.research.google.com/)
(particularly the intro notebooks have a "Open in Colab" link to ease this).
<!--The easiest way to experiment, without installation, is probably notebooks on google colab - go to the [from the `notebook/into` directory](notebooks/intro),
open one that interests you, and click the `Open in colab` that it starts with - this will open that notebook in colabl, and there should be a cell that install the latest wetsuite from this repository.-->

Once you care to use this as a library in more serious projects, consider installing the library onto your own infrastructure.


### Local install

Requirements: python3, and a bunch of libraries that  _should_ all be included via setup.py



For more serious work probably want a workstation/server install.

as of this writing, the shortest is probably a direct-from-github install:
   pip3 install https://github.com/knobs-dials/wetsuite-dev/archive/refs/heads/main.zip
(We will later start submitting to PyPI so that that becomes `pip3 install wetsuite`)


This installs wetsuite, and the various listed dependencies, into the python environment you're calling it from.
Because complex dependencies may clash with other software, 
you may prefer doing that in a sandboxed environment, such as pipenv,
though if you like to work from notebooks, this is more complex to set up.

TODO: write more text until this becomes fairly obvious and copy-pasteable.

#### Side notes: spacy and GPU

(TODO: rewrite)
<!--
Various example code defaults to the CPU variant of spacy so that it functions everywhere.

If you have more than a handful of documents, and a GPU, 
then it becomes interesting to use the GPU for the parts that can use it.


This will requires some fiddling at install time.

For plain spacy (see also its documentation) this comes down to figuring out your environment's CUDA version (on linux see `nvcc -V`), then installing with
  pip install spacy[cuda110]
instead of
  pip install spacy


We try to wrap that dependency in our own naming, so do
  pip install wetsuite[spacy-cuda110]
instead of
  pip install wetsuite

TODO: see if/when we can rely on [cuda-autodetect](https://spacy.io/usage) instead.
-->


## some overview of this source

### datasets

Lets you load readymade, provided datasets.


This should be a simple way to get started - whenever data we happen to have made
suits your purposes - datasets can always be more detailed...

Getting started should be as simple:
```
mymodel = dataset.load( 'mymodel' ) # downloads to your home directory the first time
print( mymodel.description )        # should explain how to use that data.
```

TODO: have some URL or document provide an up-to-date summary of current datasets


Currently all datasets are considered preliminary, in the sense that 
- they are unpolished, and may contain errors
  - currently they are there more for "here is a bulk of text to throw at a method or training", not to be a complete set of data


- we have not decided our policies on updating datasets (which would be good to do for expectation management)
  - think about having stable datasets, for things like benchmarking
    maybe "any dataset that has a date is fixed, any other may be updated over time" ?

- we have not decided the data format
  - currently we try to not flatten structured data too much, so is often quite nested
    Data is JSON, intended to be loaded into python objects.
  - think about having simpler datasets, a just_text() per dataset, and/or .txt downloads and such,
    because some people just want plain text to feed to programs





### datacollect

If you need a combination of data that isn't served by an existing dataset,
or more up-to-date than is provided, then you may find code and tools to create, update, and polish a dataset yourself.

Ideally you shouldn't need this, and due warning: this is more manual work, 
and note that it can take a while to fetch all data.

You might try asking us to publish dataset updates.




### extras
Contains things that are not considered core functionality,
that we do not necessarily support,
but may nonetheless be interesting to someone.

This includes 
- playthings like wordcloud
- wrappers around external packages (e.g. ocr, pdf) that ought to make them easier to use





# broad package overview

### datasets

This should be a simple way to get started with readymade datasets we happen to have made,
which ought to be as simple as:
```
mymodel = dataset.load( 'mymodel' ) # downloads to your home directory the first time
print( mymodel.description )
```


Currently all datasets are considered preliminary, in the sense that they are 
- unpolished and may contain errors
- we have not decided our policies on updating datasets
  - think about having stable datasets, for things like benchmarking
    maybe "any dataset that has a date is fixed, any other may be updated over time" ?

- we have not decided the data format
  - currently we try to not flatten structured data too much, so is often quite nested
    Data is JSON, intended to be loaded into python objects.
  - think about having simpler datasets, a just_text() per dataset, and/or .txt downloads and such,
    because some people just want plain text to feed to programs

- option: store the approximate timeframe a dataset represents


TODO: 
- have some URL or document provide an up-to-date summary of current datasets

- figure out conventions / expectations about provided datasets
    - but no guarantees, particularly while we are deciding what should go into each dataset
  - datasets without a date may be updated over time (but no guarantees how often)
  - we will try to include some -small variants

- figure out hosting of datasets

- figure out whether a dataset should contain code.
  More convenient, but not good security practice. It's probably better to keep that in this repo.

---

Varied datasets are currently there to be a bulk of text e.g. to refine training - and not to be a complete set of data

As such, many have been simplified somewhat . Look in the datacollect directory 


Some datasets aren't linguistic at all, and were made in part because of the types of combination - it's useful to have varied data accessible in one place so you can more easily combine it.


---

There are some pieces of data that are not linguistic yet are useful for specific tasks. 

For example, `gemeente`, which is some metadata per municipality, was useful just for the names, to search beleidsregels per municipality. 
It may also be useful for relations to Provices and Waterschappen, though that could be more structured.
It may also be interesting to link towards CBS areas.




### datacollect
Code mainly used to create aforementioned datasets. 

If you need a combination of data that isn't served by an existing dataset,
or a more up to date set, then you may find code and tools to create, update, and polish a dataset yourself.

Due warning: this is more manual work, 
and does not work out of the box due to requiring a database to cache fetched data.

You might try asking us to publish dataset updates.


### pdf
Deals with extracting text from PDFs, so mostly an extension of datacollect.


### extras
Contains things that are not considered core functionality,
that we do not necessarily support,
but may nonetheless be interesting to someone.

This includes playthings (e.g. wordcloud),
things that are thin wrappers around external packages (e.g. ocr).




# extras 

Code that is not considered core functionality, and may not be guaranteed to work, or supported per se, but which you may find use for nonetheless, particularly in the copy-paste department.


## pdf_text 

Helps extract text that PDFs themselves report having.
Actually a thin layer around [poppler](https://poppler.freedesktop.org/), which you could use directly yourself.

If a PDF actually contains scanned images, you would move on to:

## ocr 

Mostly wraps existing OCR packages (currently just [EasyOCR](https://github.com/JaidedAI/EasyOCR)) 
and tries to you help you extract text.

See [datacollect_ocr.ipynb](../../../notebooks/examples/datacollect_ocr.ipynb) for some basic use examples.


## spacy_server

This loads spacy and provides a basic "give me text, here is its parse" service served via HTTP.

This is mostly about the overhead of loading spacy and its models. 
In batch use incurring it once at the stat is fine,
and something similar goes for notebooks,
but when you're in the shell you might want to parse a sentence and not wait for a minute for a model to load (`spacyserver-client` in [clitools/](../clitools/) is the counterpart to use from there).
You _could_ also have this (in)directly public-facing, though note that this scales poorly, less so if you are using GPU.

Not considered part of regular use, because 
  - it's extra dependencies,
  - it returns the parse in a non-standard way, cherry-picking things some to put in JSON
  ...it's nice to have for web interfaces, though, because it can give answers within ~20ms.



# command line tools

A lot of examples and copy-pasteable fragments currently exist in code form in notebooks,
and loads from structured storage.

...but if you prefer to export things to files and work on files and run tools from the command line,
here is a start at exposing some of the useful functionality in single CLI tools.

You might want to add this directory to your PATH, to be able to use them anywhere.



## pdf-count-pages-with-text

Counts ghow many pages in a PDF file have nontrivial amounts of text,
to guess whether it 

```bash
$ pdf-count-pages-with-text test.pdf
  20 pages,   35% with nontrivial text    'test.pdf'
```


## xml-text

Prints out the contents of text nodes, completely unaware of what might be metadata.

```bash
$ ./xml-text test.xml
[output cut for brevity]
Les procès-verbaux contre les contrevenans seront affirmés dans les formes et délais prescrits par les lois.
Ils seront adressés en originaux à nos procureurs impériaux, qui seront tenus de poursuivre d'office les contrevenans devant les tribunaux de police correctionnelle, ainsi qu'il est réglé et usité pour les délits forestiers, et sans préjudice des dommages-intérêts des parties.
Les peines seront d'une amende de cinq cents fr. au plus et de cent francs au moins, double en cas de récidive, et d'une détention qui ne pourra excéder la durée fixée par le Code de police correctionnelle.
Collationné à l'original, par nous président et secrétaires du Corps législatif. Paris, le 21 Avril 1810. Signé le comte de Montesquiou, président; Puymaurin, Debosque, Plasschaert, Grellet, secrétaires.
Mandons et ordonnons que les présentes, revêtues des sceaux de L'États insérées au Bulletin des lois, soient adressées aux Cours, aux Tribunaux et aux autorités administratives, pour qu'ils les inscrivent dans leurs registres, les observent et les fassent observer; et notre Grand-Juge Ministre de la justice est chargé d'en surveiller la publication.
```


## xml-color

Show colored XML in the shell, optionally with namespaces stripped,
to try to figure out structure of unseen XML documents with less staring. 

(and avoiding some external tools/dependencies, e.g. xmllint plus pygmentize)

Slightly custom for this project, in that there are some namespaces baked in,
Focused on pretty printing to the point its output is not actually valid XML anymore


## xml-path-statistics

```bash 
$ ./xml-path-statistics -u wetgeving/wet-besluit/wettekst test.xml
[output cut for brevity]
    72   wettekst/titeldeel/paragraaf/artikel/kop/label
    72   wettekst/titeldeel/paragraaf/artikel/kop
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/publicatiejaar
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/publicatienr
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie/ondertekeningsdatum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk/publicatie
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/oorspronkelijk
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/publicatiejaar
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/publicatienr
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie/ondertekeningsdatum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/publicatie
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding/inwerkingtreding.datum
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata/inwerkingtreding
    72   wettekst/titeldeel/paragraaf/artikel/meta-data/brondata
    72   wettekst/titeldeel/paragraaf/artikel/meta-data
    72   wettekst/titeldeel/paragraaf/artikel
    79   wettekst/titeldeel/paragraaf/artikel/al
   122   wettekst/titeldeel/paragraaf/artikel/meta-data/jcis/jci

```
