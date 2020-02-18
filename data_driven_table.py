
"""
__author__= Biswajit Saha
this creates data driven table in ArcGIS layout based on data from  a table 

"""

from arcpy import mapping 
import arcpy 
import numpy as np
import os
import sys
import json


def unique_layer_style(lyr):
    sym = json.loads(lyr._arc_object.getsymbology())
    uniquevalues = sym["renderer"]['uniqueValueInfos']
    colornames = ["red","green","blue"]
    colordict = {x["value"]:dict(zip(colornames,map(lambda t: str(t),x['symbol']['color']))) for x in uniquevalues}
    return colordict


def layer(mxd, wildcard):
    listlayers = mapping.ListLayers(mxd,wildcard)
    print listlayers
    return listlayers[0] if listlayers else None


def delete_clone_elements(mxd):
    for elm in mapping.ListLayoutElements(mxd, wildcard="*_clone*"):
        elm.delete()

def add_style(styleDict, key, string, fontsize):
    import re
    style = styleDict[key]
    pat =r'(ha|%|Net|Total|Density)'
    style["string"]= re.sub(pat,lambda x:"<BOL>"+x.group(0)+"</BOL>",string)
    style['size']=fontsize
    return "<FNT size ='{size}'><CLR red ='{red}' green ='{green}' blue= '{blue}'>{string}</CLR></FNT>".format(**style)


if __name__ == "__main__":

    mxd_path = r"G:\GSC\Projects\BisWorking\kitchen\IndustrialLands\Review_and_Manage_Industrial_Precints_A4.mxd"

    mxd = mapping.MapDocument(mxd_path)
    df = mapping.ListDataFrames(mxd)[0]
    dfindex = mapping.ListDataFrames(mxd)[1]
    lyr = mapping.ListLayers(mxd,"Review*",df)[0]
    lyrlga =mapping.ListLayers(mxd,"LGA Boundary",df)[0]
    lyrlgaindex =mapping.ListLayers(mxd,"LGA Boundary",dfindex)[0]
    lyrgridindex =mapping.ListLayers(mxd,"GRID",dfindex)[0]
    styleDict = unique_layer_style(lyr)

    lgas = ["Blacktown","Cumberland","Parramatta","The Hills","Hornsby","Fairfield","Liverpool"]

    for lga in lgas:


        whereclause = lambda field,value:"\"{}\"= '{}'".format(field,value)

        whereclause1 = whereclause("LGA", lga)
        whereclause2 = "\"LGA\" ='"+lga.upper()+"'"
        lyr.definitionQuery = whereclause("LGA", lga)
        lyrlga.definitionQuery = whereclause("LGANAME", lga.upper())
        

        lyrgridindex.definitionQuery = whereclause("PAGE_ID", lga)
        lyrlgaindex.definitionQuery = whereclause("LGANAME", lga.upper())

        data = arcpy.da.FeatureClassToNumPyArray(lyr,["ID","LGA","NAME","Category"])
        data.sort(order =["LGA","Category","NAME"])

        #writing title
        heading = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "heading")[0]
        heading.text = lga
        df.extent = lyr.getExtent()
        dfindex.extent = lyrlgaindex.getExtent()

          #basic setting up
        fontSizeFactor = 0.0394
        fontsize = 7
        yPadding = 0.08
        xPadding = 0.08
        xUpper = 19.3005
        yUpper =14.6518

        row_line_width = 9.9807 #fixed

        #creating row line 
        row_height = fontsize*fontSizeFactor + yPadding*2
        num_of_rows = len(data)
        row_height_total = num_of_rows*row_height
        row_x =np.array([xUpper])
        row_y = np.linspace(yUpper,yUpper-row_height_total,num_of_rows+1)
        xx, yy = np.meshgrid(row_x, row_y)
        row_coords=np.c_[xx.ravel(),yy.ravel()]
        #np.split(data,3)
        #drawing row line
        row_line = arcpy.mapping.ListLayoutElements(mxd, "GRAPHIC_ELEMENT", "rowline")[0]
        for coord in row_coords:
            row_line_clone = row_line.clone("_clone")
            row_line_clone.elementPositionX = coord[0]
            row_line_clone.elementPositionY = coord[1]
            row_line_clone.elementWidth = row_line_width


        #writing data
        cell_x = np.array([xUpper,xUpper +row_line_width *0.15, xUpper +row_line_width *0.38,xUpper +row_line_width *0.80 ])
        cell_y = row_y[:-1] - yPadding
        xx, yy = np.meshgrid(cell_x, cell_y)
        cell_coords = np.c_[xx.ravel(),yy.ravel()]
        cell_coords = cell_coords.reshape(cell_y.size, cell_x.size, 2)
        cell_text = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "celltext")[0]
        
        
        for i,v in enumerate(data.tolist()):
            key  =v[-1]
            
           

            
            for ii, vv in enumerate(list(v)):
                cell_text_clone = cell_text.clone("_clone")
               
                string =str(vv) if isinstance(vv,int) else vv 
              

                cell_text_clone.text = add_style(styleDict,key,string.strip(),fontsize) 
                cell_text_clone.elementPositionX = cell_coords[i][ii][0]
                cell_text_clone.elementPositionY = cell_coords[i][ii][1]
                
            

        #exporting map
        arcpy.RefreshActiveView()
        export_dir = r"G:\GSC\Projects\BisWorking\kitchen\IndustrialLands\pdf"
        pdf_name =mxd.title+"_"+ lga+".pdf"
        pdf_path = os.path.join(export_dir,pdf_name)
        #remove if exists
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        mapping.ExportToPDF(mxd, pdf_path, resolution = 300)
        print "Map {} Exported!".format(pdf_name)
        delete_clone_elements(mxd)
    print "Completed!"


        
        

        


