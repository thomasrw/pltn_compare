#robert.w.thomas3@gmail.com
#
#Collect aggregate data from tripinfo output from Sumo simulations


from xml.etree import ElementTree
import os.path
from os import path
import sys

#input = '/home/thomasrw/Model/2020-02-20-06-34-27tripinfo' #normal run
#input = '/home/thomasrw/Model/2020-02-20-08-25-07tripinfo' #platoon run

#input = '/home/thomasrw/j/2020-05-31-05-44-43tripinfo' #no look behind
#input = '/home/thomasrw/j/2020-06-01-16-04-02tripinfo' #look behind

#input = '/home/thomasrw/Model/2020-06-22-11-08-57tripinfo' #all platoon
input = '/home/thomasrw/Desktop/CAV100_1_tripinfo' #no platoon
log = '/home/thomasrw/Desktop/CAV100.csv'
platoon = '/home/thomasrw/Desktop/CAV100_1_platoon_status.xml'
baseline = '/home/thomasrw/Desktop/CAV000_1_tripinfo'

#todo rig to eval logs for each run group and produce a single report
#example filename baseline_438_tripinfo
prefix = sys.argv[1] #eg 'baseline'
run = sys.argv[2]
mylog = sys.argv[3]
mysize = sys.argv[4] #need size in log file search
#prefix = "test"
#mypath = '/home/thomasrw/Model/'
mypath = '/work/thoma525/'

def compare(baseline=baseline, input=input):
    basetree = ElementTree.parse(baseline)
    baseroot = basetree.getroot()
    tree = ElementTree.parse(input)
    root = tree.getroot()
    veh = {}
    baselinecount = 0
    ogcount = 0

    for att in baseroot:
        veh[att.attrib['id']] = 0
        baselinecount += 1
    for att in root:
        ogcount += 1



    print('baseline: ' + str(baselinecount))
    print('count: ' + str(ogcount))

    count = 0
    for vehatt in root:
        #print('checking veh')
        id = vehatt.attrib['id']
        core = id
        if id.startswith('coop'):
            core = core[4:]
        elif id.startswith('def'):
            core = core[3:]
        elif id.startswith('tft'):
            core = core[3:]
        elif id.startswith('grud'):
            core = core[4:]
        elif id.startswith('rand'):
            core = core[4:]

        if core in veh.keys():
            print('match')
            count +=1
            if vehatt.attrib['arrival'] == '-1.00':
                print(vehatt.attrib['id'])

        #for att in baseroot:
            #if vehatt.attrib['id'].endswith(att.attrib['id']):
            #if core == att.attrib['id']:
                #veh[att.attrib['id']] = 0
                #print(vehatt.attrib['id'] + ' matched ' + att.attrib['id'])
                #print(core)
                #count += 1
                #print(count)
                #break
    print('compared count: ' + str(count) + ' expected: ' + str(baselinecount))
    print('original input count: ' +str(ogcount))
    #for att in baseroot:
    #    if att.attrib['id'] not in veh:
    #        print(att.attrib['id'])
    #print(len(veh.keys()))
    #for key in veh.keys():
    #    print(key)

