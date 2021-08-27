# robert.w.thomas3@gmail.com 2021
# using speed factor as a proxy for safety
# vehicles will determine if a potential platoon mate's speed factor is safe enough
# vehicles will monitor potential platoon mate for 60 seconds to assess if
# the advertised speed factor can be trusted, ie the behavior matches the assertion
#
#
# build training sets from netstate, map, and demand files
# X = observed speed factor
# y = is stated speed factor >= observed speed factor? 1 = true, 0 = false
# fit sets to  a model
# pickle the model so that it can be distributed and used "on demand" to assess behavior

from xml.etree import ElementTree
from os import path
import sys
import pickle
from sklearn.ensemble import AdaBoostClassifier
import numpy as np

MapInput = "/home/thomasrw/Model/HPC/home/mape.net.xml"
SpeedDict = "/home/thomasrw/Model/netstate/speed.p" #speed limits from map file

demandInput = "/home/thomasrw/Model/netstate/CAV000_100"
SFDict = "/home/thomasrw/Model/netstate/speedFactor.p" #speed factors from demand file
BadSFDict = "/home/thomasrw/Model/netstate/BADspeedFactor.p" #speed factors from demand file skewed down 0.1

netstateInput = "/home/thomasrw/Model/netstate/CAV000_100_netstate"
#ObsSF = "/home/thomasrw/Model/netstate/obsSF.p"
ObsSF = "/home/thomasrw/Model/netstate/obsSF" #calculated speed factor
BadObsSF = "/home/thomasrw/Model/netstate/BADobsSF"


def createModel():
    pass


def trainModel():
    pass



def buildTrainingSet():
    pass



def assessTrust():
    pass


def createSpeedDict(file=MapInput, saveFile=SpeedDict):
    '''
    Read a SUMO map file and create a dictionary of edges/lanes and speed limit
    Save resulting dictionary as a pickle file

    :param file: SUMO Map File
    :param saveFile: pickle file of resulting Dict object
    :return: dictionary
    '''

    SpeedLimits = dict()
    speed_iter = ElementTree.iterparse(file)

    for event, att in speed_iter:
        #print(att.tag)
        if att.tag == 'lane':
            SpeedLimits[att.attrib['id']] = float(att.attrib['speed'])
            #print(att.attrib['speed'])
        att.clear()

    #print(SpeedLimits)
    pickle.dump(SpeedLimits, open( saveFile, "wb"))
    return SpeedLimits


def getSpeedDict(file=SpeedDict):
    '''
    Read a pickle file and extract the SpeedLimits dictionary of lanes and speed limits

    :param file: pickle file of Dict object containing lanes and speed limits
    :return: dictionary
    '''
    SpeedLimits = pickle.load( open( file, "rb"))
    #print(SpeedLimits)
    return SpeedLimits


def createSF(file=demandInput, save=SFDict):
    '''
    Read SUMO demand file and create dictionary of vehicles and speed factors
    Save resulting dictionary in a pickle file
    :param file: SUMO demand file
    :param save: pickle file for resulting dictionary
    :return: dictionary of vehicle speed factors
    '''
    SF = dict()
    sf_iter = ElementTree.iterparse(file)

    for event, att in sf_iter:
        #print(att.tag)
        if att.tag == 'vehicle':
            SF[att.attrib['id']] = float(att.attrib['speedFactor'])
            #print(att.attrib['speedFactor'])
        att.clear()

    #print(SF)
    pickle.dump(SF, open( save, "wb"))
    return SF

def createBadSF(file=demandInput, save=BadSFDict):
    SF = dict()
    sf_iter = ElementTree.iterparse(file)

    for event, att in sf_iter:
        #print(att.tag)
        if att.tag == 'vehicle':
            #misreport speed factor by -0.1 to "appear safer"
            SF[att.attrib['id']] = float(att.attrib['speedFactor']) - 0.1
            #print(att.attrib['speedFactor'])
        att.clear()

    #print(SF)
    pickle.dump(SF, open( save, "wb"))
    return SF

def getSF(file=SFDict):
    '''
    Read a pickle file and extract the Speed Factor dictionary of vehicles and speed factors

    :param file: pickle file of Dict object containing vehicle id's and speed factors
    :return: dictionary
    '''
    SF = pickle.load( open( file, "rb"))
    #print(SF)
    return SF

