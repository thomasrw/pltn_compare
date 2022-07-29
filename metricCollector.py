#robert.w.thomas3@gmail.com
#
#crawl a directory for csv files
# - avg select columns
# - compute % VMT Lead | Follow | No Platoon
# - compute discounted fuel usage @ 4% discount for VMT lead or Follow
#
#create a new csv with a row of "averages" for each file crawled

import os
import sys
import csv
from os import path
from io import StringIO


#default for Dir in pycharm: /home/thomasrw/Desktop/metrics/
Dir = sys.argv[1]


#metrics.csv creation text for reference
'''
   
    if not path.exists(log):
        f = open(log, "w")
        f.write('Input, Veh Count,Total Timeloss,Total Fuel Consumption,Mean Timeloss,Mean Fuel Consumption,Mean Route Length,Mean Trip Duration,Mean Waitime,Mean CO,Mean CO2,Mean HC,Mean PMx,Mean NOx, Dist No Platoon, Dist Follow Platoon, Dist Lead Platoon, Dist Catchup Platoon\n')
    else:
        f = open(log, "a")

    f.write(input +','+ str(count) +',' + str(time_loss) +','+ str(fuel) +','+ str(time_loss / count) +','+ str(fuel / count) +','+ str(route_length / count) +','+ str(trip_duration / count) +','+ str(wait_time / count) +','+ str(CO / count) +','+ str(CO2 / count) +','+ str(HC / count) +','+ str(PMx / count) +','+ str(NOx / count) +',' +str(Default_dist + CAV_dist) +',' + str(Platoon_dist) +',' + str(Leader_dist) +',' + str(Platoon_catchup_dist) +'\n')
    f.close()
'''


def crawl(dir="./"):
    '''
    crawl a directory creating csvDict readers

    :param dir: directory to crawl
    :return:
    '''
    for filename in os.listdir(dir):
        with open(os.path.join(dir, filename), 'r') as csvfile: #open read-only
            reader = csv.DictReader(csvfile)
            print(filename)
            routine(reader, filename, str(dir) + '_postprocessed.csv')
            #print(os.path.join(dir, filename) + '_postprocessed')
            csvfile.close()




def averages(target):
    '''
    given a csvDictReader for size_x_metrics.csv  compute averages for selected columns

    #Veh Count
    #Mean Timeloss
    #Mean Fuel Consumption
    #Dist No Platoon
    #Dist Follow Platoon
    #Dist Lead Platoon
    #Dist Catchup Platoon

    :param target: csv file
    :return: csv string with average values for each column in target csv file
    '''

    i = 0
    #Veh Count
    vCount = 0
    #Mean Timeloss
    mTimeloss = 0
    #Mean Fuel Consumption
    mFuel = 0
    #Dist No Platoon
    mDist_No_Pltn = 0
    #Dist Follow Platoon
    mDist_Follow_Pltn = 0
    #Dist Lead Platoon
    mDist_Lead_Pltn = 0
    #Dist Catchup Platoon
    mDist_Catchup_Pltn = 0
    #Mean Route Length
    mRoute_length = 0
    #Mean Trip Duration
    mTrip_duration = 0

    for row in target:
        i += 1
        vCount += float(row[' Veh Count']) # source files have a leading space; oops...
        mTimeloss += float(row['Mean Timeloss'])
        mFuel += float(row['Mean Fuel Consumption'])
        mDist_No_Pltn += float(row[' Dist No Platoon']) # source files have a leading space; oops...
        mDist_Follow_Pltn += float(row[' Dist Follow Platoon']) # source files have a leading space; oops...
        mDist_Lead_Pltn += float(row[' Dist Lead Platoon']) # source files have a leading space; oops...
        mDist_Catchup_Pltn += float(row[' Dist Catchup Platoon']) # source files have a leading space; oops...
        mRoute_length += float(row['Mean Route Length'])
        mTrip_duration += float(row['Mean Trip Duration'])




    #if i > 0:
    print("target is:", target)
    print(i)
    calc = str(vCount/i) + ',' + str(mTimeloss/i) + ',' + str(mFuel/i) + ',' + str(mDist_No_Pltn/i) + ',' + str(mDist_Follow_Pltn/i) + ',' + str(mDist_Lead_Pltn/i) + ',' + str(mDist_Catchup_Pltn/i) + ',' + str(mRoute_length/i) + ',' + str(mTrip_duration/i) + ',' + str((mRoute_length/i)/(mTrip_duration/i))

    #else:
    #    calc = "1,1,1,1,1,1,1"

    print(calc)
    return calc