#eval only original vehicles that finished in CAV000_x
def eval2(baseline=baseline, input=input, log=log, platoon=platoon):
    '''

    :param baseline: CAV000 trip info
    :param input: CAVxxx trip info for comparison
    :param log: log file where results are written
    :param platoon: platoon status log for trip info file specified with 'input'
    :return:
    '''

    #todo read CAV000 build baseline dict
    basetree = ElementTree.parse(baseline)
    baseroot = basetree.getroot()
    #baseline_veh = {}
    veh = {}
    veh2 = {}

    count = 0  # number of vehicles completing route (unless incomplete trips are being reported)
    time_loss = 0  # time lost in seconds due to travel below individual ideal speeds
    fuel = 0  # total fuel consumption ml
    route_length = 0  # distance traveled
    trip_duration = 0  # time in seconds to reach destination
    wait_time = 0  # time in seconds with speed below 0.1m/s (eg stop & go traffic)
    # emissions from SUMO (also includes fuel)
    CO = 0  # CO emission mg
    CO2 = 0  # CO2 emission mg
    HC = 0  # HC emission mg
    PMx = 0  # PMx emission mg
    NOx = 0  # NOx emission mg

    # Vehicle Miles Traveled variables
    Default_dist = 0  # adds to no platoon
    CAV_dist = 0  # adds to no platoon
    Platoon_dist = 0  # in a platoon as follower (may include catchup to "to-be" leader)
    Leader_dist = 0  # in a platoon as leader
    Platoon_catchup_dist = 0 #in a platoon catchup status (higher speed / acceleration)


    #for att in baseroot:
    #    baseline_veh[att.attrib['id']] = 0
    #todo read input and build input dict based on CAV000 dict match using endswith()
    tree = ElementTree.parse(input)
    root = tree.getroot()
    VMT_iter = ElementTree.iterparse(platoon)

    for att in baseroot:
        veh[att.attrib['id']] = 0
        #baselinecount += 1

    for vehatt in root:

        id = vehatt.attrib['id']
        core = id
        if id.startswith('coop'):
            core = core[4:]
        elif id.startswith('def'):
            core = core[3:]
        elif id.startswith('tft'):
            core = core[3:]
        elif id.startswith('grud'):
            core = core[4:]
        elif id.startswith('rand'):
            core = core[4:]

        if core in veh.keys():
            veh2[vehatt.attrib['id']] = 0
            print('match')
            count += 1
            time_loss += float(vehatt.attrib['timeLoss'])
            fuel += float(vehatt.find('emissions').attrib['fuel_abs'])
            CO += float(vehatt.find('emissions').attrib['CO_abs'])
            CO2 += float(vehatt.find('emissions').attrib['CO2_abs'])
            HC += float(vehatt.find('emissions').attrib['HC_abs'])
            PMx += float(vehatt.find('emissions').attrib['PMx_abs'])
            NOx += float(vehatt.find('emissions').attrib['NOx_abs'])
            route_length += float(vehatt.attrib['routeLength'])
            trip_duration += float(vehatt.attrib['duration'])
            wait_time += float(vehatt.attrib['waitingTime'])
            #break

    '''
                
        print('checking veh')
        for att in baseroot:
            if vehatt.attrib['id'].endswith(att.attrib['id']):
                veh[vehatt.attrib['id']] = 0
                count += 1
                # print(att.tag)
                time_loss += float(vehatt.attrib['timeLoss'])
                fuel += float(vehatt.find('emissions').attrib['fuel_abs'])
                CO += float(vehatt.find('emissions').attrib['CO_abs'])
                CO2 += float(vehatt.find('emissions').attrib['CO2_abs'])
                HC += float(vehatt.find('emissions').attrib['HC_abs'])
                PMx += float(vehatt.find('emissions').attrib['PMx_abs'])
                NOx += float(vehatt.find('emissions').attrib['NOx_abs'])
                route_length += float(vehatt.attrib['routeLength'])
                trip_duration += float(vehatt.attrib['duration'])
                wait_time += float(vehatt.attrib['waitingTime'])
                break
    '''

    for event, att in VMT_iter:
        print('checking platoon stat')
        #for vehicle in att.findall('vehicle'):
        if att.tag == 'vehicle':
            print('got it')
            if att.attrib['id'] in veh2.keys():
                print('key match')
                delta = float(att.attrib['distance']) - float(veh2[att.attrib['id']])
                veh2[att.attrib['id']]=att.attrib['distance']
                if att.attrib['type'] == 'DEFAULT_VEHTYPE':
                    Default_dist += delta
                    print('no platoon')
                elif att.attrib['type'] == 'CAV_VEHTYPE':
                    Default_dist += delta
                    print('no platoon')
                elif att.attrib['type'] == 'PLATOON_VEHTYPE':
                    Platoon_dist += delta
                    print('follow')
                elif att.attrib['type'] == 'LEADER_VEHTYPE':
                    Leader_dist += delta
                    print('lead')
                elif att.attrib['type'] == 'CATCHUP_VEHTYPE':
                    Platoon_catchup_dist += delta
                    print('catchup')
                else:
                    print('UNKNOWN VEHTYPE ENCOUNTERED: distance not counted')
            else:
                print('no key match')
        att.clear()


   
    if not path.exists(log):
        f = open(log, "w")
        f.write('Input, Veh Count,Total Timeloss,Total Fuel Consumption,Mean Timeloss,Mean Fuel Consumption,Mean Route Length,Mean Trip Duration,Mean Waitime,Mean CO,Mean CO2,Mean HC,Mean PMx,Mean NOx, Dist No Platoon, Dist Follow Platoon, Dist Lead Platoon, Dist Catchup Platoon\n')
    else:
        f = open(log, "a")

    f.write(input +','+ str(count) +',' + str(time_loss) +','+ str(fuel) +','+ str(time_loss / count) +','+ str(fuel / count) +','+ str(route_length / count) +','+ str(trip_duration / count) +','+ str(wait_time / count) +','+ str(CO / count) +','+ str(CO2 / count) +','+ str(HC / count) +','+ str(PMx / count) +','+ str(NOx / count) +',' +str(Default_dist + CAV_dist) +',' + str(Platoon_dist) +',' + str(Leader_dist) +',' + str(Platoon_catchup_dist) +'\n')
    f.close()


    #todo only consider inputs from CAV000 match
    #todo only consider platoon status for input dict (as previously implemented)



