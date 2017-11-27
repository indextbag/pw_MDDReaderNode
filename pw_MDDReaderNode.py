#cmds.deformer(type='mddReader')

import sys
import maya.OpenMaya as om
import maya.OpenMayaAnim as anim
import maya.OpenMayaMPx as ompx
from struct import unpack
import os

kPluginNodeTypeName = "mddReader"

nodeId = om.MTypeId(0x870211)

# Node definition
class pw_mddReaderClass(ompx.MPxDeformerNode):
    # class variables
    time = om.MObject()
    offset = om.MObject()
    cycle = om.MObject()
    fileName = om.MObject()
    # constructor
    def __init__(self):
        ompx.MPxDeformerNode.__init__(self)
        self.last = None

    def postConstructor(self):
        selList = om.MSelectionList()
        selList.add("time1")
        timeNode = om.MObject()
        selList.getDependNode(0, timeNode)
        timeFn = om.MFnDependencyNode(timeNode)

        dgModifier = om.MDGModifier()
        nodeFn = om.MFnDependencyNode(self.thisMObject())
        inTime = nodeFn.findPlug("time")
        outTime = timeFn.findPlug("outTime")
        dgModifier.connect(outTime, inTime)
        dgModifier.doIt()

    # deform
    def deform(self,dataBlock,geomIter,matrix,multiIndex):
        fileName = dataBlock.inputValue(self.fileName).asString()
        time = dataBlock.inputValue(self.time).asInt()
        offset = dataBlock.inputValue(self.offset).asInt() * -1
        cycle = dataBlock.inputValue(self.cycle).asBool()
        envelope = dataBlock.inputValue( ompx.cvar.MPxDeformerNode_envelope ).asFloat()
        if fileName and os.path.exists(fileName):

            fileHandle = open(fileName, 'rb')
            frames, points = unpack('>2i', fileHandle.read(8))
            headerOffset = 8 + (frames * 4)
            #cycle check
            if cycle:
                time = (time+offset)% frames
            else:
                time = time + offset
                if time > frames:time = frames
                elif time < 1:time = 1
            fileHandle.seek(headerOffset + (time * 12 * points))
            pointList = om.MPointArray()

            while not geomIter.isDone():
                srcPt = geomIter.position()
                mddPt = unpack(">3f", fileHandle.read(12))
                if geomIter.index() <= points:
                    mddPt = om.MPoint(mddPt[0], mddPt[1], mddPt[2])
                    weight = self.weightValue( dataBlock, multiIndex, geomIter.index() )
                    #weight = weight
                    #print weight
                    if weight == 0.0:
                        pointList.append( srcPt )
                    elif weight == 1.0:
                        pointList.append( mddPt )
                    else:
                        dirVec = om.MVector(srcPt) - om.MVector(mddPt)
                        dirLen = dirVec.length()
                        factor = dirLen * weight
                        addVec = dirVec * dirLen / factor
                        #addVec = om.MVector(addVec.x * envelope, addVec.y * envelope, addVec.z * envelope, )
                        result = srcPt + addVec
                        pointList.append( om.MPoint(result) )
                else:
                    pointList.append( srcPt )
                geomIter.next()
            #
            #for p in xrange(min(points,geomIter.count())):
            #    weight = self.weightValue( dataBlock, multiIndex, p )
            #    pt = unpack(">3f", fileHandle.read(12))
            #    pointList.append( om.MPoint(pt[0], pt[1], pt[2]) * weight )


            fileHandle.close()
            geomIter.setAllPositions(pointList)

    # creator
    @classmethod
    def nodeCreator(self):
        return ompx.asMPxPtr(self())

    # initializer
    @classmethod
    def nodeInitializer(self):
        nAttr = om.MFnNumericAttribute()
        tAttr = om.MFnTypedAttribute()
        outputGeom = ompx.cvar.MPxDeformerNode_outputGeom

        #time
        self.time = nAttr.create('time', 'tm', om.MFnNumericData.kInt, 0)
        nAttr.setKeyable(True)
        #nAttr.setHidden(True)
        nAttr.setStorable(False)
        self.addAttribute(self.time)
        self.attributeAffects(self.time, outputGeom)
        #offset
        self.offset = nAttr.create('offset', 'ofs', om.MFnNumericData.kInt, 0)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        self.addAttribute(self.offset)
        self.attributeAffects(self.offset, outputGeom)
        #cycle
        self.cycle = nAttr.create('cycle', 'cy', om.MFnNumericData.kBoolean, False)
        nAttr.setKeyable(True)
        nAttr.setStorable(True)
        self.addAttribute(self.cycle)
        self.attributeAffects(self.cycle, outputGeom)
        #fileName
        self.fileName = tAttr.create('fileName', 'fn', om.MFnData.kString)
        tAttr.setStorable(True)
        tAttr.setKeyable(False)
        self.addAttribute(self.fileName)
        self.attributeAffects(self.fileName, outputGeom)


# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.registerNode(kPluginNodeTypeName, nodeId, pw_mddReaderClass.nodeCreator, pw_mddReaderClass.nodeInitializer, ompx.MPxNode.kDeformerNode )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( nodeId )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )

