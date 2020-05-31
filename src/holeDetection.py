import copy
from datetime import datetime
import FreeCAD
from FreeCAD import Base
import FreeCADGui
import Part

###
bColorFaces = False
bWriteReport = True
reportFilePath = "D:/projects/current/freeCAD/cikoni/"
###
threadRadius = [1.60,1.75,2.05,2.50,2.90,3.30,3.70,4.20,5.00,6.00,6.80,7.80,8.50,9.50,10.20,12.00,14.00,15.50]

def IsClosedCurve(iEdge):
    param1 = iEdge.FirstParameter
    param2 = iEdge.LastParameter
    curve = iEdge.Curve
    value1 = curve.value(param1)
    value2 = curve.value(param2)
    dist = value1.distanceToPoint(value2)
    if dist < 1E-6:
        return True
    return False

def GetAxisOfBspline(iCurve):
    param1 = iCurve.FirstParameter
    param2 = (iCurve.FirstParameter+iCurve.LastParameter)*0.5
    value1 = iCurve.value(param1)
    value2 = iCurve.value(param2)
    crossProd = value1.cross(value2)
    crossProd.normalize()
    return crossProd

def GetCenterOfBspline(iCurve):
    points = iCurve.discretize(Number=10)
    center = FreeCAD.Vector(0,0,0)
    for point in points:
        center = center + point
    center = center / len(points)
    return(center)

def GetBoundaryEdges(iFace):
    edges = iFace.Edges

def AskFacesFromEdge(iEdge, iShape):
    allFaces = iShape.Faces
    selFaces = []
    for face in allFaces:
        edges = face.Edges
        for edge in edges:
            if edge.isSame(iEdge) == True:
                selFaces.append(face)
    
    return selFaces

# Groups split cylinder boundary into edge sets 
# Every edge set represents the boundary of cylinder
def GroupEdgeSets(holeFaces):
    edgeSets = []
    allEdges = []
    for face in holeFaces:
        # Part.show(face)
        if (str(face.Surface) in "<Cylinder object>"):
            edges = face.Edges
            for edge in edges:
                isPresent = False
                for allEdge in allEdges:
                    if edge.isSame(allEdge):
                        isPresent = True
                if isPresent == False:
                    # check if it is a circle
                    if(IsClosedCurve(edge) == True):
                        allEdges.append(edge)
                    else:
                        pnts =  edge.discretize(3)
                        vec1 = pnts[0] - pnts[1]
                        vec2 = pnts[2] - pnts[1]
                        v1CrossV2 = vec1.cross(vec2)
                        if v1CrossV2.Length > 1E-3: # not coliner
                            allEdges.append(edge)
    
    sortedEdgeSets =  Part.sortEdges(allEdges)
    
    filteredEdgeSets = sortedEdgeSets
    if(len(filteredEdgeSets) > 2):
        filteredEdgeSets = []
        holeAxis = holeFaces[0].Surface.Axis
        # filter edges ets not parallel to hole axis
        nPoints = 10
        for edgeSet in sortedEdgeSets:
            bSelect = True
            edgeSetPoints = []
            for tedge in edgeSet:
                disPoints = tedge.discretize(nPoints)
                edgeSetPoints.extend(disPoints)
            nPoints = len(edgeSetPoints)
            idx1 = int(nPoints*0.25)
            idx2 = int(nPoints*0.5)
            idx3 = int(nPoints*0.75)
            pnt1 = edgeSetPoints[idx1]
            pnt2 = edgeSetPoints[idx2]
            pnt3 = edgeSetPoints[idx3]
            v1 = pnt1 - pnt2
            v2 = pnt3 - pnt2
            normal = v1.cross(v2)
            normal.normalize()
            # c,normal = fitPlaneLTSQ(npPoints)
            fDot = abs(holeAxis.dot(normal))
            if (fDot > 0.75):
                filteredEdgeSets.append(edgeSet)
        
        # for tses in filteredEdgeSets:
        #     for te in tses:
        #         Part.show(te)
    
    radius = holeFaces[0].Surface.Radius
    toll = radius*0.1
    # print("Sorted edges :",sortedEdges)
    edgeGroups = []
    for i in range(0,len(filteredEdgeSets)):
        aEdgeSet = filteredEdgeSets[i]
        bGrouped = False
        if len(aEdgeSet) == 1:
            checkEdge = aEdgeSet[0]
            if(IsClosedCurve(checkEdge) == True):
                bGrouped = True
        elif len(aEdgeSet) == 2:
            checkEdge1 = aEdgeSet[0]
            checkVerts1 = checkEdge1.Vertexes
            checkEdge2 = aEdgeSet[1]
            checkVerts2 = checkEdge2.Vertexes
            if(checkVerts1[0].Point.distanceToPoint(checkVerts2[0].Point) < toll or checkVerts1[0].Point.distanceToPoint(checkVerts2[1].Point) < toll):
                if(checkVerts1[1].Point.distanceToPoint(checkVerts2[0].Point) < toll or checkVerts1[1].Point.distanceToPoint(checkVerts2[1].Point)):
                    bGrouped = True
        elif len(aEdgeSet) > 2:
            for j in range (0,len(aEdgeSet)):
                neighs = 0
                checkEdge = aEdgeSet[j]
                checkVerts = checkEdge.Vertexes
                for k in range (0,len(aEdgeSet)):
                    currEdge = aEdgeSet[k]
                    if(checkEdge.isEqual(currEdge) == False):
                        currVerts = currEdge.Vertexes
                        if(checkVerts[0].Point.distanceToPoint(currVerts[0].Point) < toll or checkVerts[0].Point.distanceToPoint(currVerts[1].Point) < toll or checkVerts[1].Point.distanceToPoint(currVerts[0].Point) < toll or checkVerts[1].Point.distanceToPoint(currVerts[1].Point) < toll ):
                            neighs = neighs + 1
                if neighs > 1:
                    bGrouped = True
                else:
                    bGrouped = False
                    break
        
        if bGrouped == True:
            edgeGroups.append(aEdgeSet)
    
    # for tses in edgeGroups:
    #     for te in tses:
    #         Part.show(te)
    
    return edgeGroups



