#/bin/bash
#
# NI RF Data Recording API - Device setup utility script for Docker container
#
# Description:
#   This bash script is used to initialize one or more TX/RX SDR devices to be utilized with NI RF Data Recording API.
#
#  Usage: 
#	bash setup_x310s_default.sh --device \"interface1:ipaddr1[:uhd_fpga_image1],interface2:ipaddr2[:uhd_fpga_image2],...\" [OPTIONS]"
#
#	--device: Specify the parameters for each device being initialized
#		Each device must be initialized by providing the following info:
#		- interface: name of ethernet interface where the SDR is connected;
#		- ip address: IP address to be assigned to the Eth port.
#		Note: The code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;
# 		- uhd_fpga_image: type of UHD image to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled.
#		Example: "bash setup_x310s_default.sh --device enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1"
#
#	OPTIONS includes:
#	   -i | --image_dl - download the FPGA images that are compatible with the current UHD driver. Use in case of image version mismatch error."
#
# Pre-requests: Run within the Docker container after successful build.
#

doImgDL=0
isDevs=0

# IPv4_regex="((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}" 
# Note: The following regex doesn't verify that the numbers in the IPv4 address are within 0-255, but restricts it up to 3 digits
IPv4_regex="[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" 
dev_format_regex="([a-z0-9]+):${IPv4_regex}(:[A-Z][A-Z])?"

# while loop used to parse each argument
while [[ "$1" != "" ]];
do
   case $1 in
      
      -d | --device ) 
         # read the list of devices' parameters
	 if ! [[ "$2" != "" ]]
         then
             echo "ERROR: no device specification provided, at least one required."
	     echo "Run \"bash setup_x310s_default.sh --help\" for command usage."
	     exit
         fi
	 isDevs=1
	 devs=$(echo $2 | tr "," "\n")
         echo $devs
         for dev in $devs
         do
	    if ! [[ $dev =~ $dev_format_regex ]]
            then
	        echo "ERROR: Device info in wrong format --> $dev"
		echo "Run \"bash setup_x310s_default.sh --help\" for command usage."
	        exit
	    fi
         done
	 

	 shift 		# Skip the value of this flag and shift to the next argument flag
      ;;

      -i | --image_dl )
         doImgDL=1	# trigger FPGA driver image download
      ;;

      -h | --help | * )
         echo "Usage: bash setup_x310s_default.sh --device \"interface1:ipaddr1[:uhd_fpga_image1],interface2:ipaddr2[:uhd_fpga_image2],...\" [OPTIONS]"
         echo ""
	 echo "Each device must be initialized by providing the following info:"
         echo "  - interface: name of ethernet interface where the SDR is connected;"
         echo "  - ip address: IP address to be assigned to the Eth port. Note: The code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;"
         echo "  - uhd_fpga_image: type of UHD image to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled."
         echo " Example: \"enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1\""
	 echo ""
	 echo "OPTIONS includes:"
         echo "   -i | --image_dl - download the FPGA images compatible with current UHD driver. Use in case of image version mismatch error."
	 exit
      ;;
   esac
   shift
done

if [[ $isDevs -eq 0 ]]	# check if device parameters have been setup
then
    echo "ERROR: -d | --device option not specified. Run \"bash setup_x310s_default.sh --help\" for command usage."
    exit
fi

# assign static IPs to Ethernet interfaces to use the USRPs
# NOTE: Usually the USRP IP ends with xxx.xxx.xxx.2 and on the host we should configure the Ethernet port using the same address but ending with xxx.xxx.xxx.1
# EXAMPLE
# device 1
# ifconfig enp7s0f0 192.168.40.1
# device 2
# ifconfig enp7s0f2 192.168.50.1
# device 3
# ifconfig enp7s0f3 192.168.60.1

echo "Configuring device IPv4..."
for dev in $devs
do
    specs=$(echo $dev | tr ":" "\n")
    spec_arr=($specs)
    echo "ifconfig ${spec_arr[0]} ${spec_arr[1]}"
    ifconfig ${spec_arr[0]} ${spec_arr[1]}
done

# display initialized UHD devices
# USRP IP: xxx.xxx.xxx.2
addr_node=2
for dev in $devs
do
    specs=$(echo $dev | tr ":" "\n")
    spec_arr=($specs)
num_spec=${#spec_arr[@]}
usrp_ip=$(echo ${spec_arr[1]} | sed "s/.$/${addr_node}/") # setup ip xxx.xxx.xxx.2

echo "uhd_find_devices --args=\"type=x300,addr=${usrp_ip}\""
    uhd_find_devices --args="type=x300,addr=${usrp_ip}"
done

# NOTE: The following steps need to be executed only when we need to update the firmware on the SDRs
# To download the FPGA images compatible with the current UHD driver on the system
if [ $doImgDL -eq 1 ]
then
    echo "--image_dl : downloading the new FPGA images.."
    echo "******************************"
    echo "IMPORTANT: After updating the FPGA image, each device needs to be POWERED OFF and POWERED ON again for the new image to be loaded."
    echo "******************************"
    echo "Running image downloader..."
    uhd_images_downloader
    
    echo "Load new FPGA images on each device..."
    # now let's load the new FPGA images on each device in order to be compatible with the driver
    # uhd_image_loader --args="type=x300,addr=192.168.40.2,fpga=HG"
    # uhd_image_loader --args="type=x300,addr=192.168.50.2,fpga=HG"
    # uhd_image_loader --args="type=x300,addr=192.168.60.2,fpga=HG"

    # USRP IP: xxx.xxx.xxx.2
    addr_node=2
    for dev in $devs
    do
        specs=$(echo $dev | tr ":" "\n")
        spec_arr=($specs)
	num_spec=${#spec_arr[@]}
	usrp_ip=$(echo ${spec_arr[1]} | sed "s/.$/${addr_node}/") # setup ip xxx.xxx.xxx.2
	uhd_fpga_image_type="HG"
	if [[ $num_spec -gt 2 ]]
	then
	    uhd_fpga_image_type=${spec_arr[2]}
	fi
	echo "uhd_image_loader --args=\"type=x300,addr=${usrp_ip},fpga=${uhd_fpga_image_type}\""
        uhd_image_loader --args="type=x300,addr=${usrp_ip},fpga=${uhd_fpga_image_type}"	# load the new image on the board
    done
    echo "******************************"
    echo "Please POWER OFF and then POWER ON again for the new FPGA images to be loaded."
    echo "******************************"
fi
