# Install Dependencies and Run the API using Docker
## Build Docker Image
Use the following command to build the Docker Container with all the necessary dependencies to run the RF Data Recording API (NOTE: Building UHD from source code will take some time):
```
cd ni-rf-data-recording-api/tools/docker
sudo docker build -t user/ni-rf-data-recorder-api .
```
## Launch Docker Container
Start docker container with all necessary flags:
* `--network host` : Allow access to the physical network interfaces
* `--privileged` : Allow to escalate user privileges
* `-v <host-dir>:<vm-dir>` : Add the necessary volume mappings from host to virtual machine.

Note that in order to mount a host directory into the volume, it is necessary to provide the absolute path to the `-v` argument. We can run the following commands from the repository root folder to run the container and give it access to the utility script folder mounted under `/utils` and the API source code under `/src`:
```
cd ../../
RFDATAFACTORYPATH=`pwd`
sudo docker run -ti --rm --network host --privileged -v $RFDATAFACTORYPATH/tools/docker/utils:/utils -v $RFDATAFACTORYPATH/src:/src user/ni-rf-data-recorder-api
```

## Setup SDR Devices
Once logged in to the container, turn on the devices and assign the IP address to each USRP device that are intended to be operated during the experiments. To do so, navigate to `/utils` within the container and launch the provided shell script [`utils/setup_x310s_default.sh`](utils/setup_x310s_default.sh) to initialize all the available devices by providing the necessary details. Usage of this script is described here:
```
Usage: bash setup_x310s_default.sh --device "interface1:ipaddr1[:uhd_fpga_image],interface2:ipaddr2[:uhd_fpga_image],..." [OPTIONS]

Each device must be initialized by providing the following info:
  - interface: name of ethernet interface where the SDR is connected;
  - ip address: IP address to be assigned to the Eth port. Note that this code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;
  - uhd_fpga_image: type of UHD image to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled.
 Example: "bash setup_x310s_default.sh --device enp3s0:192.168.50.1,enp5s0:192.168.60.1,enp10s0f1:192.168.40.1 --probe"

OPTIONS includes:
   -i | --image_dl - download the FPGA images compatible with current UHD driver. Use in case of image version mismatch error.
   -p | --probe - probe devices and print devices info.
```
This command will also take care of expanding the network buffer size and set the MTU size of all Eth ports connected to USRPs to get maximum sampling rate.

## Access RF Data Recording API Source Code
Finally, you can run the main RF recording script or reference the API source code from the directory `/src`. For more details on how to run the code, please refer to the main [README](../../README.md).

## Not Successful Build 
If the build is not successful due to any reason, follow the [Getting Started Guide](../../docs/Getting_Started_Guide_of_NI_RF_Data_Recording_API.pdf) to build and install UHD python API manually.