def EvaluateHole(aFace, aShape):
    isHole = False
    edges = aFace.Edges
    holeCenter = FreeCAD.Vector(0.0,0.0,0.0)
    holeAxis = FreeCAD.Vector(0.0,0.0,0.0)
    axisList = []
    holeFaces = []
    boundaryEdges = []
    
    # 1 check
    # if the boundary edges are closed, the face is a hole
    bIsClosedCurve = True
    isHole = True
    for edge in edges:
        curve = edge.Curve
        if(IsClosedCurve(edge) == False):
            # Part.show(edge)
            bIsClosedCurve = False
            isHole = False
            break
    if (bIsClosedCurve == True):
        holeCenter = aFace.CenterOfMass
        holeAxis = aFace.Surface.Axis
        holeFaces.append(aFace)
    
    # 2 check
    # could be a sectioned cylinder
    # Collect group of faces contributing to hole
    if bIsClosedCurve == False and isHole == False: 
        aSurf = aFace.Surface
        edges = aFace.Edges
        for edge in edges:
            commonfaces = AskFacesFromEdge(edge, aShape)
            for cface in commonfaces:
                cSurf = cface.Surface
                if (str(cSurf) in "<Cylinder object>"):
                    if aFace.Surface.Center.distanceToPoint(cface.Surface.Center) < 1E-3:
                        isAdded = False
                        for hf in holeFaces:
                            if hf.isEqual(cface) == True:
                                isAdded = True
                        if isAdded == False:
                            holeFaces.append(cface)
        
        if len(holeFaces) > 0:
            holeAxis = FreeCAD.Vector(0,0,0)
            for hf in holeFaces:
                holeAxis = holeAxis + hf.Surface.Axis
            holeAxis = holeAxis/len(holeFaces)
        else:
            print("Cannot find hole faces")
            return holeFaces
        
        isHole = False
        boundaryEdges =  GroupEdgeSets(holeFaces)
        holeCenter = FreeCAD.Vector(0,0,0)
        if len(boundaryEdges) > 1:
            for eg in boundaryEdges:
                edgeSetPoints = []
                nPoints = 10
                totalArcLen = 0.0
                for tedge in eg:
                    disPoints = tedge.discretize(nPoints)
                    edgeSetPoints.extend(disPoints)
                pntCenter = FreeCAD.Vector(0,0,0)
                for pnt in edgeSetPoints:
                    pntCenter = pntCenter + pnt
                pntCenter = pntCenter / len(edgeSetPoints)
                holeCenter = holeCenter + pntCenter
            holeCenter = holeCenter / len(boundaryEdges)
            # sp = Part.makeSphere(0.1,Base.Vector(holeCenter.x,holeCenter.y,holeCenter.z))
            # Part.show(sp)
            isHole = True
    
    if isHole == False:
        print("check 2 : Not a hole ")
        del holeFaces[:]
        return holeFaces
    
    # 3 check
    # line intersection with the shape
    # line passes through hole center
    # length of line is holeFaces diagonal
    # if line does not intersect, the face is a hole
    
    lineLength = aShape.BoundBox.DiagonalLength
    faceBB = FreeCAD.BoundBox(0.0,0.0,0.0,0.0,0.0,0.0)
    for hf in holeFaces:
        hfBB = hf.BoundBox
        faceBB.add(hfBB)
    lineLength = faceBB.DiagonalLength
    
    p1 = FreeCAD.Vector(0,0,0)
    p2 = FreeCAD.Vector(0,0,0)
    aVec = holeAxis
    aVec.normalize()
    p1 = holeCenter - aVec.multiply(lineLength)
    aVec = holeAxis
    aVec.normalize()
    p2 = holeCenter + aVec.multiply(lineLength)
    
    line=Part.makeLine(p1,p2)
    # Part.show(line)
    
    # estimate intersection
    intersect = aShape.common(line)
    nLeft = 0
    nRight = 0
    
    interPoints = []
    for inVert in intersect.Vertexes:
        point = inVert.Point
        interPoints.append(point)
    
    isHole = True
    if len(interPoints) > 0:
        dir = interPoints[0] - holeCenter
        for intPnt in interPoints:
            vec = intPnt - holeCenter
            if vec.dot(dir) < 0.0:
                nLeft = nLeft + 1
            else:
                nRight = nRight + 1
        
        if(nLeft > 0 and nRight > 0): 
            # intersect happened both sides
            # propably a closed tube
            isHole = False
    
    if isHole == False:
        print("check 3 : Not a hole ")
        del holeFaces[:]
        return holeFaces
    radius = aFace.Surface.Radius
    nPnts = 10
    
    # check 4
    # Eliminate outer faces 
    if bIsClosedCurve == False:
        isHole = True
        boundaryVert =  boundaryEdges[0][0].Vertexes[0]
        cLine = Part.makeLine(holeCenter,boundaryVert.Point)
        # Part.show(cLine)
        cIntersect = aShape.common(cLine)
        if len(cIntersect.Vertexes) > 0:
            isHole = False
        
        if isHole == False:
            print("check 4 : Not a hole ")
            del holeFaces[:]
            return holeFaces
    
    # # check 5
    # # see if it is fillet
    # # draw a circle at the center and discritize to points
    # # if all points intersect, the face is a hole 
    # if bIsClosedCurve == False:             
    #     radius = aFace.Surface.Radius
    #     nPnts = 10
    #     bcircle = Part.makeCircle(radius*1.01, Base.Vector(holeCenter.x,holeCenter.y,holeCenter.z), Base.Vector(holeAxis.x,holeAxis.y,holeAxis.z))
    #     bcircPnts = bcircle.discretize(nPnts)
    #     # print("circPnts : ",circPnts)
    #     # Part.show(ccircle)
    #     isHole = True
    #     for c in range(0,nPnts):
    #         next = c + 1
    #         if next >= nPnts:
    #             next = 0      
    #         if bcircPnts[c].distanceToPoint(bcircPnts[next]) > 1E-3:
    #             aLine = Part.makeLine(bcircPnts[c],bcircPnts[next])
    #             Part.show(aLine)
    #             # print("Circe segment ",c)
    #             intersect = aShape.common(aLine)
    #             if len(intersect.Vertexes) == 0:
    #                 isHole = False
    #         if isHole == False:
    #             break
    
    #     if isHole == False:
    #         print("check 5 : Not a hole ")
    #         del holeFaces[:]
    #         return holeFaces
    
    return holeFaces

