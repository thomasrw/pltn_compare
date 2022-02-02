 #Copyright (c) 2021 Robert Thomas
 #_utils2.py version 2

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# @file     _utils2.py
# @author   Robert Thomas
# @date     2020-03-02


'''
Additional utility functions and classes for simpla
'''


import os
import sys
import optparse


if 'SUMO_HOME' in os.environ:
     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
     sys.path.append(tools)
     print("SUMO_HOME detected by _UTILS2")
else:
     sys.exit("please declare environment variable 'SUMO_HOME'")


import traci
import traci._vehicle
import simpla
from simpla._utils import openGap
import simpla._config as cfg
import random

from xml.etree import ElementTree


DEBUG_UTILS2 = True

if DEBUG_UTILS2:
    print("_UTILS2 loaded")


_oversize = []


class SizeRestrictor(traci.StepListener):
    '''
    Class that manages platoon size so that no one platoon grows too large.
    Manages platoon size reactively, taking actions after a platoon becomes oversized.
    '''



    def __init__(self, mgr, maxSize, coolDown):
        '''
        SizeRestrictor()

        :param mgr: platoon manager whose platoons will be monitored
        :param maxSize: int >= 2; the platoon will split if the size increases beyond this number
        :param coolDown: float; duration before vehicles pruned from a platoon may attempt to rejoin
        '''

        self._pltnMgr = mgr
        self._maxSize = int(maxSize) #need to check for size >=2
        self._coolDown = float(coolDown)

        self._separation = cfg.MAX_PLATOON_GAP + 1


        if DEBUG_UTILS2:
            print("Created SizeRestrictor for platoon manager: " + str(self._pltnMgr))

    def step(self, s=0): #s=0 optional argument unused though expected by TracI
        '''
        Check size of each platoon managed by _pltnMgr and split if size > maxSize
        :return: True
        '''


        print("step part 1")
        print(self._pltnMgr._platoons.values())
        self._checkSize()

        if len(_oversize) > 0:
            self._initiateSplit(_oversize)

        print("got to step")

        return True #return value indicates if the listener wants to stay active


    def _checkSize(self):
        '''
        Checks the size of each platoon
        :return: list of oversized platoons
        '''
        global _oversize
        for pltn in self._pltnMgr._platoons.values():
            size = int(pltn.size())
            print("SIZE IS!!!!!!!: " + str(size))
            if size > self._maxSize:
                _oversize.append(pltn)
                print("added oversize pltn: " + str(pltn.getID()))
        #print(str(_oversize[0].getID()))
        return _oversize



    def _initiateSplit(self, oversize):
        '''
        Instigate a split in each oversized platoon using openGap() at the first surplus vehicle
        :param oversize: list of oversized platoons
        :return:
        '''
        global _oversize
        for pltn in oversize:
            #openGap(pltn.getVehicles()[self._maxSize].getID(), self._separation, 1, 1, self._coolDown)
            #cant add GapController (listener) inside of traci.simulation step
            #need to add cooldown to switch wait time or feed gap inputs to another method outside of step
            np = pltn.split(self._maxSize)
            if np == None:
                print("COULD NOT SPLIT")
            else:
                self._pltnMgr._platoons[np.getID()] = np


        _oversize = [] #reset oversize

        #call split
        #also openGap so that the platoon does not try to reform instantly

def seekLeader(vehID, dist):
    '''
    Addresses the behavior of two connected vehicles near each other but in different lanes not changing lanes
    proactively to form a platoon.
    Looks for potential leader in neighboring lanes. Attempts to change lanes to the nearest connected lead neighbor.
    Once following another connected vehicle, the platoon manager will determine if vehID will join the platoon.


    :param vehID: string
    :param dist: double
    :return: (string, double) leader VehID and double distance. Note: the returned leader could be further away than
    the given dist.
    '''

    return traci.vehicle.getLeader(vehID, dist)

