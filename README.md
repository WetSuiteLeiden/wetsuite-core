
# wetsuite core library

This is part of a wider project with wider aims, [introduced here](https://github.com/WetSuiteLeiden).


## This is just data and code

The data and this code are only helpers to the wider purpose of 
making it easier for you to get started analysing legal text.

This part is:
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

To install the library that in particular the notebooks rely on,
on colab or a workstation/server install:
   pip install -U wetsuite
Requirements: python3, and a bunch of libraries that  _should_ all be pulled in.

For more notes on installation, see the project's [install instructions](https://github.com/WetSuiteLeiden/example-notebooks/blob/main/getting-started/library_install_instructions.ipynb)

Because complex dependencies may clash with other software, 
you may prefer to experiment within colab, or in your own setup do that within a 
sandboxed environment, such as pipenv, 
though if you like to work from notebooks that is more complex to set up.


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