def createObservationData(file=netstateInput, speeds=SpeedDict, save=ObsSF, statedSF=SFDict, increment=10000):
    '''

    :param file: SUMO netstate file
    :param speeds: pickle file of Dict object containing lanes and speed limits
    :param save: location + file prefix to save dictionary of calculated ("observed") speed factors
    :param increment: how often to dump observation dict() to avoid exceeding avail memory while processing
    :return: int count of increment files generated
    '''
    rawObs = dict()
    NS_iter = ElementTree.iterparse(file)
    postedLimit = getSpeedDict(speeds)
    lane = ""
    speedLimit = 0.0
    vehSpeedList = dict()
    counter = 0
    partsCounter = 0
    StatedData = getSF(statedSF)
    for event, att in NS_iter:
        #print(event)
        if att.tag == 'vehicle':
            #print(att.attrib['id'])
            #add noise to the speed readings - Saiprasert, C., & Pattara-Atikom, W. (2013). Smartphone enabled
            #dangerous driving report system. International IEEE Conference on System Sciences (HICSS). IEEE.
            vehSpeedList[att.attrib['id']] = float(att.attrib['speed']) + np.random.normal(1.072222, 1.108333)
        if att.tag == 'lane':
            #print(att.attrib['id'])
            limit = postedLimit[att.attrib['id']]
            for veh in vehSpeedList.keys():
                #todo add speed noise
                if veh in rawObs:
                    rawObs[veh].append((vehSpeedList[veh] / limit) / StatedData[veh])
                else:
                    rawObs[veh] = [(vehSpeedList[veh] / limit) / StatedData[veh]]

            #print(rawObs)
            #print("vehlist was - ", vehSpeedList)
            vehSpeedList = dict()  # reset list
            #print("should be blank - ", vehSpeedList)
        if att.tag == 'timestep':
            counter += 1
            if counter >= increment: #take incremental results and reset rawObs
                partsCounter += 1

                part = save + "_" + str(partsCounter) + ".p"
                print(part)
                pickle.dump(rawObs, open(part, "wb"))
                rawObs = dict()
                counter = 0

            print(att.attrib['time'])
            limit = 0.0 #reset limit


        att.clear()
    if counter > 0:
        partsCounter += 1
        part = save + "_" + str(partsCounter) + ".p"
        pickle.dump(rawObs, open(part, "wb"))
        #pickle.dump(rawObs, open(save, "wb"))
    print('Observation Data generated in ', partsCounter, ' pieces')
    return partsCounter

reconstructName = "complete"
def reconstructObservationData(prefix=ObsSF, pieces=8, start=1, name=reconstructName):
    ObsData = dict()
    i = start
    while i <= pieces:
        print(i)
        ObsData.update(pickle.load( open( (prefix + "_" + str(i) + ".p"), "rb")))
        i += 1
    pickle.dump(ObsData, open((prefix +"_" + name + ".p"), "wb"))
    return ObsData

def getObservationData(file):
    data = pickle.load(open(file, "rb"))
    return data



def splitXdata(input, length=600):
    xData = []
    for key in input.keys():
        if len(input[key]) >=length:
            #xData = [input[key][x:x+length] for x in range(0, (len(input[key]) - length), length)]
            xData.append( [input[key][x:x + length] for x in range(0, (len(input[key]) - length), length)])
    #print(xData)
    return xData

'''
1. create parts with:
createSpeedDict()
createSF()
createBadSF()
createObservationData()
createObservationData(netstateInput, SpeedDict, BadObsSF, BadSFDict, 10000)
2. create observation test files with
reconstructObservationData(ObsSF,8,2,"testGood")
reconstructObservationData(BadObsSF,8,2,"testBad")
3. create test sets ready for SVM ingestion
mydata = ObsSF + "_1.p"
mydict = getObservationData(mydata)
myX = splitXdata(mydict)
Xvert = []
Yvert = []
for veh in myX:
    for vert in veh:
        Xvert.append(vert)
        Yvert.append(1) #1 for good samples
myX = []
mydata = BadObsSF + "_1.p"
mydict = getObservationData(mydata)
myX = splitXdata(mydict)
for veh in myX:
    for vert in veh:
        Xvert.append(vert)
        Yvert.append(0) #0 for bad samples
4. train model on _1.p sets
clf = AdaBoostClassifier()
clf.fit(Xvert, Yvert)
5. load model and use to project good data

6. load model and use to project bad data #memory errors if try to combine both sets

'''
#createSpeedDict()
#getSpeedDict()

#createSF()
#getSF()
#createBadSF()

#createObservationData()
#def createObservationData(file=netstateInput, speeds=SpeedDict, save=ObsSF, statedSF=SFDict, increment=10000):
#createObservationData(netstateInput, SpeedDict, BadObsSF, BadSFDict, 10000)
print('trust.py loaded ok')
#reconstructObservationData()
#reconstructObservationData(BadObsSF)
#def reconstructObservationData(prefix=ObsSF, pieces=8, start=1, name=reconstructName):
#reconstructObservationData(ObsSF,8,2,"testGood")
#reconstructObservationData(BadObsSF,8,2,"testBad")
#print("reconstruct complete")


