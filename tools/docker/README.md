# Install dependencies and run the API using Docker
## Build Docker image
Use the following command to build the docker container with all the necessary dependencies to run the RF Data Recording API (NOTE: this will take some time):
```
cd ni-rf-data-recording-api/tools/docker
sudo docker build -t mauro/ni-api-rf-datarecorder .
```
## Launch the container
Start docker container with all the necessary flags:
* `--network host` : allow access the physical network interfaces
* `--privileged` : allow to escalate user privileges
* `-v <host-dir>:<vm-dir>` : add the necessary volume mappings from host to virtual machine.

Note that in order to mount a host directory into the volume, is it necessary to provide the absolute path to the `-v` argument. We can run the following commands from the repository root folder to run the container and give it access to the utility script folder mounted under `/utils` and the API source code under `/src`:
```
cd ../../
RFDATAFACTORYPATH=`pwd`
sudo docker run -ti --rm --network host --privileged -v $RFDATAFACTORYPATH/tools/docker/utils:/utils -v $RFDATAFACTORYPATH/src:/src mauro/ni-api-rf-datarecorder
```

## Setup SDR devices
Once logged in the container, turn on the devices and assign the IP address to each USRP device that are intended to be operated during the experiments. To do so, navigate to `/utils` within the container and launch the provided shell script [`utils/setup_x310s_default.sh`](utils/setup_x310s_default.sh) to initialize all the available devices by providing the necessary details. Usage of this script is described here:
```
Usage: bash setup_x310s_default.sh --device "interface1:ipaddr1[:driver1],interface2:ipaddr2[:driver2],..." [OPTIONS]

Each device must be initialized by providing the following info:
  - interface: name of ethernet interface where the SDR is connected;
  - ip address: IP address to be assigned to the eth port. Note that this code assumes eth port ip ending in xxx.xxx.xxx.1 and the daughterboard ip ending in xxx.xxx.xxx.2;
  - driver: type of driver to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled.
 Example: "bash setup_x310s_default.sh --device enp3s0:192.168.50.1,enp5s0:192.168.60.1,enp10s0f1:192.168.40.1 --probe"

OPTIONS includes:
   -i | --image_dl - download the FPGA images compatible with current UHD driver. Use in case of image version mismatch error.
   -p | --probe - probe devices and print devices info.
```
This command will also take care of expanding the network buffer size and set the MTU size of all Eth ports connected to USRPs to get maximum sampling rate.

## Access the API source code
Finally, we can run the main recording script or reference the API source code from the directory `/src`. For more details on how to run the code, please refer to the main [README](../../README.md) and the [documentation](../../docs/Getting_Started_Guide_of_NI_RF_Data_Recording_API.pdf).