#eval all inputs
def eval(input=input, log=log, platoon=platoon):
    print(input)
    print(log)
    print(platoon)
    tree = ElementTree.parse(input)
    root = tree.getroot()

    print("input tripinfo loaded")

    #VMT_tree = ElementTree.parse(platoon)
    #VMT_root = VMT_tree.geetroot()

    VMT_iter = ElementTree.iterparse(platoon)

    print("input platoon status loaded as iter")

    count = 0 #number of vehicles completing route (unless incomplete trips are being reported)
    time_loss = 0 #time lost in seconds due to travel below individual ideal speeds
    fuel = 0 #total fuel consumption ml
    route_length = 0 #distance traveled
    trip_duration = 0 #time in seconds to reach destination
    wait_time = 0 #time in seconds with speed below 0.1m/s (eg stop & go traffic)
    #emissions from SUMO (also includes fuel)
    CO = 0 #CO emission mg
    CO2 = 0 #CO2 emission mg
    HC = 0 #HC emission mg
    PMx = 0 #PMx emission mg
    NOx = 0 #NOx emission mg

    #Vehicle Miles Traveled variables
    Default_dist = 0 #adds to no platoon
    CAV_dist = 0 #adds to no platoon
    Platoon_dist = 0 #in a platoon as follower (may include catchup to "to-be" leader)
    Leader_dist = 0 #in a platoon as leader
    Platoon_catchup_dist = 0 #in a platoon catchup status (higher speed / acceleration)
 
    veh = {} #init dictionary to extract only data from vehicles in platoon_status log that also appear in tripinfo (default: completed trips only)


    for att in root:
        #print(att.attrib['id'])
        #print(att.find('emissions').attrib['fuel_abs'])
        veh[att.attrib['id']] = 0
        count += 1
        #print(att.tag)
        time_loss += float(att.attrib['timeLoss'])
        fuel += float(att.find('emissions').attrib['fuel_abs'])
        CO += float(att.find('emissions').attrib['CO_abs'])
        CO2 += float(att.find('emissions').attrib['CO2_abs'])
        HC += float(att.find('emissions').attrib['HC_abs'])
        PMx += float(att.find('emissions').attrib['PMx_abs'])
        NOx += float(att.find('emissions').attrib['NOx_abs'])
        route_length += float(att.attrib['routeLength'])
        trip_duration += float(att.attrib['duration'])
        wait_time += float(att.attrib['waitingTime'])
    print(count)

    for event, att in VMT_iter:
        #for vehicle in att.findall('vehicle'):
        if att.tag == 'vehicle':
            print('got it')
            if att.attrib['id'] in veh:
                delta = float(att.attrib['distance']) - float(veh[att.attrib['id']])
                veh[att.attrib['id']]=att.attrib['distance']
                if att.attrib['type'] == 'DEFAULT_VEHTYPE':
                    Default_dist += delta
                    print('no platoon')
                elif att.attrib['type'] == 'CAV_VEHTYPE':
                    Default_dist += delta
                    print('no platoon')
                elif att.attrib['type'] == 'PLATOON_VEHTYPE':
                    Platoon_dist += delta
                    print('follow')
                elif att.attrib['type'] == 'LEADER_VEHTYPE':
                    Leader_dist += delta
                    print('lead')
                elif att.attrib['type'] == 'CATCHUP_VEHTYPE':
                    Platoon_catchup_dist += delta
                    print('catchup')
                else:
                    print('UNKNOWN VEHTYPE ENCOUNTERED: distance not counted')
        att.clear()


    if not path.exists(log):
        f = open(log, "w")
        f.write('Input, Veh Count,Total Timeloss,Total Fuel Consumption,Mean Timeloss,Mean Fuel Consumption,Mean Route Length,Mean Trip Duration,Mean Waitime,Mean CO,Mean CO2,Mean HC,Mean PMx,Mean NOx, Dist No Platoon, Dist Follow Platoon, Dist Lead Platoon, Dist Platoon Catchup\n')
    else:
        f = open(log, "a")

    f.write(input +','+ str(count) +',' + str(time_loss) +','+ str(fuel) +','+ str(time_loss / count) +','+ str(fuel / count) +','+ str(route_length / count) +','+ str(trip_duration / count) +','+ str(wait_time / count) +','+ str(CO / count) +','+ str(CO2 / count) +','+ str(HC / count) +','+ str(PMx / count) +','+ str(NOx / count) +',' +str(Default_dist + CAV_dist) +',' + str(Platoon_dist) +',' + str(Leader_dist) +',' + str(Platoon_catchup_dist) +'\n')
    f.close()


