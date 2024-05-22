
Run the source (pulled from github HEAD) in a docker container,
mainly to test for some "works on the developer's machine but not yours" issues. 


tl;dr before we write more README:

* get a copy of this `Dockerfile` and `runtest-inside`  (the code itself gets pulled from github as part of the build, so you don't need the rest of the code)

*  `docker build .  -t wetsuite-tests`

*  `docker run wetsuite-tests /runtest-inside`
