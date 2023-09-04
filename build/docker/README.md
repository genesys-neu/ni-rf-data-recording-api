# Install Dependencies and Run the API using Docker
## Build Docker Image
Use the following command to build the Docker Container with all the necessary dependencies to run the RF Data Recording API (NOTE: Building UHD from source code will take some time):

**Windows PowerShell**
```powershell
cd ni-rf-data-recording-api/build/docker
docker build -t user/ni-rf-data-recorder-api .
```
**Unix**
```bash
cd ni-rf-data-recording-api/build/docker
sudo docker build -t user/ni-rf-data-recorder-api .
```
## Launch Docker Container
Start docker container with all necessary flags:
* `--network host` : Allow access to the physical network interfaces
* `--privileged` : Allow to escalate user privileges
* `-v <host-dir>:<vm-dir>` : Add the necessary volume mappings from host to virtual machine.

Note that in order to mount a host directory into the volume, it is necessary to provide the absolute path to the `-v` argument. We can run the following commands from the repository root folder to run the container and give it access to the utility script folder mounted under `/utils` and the API source code under `/src`:
- First, switch to the repository root folder: 
```
cd ../../
```
- Then, run the docker container:

**Windows PowerShell**
```powershell
set RFDATAFACTORYPATH=pwd
docker run -ti --rm --network host --privileged -v $RFDATAFACTORYPATH/build/docker/utils:/utils -v $RFDATAFACTORYPATH/src:/src user/ni-rf-data-recorder-api
```
**Unix**
```bash
RFDATAFACTORYPATH=`pwd`
sudo docker run -ti --rm --network host --privileged -v $RFDATAFACTORYPATH/build/docker/utils:/utils -v $RFDATAFACTORYPATH/src:/src user/ni-rf-data-recorder-api
```
Note: If you exit the docker container, you need to switch to the repository root folder, i.e. ni-rf-data-recording-api, to run the container. 

## Change the USRP's IP address
You may need to change the USRP's IP address for several reasons:
- to satisfy your particular network configuration,
- to use multiple USRP-X Series devices on the same host computer,
- to set a known IP address into USRP (in case you forgot).

To change the USRP's IP address, you must know the current address of the USRP. You can setup the network properly using the [`utils/experiment_settings_x310s_default.sh`] described below. To change the USRP's IP, please look to Section "Change the USRP's IP address" in [Getting Started Guide](../../docs/Getting_Started_Guide_of_NI_RF_Data_Recording_API.pdf).

## Setup Network and Update UHD FPGA Images of SDR Devices
Once logged in to the container, turn on the devices if they are not yet on. To update UHD FPGA images and assign the IP address to each interface connected to USRP device that are intended to be operated during the experiments, you need to do the following:
- Navigate to `/utils` within the container and launch the provided shell script [`utils/setup_x310s_default.sh`](utils/setup_x310s_default.sh) to initialize all the available devices by providing the necessary details. Usage of this script is described here:
```
Usage: bash setup_x310s_default.sh --device "interface1:ipaddr1[:uhd_fpga_image1],interface2:ipaddr2[:uhd_fpga_image2],..." [OPTIONS]

Each device must be initialized by providing the following info:
  - interface: name of Ethernet interface where the SDR is connected;
  - ip address: IP address to be assigned to the Ethernet port. Note: The code assumes the Etherent port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;
  - uhd_fpga_image: type of UHD image to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled.
 Example: "enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1"

OPTIONS includes:
   -i | --image_dl - download the FPGA images compatible with current UHD driver. Use in case of image version mismatch error.
```
**IMPORTANT: If the `-i | --image_dl` option is used to update UHD FPGA image, the USRP needs to be POWERED OFF and then POWERED ON again to use the new FPGA.**

After all devices have been initialized, the environment settings for the experiments can be set with the script [`utils/experiment_settings_x310s_default.sh`](utils/experiment_settings_x310s_default.sh). Usage of this script is similar to the previous one and is described here:
```
Usage: bash experiment_settings_x310s_default.sh --device "interface1:ipaddr1,interface2:ipaddr2,..." [OPTIONS]

Each device must be initialized by providing the following info:
  - interface: name of ethernet interface where the SDR is connected;
  - ip address: IP address to be assigned to the Eth port. Note: The code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;
 Example: "enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1"

OPTIONS includes:
   -p | --probe - probe devices and print devices info.
```

This command will also take care of expanding the network buffer size and set the MTU size of all Eth ports connected to USRPs to get maximum sampling rate. Using the option `-p | --probe` will also output detailed informations for the initialized devices.

## Access RF Data Recording API Source Code
Finally, you can run the main RF recording script or reference the API source code from the directory `/src`. For more details on how to run the code, please refer to the main [README](../../README.md).

## For Not Successful Build 
If the build is not successful due to any reason, follow the [Getting Started Guide](../../docs/Getting_Started_Guide_of_NI_RF_Data_Recording_API.pdf) to build and install UHD python API manually.