def vmt(target_row):
    '''
    given a row of platoon status metrics, compute the percent vehicle miles traveled (VMT) based on platoon status
    for the categories: lead, follow, and no_platoon

    :param target_row: csv string of platoon status values
    :return: csv string with %VMT categories for lead, follow, and no_platoon
    '''

    target = target_row.split(",")
    #considering catchup mode as in platoon follow
    d = 0
    for entry in target[3:len(target)]:
        d += float(entry)

    # % no platoon
    np = float(target[3]) / d

    # % follow
    follow = (float(target[4]) + float(target[6])) / d

    # % lead
    l = float(target[5]) / d

    # % catchup
    c = float(target[6]) / d




    calc = str(l) + ',' + str(follow) + ',' + str(np) + ',' + str(c)
    print(calc)
    #%VMT Lead, %VMT Follow, %VMT No Platoon
    return calc

def discount(target_row, discount=4):
    '''
    using vmt category percentages, compute a discounted fuel usage value based on platoon activity

    :param target_row: csv string of averages() and vmt() outputs
    :param discount: float discount value to apply to fuel usage while in a platoon status
    :return: string value forf loat fuel metric with platoon VMT discounted by 'discount' percentage (default 4%)
    '''

    target = target_row.split(",")
    #mFuel is target[2]
    #platoon status is target[7] + target[8]
    #no platoon is target[9]

    disc = (100 - float(discount)) / 100 #0.96 for default value
    discount_fuel = (float(target[2]) * float(target[12]) * 1) + (float(target[2]) * (1 - float(target[12])) * disc )

    print(target)

    print(float(target[10]))
    print(float(target[11]))
    print(float(target[12]))
    print(target[2], discount_fuel)






    return str(discount_fuel)




def routine(reader, input, log="./log"):
    '''
    composition of other functions, writes final result to log file
    :param reader: csvDict reader generated by crawl()
    :return:
    '''

    logfile = log
    print(logfile)

    stage1 = "" #store for averages of existing metrics of interest
    stage2 = "" #store for VMT % computations
    stage3 = "" #store for discounted fuel computation

    stage1 = averages(reader)
    stage2 = stage1 + ',' + vmt(stage1)
    stage3 = stage2 + ',' + discount(stage2) + '\n'

    consolidated = input + ',' + stage3
    print(stage3)

    if not path.exists(logfile):
        f = open(logfile, "w")
        ##stage 1
        #vCount += float(row[' Veh Count'])  # source files have a leading space; oops...
        #mTimeloss += float(row['Mean Timeloss'])
        #mFuel += float(row['Mean Fuel Consumption'])
        #mDist_No_Pltn += float(row[' Dist No Platoon'])  # source files have a leading space; oops...
        #mDist_Follow_Pltn += float(row[' Dist Follow Platoon'])  # source files have a leading space; oops...
        #mDist_Lead_Pltn += float(row[' Dist Lead Platoon'])  # source files have a leading space; oops...
        #mDist_Catchup_Pltn += float(row[' Dist Catchup Platoon'])  # source files have a leading space; oops...
        ##stage 2
        #%VMT Lead
        #%VMT Follow
        #%VMT No Platoon
        ##stage 3
        #discount fuel


        f.write('input,vCount,mTimeloss,mFuel,mDist_no_pltn,mdist_follow_pltn,mdist_lead_pltn,mdist_catchup_pltn,mRoute_length,mTrip_duration,AvgSpeed,%VMT lead,%VMT follow,%VMT no platoon,%VMT catchup,discount fuel\n')
    else:
        f = open(logfile, "a")

    f.write(consolidated)
    print(logfile)
    f.close()








crawl(Dir)