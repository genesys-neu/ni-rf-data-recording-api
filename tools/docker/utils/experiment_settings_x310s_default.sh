#/bin/bash
#
# NI RF Data Recording API - Experimental settings utility script for Docker container
#
# Description:
#   This bash script is used to set the default settings used for experiments with NI RF Data Recording API.
#
# Usage: 
#	  bash experiment_settings_x310s_default.sh --device \"interface1:ipaddr1,interface2:ipaddr2,...\" [OPTIONS]"
#
#	  -d | --device: Specify the parameters for each device being initialized
#		  Each device must be initialized by providing the following info:
#		  - interface: name of ethernet interface where the SDR is connected;
#		  - ip address: IP address to be assigned to the Eth port.
#		  Note: The code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;
#		  Example: "bash experiment_settings_x310s_default.sh --device enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1 --probe"
#
#	OPTIONS includes:
#	   -p | --probe - probe devices and print devices info."
#
# Pre-requests: Run within the Docker container after successful build.

doProbe=0
isDevs=0

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

      -p | --probe )
         doProbe=1	# probe devices after activation and print info
      ;;

      -h | --help | * )
         echo "Usage: bash experiment_settings_x310s_default.sh --device \"interface1:ipaddr1,interface2:ipaddr2,...\" [OPTIONS]""
         echo ""
	       echo "Each device must be initialized by providing the following info:"
         echo "  - interface: name of ethernet interface where the SDR is connected;"
         echo "  - ip address: IP address to be assigned to the Eth port. Note: The code assumes the Eth port IP ending in xxx.xxx.xxx.1 and the USRP IP ending in xxx.xxx.xxx.2;"
         echo " Example: \"enp7s0f0:192.168.40.1,enp7s0f1:192.168.50.1,enp7s0f2:192.168.60.1\""
	       echo ""
	       echo "OPTIONS includes:"
         echo "   -p | --probe - probe devices and print devices info."
         exit
      ;;
   esac
   shift
done

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

if [ $doProbe -eq 1 ]
then
    echo "--probe : probing devices.."
    # probe UHD devices and test that there are no errors with the following commands
    addr_node=2
    for dev in $devs
    do
        specs=$(echo $dev | tr ":" "\n")
        spec_arr=($specs)
        usrp_ip=$(echo ${spec_arr[1]} | sed "s/.$/${addr_node}/")  # substitute the number of USRP node in the IP address
        uhd_usrp_probe --args addr=$usrp_ip
    done
fi
