import copy
import FreeCAD
import FreeCADGui
import Part

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

def EvaluateHole(aFace, aShape):
    isHole = False
    edges = aFace.Edges
    curves = []
    centerList = []
    axisList = []
    holeFaces = []
    for edge in edges:
        curve = edge.Curve
        if(IsClosedCurve(edge)):
            # print("Is closed curve true")
            curves.append(curve)
            center = FreeCAD.Vector(0,0,0)
            axis = FreeCAD.Vector(1,0,0)
            if "BSpline" in str(curve):
                center = GetCenterOfBspline(curve)
                axis = GetAxisOfBspline(curve)
            else:
                center = curve.centerOfCurvature(0)
                axis = curve.Axis
            axisList.append(axis)
            centerList.append(center)
            isHole = True
    
    if isHole == True:
        holeFaces.append(aFace)
    
    else: # could be a sectioned cylinder
        # If neighbour faces are also cylinder
        # it is a hole
        edges = aFace.Edges
        for edge in edges:
            faces = AskFacesFromEdge(edge, aShape)
            for face in faces:
                if face.isSame(aFace):
                    continue
                surf = face.Surface
                if (str(surf) in "<Cylinder object>"):
                    aSurf = aFace.Surface
                    if aSurf.Axis.isEqual(surf.Axis,1E-3) == True:
                        isFound = False
                        for hf in holeFaces:
                            if hf.isEqual(face) == True:
                                isFound = True
                        if isFound == False:
                            holeFaces.append(face)
        if len(holeFaces) > 0:
            holeFaces.append(aFace)
            # print("Sectioned cylinder with ", len(holeFaces))
            isHole = True
    
    if isHole == False:
        return holeFaces
    
    if len(centerList) > 0:
        # filter unique centers
        centerListCopy = copy.deepcopy(centerList)
        centerList.clear()
        for cc in centerListCopy:
            found = False
            for c in centerList:
                if cc.distanceToPoint(c) < 1E-3:
                    found = True
                    break
            if found == False :
                centerList.append(cc)
    else:
        centerList.append(aFace.Surface.Center)
        axisList.append(aFace.Surface.Axis)
    print("centerList :",centerList)
    print("axisList :",axisList)
    
    # line intersection with the shape
    # line passes through centers
    # length of line is shape diagonal
    
    # estimating shape diagonals from bounding box
    lineLength = aShape.BoundBox.DiagonalLength
    
    holeCenter = FreeCAD.Vector(0,0,0)
    for c in centerList:
        holeCenter = c.add(holeCenter)
    holeCenter.multiply(1.0/len(centerList))
    
    holeAxis = FreeCAD.Vector(0,0,0)
    for a  in axisList:
        holeAxis = a.add(holeAxis)
    holeAxis.multiply(1.0/len(axisList))
    
    p1 = FreeCAD.Vector(0,0,0)
    p2 = FreeCAD.Vector(0,0,0)
    if(len(centerList) > 1):
        vecP12 = centerList[1] - centerList[0]
        vecP12.normalize()
        p1 = centerList[0] - vecP12.multiply(lineLength)
        
        vecP12 = centerList[1] - centerList[0]
        vecP12.normalize()
        p2 = centerList[1] + vecP12.multiply(lineLength)
    
    else:
        aVec = axisList[0]
        aVec.normalize()
        p1 = centerList[0] - aVec.multiply(lineLength)
        aVec = axisList[0]
        aVec.normalize()
        p2 = centerList[0] + aVec.multiply(lineLength)
    
    line=Part.makeLine(p1,p2)
    # Part.show(line)
    
    # estimate intersection
    intersect = aShape.common(line)
    nLeft = 0
    nRight = 0
    avgCenter = FreeCAD.Vector(0,0,0)
    for c in centerList:
        avgCenter = avgCenter + c
    avgCenter = avgCenter / len(centerList)
    
    interPoints = []
    for inVert in intersect.Vertexes:
        point = inVert.Point
        interPoints.append(point)
    
    if len(interPoints) > 0:
        dir = interPoints[0] - avgCenter
        for intPnt in interPoints:
            vec = intPnt - avgCenter
            if vec.dot(dir) < 0.0:
                nLeft = nLeft + 1
            else:
                nRight = nRight + 1
        
        if(nLeft > 0 and nRight > 0): 
            # intersect happened both sides
            # propably a closed tube
            print("Closed tube")
            holeFaces.clear()
            isHole = False
    else:
        isHole = True
    
    if isHole == True:
        edges = aFace.Edges
        for edge in edges:
            pnts = edge.discretize(3)
            vec1 = pnts[0] - pnts[1]
            vec1.normalize()
            vec2 = pnts[2] - pnts[1]
            vec2.normalize()
            crossProd = vec1.cross(vec2)
            print("Cross prod :", crossProd)
            if crossProd.Length < 1E-3:
                line=Part.makeLine(pnts[1],avgCenter)
                intersect = aShape.common(line)
                if len(intersect.Vertexes) > 0:
                    holeFaces.clear()
                    isHole = False
                    break
    
    return holeFaces

