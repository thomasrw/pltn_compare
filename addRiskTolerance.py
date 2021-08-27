
#todo convert to add prefix for risk tolerance H | M | L
#todo input is a file name (full path)
#todo output is input+rt [risk tolerance]

from xml.etree import ElementTree
import os.path
from os import path
import sys
import random

myfile='/home/thomasrw/Model/netstate/CAV000_100'
#myfile = sys.argv[1]

def addTolerance(file=myfile):
    '''
    add risk tolerance to vehicle specification via naming convention prefix of H | M | L for high, medium, low
    roughly follows nomral distribution - 16% low risk, 68% medium, 16% high
    :param file: demand file needing risk tolerance added
    :return: file_rt demand file with augmented vehicle specifications to include risk tolerance indicator in naming
    convention
    '''

    tree = ElementTree.parse(file)
    root = tree.getroot()

    for att in root:
        prefix = ''
        if att.tag == 'vehicle':
            pick = round(random.random(), 2)
            if pick <= 0.16:
                prefix = 'L'
            elif pick <= 0.84:
                prefix = 'M'
            else:
                prefix = 'H'

        id = att.get('id')
        id = prefix + id
        att.set('id', id)
        print('updated', id)

    newfile = file + 'rt'
    tree.write(newfile)




def format(target, percent):
    tree =ElementTree.parse(target)
    root = tree.getroot()
    #root.tag = "additional"
    #root.attrib = None
    #for att in root:
    #    att.set('departSpeed', 'max')
    b = ElementTree.SubElement(root, 'vType')
    b.set('id', 'CAV_VEHTYPE')
    b.tail = '\n'

    # sort so vtypes come first. vtypes must be defined before vehicles that use them
    root[:] = sorted(root, key=lambda child: (child.tag,child.get('name')))

    for att in root:
        if att.tag == 'vehicle':
            if random.randrange(100) + 1 <= int(percent):
                #change type to connected type specified in mysimpla.cfg.xml
                att.set('type', 'CAV_VEHTYPE')
                #add discriminator for joining strategy when using adhoc platoon game based on %results
                #from paper:
                #Cooperator 22% [1-22]
                #Defector 16% [23-38]
                #TitForTat 23% [39-61]
                #Grudger 23% [62-84]
                #Random(0.5) 16% [85-100]

                pick = random.randrange(100) + 1 #needs new rand to that full range of strategy considered
                if pick <= 22:
                    id = att.get('id')
                    id = 'coop' + id
                    att.set('id', id)

                elif pick <=38: #<=22 would have already been selected if true
                    id = att.get('id')
                    id = 'def' + id
                    att.set('id', id)
                elif pick <= 61:
                    id = att.get('id')
                    id = 'tft' + id
                    att.set('id', id)
                elif pick <= 84:
                    id = att.get('id')
                    id = 'grud' + id
                    att.set('id', id)
                else:
                    id = att.get('id')
                    id = 'rand' + id
                    att.set('id', id)

    #todo clean so not dependent on sys.argv[1] (number)
    myfile = mypath + "CAV" + str(percent).zfill(3) + '_' + str(number)
    tree.write(myfile)

print('addRiskTolerance loaded')
addTolerance()

'''
mytarget = mypath + "CAV000" + '_' + str(number)
#format(mytarget, mypercent)

for i in range(100):
    format(mytarget, i+1)
    print(str(i) + " complete")

print("success for " + mytarget)
'''


