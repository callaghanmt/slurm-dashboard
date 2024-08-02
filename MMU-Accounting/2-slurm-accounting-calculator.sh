#!/bin/bash

#This script calculates the costs a partition has incurred over a provided timespan.

#Setting env variables

#Absolute path to directory to store costs report. Modify accoridngly.
cost_report_dir=/root/SlurmCosts

#How many days in the past to run the report against.
reporting_days=2

#Report currency. Must match whats defined in the slurm-azure-script!
currency="GBP"

#Select the partition to run the report againts. Change partition as required.
target_partition="HB120v3Spot"

#select the SLURM account that the HPC users reside in. Change account as required.
target_account="lr_users"

#select the SLURM accounting cluster. Some HPC clusters have been set up for multiple clusters?
# run sacctmgr list cluster format=cluster%30
target_cluster="lrhpccluster1"

#Create a variable of all the usernames of users in the target account of SLURM.
#Used to generate a per user cost.
user_list=$(sacctmgr --noheader --parsable2 show association where cluster=$target_cluster account=$target_account format=user)

#Start date. Using "date" with format for YYYY-MM-DDTHH:MM:SS.
#go back number of days using "-d - <selected> days"
start_date=$(date +"%Y-%m-%dT00:00:00" -d "-${reporting_days} days")
#End date. Using "date" with format for YYYY-MM-DDTHH:MM:SS.
end_date=$(date +"%Y-%m-%dT00:00:00")
#Timestamp for report
report_timestamp=$(date +"%Y-%m-%d")

#############FUNCTION START##########
#The TRES must be converted back to a cost. It must be converted (divide by 100000000).
#We must also get the cost up to two decimal places.
#The 'scale=2' indicates that we want 2 decimal places to whatever we pipe into 'bc'.
#The 'bc' command is used to invoke a command line calculator.
#A conditional IF statement is used to check if the variable $price is empty.
check_valid_cost() {
        if [ ! -z "${tres_cost}" ]
        then
                echo "scale=2; $tres_cost/100000000" |bc
        else
                #if there is no TRES recorded. it must mean be 0 incured TRES/Cost.
                echo "0"

        fi
}

#############FUNCTION START##########
#The TRES must be converted back to a cost. It must be converted (divide by 100000000).
#We must also get the cost up to two decimal places.
#The 'scale=2' indicates that we want 2 decimal places to whatever we pipe into 'bc'.
#The 'bc' command is used to invoke a command line calculator.
#A conditional IF statement is used to check if the variable $price is empty.
check_user_valid_cost() {
        if [ ! -z "${user_tres_cost}" ]
        then
                echo "scale=2; $user_tres_cost/100000000" |bc
        else
                #if there is no TRES recorded. it must mean be 0 incured TRES/Cost.
                echo "0"

        fi
}


################Script Start#################
#Create the dir to store the report (if it does not already exist)
mkdir -p $cost_report_dir

#***** Calculate TOTAL cost of a partition *****
#Store sreport in a variable and run sreport with parameters specified.
# -p means parsable -n means no headers
# piped into sed and awk to select the correct row where TRES is specified.
tres_cost=$(sreport -p -n --tres=billing job SizesByAccount cluster=$target_cluster partition=$target_partition grouping=10000 start=$start_date end=$end_date | sed 's/|/ /g' | awk '{ print $3 }')

#Convert to currency by invoking a function (depends on what currency was used for the SLURM-Azure-Price script)
total_cost=$(check_valid_cost)

#Store in report directory.
echo "Total Cost between" $start_date "and" $end_date "=" $total_cost $currency > $cost_report_dir/$target_account-$target_partition-costs.$report_timestamp

#***** Calculate per user Cost of a partition *****
#breakline in report for formatting
echo "******************** Per User Breakdown *******************" >> $cost_report_dir/$target_account-$target_partition-costs.$report_timestamp

#start for loop to go through list of all SLURM account users
for user_list in $user_list; do

        #store srepot of a user in a variable with parameters specified.
        # -p means parsable -n means no headers
        # piped into sed and awk to select the correct row where TRES is specified.
        user_tres_cost=$(sreport -p -n --tres=billing job SizesByAccount partition=$target_partition user=$user_list grouping=10000 start=$start_date end=$end_date | sed 's/|/ /g' | awk '{ print $3 }')

        #***ERROR CHECK****
        #check to catch invalid users e.g. not used cluster.
        #for some reason when SREPORT errors out, the variable $user_tres_cost becomes equal to entire partition cost ($ tres_cost)
        # if statment catches this and sets $user_tres_cost to empty.
        if [[ "$user_tres_cost" -eq "$tres_cost" ]]; then
                user_tres_cost=""
        fi
        #***ERROR CHECK END***

        #Convert to currency by invoking a function (depends on what currency was used for the SLURM-Azure-Price script)
        user_total_cost=$(check_user_valid_cost)
        #append to current report.
        echo "User:" $user_list "costs incurred =" $user_total_cost $currency >> $cost_report_dir/$target_account-$target_partition-costs.$report_timestamp
        #sleep script for a second to not overwhelm sreport
        sleep 1
done