def ComputeHoleParameters(holeFace):
    holeSurf = holeFace.Surface
    
    # Length
    centerList = []
    edges = face.Edges
    for edge in edges:
        curve = edge.Curve
        if(IsClosedCurve(edge)):
            center = FreeCAD.Vector(0,0,0)
            if "BSpline" in str(curve):
                center = GetCenterOfBspline(curve)
            else:
                center = curve.centerOfCurvature(0)
            centerList.append(center)
    
    length = holeFace.Length
    if len(centerList) > 1:
        length = (centerList[1] - centerList[0]).Length
        
    # print("Length : " ,length)
    
    # Radius
    radius = holeSurf.Radius
    # print("Radius : " ,radius)
    
    return length, radius*2.0

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
color_dict = {'green':(0.0,1.0,0.0), "yellow":(1.0,1.0,0.0), "orange":(1.0,0.647,0.0)}

# loop thorugh all objects
for obj in objects:
    if("Part::PartFeature" in str(obj)):
        parentColor = obj.ViewObject.DiffuseColor
        colors = []
        aShape = obj.Shape
        aShape.removeSplitter()
        shapeType = aShape.ShapeType
        allHoles = []
        if(shapeType == 'Solid'): # only for solid
            faces = aShape.Faces
            for face in faces: 
                isHole = False
                isEvaluatedBefore = False
                # make sure the face is not already detected as hole
                for fHole in allHoles:
                    for hFace in fHole:
                        if face.isEqual(hFace):
                            isHole = True
                            isEvaluatedBefore = True
                
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
                            # print("Evaluated hole faces ", holeFaces)
                
                holeColor = 'green'
                if isHole == True:
                    length, diameter = ComputeHoleParameters(face)
                    l_by_d = length/diameter
                    is_grt_2 =  True if diameter > 2.0 else False
                    is_right_increment = IsRightIncrement(diameter)
                    holeColor = GetHoleColor(is_grt_2,is_right_increment,l_by_d)
                    # print("Hole color :", holeColor)
                    colors.append(color_dict.get(holeColor))
                else:
                    colors.append(parentColor[0])
                    continue
                
                if isEvaluatedBefore == False:
                    center = face.Surface.Center
                    HoleParams.append([length,diameter,center,is_right_increment,holeColor])
                    
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
                
        print("Holes :", allHoles)
        print("Holes Found :", len(allHoles))
        obj.ViewObject.DiffuseColor = colors
        
        # write report
        reportFile = "D:\\projects\\current\\freeCAD\\cikoni\\report.txt"
        report = open(reportFile,"w")
        report.write('Total number of holes: Nt = {}\n'.format(nHoles))
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
            line = '{} {} {} {} {} {} {} {} {}\n'.format(h,center.x, center.y, center.z, param[0], param[1], l_by_d, right_increment, param[4])
            report.write(line)
            h = h + 1
        report.close() 