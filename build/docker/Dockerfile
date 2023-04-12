FROM ubuntu:20.04
LABEL MAINTAINER="Mauro Belgiovine <belgiovine.m@northeastern.edu> & Lawson Gu <lawson.gu@ni.com>"
RUN apt update
RUN apt-get install -y software-properties-common

# install python
# To install different version of Python, use the following commands. 
# Note: Building and Installing UHD driver for NI USRP from source requires Minimum Python Version: 3.5.
# Note: Ubuntu 20.04 has been built based on Python 3.8.
# Add the deadsnakes PPA to your system’s sources list:
#RUN add-apt-repository ppa:deadsnakes/ppa
#RUN apt install -y python3.9
#RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1
#RUN update-alternatives --set python /usr/bin/python3.9 
#RUN alias python='/usr/bin/python3.9'

RUN echo "export PYTHONPATH=/usr/local/lib/python3.8/site-packages">>~/.bashrc
RUN /bin/bash -c "source ~/.bashrc" source ~/.bashrc

# install required packages
RUN apt install -y python3-pip
RUN pip3 install pandas sympy numpy scipy

# install building tools and python dependencies for UHD
RUN apt install -y autoconf automake build-essential ccache cmake cpufrequtils doxygen ethtool fort77 g++ gir1.2-gtk-3.0 git gobject-introspection gpsd gpsd-clients inetutils-tools libasound2-dev libboost-all-dev libcomedi-dev libcppunit-dev libfftw3-bin libfftw3-dev libfftw3-doc libfontconfig1-dev libgmp-dev libgps-dev libgsl-dev liblog4cpp5-dev libncurses5 libncurses5-dev libpulse-dev libqt5opengl5-dev libqwt-qt5-dev libsdl1.2-dev libtool libudev-dev libusb-1.0-0 libusb-1.0-0-dev libusb-dev libxi-dev libxrender-dev libzmq3-dev libzmq5 ncurses-bin python3-cheetah python3-click python3-click-plugins python3-click-threading python3-dev python3-docutils python3-gi python3-gi-cairo python3-gps python3-lxml python3-mako python3-numpy python3-numpy-dbg python3-opengl python3-pyqt5 python3-requests python3-scipy python3-setuptools python3-six python3-sphinx python3-yaml python3-zmq python3-ruamel.yaml swig wget

# create a work directory and clone UHD repo
RUN cd $HOME
RUN mkdir workarea
RUN cd workarea
RUN git clone https://github.com/EttusResearch/uhd

# let's build UHD from source (note that with Dockerfile current directory path is not kept in the next commands)
RUN cd uhd && git checkout v4.3.0.0 && cd host && mkdir build && cd build && cmake .. && make && make test && make install

# setup the library references
RUN ldconfig
RUN echo "LD_LIBRARY_PATH=/usr/local/lib">>~/.bashrc
RUN /bin/bash -c "source ~/.bashrc" source ~/.bashrc

# install net-tools (needed to look at the ethernet card configuration)
RUN apt install -y net-tools

# install sigmf and pytest 
RUN pip3 install sigmf pytest

# install python package to read TDMS files
RUN pip3 install npTDMS[hdf,pandas,thermocouple_scaling]

# install python colored output packages
RUN pip3 install colored termcolor

# Install other packages
RUN pip3 install matplotlib
RUN pip3 install python-math
