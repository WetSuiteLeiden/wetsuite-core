
Run the source's tests in a docker container,
mainly to test for some "works on the developer's machine but not on a fresh install" issues. 


tl;dr before we write more README:

* get a copy of this `Dockerfile` and `runtest-inside`  (the code itself gets pulled from github HEAD as part of the build, so you don't need the rest of the code)

*  `docker build .  -t wetsuite-tests`

*  `docker run wetsuite-tests /runtest-inside`
