FROM phusion/baseimage:jammy-1.0.0

RUN apt-get update
RUN apt-get -y install python3 python3-pip

RUN pip3 install pytest
RUN pip3 install pytest-cov

# would be pulled in anyway, should be removed eventually, currently here for docker-level cacheing during debug
# in particular torch is likely to be slow
RUN pip3 install numpy matplotlib python-dateutil
RUN pip3 install networkx spacy sympy filelock pyyaml cmake fsspec tokenizers tqdm
RUN pip3 install wordcloud
RUN pip3 install torch>=1.8.0
RUN pip3 install easyocr

# Install the core part as a library (will only include the parts of the repo that setup.py mentions)
# takes a while, mostly in CUDA dependencies
# --quiet
RUN pip3 install -U https://github.com/WetSuiteLeiden/wetsuite-core/archive/refs/heads/main.zip

# Copy all the source -- mostly for the 
ADD https://github.com/WetSuiteLeiden/wetsuite-core/archive/refs/heads/main.tar.gz /root/test/
RUN cd /root/test && tar xf main.tar.gz && rm main.tar.gz

ADD runtest-inside /runtest-inside
RUN chmod +x /runtest-inside