def ComputeHoleParameters(holeFaces):
    
    # Length and center
    boundaryEdges =  GroupEdgeSets(holeFaces)
    holeCenter = FreeCAD.Vector(0,0,0)
    boundaryCenters = []
    length = 0.0
    if len(boundaryEdges) > 1:
        for es in boundaryEdges:
            edgeSetPoints = []
            nPoints = 10
            for tedge in es:
                disPoints = tedge.discretize(nPoints)
                edgeSetPoints.extend(disPoints)
            pntCenter = FreeCAD.Vector(0,0,0)
            for pnt in edgeSetPoints:
                pntCenter = pntCenter + pnt
            pntCenter = pntCenter / len(edgeSetPoints)
            boundaryCenters.append(pntCenter)
            holeCenter = holeCenter + pntCenter
        holeCenter = holeCenter / len(boundaryEdges)
        length = boundaryCenters[0].distanceToPoint(boundaryCenters[1])
    if len(boundaryEdges) > 2:
        length = holeFaces[0].Length
    
    # Radius
    radius = holeFaces[0].Surface.Radius
    # print("Radius : " ,radius)
    
    return length, radius*2.0, holeCenter

def IsRightIncrement(diameter):
    number_dec = diameter%1.0
    increment = 0.1 if diameter < 10.0 else 0.5
    mod = number_dec % increment
    if mod < 1E-6:
        return True
    else:
        res = abs(mod-increment)
        if res < 1E-3:
            return True
        else:
            return False

