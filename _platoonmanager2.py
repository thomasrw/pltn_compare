 #Copyright (c) 2021 Robert Thomas
 # _platoonmanger2.py version 2

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

# @file     _platoonmanager2.py
# @author   Robert Thomas
# @date     2020-04-05



import os
import sys
import optparse


if 'SUMO_HOME' in os.environ:
     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
     sys.path.append(tools)
     print("SUMO_HOME detected by platoonmanager2")
else:
     sys.exit("please declare environment variable 'SUMO_HOME'")


import traci
from traci.exceptions import TraCIException
import traci.constants as tc


import simpla._reporting as rp
import simpla._config as cfg
import simpla._pvehicle
from simpla import SimplaException
from simpla._platoonmode import PlatoonMode
from _collections import defaultdict
import _utils2

warn = rp.Warner("PlatoonManager2")
report = rp.Reporter("PlatoonManager2")



class PlatoonManager2(simpla._platoonmanager.PlatoonManager):
    '''
    Modifies and extends PlatoonManager to:
    Fixme 1) consider vehicles in neighboring lanes as potential platoon partners
    2) allow restriction of platoon max size
    TODO 3) specify platoon negotiation algorithm
    TODO 4) specify algorithm for establishing trust between connected vhehicles
    5) For single vehicles, consider slowing down to reach a platoon partner
    '''
    #todo add ability to specify platoon negotiation algorithm
    #todo add ability to specify trust determination algorithm

    #fixme simpla reporting at verbosity level 4 can throw an error on managing list with none type
    # could be related to _utils2.seekLeaders()


    #_MAX_PLATOON_SIZE= -1


    def __init__(self, maxsize=-1):
        '''
        PlatoonManager2()

        Creates and initializes the PlatoonManger with additional options
        :param maxsize: (int) max number of vehicles allowed in a platoon. Numbers < 1 are not enforced.
        '''

        simpla._platoonmanager.PlatoonManager.__init__(self)
        self._MAX_PLATOON_SIZE = maxsize
        self._hasVehBehind = dict()
        self._pltnApprovalStatus = dict() #used to remember pre-approved(or denied) platoon pairings

    def getStatus(self):
        return self._pltnApprovalStatus

    def updateStatus(self, status):
        self._pltnApprovalStatus = status

    def step(self, t=0):
        '''
        step()

        Adds to PlatoonManager step function awareness of potential platoons behind a single vehicle to allow for
        instances where a vehicle should slow down to join the nearest platoon vice trying to catchup to the next
        platoon in front. If a participant's priority is fuel efficiency, slowing down to join a platoon vice speeding
        provides more utility

        :param t:
        :return: True on success
        '''

        #re-initialize _hasVehBehind for this step
        self._hasVehBehind = dict()

        #run step as normal
        print("start step")
        simpla._platoonmanager.PlatoonManager.step(self, t)
        print("finish original step")

        #check if vehicles were added to _hasVehBehind during step execution
        #if so, determine if they are in a platoon of size > 1
        #if not, tell the veh to slow down so the connected veh behind have a chance to catch up
        for veh in self._hasVehBehind:
            print("checking on: " + veh)
            if self._connectedVehicles[veh].getPlatoon().size() <= 1:
                print("adjust speed of: " + veh)
                traci.vehicle.setSpeedFactor(veh, 1.09) # 0.01 less than default (non-platoon)

                #self._connectedVehicles[vehID] = veh
                #self._platoons[veh.getPlatoon().getID()] = veh.getPlatoon()

        print("finish total step")




        return True #keep listener active



    def setMaxSize(self, size):
        '''
        Sets the _MAX_PLATOON_SIZE variable for the calling pltnmgr2
        :param size: int
        :return:
        '''
        self._MAX_PLATOON_SIZE = size


    def getMaxSize(self):
        '''
        Returns the _MAX_PLATOON_SIZE variable of the calling pltnmgr2
        :return: int
        '''
        return self._MAX_PLATOON_SIZE


    def sizePolicyExists(self):
        '''
        Returns True if _MAX_PLATOON_SIZE is set >= 1
        :return: bool
        '''
        #Platoon size less than 1 is not enforceable
        if self.getMaxSize() >= 1:
            return True
        else:
            return False

    def _updateVehicleStates(self):
        '''_
        updateVehicleStates()

        This updates the vehicles' states with information from the simulation

        todo:
        PLTNMGR2 expands getLeader to also consider adjacent lanes vice only the current lane by replacing calls to
        traci.vehicle.getLeader(vehID, dist) with _utils2.seekLeader(vehID, dist)
        '''
        self._subscriptionResults = traci.vehicle.getAllSubscriptionResults()
        for veh in self._connectedVehicles.values():
            if (veh.getID() not in self._subscriptionResults):
                # FIXME: For some reason, this is in rare occasions called with vehicles,
                #        which have no subscription results.
                print("RETURN CALLED")
                return
            veh.state.speed = self._subscriptionResults[veh.getID()][tc.VAR_SPEED]
            veh.state.edgeID = self._subscriptionResults[veh.getID()][tc.VAR_ROAD_ID]
            veh.state.laneID = self._subscriptionResults[veh.getID()][tc.VAR_LANE_ID]
            veh.state.laneIX = self._subscriptionResults[veh.getID()][tc.VAR_LANE_INDEX]

            # PLTNMGR2 replaces call to traci.vehicle.getLeader with _utils2.seekLeader
            print("veh: " + veh.getID())
            #veh.state.leaderInfo = _utils2.seekLeader(veh.getID(), self._catchupDist)
            veh.state.leaderInfo = _utils2.seekLeader2(veh.getID(), self._catchupDist, 2, self)

            print("first call:" )

            if veh.state.leaderInfo is None:
                print("veh.state.leaderInfo is None")
                veh.state.leader = None
                veh.state.connectedVehicleAhead = False
                continue

            if veh.state.leader is None or veh.state.leader.getID() != veh.state.leaderInfo[0]:
                if self._isConnected(veh.state.leaderInfo[0]):
                    veh.state.leader = self._connectedVehicles[veh.state.leaderInfo[0]]
                    veh.state.connectedVehicleAhead = True
                    # flag vehAhead as having a platoon interest behind it
                    vehAheadID = veh.state.leaderInfo[0]
                    self._hasVehBehind[vehAheadID] = vehAheadID
                    print("111 add to _hasVehBehind: " + vehAheadID)
                else:
                    # leader is not connected -> check whether a connected vehicle is located further downstream
                    veh.state.leader = None
                    veh.state.connectedVehicleAhead = False
                    vehAheadID = veh.state.leaderInfo[0]
                    print("vehAheadID is: " + vehAheadID)
                    dist = veh.state.leaderInfo[1] + traci.vehicle.getLength(vehAheadID)
                    while dist > 0 and dist < self._catchupDist: #add >0 check due to dist becoming negative in some situations due to loop info
                        #PLTNMGR2 replaces call to traci.vehicle.getLeader with _utils2.seekLeader
                        print('in the while loop')
                        print(dist)
                        #nextLeaderInfo = _utils2.seekLeader(vehAheadID, self._catchupDist - dist)
                        nextLeaderInfo = _utils2.seekLeader2(vehAheadID, self._catchupDist - dist, 2, self)
                        print("this call:")# + nextLeaderInfo)
                        if nextLeaderInfo is None:
                            break
                        vehAheadID = nextLeaderInfo[0]
                        if self._isConnected(vehAheadID):
                            #PLTNMGR2: Check if joining vehAheadID's platoon would violate the pltn max size constraint
                            # this matters because otherwise the vehicle may try to catchup to the vehAhead
                            if self.sizePolicyExists():
                                leader = self._connectedVehicles[vehAheadID]
                                if leader.getPlatoon().size() + veh.getPlatoon().size() > self.getMaxSize():
                                    # combined size would be too big, so keep looking within catchupDist
                                    print("CONTINUE")
                                    dist += nextLeaderInfo[1] + traci.vehicle.getLength(vehAheadID)

                                    continue

                            veh.state.connectedVehicleAhead = True
                            #flag vehAhead as having a platoon interest behind it
                            self._hasVehBehind[vehAheadID] = vehAheadID
                            print("add to _hasVehBehind: " + vehAheadID)
                            if rp.VERBOSITY >= 4:
                                report("Found connected vehicle '%s' downstream of vehicle '%s' (at distance %s)" %
                                       (vehAheadID, veh.getID(), dist + nextLeaderInfo[1]))
                            break
                        dist += nextLeaderInfo[1] + traci.vehicle.getLength(vehAheadID)
                    print('out of the while loop')

    def _manageLeaders(self):
        '''_manageLeaders()

        Iterates over platoon-leaders and
        1) checks whether two platoons (including "one-vehicle platoons") may merge for being sufficiently close
        2) advises platoon-leaders to try to catch up with a platoon in front

        PLTNMGR2 adds the condition of doing the above only if the joining of the two platoons would not violate the
        maximum size allowance for platoons (if defined as >= 1)
        '''
        # list of platoon ids that merged into another platoon
        toRemove = []

        # max size Platoons are allowed to have
        #maxSize = 10
        for pltnID, pltn in self._platoons.items():
            # platoon leader
            pltnLeader = pltn.getLeader()
            # try setting back mode to regular platoon mode if leader is kept in FOLLOWER mode due to safety reasons
            # or if the ordering within platoon changed
            if pltnLeader.getCurrentPlatoonMode() == PlatoonMode.FOLLOWER:
                pltn.setModeWithImpatience(PlatoonMode.LEADER, self._controlInterval)
            elif pltnLeader.getCurrentPlatoonMode() == PlatoonMode.CATCHUP_FOLLOWER:
                pltn.setModeWithImpatience(PlatoonMode.CATCHUP, self._controlInterval)
            # get leader of the leader
            leaderInfo = pltnLeader.state.leaderInfo

            if leaderInfo is None or leaderInfo[1] > self._catchupDist:
                # No other vehicles ahead
                # reset vehicle types (could all have been in catchup mode)
                if pltn.size() == 1:
                    pltn.setModeWithImpatience(PlatoonMode.NONE, self._controlInterval)
                else:
                    # try to set mode to regular platoon mode
                    pltn.setModeWithImpatience(PlatoonMode.LEADER, self._controlInterval)
                continue

            #PLTNMGR2: if already at max size, no need to pursue adding to the platoon
            if self.sizePolicyExists() and pltn.size() == self.getMaxSize():
                continue

            if not self._isConnected(leaderInfo[0]):
                # Immediate leader is not connected
                if pltnLeader.state.connectedVehicleAhead:
                    # ... but further downstream there is a potential platooning partner
                    #TODO check if this condition is met after implementing seekLeader
                    #TODO it is.... 5/25/2020
                    print("this is happening pltnmgr2 catchup condition")
                    pltn.setModeWithImpatience(PlatoonMode.CATCHUP, self._controlInterval)
                elif pltn.size() == 1:
                    pltn.setModeWithImpatience(PlatoonMode.NONE, self._controlInterval)
                else:
                    # try to set mode to regular platoon mode
                    pltn.setModeWithImpatience(PlatoonMode.LEADER, self._controlInterval)
                continue

            # leader vehicle
            leaderID, leaderDist = leaderInfo
            leader = self._connectedVehicles[leaderID]

            # Commented out -> isLastInPlatoon should not be a hindrance to join platoon
            # tryCatchup = leader.isLastInPlatoon() and leader.getPlatoon() != pltn
            # join = tryCatchup and leaderDist <= self._maxPlatoonGap

            # Check if leader is on pltnLeader's route
            # (sometimes a 'linkLeader' on junction is returned by traci.getLeader())
            # XXX: This prevents joining attempts on internal lanes (probably doesn't hurt so much)
            pltnLeaderRoute = traci.vehicle.getRoute(pltnLeader.getID())
            pltnLeaderRouteIx = traci.vehicle.getRouteIndex(pltnLeader.getID())
            leaderEdge = leader.state.edgeID
            if leaderEdge not in pltnLeaderRoute[pltnLeaderRouteIx:]:
                continue

            if leader.getPlatoon() == pltn:
                # Platoon order is corrupted, don't join own platoon.
                continue


            #PLTNMGR2: Check if joining the target platoon would violate the pltn max size constraint
            if self.sizePolicyExists() and leader.getPlatoon().size() + pltn.size() > self.getMaxSize():
                #combined size would be too big, so do nothing
                continue

            if leaderDist <= self._maxPlatoonGap:
                # Try to join the platoon in front
                if leader.getPlatoon().join(pltn):
                    toRemove.append(pltnID)
                    # Debug
                    if rp.VERBOSITY >= 2:
                        report("Platoon '%s' joined Platoon '%s', which now contains " % (pltn.getID(),
                                                                                          leader.getPlatoon().getID()) +
                               "vehicles:\n%s" % str([veh.getID() for veh in leader.getPlatoon().getVehicles()]))
                    continue
                else:
                    if rp.VERBOSITY >= 3:
                        report("Merging of platoons '%s' (%s) and '%s' (%s) would not be safe." %
                               (pltn.getID(), str([veh.getID() for veh in pltn.getVehicles()]),
                                leader.getPlatoon().getID(),
                                str([veh.getID() for veh in leader.getPlatoon().getVehicles()])))
            else:
                # Join failed due to too large distance. Try to get closer (change to CATCHUP mode).
                if not pltn.setMode(PlatoonMode.CATCHUP):
                    if rp.VERBOSITY >= 3:
                        report(("Switch to catchup mode would not be safe for platoon '%s' (%s) chasing " +
                                "platoon '%s' (%s).") %
                               (pltn.getID(), str([veh.getID() for veh in pltn.getVehicles()]),
                                leader.getPlatoon().getID(),
                                str([veh.getID() for veh in leader.getPlatoon().getVehicles()])))

        # remove merged platoons
        for pltnID in toRemove:
            self._platoons.pop(pltnID)



print("platoon Manager2")


