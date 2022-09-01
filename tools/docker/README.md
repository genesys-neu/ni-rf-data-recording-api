# Install dependencies using Docker
## Build Docker image
Use the following command to build the docker container 
sudo docker build -t mauro/ni-api-rf-datarecorder .

## start docker container with all the necessary flags
 --network host : this will allow to access the physical network interfaces
 --privileged : this will allow to escalate user privileges
 -v /home/mauro/Research/NI_RF_Data_Recording_API/utils:~/utils
sudo docker run -ti --rm --network host --privileged -v /home/ni_demo/Research/NI_RF_Data_Recording_API/utils:/utils mauro/ni-api-rf-datarecorder

# setup devices
 after running the container, turn on the devices and run the following command in order to assign the IP to the USRP devices
sh utils/setup_x310s_default.sh
