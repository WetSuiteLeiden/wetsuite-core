FROM phusion/baseimage:jammy-1.0.0

RUN apt-get update
RUN apt-get -y install python3 python3-pip

RUN pip3 install pytest
RUN pip3 install pytest-cov

# would be pulled in anyway, should be removed eventually, currently here for docker-level cacheing during debug
# in particular torch is slow
RUN pip3 install filelock cmake fsspec pyyaml msgpack lxml beautifulsoup4 soupsieve 
RUN pip3 install numpy matplotlib python-dateutil PyMuPDF networkx 
RUN pip3 install wordcloud tqdm
RUN pip3 install pysftp
RUN pip3 install spacy sympy tokenizers 
RUN pip3 install torch>=1.8.0
RUN pip3 install easyocr

RUN echo "change this text to defeat the cache at this point, to ensure the github fetches get the lastest"

# Install the core part as a library (will only include the parts of the repo that setup.py mentions)
# takes a while, mostly in CUDA dependencies
# WARNING: this will get cached 
RUN pip3 install -U https://github.com/WetSuiteLeiden/wetsuite-core/archive/refs/heads/main.zip

# Copy all the source, now mostly for the tests (the rest isn't used)
ADD https://github.com/WetSuiteLeiden/wetsuite-core/archive/refs/heads/main.tar.gz /root/test/
RUN cd /root/test && tar xf main.tar.gz && rm main.tar.gz

ADD runtest-inside /runtest-inside
RUN chmod +x /runtest-inside
