import copy
import FreeCAD
import FreeCADGui
import Part

def IsClosedCurve(iCurve):
    param1 = iCurve.FirstParameter
    param2 = iCurve.LastParameter
    value1 = iCurve.value(param1)
    value2 = iCurve.value(param2)
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


def EvaluateFace(aFace, aShape):
    isHole = True
    edges = face.Edges
    curves = []
    centerList = []
    axisList = []
    for edge in edges:
        curve = edge.Curve
        if(IsClosedCurve(curve)):
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
    
    if len(centerList) > 1:
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
                    
    # filter unique centers
    
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
            print("Not a hole")
            isHole = False
    else:
        isHole = True
        
    return isHole


# get the active document
doc = FreeCAD.ActiveDocument
# objects present in the doc
objects = doc.Objects
    
# loop thorugh all objects
    
nHoles = 0
for obj in objects:
    if("Part::PartFeature" in str(obj)):
        parentColor = obj.ViewObject.DiffuseColor
        cylinderColor = (0.0,1.0,0.0)
        colors = []
        aShape = obj.Shape
        aShape.removeSplitter()
        shapeType = aShape.ShapeType
        if(shapeType == 'Solid'): # only for solid
            faces = aShape.Faces
            for face in faces: 
                isFaceSelected = False
                surf = face.Surface
                wires = face.Wires
                nWires = len(wires)
                if (str(surf) in "<Cylinder object>"):
                    isFaceSelected = EvaluateFace(face,aShape)
                        
                if isFaceSelected == True:
                    nHoles = nHoles + 1
                    colors.append(cylinderColor)
                else:
                    colors.append(parentColor[0])
        
        print("Holes Found :", nHoles)
        obj.ViewObject.DiffuseColor = colors