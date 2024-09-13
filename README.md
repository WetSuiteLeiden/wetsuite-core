
# wetsuite core library

This is part of a wider project with wider aims, [introduced here](https://github.com/WetSuiteLeiden),

That project includes:
- a website that guides you into starting a project
- helper functions to ease some common tasks, such as loading data and processing text
- accessing datasets to work on,
- notebooks that 
  - introduce data sources
  - demonstrate our added helpers
  - demonstrate some common methods
  - give some examples of "if you had this question, this is how you might go about solving it"

This particular repository is only that second item there - the helper functions
that, for the most part, making it easier to get started analysing legal text.


## If you are interesting in using the library
As this code is part of an installable library, 
you do not have to do anything directly with this repository.

The introductory notebooks will explain how, 
so if you are looking around the repositories, 
you may wish to move onto the [wetsuite-notebooks](https://github.com/knobs-dials/wetsuite-notebooks) repository.

There is also a notebook that gets into [how to install this library](https://github.com/WetSuiteLeiden/example-notebooks/blob/main/library_install_instructions.ipynb).


## If you are interesting in specific code inside `src`



### `datasets/`
Perhaps most interesting is the `datasets.load()` function that downloads our pre-made datasets.

If these prove to not be _quite_ what you wanted,
look to the [datacollect repository](https://github.com/WetSuiteLeiden/data-collection) to start collecting your own.


### `helpers/`
A collection of helper functiont to deal with 
text and pattern recognition, text parsing, 
XML data loading an manipulation, dates, local storage,

For the most part, it is all the things that we needed
to suppor all the examples in the [example notebooks repository](https://github.com/WetSuiteLeiden/example-notebooks).



### `extras/`
Arguably part of helpers, but set apart to note that code is
_not_ considered core functionality,
not necessarily supported by us,
that may be messy by nature, 
but may nonetheless be interesting to someone.

This includes 
- playthings like wordcloud
- wrappers around external packages (e.g. ocr, pdf) that ought to make them easier to use


### `datacollect/`
For the most part, this is code we needed to support our dataset collection,
which is mostly public in [the data collection notebooks repository](https://github.com/WetSuiteLeiden/data-collection).

Arguably part of helpers, except that little of this is use outside a very specific data source.



