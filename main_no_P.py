#!/usr/bin/env python



import os
import sys
import optparse
import time


if 'SUMO_HOME' in os.environ:
     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
     sys.path.append(tools)
     print("SUMO_HOME detected!")
else:
     sys.exit("please declare environment variable 'SUMO_HOME'")


import traci
import simpla
import _utils2
import _platoonmanager2
import sys

# add command line option for not using gui interface (faster simulation runs)
def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true", default=False, help="run the command line version of SUMO")
    options, args = opt_parser.parse_args()
    return options

# TraCI control loop
def run():
    step = 0

    #setup VMT logfile
    log = logname + "platoon_status.xml"
    file = workdir + log
    #file = '/home/thomasrw/Desktop/' + log
    #file = '/work/thoma525/' + log

    logfile = open(file, 'w')
    logfile.write('<platoon_status>\n')

    tree = ''

    while step < 72000:
    #while traci.simulation.getMinExpectedNumber() > 0:

        tree += '<time value="' + str(step) + '">\n'

        for veh_id in traci.vehicle.getIDList():
            distance = traci.vehicle.getDistance(veh_id)
            type = traci.vehicle.getTypeID(veh_id)


            tree += '<vehicle id="' + str(veh_id) + '" distance="' + str(distance) + '" type="' + str(type) + '"/>\n'

        # print(veh_id, distance, type)

        tree += '</time>\n'
        if step % 10000 == 0:  # write to file every 10,000 steps
            logfile.write(tree)
            tree = ''


        traci.simulationStep()
        print(step)
        step += 1

    if tree == '':
        pass #last step was a write step
    else:
        logfile.write(tree) #write final entry from last set of steps

    logfile.write('</platoon_status>')
    logfile.close()

    traci.close()
    sys.stdout.flush()




# main entry point

logname = sys.argv[1]
logname = logname + "_"

demandfile = sys.argv[2]
#demandpath = "/work/thoma525/"

demandpath = sys.argv[5]
#demandpath = "/home/thomasrw/Desktop"

#demand = demandpath + demandfile
#running local - using full  path as argument
demand = demandfile

pltnsize = int(sys.argv[3])

workdir = sys.argv[4]

#additional = "/home/thoma525/myOUT-route.xml," + demand + ",/home/thoma525/detPOI_OUT.xml,/home/thoma525/valCount.xml"
#below for local run only
outroute = sys.argv[8]
detPOIout = sys.argv[9]
valcount = sys.argv[10]
additional = outroute + "," + demand + "," + detPOIout + "," + valcount
#additional = "/home/thomasrw/Model/HPC/home/myOUT-route.xml," + demand + ",/home/thomasrw/Model/HPC/home/detPOI_OUT.xml,/home/thomasrw/Model/HPC/home/valCount.xml"


if __name__ == "__main__":
    options = get_options()
    if options.nogui:
        sumoBinary = "sumo" #"/usr/share/sumo/bin/sumo"
    else:
        sumoBinary = "/usr/share/sumo/bin/sumo-gui"

    # passing the "--start" option to tell sumo-gui to begin without waiting for the play button to be pressed
    #sumoCmd = [sumoBinary, "-c", "/home/thoma525/myconfig", "-a", additional, "--output-prefix", logname, "--start"]
    config = sys.argv[6]
    #sumoCmd = [sumoBinary, "-c", "/home/thomasrw/Model/HPC/home/myconfig.bluelight", "-a", additional, "--output-prefix", logname, "--start"]
    sumoCmd = [sumoBinary, "-c", config, "-a", additional, "--output-prefix", logname, "--start"]

    #sumoCmd = [sumoBinary, "-c", "/home/thomasrw/Model/myconfig"]
    simplaConfig = sys.argv[7]
    #simplaConfig = "/home/thomasrw/Model/HPC/home/mysimpla.cfg.xml"
    #simplaConfig = "/usr/share/sumo/tools/simpla/template.cfg.xml"

    #simplaConfig2 = "/home/thomasrw/Model/mysimpla2.cfg.xml"


    traci.start(sumoCmd)
    #simpla.load(simplaConfig)

    #simpla.load(simplaConfig2)

    #simplaConfig = "/home/thomasrw/j/mysimpla.cfg.xml"
    #simpla._config.load(simplaConfig) #removed for _no_P baseline
    ##mgr = simpla._platoonmanager.PlatoonManager()

    #mgr = _platoonmanager2.PlatoonManager2(pltnsize) #removed for _no_P baseline
    #mgr_id = traci.addStepListener(mgr) #removed for no_P baseline

    start = time.time()
    run()
    end = time.time()
    total = end - start
    print("time taken is: " + str(total))