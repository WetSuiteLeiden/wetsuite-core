
Run the source's tests in a docker container,
mainly to test for some "works on the developer's machine but not on a fresh install" issues. 


tl;dr before we write more README:

* get a copy of this `Dockerfile` and `runtest-inside` file  (the code itself gets pulled from github HEAD as part of the build, so you don't need the rest of the code) in the same, otherwise empty directory

*  `docker build . --no-cache -t wetsuite-tests`
    - `--no-cache` helps ensure you don't accidentally use old pulled code when you have run this before. (It does take a bunch longer, there are cleverer ways to still use that cache)
    - `-t wetsuite-tests` gives a name to the image so you can later tell what it is

*  `docker run wetsuite-tests /runtest-inside`

