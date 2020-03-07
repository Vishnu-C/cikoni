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
            center = curve.centerOfCurvature(0)
            centerList.append(center)
            axis = FreeCAD.Vector(1,0,0)
            if "BSpline" in str(curve):
                axis = GetAxisOfBspline(curve)
            else:
                axis = curve.Axis
            axisList.append(axis)
    
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
    Part.show(line)
    
    # estimate intersection
    intersect = aShape.common(line)
    nLeft = 0
    nRight = 0
    for inVert in intersect.Vertexes:
        point = inVert.Point
        distLeft = point.distanceToPoint(centerList[0])
        distRight = point.distanceToPoint(centerList[1])
        if distLeft < distRight:
            nLeft = nLeft + 1
        else:
            nRight = nRight + 1
        if(nLeft > 0 and nRight > 0): 
            # intersect happened both sides
            # propably a closed tube
            isHole = False
    
    return isHole


# get the active document
doc = FreeCAD.ActiveDocument
# objects present in the doc
objects = doc.Objects
    
# loop thorugh all objects
    
faceCount = 0
for obj in objects:
    if("Part::PartFeature" in str(obj)):
        parentColor = obj.ViewObject.DiffuseColor
        cylinderColor = (0.0,1.0,0.0)
        colors = []
        aShape = obj.Shape
        shapeType = aShape.ShapeType
        if(shapeType == 'Solid'): # only for solid
            faces = aShape.Faces
            isFaceSelected = False
            for face in faces:
                surf = face.Surface
                nEdges = len(edges)
                wires = face.Wires
                nWires = len(wires)
                if (str(surf) in "<Cylinder object>"):
                    # print("surf : ",surf)
                    edges = face.Edges
                    boundaryCurves = []
                    for edge in edges:
                        curve = edge.Curve
                        # print("Looking for circle/Ellipse :", curve)
                        # if("Circle" in str(curve) or "Ellipse" in str(curve)):
                        if IsClosedCurve(curve):
                            if(len(edge.Vertexes) < 2):
                                # print("Found closed curve")
                                boundaryCurves.append(curve)
                        
                    # print("Boundary curves :", len(boundaryCurves))
                    if len(boundaryCurves) > 0 :
                        isFaceSelected = EvaluateFace(face,aShape)
                        
                if isFaceSelected == True:
                    faceCount = faceCount + 1
                    colors.append(cylinderColor)
                else:
                    colors.append(parentColor[0])
        
        print("face count :", faceCount)
        obj.ViewObject.DiffuseColor = colors