def seekLeader2(vehID, dist, pmethod, mgr):
    '''

    :param vehID: String vehicle id seeking leader
    :param dist: double minimum lookahead
    :param pmethod: int key for determining how to filter results based on platoon method
        1 = dynnamic
        2 = ad hoc game
        3 = orchestrated (pre-approved)
    :param mgr: Platoon Manager
    :return: (string, double) matching vehID and distance
        Note that the returned leader may be further away than the given dist and that the vehicle
        will only look on its current best lanes and not look beyond the end of its final route edge.
    '''

    maybe = traci.vehicle.getLeader(vehID, dist)
    status = mgr.getStatus()
    if maybe == None: #no lead found
        return maybe
    elif pmethod == 1:
        return maybe
    elif pmethod == 2:
        #check deny list for pltn leader of 'mabye', if not there, return maybe
        print("maybe[0] is: " + maybe[0])
        if not mgr._isConnected(maybe[0]):
            print(maybe[0] + " is not connected")
            return maybe
        PLeader = mgr._connectedVehicles[maybe[0]].getPlatoon().getLeader()
        try:
            trailingVeh = mgr._connectedVehicles[vehID]
        except:
            print(vehID + " VehID not found")
            return None
        trailingPltn = trailingVeh.getPlatoon()

        #if (PLeader, mgr._connectedVehicles[maybe[0]])  in status:
        if (PLeader, trailingVeh) in status:
            if  status[(PLeader,trailingVeh)]: #true means approved
                return maybe
            else: return None #false means not approved, reutrn None to preclude further consideration
        else: #status unknown - need to play adhoc game to determine platoon approval status
            status[(PLeader,trailingVeh)] = dynamicPlatoonAdHocPlatoonGame(trailingVeh.getPlatoon(), PLeader.getPlatoon())
            status[(trailingVeh,PLeader)] = status[(PLeader, trailingVeh)] #tuple part order should not matter
            mgr.updateStatus(status)

            if  status[(PLeader,trailingVeh)]: #true means approved
                return maybe
            else: return None

    elif pmethod == 3:
        #check approved list - list must be complete for the sim
        if not mgr._isConnected(maybe[0]):
            print(maybe[0] + " is not connected")
            return maybe
        PLeader = mgr._connectedVehicles[maybe[0]].getPlatoon().getLeader()
        if PLeader in status and status[PLeader]:
            return maybe
        else: return None

    else:
        print("unexpected condition seeking leader")
        return None
'''
    #list of nearby (with in dist) vehicles in front of vehicle(vehID), to include neighboring lanes
    leaders=[]

    #build the leaders list with left and right neighbors + the leader directly in front

    #try:
    print('try left')
    print(vehID + " : " + str(dist))
    print(traci.vehicle.getLeftLeaders(vehID))
    leaders.extend(traci.vehicle.getLeftLeaders(vehID))
    #except:
     #   print('problem seeking left, returning None')
      #  return None

    #print("error left")


    #fixme: looking right fails under some (unknown) condition(s)

    #try:
    print('try right')
    leaders.extend(traci.vehicle.getRightLeaders(vehID))
    #except:
     #   print('problem right')
      #  return None
    #    print('attempting to reconnect....' + '\n')
    #    traci.connect(port=39461)  # trying to re-establish connection  .... try traci.init() next .. may have to recreate platoon mgrs
    #    print('success')



    print('try straight forward')
    leaders.append(traci.vehicle.getLeader(vehID, dist))

    #prune the None's so the list may be sorted
    i=0
    #todo pop on a second pass to ensure popping correclty 
    for l in leaders:
        if l is None:
            leaders.pop(i)
            continue #skip incrementing i because because pop just decremented by 1 so i is already current
        i+= 1
    leaders.sort(key = lambda x: x[1])

    if DEBUG_UTILS2:
        print(leaders)

    #return traci.vehicle.getLeader(vehID, dist)

    if len(leaders) is 0:
        if DEBUG_UTILS2:
            print("NONE returned")
        return None
    elif leaders[0][1] > dist:
        if DEBUG_UTILS2:
            print("elif NONE")
        return None

    elif leaders[0][1] <= dist:
        if DEBUG_UTILS2:
            print("leader returned: " + str(leaders[0]))
        #todo return leaders[0]
        return traci.vehicle.getLeader(vehID, dist)



            #return leaders[0]

    else:
        # duplicate default simpla behavior, this should never execute
        print("Check _utils2.seekLeader()")
        return traci.vehicle.getLeader(vehID, dist)


'''


    #duplicate default behavior
    #return traci.vehicle.getLeader(vehID, dist)

    #find leaders left & right
    #filter for connected vehicles
    #adivse lane change to match nearest


#route_map = {}

