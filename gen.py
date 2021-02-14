import bpy
import bmesh
import numpy as np
import mathutils
import os

def generateInclinedPlane( baseLocation):
    baseAngleDeg = 30
    baseAngleRad = np.pi * baseAngleDeg / 180
    bpy.ops.mesh.primitive_plane_add(size = 0.5,
                                     location = baseLocation, 
                                     rotation = (baseAngleRad, 0, 0))
                                     
def generateInclinedCube( baseLocation):
    baseAngleDeg = 30
    baseAngleRad = np.pi * baseAngleDeg / 180
    bpy.ops.mesh.primitive_cube_add(size = 1.0,
                                    location = baseLocation)
                                    
def elongateNeckPart( baseLocation):
    planeObject = bpy.data.objects['Plane']
    
    p1 = planeObject.matrix_world @ planeObject.data.vertices[0].co
    p2 = planeObject.matrix_world @ planeObject.data.vertices[1].co
    p3 = planeObject.matrix_world @ planeObject.data.vertices[2].co
    
    plane_norm = mathutils.geometry.normal([p1, p2, p3])
    
    workObject = bpy.data.objects['model']
    #workObject.select_set(True)
    numOfElongatedVertices = 0
    xSum = 0
    ySum = 0
    zSum = 0
    
    xMean = 0
    yMean = 0
    zMean = 0
    
    yarr = np.array([])
    numOfVertices = len(workObject.data.vertices)
    for workObjVert in workObject.data.vertices:
        pt = workObject.matrix_world @ workObjVert.co
        d = mathutils.geometry.distance_point_to_plane(pt, p1, plane_norm)
        epsilon = 2e-2
        if d < epsilon:
            #print("Current distance : " + str(d))
            pt[2] = baseLocation[2]
            workObjVert.co = workObject.matrix_world.inverted() @ pt
            
            xSum = xSum + pt[0]
            ySum = ySum + pt[1]
            zSum = zSum + pt[2]
            
            yarr = np.append(yarr,[ pt[1] ])
            
            numOfElongatedVertices = numOfElongatedVertices + 1
    
    print("NUM OF VERTS" + str(numOfElongatedVertices))
    print("Y SUM " + str(ySum))
    
    xMean = float(xSum) / float(numOfElongatedVertices)
    yMean = 0.5 * (np.amax(yarr) + np.amin(yarr))#float(ySum) / float(numOfElongatedVertices)
    zMean = float(zSum) / float(numOfElongatedVertices)
    
    return (xMean, yMean, zMean)
    
def generateCuttingCylinder( cylinderCenter, diameter, height):
    bpy.ops.mesh.primitive_cylinder_add(radius = diameter * 0.5,
                                        depth = height,
                                        location = cylinderCenter)
            
            
def createSectionCube(baseLocation):
    bpy.ops.mesh.primitive_cube_add(size = 1.0,
                                    location = baseLocation,
                                    scale = (1, 1, 0.01))
                                    
def performNeckCutout():
    workObject = bpy.data.objects['model']
    toolObject = bpy.data.objects['Cube']
    
    boolOperationDif = workObject.modifiers.new( type = "BOOLEAN", 
                                                 name = "bool_1")
    boolOperationDif.object = toolObject
    boolOperationDif.operation = 'DIFFERENCE'
    
    bpy.ops.object.modifier_apply(modifier = "bool_1")
    
    
def performCylinderCutout():
    workObject = bpy.data.objects['model']
    toolObject = bpy.data.objects['Cylinder']
    
    boolOperationDif = workObject.modifiers.new( type = "BOOLEAN", 
                                                 name = "bool_2")
    boolOperationDif.object = toolObject
    boolOperationDif.operation = 'DIFFERENCE'
    
    bpy.ops.object.modifier_apply(modifier = "bool_2")
    

def getObjectDimensions( objectToAnalyze):
    dimGlobalCoords = workObject.matrix_world @ objectToAnalyze.dimensions
    return dimGlobalCoords
    
def getObjectLocation( objectToAnalyze):
    locGlobalCoords = workObject.matrix_world @ objectToAnalyze.location
    return locGlobalCoords
    
def createToolCylinder():
    locPos = (0, 0, 0)
    rad = 0.1
    depth = 0.2
    toolCylinder = bpy.ops.mesh.primitive_cylinder_add(radius = rad, depth = depth, location = locPos)
    return toolCylinder

def clearScene():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj) 
        
def importModel(filein):
    filename = filein
    bpy.ops.import_scene.obj(filepath = filename)
    
def exportModel(workObject, outFileName):
    
    for objs in bpy.data.objects:
        objs.select_set(False)
    
    workObject.select_set(True)
    filename = outFileName
    bpy.ops.export_scene.obj(filepath = filename,
                             use_selection = True)
    

def voxelRemesh( object):
    remeshOperation = object.modifiers.new(type = "REMESH",
                                            name = "vox_remesh")
    remeshOperation.adaptivity = 0.001
    remeshOperation.voxel_size = 0.002
    bpy.ops.object.modifier_apply(modifier = "vox_remesh")
                                            

if __name__ == "__main__":
    clearScene()
    filename_in = "/media/intd/docs/Documents/FRLNC/BlenderLogoScript/bethrawhead/model.obj"
    filename_out = "/media/intd/docs/Documents/FRLNC/BlenderLogoScript/bethrawhead/model_out.obj"
    importModel(filename_in)
    
    for obj in bpy.data.objects:
        if obj.name.startswith("model"):
            obj.name = "model"
    
    workObject = bpy.data.objects['model']
    
    dim = getObjectDimensions(workObject)
    loc = getObjectLocation(workObject)           
    
    baseLocation = (loc[0], loc[1], loc[2] - 0.5 * dim[2])
    generateInclinedPlane( baseLocation)
    cylinderCenterCutout = elongateNeckPart( baseLocation)
    
    print("CYL LOC : " + str(cylinderCenterCutout[0]) + "; " + 
                         str(cylinderCenterCutout[1]) + "; " + 
                         str(cylinderCenterCutout[2]))    
    
    createSectionCube( baseLocation)
    performNeckCutout()
    voxelRemesh( workObject)
    generateCuttingCylinder(cylinderCenterCutout, 0.05, 0.1)
    performCylinderCutout()
    
    exportModel(workObject, filename_out)