def GetHoleColor(is_grt_2,is_right_increment,l_by_d):
    
    colors = ["green","yellow","orange"]
    
    selectedColorIdx = 0
    if(l_by_d <= 5.0):
        selectedColorIdx = 0
        if is_grt_2 == False:
            selectedColorIdx = selectedColorIdx + 1
        if is_right_increment == False:
            selectedColorIdx = selectedColorIdx + 1
        
    elif(l_by_d > 5.0 and l_by_d < 8.0):
        selectedColorIdx = 1
        if is_grt_2 == False:
            selectedColorIdx = selectedColorIdx + 1
        elif is_right_increment == False:
            selectedColorIdx = selectedColorIdx + 1
    
    elif(l_by_d >= 8.0):
        selectedColorIdx = 2
    
    return colors[selectedColorIdx]

def GetHoleFaceIdx(aFace, allHoles):
    for h in range (0,len(allHoles)):
        hFaces = allHoles[h]
        for hFace in hFaces:
            if aFace.isEqual(hFace):
                return h
    return -1

def GetExpectedThreads(holeRadiusList):
    nThreads = 0
    for r in holeRadiusList:
        for tr in threadRadius:
            if abs(tr-r) < 1E-3:
                nThreads = nThreads + 1
    return nThreads


# get the active document
doc = FreeCAD.ActiveDocument
# objects present in the doc
objects = doc.Objects

# values for the report
nHoles = 0 # number of holes
nGreen = 0 # number of green holes
nYellow = 0 # number of yellow holes
nOrange = 0 # number of Orange holes
nOffStandard = 0 # number of non standard holes
nholes_l_d_lessEq_5 = 0 # number of holes l/d <= 5.0
nholes_l_d_between_5_8 = 0 # number of holes 5.0 < l/d < 8.0
nholes_l_d_great_8 = 0 # number of holes l/d >= 8.0
HoleParams = []
color_dict = {'green':(0.0,1.0,0.0), 'yellow':(1.0,1.0,0.0), 'orange':(1.0,0.647,0.0)}