#temporary
#route_map['flow1'] = 'gneE12_to_158140892'
'''
<flow id="flow2" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="800" from="gneE13" to="158140892"/>
    <flow id="flow3" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="800" from="gneE14" to="158140892"/>

    <flow id="flow4" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="266" from="gneE12" to="30199406#0"/>
    <flow id="flow5" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="265" from="gneE13" to="30199406#0"/>
    <flow id="flow6" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="265" from="gneE14" to="30199406#0"/>

    <flow id="flow7" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="34" from="gneE7" to="30199406#0"/>
    <flow id="flow8" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="34" from="gneE8" to="30199406#0"/>

    <flow id="flow9" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="16" from="gneE16" to="30049266"/>
    <flow id="flow10" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="16" from="gneE17" to="30049266"/>

    <flow id="flow11" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="17" from="gneE16" to="30048660"/>
    <flow id="flow12" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="17" from="gneE17" to="30048660"/>

    <flow id="flow13" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="17" from="gneE16" to="265151576"/>
    <flow id="flow14" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="17" from="gneE17" to="265151576"/>

    <flow id="flow15" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="34" from="561394916" to="30199406#0"/>

    <flow id="flow16" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE6" to="32400285"/>
    <flow id="flow17" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE6" to="30049266"/>
    <flow id="flow18" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE6" to="30048660"/>
    <flow id="flow19" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="327" from="gneE6" to="265151576"/>

    <flow id="flow20" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE3" to="32400285"/>
    <flow id="flow21" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE3" to="30049266"/>
    <flow id="flow22" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE3" to="30048660"/>
    <flow id="flow23" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="327" from="gneE3" to="265151576"/>

    <flow id="flow24" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE0" to="32400285"/>
    <flow id="flow25" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE0" to="30049266"/>
    <flow id="flow26" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="112" from="gneE0" to="30048660"/>
    <flow id="flow27" type="DEFAULT_VEHTYPE" begin="0" end="3600" vehsPerHour="327" from="gneE0" to="265151576"/>
'''

def createDemand(tripinfo, triproutes, target='./demand.xml'):
    '''
    Reads a SUMO tripinfo file and writes a sorted list of vehicles suitable for an emitter demand file.
    Used for making a repeatable network load originally produced with probabilities e.g. vehicles per hour such that
    simulations with different settings can be compared.
    Example:
    <tripinfo id="flow9.0" depart="0.00" departLane="gneE16_0" departPos="5.10" departSpeed="0.00" departDelay="0.00" arrival="87.50" arrivalLane="30049266_0" arrivalPos="249.78" arrivalSpeed="27.73" duration="87.50" routeLength="2162.34" waitingTime="0.00" waitingCount="0" stopTime="0.00" timeLoss="7.61" rerouteNo="1" devices="vehroute_flow9.0 tripinfo_flow9.0 routing_flow9.0 emissions_flow9.0" vType="DEFAULT_VEHTYPE" speedFactor="1.25" vaporized="">
        <emissions CO_abs="6647.464304" CO2_abs="447193.869180" HC_abs="41.408575" PMx_abs="9.811259" NOx_abs="178.812162" fuel_abs="192.228106" electricity_abs="0"/>
    </tripinfo>
    becomes: <vehicle id="flow9.0" depart="0.00" departLane="0" departPos="5.10" departSpeed="0.00" type="DEFAULT_VEHTYPE" speedFactor="1.25" route="gneE16_to_30049266"/>

    :param tripinfo: tripinfo file produced by SUMO
    :param triproutes: xml file containing flows as <flows> <flow id= .../> </flows>
    :return:
    '''

    vehicles = []
    count = 0
    tree = ElementTree.parse(tripinfo)
    root = tree.getroot()

    #sort trips by departure time
    root[:] = sorted(root, key=lambda child: float(child.attrib['depart']))

    for att in root:
        #print(att.tag)

        if 'id' in att.attrib:
            #remove extra attributes
            att.attrib.pop('departDelay')
            att.attrib.pop('arrival')
            att.attrib.pop('arrivalLane')
            att.attrib.pop('arrivalPos')
            att.attrib.pop('arrivalSpeed')
            att.attrib.pop('duration')
            att.attrib.pop('routeLength')
            att.attrib.pop('waitingTime')
            att.attrib.pop('waitingCount')
            att.attrib.pop('stopTime')
            att.attrib.pop('timeLoss')
            att.attrib.pop('rerouteNo')
            att.attrib.pop('devices')
            att.attrib.pop('vaporized')

            #adjust departLane from "edge_lane" to just "lane"
            lane = att.attrib['departLane'].split('_')[-1]
            att.set('departLane', lane)

            #adjust vType to type
            veh_type = att.attrib['vType']
            att.attrib.pop('vType')
            att.set('type', veh_type)

            #add route
            routes = buildRouteMap(triproutes)
            att.set('route', routes[att.attrib['id'].split('.')[0]]) #assumes vehID contains only one '.'

            #drop emissions element
            att.remove(att.getchildren()[0]) #assumes emissions is the first and only sub-element

            #adjust 'tripinfo' to 'vehicle'
            att.tag = 'vehicle'


            #if count >=40:
            #    break
            count += 1
            vehicles.append(att)


    print(str(count))
    print(vehicles)
    for v in vehicles:
        print(v.attrib)
    #todo clean this up
    tree.write(target)

