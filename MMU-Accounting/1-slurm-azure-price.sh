#!/bin/bash

##################################################################################
# Copyright © Red Oak Consulting LLP - All Rights Reserved                       #
# Unauthorized copying of this file, via any medium is strictly prohibited       #
# Proprietary and confidential                                                   #
# Written by Manveer Munde and Samiul Haque, April 2024                          #
##################################################################################

# This scripts scrapes the Azure retail prices API to update the pricing of nodes via SLURM TRESBillingWeights.


#Client Specifiic Proxy Settings (Uncomment the next two lines IF REQUIRED)
export https_proxy=http://zscaler.internal.lr.org:443
export http_proxy=http://zscaler.internal.lr.org:80

#Setting env variables

#variable to store absolute path to the directory that stores all the fetched prices. Modify accoridngly.
price_output_dir=/root/AzurePrices

#variable to select currency used by API call. Valid options are 'EUR', 'USD', 'GBP', 'CAD' etc.
currency=GBP

#variable to store path to the dir where  cyclecloud.conf resides. Azure.conf is where TRES is modified.
azure_conf_path=/sched/
#*******************************SKU Specific Variables**********************************
#Identify the unique SKU ID of a Azure VM SKU and store as a variable below.

#HB120rs v3 Series
westeu_hb120rsv3_spot_id='DZH318Z08KCJ/000F'
westeu_hb120rsv3_payandgo_id='DZH318Z08KCJ/0001'

#HC44rs Series
westeu_hc44rs_spot_id='DZH318Z0BXNX/001C'
westeu_hc44rs_payandgo_id='DZH318Z0BXNX/000G'

#Create the dir to store latest Azure Prices (if it does not already exist)
mkdir -p $price_output_dir

#############FUNCTION START##########
#The price is given as per hour. It must be converted to per minute (divide by 60).
#We must also get rid of any decimal points as SLURM accounting cannont handle decimal points (multiplied by 100000000).
#The 'scale=0' indicates that we want 0 decimal places to whatever we pipe into 'bc'.
#The 'bc' command is used to invoke a command line calculator.
#A conditional IF statement is used to check if the variable $price is empty.
#If it is empty, write "ERROR" into the variable.
#Kill the parent shell process "$$" is the PID of the running shell.
check_valid_price() {
        if [ ! -z "${price}" ]
        then
                echo "scale=0; $price*100000000/60" |bc
        else
                echo "ERROR"
                logger "Invalid Price Detected, Check Internet Connection, Aborting Price Refresh"
                kill -9 $$
        fi
}
#############FUNCTION END#############

#Breakline in /var/log/messages (admin purposes)
logger "**********ROMS AZURE PRICE REFRESH SERVICE**********"

#********************************PRICE REFRESH START***************************************
#Get price for VM using curl and custom url (with VM specific SKU ID) and store in a temporary variable.
#Added max-time to curl to prevent script hanging if there is not net connection.
#The 'jq' command selects the 'retailPrice' field from the JSON pulled from azure.
#Please only modify the SKU ID variable in the URL that is curled.
price=$(curl --max-time 5 -s -H Metadata:true https://prices.azure.com/api/retail/prices?currencyCode=%27${currency}\&\$filter=skuId%20eq%20%27${westeu_hb120rsv3_spot_id}%27 | jq '.Items [].retailPrice')

#Logging price per hour to /var/log/messages for admin purposes.
logger "West Europe HB120rs v3 Spot cost per hour: $price $currency"

#set price of SKU. Invoking function to calculate and check valid price.
westeu_hb120rsv3_spot_price=$(check_valid_price)

#Log Price to AzurePrice Dir for Admin Purposes.
echo $(date '+%Y-%m-%d T%T') : TRESBillingWeights = $westeu_hb120rsv3_spot_price Price Per Hour = $price $currency >> ${price_output_dir}/westeu_hb120rsv3_spot_${currency}

#Repeat for other VM SKUS

#********************************Update Azure.conf*************************************

#make a backup of cyclecloud.conf file
cp -a $azure_conf_path/cyclecloud.conf $azure_conf_path/cyclecloud.bak

#Get current SLURMCTL status and store in a variable.
# This command uses a grep to extract the word that comes after "Active:". Here's how it works:
# -o option tells grep to only print the matched part of the line.
# -P enables Perl-compatible regular expressions.
# The pattern (?<=Active: )\w+ uses a positive lookbehind ((?<=Active: )) to assert that "Active: " precedes the word, and \w+ matches one or more word characters (letters, digits, or underscores). This extracts the word after "Active:".
slurmstat=$(systemctl status slurmctld.service | grep -oP '(?<=Active: )\w+')

#check condition to see if slurmctl active.
if [[ "$slurmstat" == "active" ]]; then
        echo "SLURMCTLD ACTIVE, begin changes to cyclecloud.conf"
        #Logging SLURM status and step for admin purposes.
        logger "SLURMCTLD ACTIVE, begin changes to cyclecloud.conf"

        # /PartitionName=<partition name>/ is the pattern to search for.
        # s/ is the substitution command in sed.
        # \(State=up\) captures the pattern "State=up" using parentheses for later reference.
        # .* matches anything after "State=up".
        # \1 in the replacement part refers to the captured pattern "State=up".


        #modifying hb120 v3 spot partition. Change partition according to cluster.
        sed -i "/^PartitionName=HB120v3Spot/s/\(State=UP\).*/\1 TRESBillingWeights=\"Node=$westeu_hb120rsv3_spot_price\"/g" $azure_conf_path/cyclecloud.conf

        #restart SLURMCTLD after changes have been made
        systemctl restart slurmctld

else
        #if slurmctld is not active, exit code 1.
        logger "SLURMCTLD not active, Exiting script, No MODIFICATIONS have been made"
        echo "SLURMCTLD not active, Exiting script, No MODIFICATIONS have been made"
        exit 1
fi

#wait 10 seconds to wait for SLURMCTL to start again
sleep 10

#check status of SLURMCTLD post changes. revert to backup cyclecloud.conf if service status is failed.
slurmstat=$(systemctl status slurmctld.service | grep -oP '(?<=Active: )\w+')

#check condition to see if slurmctl active.
if [[ "$slurmstat" == "active" ]]; then
        echo "SLURMCTLD ACTIVE, price update SUCCESS"
        logger "SLURMCTLD ACTIVE, price update SUCCESS"
        exit 0
else
        #if slurmctld is not active. assume bad cyclecloud.conf file. Revert to backup copy.
        echo "SLURMCTLD not active, price update FAILED"
        logger "SLURMCTLD not active, price update FAILED"
        echo "Reverting to backup cyclecloud.conf"
        logger "Reverting to backup azure.conf"
        mv $azure_conf_path/cyclecloud.bak $azure_conf_path/cyclecloud.conf
        chown slurm:slurm $azure_conf_path/cyclecloud.conf
        chmod 644 $azure_conf_path/cyclecloud.conf
        systemctl restart slurmctld
        exit 1
fi