# loop thorugh all objects
for obj in objects:
    if("Part::PartFeature" in str(obj)):
        parentColor = obj.ViewObject.DiffuseColor
        aShape = obj.Shape
        aShape.removeSplitter()
        shapeType = aShape.ShapeType
        allHoles = []
        if(shapeType == 'Solid'): # only for solid
            # Find hole faces 
            faces = aShape.Faces
            # face = faces[6]
            for face in faces: 
                isHole = False
                isEvaluatedBefore = False
                # make sure the face is not already detected as hole
                for hFaces in allHoles:
                    for hFace in hFaces:
                        if face.isEqual(hFace):
                            isHole = True
                            isEvaluatedBefore = True
                            break
                
                if isEvaluatedBefore == False:                  
                    holeFaces = []
                    surf = face.Surface
                    wires = face.Wires
                    nWires = len(wires)
                    if (str(surf) in "<Cylinder object>"):
                        holeFaces = EvaluateHole(face,aShape)
                        if(len(holeFaces) > 0):
                            isHole = True
                            allHoles.append(holeFaces)
            print("Number of holes found : ", len(allHoles))
            
            # Hole parameters for the report 
            for aHole in allHoles:
                length, diameter , holeCenter= ComputeHoleParameters(aHole)
                l_by_d = length/diameter
                is_grt_2 =  True if diameter > 2.0 else False
                is_right_increment = IsRightIncrement(diameter)
                holeColor = GetHoleColor(is_grt_2,is_right_increment,l_by_d)
                HoleParams.append([length,diameter,holeCenter,is_right_increment,holeColor])
                
                nHoles = nHoles + 1
                if (holeColor == 'green'):
                    nGreen = nGreen + 1 
                elif (holeColor == 'yellow'):
                    nYellow = nYellow + 1
                elif (holeColor == 'orange'):
                    nOrange = nOrange + 1
                if (is_right_increment == False):
                    nOffStandard = nOffStandard + 1
                if(l_by_d <= 5.0):
                    nholes_l_d_lessEq_5 = nholes_l_d_lessEq_5 + 1
                elif(l_by_d > 5.0 and l_by_d < 8.0):
                    nholes_l_d_between_5_8 = nholes_l_d_between_5_8 + 1
                elif(l_by_d >= 8.0):
                    nholes_l_d_great_8 = nholes_l_d_great_8 + 1
            
            if bColorFaces == True:
                # Set face color in FreeCAD Gui
                colors = []
                faces = aShape.Faces
                for face in faces: 
                    idx = GetHoleFaceIdx(face,allHoles)
                    if idx != -1:
                        hc = HoleParams[idx][4]
                        colors.append(color_dict.get(hc))
                    else:
                        colors.append(parentColor[0])
                
                obj.ViewObject.DiffuseColor = colors
            
            radiusList = [radius[1] for radius in HoleParams]
            nThreads = GetExpectedThreads(radiusList)
            print("Nthreads :", nThreads)
            if bWriteReport == True:
                # write report            
                reportName = datetime.today().strftime('%Y%m%d')+"_"+obj.Label+"_report.txt"
                reportFile = reportFilePath + reportName
                report = open(reportFile,"w")
                report.write('Name : {}\n'.format(reportName))
                report.write('Total number of holes: Nt = {}\n'.format(nHoles))
                report.write('Number of expected threads: Y = {}\n'.format(nThreads))
                report.write('Number of standard holes: X = {}\n'.format(nHoles-nThreads))
                report.write('Number of green holes: Ng = {}\n'.format(nGreen))
                report.write('Number of yellow holes: Ny = {}\n'.format(nYellow))
                report.write('Number of orange holes: No = {}\n'.format(nOrange))
                report.write('Number of holes with off-standard diameter: Nn = {}\n'.format(nOffStandard))
                report.write('Number of holes with L <= 5d: L0 = {}\n'.format(nholes_l_d_lessEq_5))
                report.write('Number of holes with 5d < L < 8d: L5 = {}\n'.format(nholes_l_d_between_5_8))
                report.write('Number of holes with L > 8d: L8 = {}\n'.format(nholes_l_d_great_8))
                report.write("\n")
                report.write("Detected holes:\n")
                h = 0
                report.write("# Hole position (xyz) length_1 Diameter_1 L/D Y/N (right increment/std) hole_color\n")
                for param in HoleParams:
                    center = param[2]
                    l_by_d = param[0] / param[1]
                    right_increment = 'Y' if param[3] else 'N'
                    line = '{} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {} {}\n'.format(h,round(center.x,2), round(center.y,2), round(center.z,2), round(param[0],2), round(param[1],2), round(l_by_d,2), right_increment, param[4])
                    report.write(line)
                    h = h + 1
            report.close()
        else:
            print("Not a solid") 