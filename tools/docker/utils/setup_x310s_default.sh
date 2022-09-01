#/bin/bash

doImgDL=0
doProbe=0
isDevs=0

#IPv4_regex="((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"  
IPv4_regex="[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" # note: this regex doesn't verify that the number in the IPv4 address are within 0-255, but restricts it up to 3 digits
dev_format_regex="([a-z0-9]+):${IPv4_regex}(:[A-Z][A-Z])?"


while [[ "$1" != "" ]];
do
   case $1 in
      
      -d | --device )
	 if ! [[ "$2" != "" ]]
         then
             echo "ERROR: no device specification provided, at least one reqired."
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
	        echo "ERROR: device info in wrong format --> $dev"
		echo "Run \"bash setup_x310s_default.sh --help\" for command usage."
	        exit
	    fi
         done
	 

	 shift 		# skip the value of this flag and shift to the next argument flag
      ;;

      -i | --image_dl )
         doImgDL=1
      ;;

      -p | --probe )
	 doProbe=1
      ;;

      -h | --help | * )
         echo "Usage: bash setup_x310s_default.sh --device \"interface1:ipaddr1[:driver1],interface2:ipaddr2[:driver2],...\" [OPTIONS]"
         echo ""
	 echo "Each device must be initialized by providing the following info:"
         echo "  - interface: name of ethernet interface where the SDR is connected;"
         echo "  - ip address: IP address to be assigned to the eth port. Note that this code assumes eth port ip ending in xxx.xxx.xxx.1 and the daughterboard ip ending in xxx.xxx.xxx.2;"
         echo "  - driver: type of driver to be installed to FPGA (default is HG). This value is only required with --image_dl option enabled."
         echo " Example: \"enp3s0:192.168.50.1,enp5s0:192.168.60.1,enp10s0f1:192.168.40.1\""
	 echo ""
	 echo "OPTIONS includes:"
         echo "   -i | --image_dl - download the FPGA images compatible with current UHD driver. Use in case of image version mismatch error."
         echo "   -p | --probe - probe devices and print devices info."
	 exit
      ;;
   esac
   shift
done

if [[ $isDevs -eq 0 ]]
then
    echo "ERROR: -d | --device option not specified. Run \"bash setup_x310s_default.sh --help\" for command usage."
    exit
fi

# assign static IPs based on the one assigned to the daughterboards on the USRPs
# NOTE: usually the daughterboard ends with xxx.xxx.xxx.2 and on the host we should configure the ethernet port using the same address but ending with xxx.xxx.xxx.1
echo "Configuring device IPv4..."
for dev in $devs
do
    specs=$(echo $dev | tr ":" "\n")
    spec_arr=($specs)
    echo "ifconfig ${spec_arr[0]} ${spec_arr[1]}"
    ifconfig ${spec_arr[0]} ${spec_arr[1]}
done

# EXAMPLE
# device 1
# ifconfig enp3s0 192.168.50.1
# device 2
# ifconfig enp5s0 192.168.60.1
# RX ONLY
# ifconfig enp10s0f1 192.168.40.1


# this command should show the two devices now
uhd_find_devices

# NOTE: the following steps need to be executed only when we need to update the firmware on the SDRs
# let's download the FPGA images compatible with the current UHD driver
if [ $doImgDL -eq 1 ]
then
    echo "--image_dl : downloading the new FPGA images.."
    echo "******************************"
    echo "IMPORTANT: after updating the FPGA image, each device needs to be POWERED OFF and POWERED ON again for the new image to be loaded."
    echo "******************************"
    uhd_images_downloader

    # now let's load the new FPGA images on each device in order to be compatible with the driver
    # uhd_image_loader --args="type=x300,addr=192.168.60.2,fpga=HG"
    # uhd_image_loader --args="type=x300,addr=192.168.50.2,fpga=HG"
    # uhd_image_loader --args="type=x300,addr=192.168.40.2,fpga=HG"

    # daughter board ip: xxx.xxx.xxx.2
    addr_node=2
    for dev in $devs
    do
        specs=$(echo $dev | tr ":" "\n")
        spec_arr=($specs)
	num_spec=${#spec_arr[@]}
	db_ip=$(echo ${spec_arr[1]} | sed "s/.$/${addr_node}/")		# substitute the number of daughterboard node in the IP address
	driver_type="HG"
	if [[ $num_spec -gt 2 ]]
	then
	    driver_type=${spec_arr[2]}
	fi
        uhd_image_loader --args="type=x300,addr=${db_ip},fpga=${driver_type}"
    done
fi

if [ $doProbe -eq 1 ]
then
    echo "--probe : probing devices.."
    
    # after the power cycle, we can probe the devices and test that there are no errors with the following commands
    addr_node=2
    for dev in $devs
    do
        specs=$(echo $dev | tr ":" "\n")
        spec_arr=($specs)
        db_ip=$(echo ${spec_arr[1]} | sed "s/.$/${addr_node}/")         # substitute the number of daughterboard node in the IP address
        uhd_usrp_probe --args addr=$db_ip
    done
fi

# resize the buffer to be more efficient. Use max buffer size provided by the system
sysctl -w net.core.rmem_max=24912805
sysctl -w net.core.wmem_max=24912805

for dev in $devs
do
    specs=$(echo $dev | tr ":" "\n")
    spec_arr=($specs)
    echo "ifconfig ${spec_arr[0]} mtu 9000 up"
    ifconfig ${spec_arr[0]} mtu 9000 up
done