def buildRouteMap(input):
    '''
    Reads flows from input and outputs a Dict of routes by flow
    :param input: flow definitions as xml
    :return: Dict{}
    '''

    route_map = {}
    tree = ElementTree.parse(input)
    root = tree.getroot()

    #route_map['flow1'] = 'gneE12_to_158140892'

    for att in root:
        if att.tag == 'vType':
            continue
        route_map[att.attrib['id']] = att.attrib['from'] + '_to_' + att.attrib['to']
    return route_map


def dynamicPlatoon(pltn1, pltn2):
    '''
    Mirrors default behavior of simpla... connected vehicles will always attempt to platoon when in range of each other.
    Attempts to add pltn2 to the end of pltn1; returns True if successful.

    :param pltn1:
    :param pltn2:
    :return: Bool
    '''
    return pltn1.join(pltn2)


def dynamicPlatoonAdHocPlatoonGame(pltn1, pltn2):
    '''
    Decentralized Platoon Coordination implementation based on Thomas, R. W., & Vidal, J.M. (2019). Ad Hoc Vehicle
    Platoon Formation. IEEE Southeastcon.

    :param pltn1:
    :param pltn2:
    :return: Bool
    '''
    #todo what if the join fails for some unrelated reason (e.g. maneuver was unsafe)?
    #negotiate platoon
    #-if fails, remember each other and break on attempts
    #-if succeed, remembrer success
    #--try to platoon, if fails for unrelated reason like unsafe manuver... platoon is already "authorized"
    #--at next step try to join again (no need to negotiate)

    #front veh becomes leader, simple
    #rear veh becomes leader, still join as normal, aggregate metrics will still be accurate

    print("*************************** checking game status ********************")

    player1 = pltn1.getLeader()
    player2 = pltn2.getLeader()
    print(player1.getID() + "," + player2.getID())
    #history = '/home/thomasrw/Desktop/historya.txt'
    history = '/work/thoma525/history.txt'
    logfile = open(history, 'a')
    #logfile.close()

    #assumes not first encounter

    #always platoon conditions: c:*, t:t, g:g, t:g, g:t
    if player1.getID().startswith('c') or player2.getID().startswith('c'):
        logfile.close()
        return True #cooperator always platoons

    if player1.getID().startswith('t') and player2.getID().startswith('t'):
        logfile.close()
        return True #TforT always platoons with itself

    if player1.getID().startswith('g') and player2.getID().startswith('g'):
        logfile.close()
        return True #Grudger always platoons with itself

    if player1.getID().startswith('t') and player2.getID().startswith('g'):
        logfile.close()
        return True #TforT always platoons with Grudger

    if player1.getID().startswith('g') and player2.getID().startswith('t'):
        logfile.close()
        return True #Grudger always platoons with TforT

    #never platoon (includes beyond 1st encounter)
    if player1.getID().startswith('d') and player2.getID().startswith('d'):
        logfile.close()
        return False #D:D always denies

    if player1.getID().startswith('d') or player2.getID().startswith('d'):
        if player1.getID().startswith('t') or player2.getID().startswith('t'):
            logfile.close()
            return False #D:T always denies after first encounter
        elif player1.getID().startswith('g') or player2.getID().startswith('g'):
            logfile.close()
            return False  # D:G always denies after first encounter

    #always a chance with random...
    if player1.getID().startswith('r') and player2.getID().startswith('r'):
        logfile.close()
        return random.randrange(100) < 75 #R:R will platoon 75% of the time (when one or both choose cooperate)

    if player1.getID().startswith('r') or player2.getID().startswith('r'):
        if player1.getID().startswith('d') and player2.getID().startswith('d'):
            return random.randrange(100) < 50 #R will still cooperate 50% of the time
        if player1.getID().startswith('g') and player2.getID().startswith('g'):
            return random.randrange(100) < 50 #G will eventually deny all but R will still cooperate 50% of the time
        if player1.getID().startswith('t') and player2.getID().startswith('t'):
            return random.randrange(100) < 75 #R will cooperate 50% of the time meaning T will cooperate on the next turn


    '''
    if player1.getID().startswith('t') or player2.getID().startswith('t'): #first instance will be true
        #todo playout and record results to history
        if player1.getID().startswith('d') or player2.getID().startswith('d'): #all future attempts will fail
            logfile.write(player1.getID() + "," + player2.getID() + ",deny\n")
            logfile.write(player2.getID() + "," + player1.getID() + ",deny\n") #order of players should not matter
        if player1.getID().startswith('r') or player2.getID().startswith('r'):
            if random.randrange(10) < 5:  # 50% chance random will cooperate, so next attempt will pass too
                logfile.write(player1.getID() + "," + player2.getID() + ",approve_mod\n") #need to replay to determine turn after next
                logfile.write(player2.getID() + "," + player1.getID() + ",approve_mod\n")  # order of players should not matter
            else:   #next attempt tft player will defect, but r player may cooperate
                logfile.write(player1.getID() + "," + player2.getID() + ",random_mod\n") #update tft play for next time, regardless of outcome
                logfile.write(player2.getID() + "," + player1.getID() + ",random_mod\n")  # order of players should not matter

        logfile.close()

        return True
    if player1.getID().startswith('g') or player2.getID().startswith('g'): #first instance will be true
        #todo playout and record results to history
        if player1.getID().startswith('d') or player2.getID().startswith('d'): #all future attempts will fail
            logfile.write(player1.getID() + "," + player2.getID() + ",deny\n")
            logfile.write(player2.getID() + "," + player1.getID() + ",deny\n") #order of players should not matter

        if player1.getID().startswith('r') or player2.getID().startswith('r'):
            if random.randrange(10) < 5:  # 50% chance random will cooperate, so next attempt will pass too
                logfile.write(player1.getID() + "," + player2.getID() + ",approve_mod\n") #need to replay to determine turn after next
                logfile.write(player2.getID() + "," + player1.getID() + ",approve_mod\n")  # order of players should not matter

            else: #all future attempts fail
                logfile.write(player1.getID() + "," + player2.getID() + ",deny\n")
                logfile.write(player2.getID() + "," + player1.getID() + ",deny\n")  # order of players should not matter

        logfile.close()

        return True
    logfile.close()

    if player1.getID().startswith('d'):
        logfile.close()

        if player2.getID().startswith('d'):
            return False
        elif player2.getID().startswith('r'):
            return random.randrange(10) < 5 #50% chance random will cooperate
        else:
            print("unexpected condition while playing Ad Hoc Game")
            return False
    elif player1.getID().startswith('r'):
        if random.randrange(10) < 5: #50% chance random will cooperate
            return True
        # evaluate player 2 if player 1 (r) did not cooperate
        elif player2.getID().startswith('r'):
            return random.randrange(10) < 5 #50% chance random will cooperate
        elif player2.getID().startswith('d'):
            return False #defector does not cooperate and random has already chosen not to cooperate
        else:
            print("unexpected condition while playing Ad Hoc Game")
            return False
    else:
        print("unexpected condition while playing Ad Hoc Game")
        return False



    #return True #always approve for testing integration of method call
    '''
def centralPlatoonClustering(emitterFile, maxsize=-1):
    '''
    Centralized Platoon Coordination implementation based on Van De Hoef, S. Johansson, K. H., & Dimarogonas, D. V.
    (2015). Coordintating truck platooning by clustering pairwise fuel-optimal plans. IEEE 8th International Conference
    on Intelligent Transportation Systems (pp. 408-415). IEEE.


    :param emitterFile: xml file such as that produced by dfrouter that generates vehicles with a given route at a given
    time

    :return: list of PlatoonManagers #control strings so there is a "default" platoon manager for each schedule platoon
    '''
    pass



'''   ***from stack overflow for changing element names

https://stackoverflow.com/questions/54796054/xml-change-tag-name-using-python

import xml.etree.ElementTree as ET

tree = ET.parse("input.xml")

for elem in tree.findall("Employee/SSN"):
    elem.tag = "EESSN"

tree.write("output.xml")
'''

#print("hello Demand")
#myDemand = createDemand('/home/thomasrw/j/2020-03-28-13-05-16tripinfo', "/home/thomasrw/j/flows.xml")

#buildRouteMap("/home/thomasrw/j/flows.xml")