'''
print('Veh Count: ' + str(count))
print('Total TimeLoss: ' + str(time_loss))
print('Total Fuel Consumption: ' + str(fuel))

print('Mean TimeLoss: ' + str(time_loss/count))
print('Mean Fuel Consumption: ' + str(fuel/count))
print('Mean Route Length: ' + str(route_length/count))
print('Mean Trip Duration: ' + str(trip_duration/count))
print('Mean Wait Time: ' + str(wait_time/count))

print('Mean CO: ' + str(CO/count))
print('Mean CO2: ' + str(CO2/count))
print('Mean HC: ' + str(HC/count))
print('Mean PMx: ' + str(PMx/count))
print('Mean NOx: ' + str(NOx/count))
'''

#eval()


Baseline = mypath + 'CAV000_' + str(run) + '_tripinfo'
Input = mypath + prefix + '_'+ str(run) + '_' + str(mysize) + '_tripinfo'
Log = mypath + mylog + '_metrics.csv'
Platoon = mypath + prefix + '_' + str(run) + '_' + str(mysize) + '_platoon_status.xml'
#eval(Input, Log, Platoon)


#remove after cleantest
Baseline = mypath + 'cleantestbaseline_tripinfo'
Input = mypath + 'cleantest_tripinfo'
Log = mypath + 'cleantest_log_metrics.csv'
Platoon = mypath + 'demand/cleantest_platoon_status.xml'

print(Baseline)
print(Input)
print(Log)
print(Platoon)

eval2(Baseline, Input, Log, Platoon)
print("done")

'''
try:
    eval2(Baseline, Input, Log, Platoon)
    print('eval completed OK')
except:
    print('run info problem, probably not there from cleanup')
'''

#eval2()
#compare()