'''

#mydata = ObsSF + "_1.p"
#mydata = BadObsSF + "_1.p"
#mydata = ObsSF + "_complete.p"
#mydata = ObsSF + "_testGood.p"
mydata = BadObsSF + "_testBad.p"
#print(getObservationData(mydata))
mydict = getObservationData(mydata)
print(len(mydict))
for key in mydict.keys():
    pass#print(len(mydict[key]))

myX = splitXdata(mydict)
print("myX is ", len(myX))
for ea in myX:
    pass#print(len(ea[0]))


#pickle.dump(myX, open("/home/thomasrw/Model/netstate/myX.p", "wb"))
'''
'''
print("ok for good data, starting bad")
#mybad =BadObsSF + "_1.p"
#mybad =BadObsSF + "_complete.p"
mybad = BadObsSF + "_testBad.p"


mybaddict = getObservationData(mybad)
myBX = splitXdata(mybaddict)
print("myBX is ", len(myBX))

pickle.dump(myBX, open("/home/thomasrw/Model/netstate/myBX.p", "wb"))
'''
'''
print("loading myX")
#myX = pickle.load(open("/home/thomasrw/Model/netstate/myX.p", "rb"))

#print(len(myX[0]))
#print(len(myX[0][0]))
#for ea in myX[0]:
#    print(len(ea))

Xvert = []
Yvert = []
for veh in myX:
    for vert in veh:
        Xvert.append(vert)
        #Yvert.append(1) #1 for good samples
        Yvert.append(0) #0 for bad samples

        #print(Xvert[len(Xvert)-1])
#print(len(Xvert))
#print(Yvert)
print("length of data is: ", len(Yvert))


'''
'''
print("reset myX after data loaded to conserve memory")
myX = []
#mydata = BadObsSF + "_1.p"
mydata = BadObsSF + "_testBad.p"

mydict = getObservationData(mydata)
print(len(mydict))
for key in mydict.keys():
    pass#print(len(mydict[key]))

myX = splitXdata(mydict)
print("myX is ", len(myX))
for ea in myX:
    pass#print(len(ea[0]))

for veh in myX:
    for vert in veh:
        Xvert.append(vert)
        Yvert.append(0) #0 for bad samples
        #print(Xvert[len(Xvert)-1])
#print(len(Xvert))
#print(Yvert)
print("length of combined data is: ", len(Yvert))
quit()

print("data ready... begin fit")
#clf = AdaBoostClassifier()
#clf.fit(Xvert, Yvert)

#pickle.dump(clf, open("/home/thomasrw/Model/netstate/clf.p", "wb"))
quit()
'''


'''
myBX = pickle.load(open("/home/thomasrw/Model/netstate/myBX.p", "rb"))

for veh in myBX:
    for vert in veh:
        Xvert.append(vert)
        Yvert.append(0)

print("number of items: ",len(Xvert))
'''

'''
#print(len(Yvert))
#print("data ready... begin fit")
#clf = AdaBoostClassifier()
#clf.fit(Xvert, Yvert)

#pickle.dump(clf, open("/home/thomasrw/Model/netstate/clf.p", "wb"))
#print("data fit complete, run predictions...")

'''
'''
clf = pickle.load(open("/home/thomasrw/Model/netstate/clf.p", "rb"))

Xtest = np.reshape( Xvert[0], (1, -1))
print("should be 1: ", clf.predict(Xtest))

Xtest2 = np.reshape(Xvert[48060], (1, -1))
print("should be 0: ", clf.predict(Xtest2))
#clf.score(Xvert, Yvert)

falsePOS = 0
falseNEG = 0
trueRead = 0
for x in range(0,len(Xvert)):
    Xtest = np.reshape(Xvert[x], (1, -1))
    if clf.predict(Xtest)[0] != Yvert[x] and Yvert[x] == 1:
        falsePOS += 1 #Classified as bad when really ok
        print("false POS", falsePOS)
    elif clf.predict(Xtest)[0] != Yvert[x] and Yvert[x] == 0:
        falseNEG += 1 #Classified as ok when not really
        print("false NEG", falseNEG)
    else:
        trueRead += 1

print("False POS: ", falsePOS, " " ,falsePOS/len(Xvert) , "%")
print("False NEG: ", falseNEG, " " ,falseNEG/len(Xvert) , "%")
print("True: ", trueRead, " " ,trueRead/len(Xvert) , "%")

'''