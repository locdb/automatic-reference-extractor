import os
import xml.etree.ElementTree as ElementTree
from multiprocessing import Pool
from xmlProcessing import fileuploadXML
from textProcessing import fileuploadText
from imgProcessing import fileuploadIMG, processSegment
from pathParameter import LOCDB, debugMode
import pyPdf
import collections
from flask import Response

'''
Description:
method that checks if a inputfile has any extesion from a set of extensions
Input:
filename: the filename with extension
ext: a set of extensions which are allowed
Output:
returns the booleoan value of the check
'''
def check_file_extension(filename, ext):
    return '.' in filename and filename.rsplit('.', 1)[1] in ext


'''
Description:
method that processes the inputfile
Input:
input_folder, output_folder from app
MAX_PROCESSES: number of parallel processes
Settings: list of all settings -> see app for more info
filenameList: nameList of the input file
Output:
returns the result of processing which can be an error statment as well
'''
def processFile(UPLOAD_FOLDER,OUTPUT_FOLDER, MAX_PROCESSES, Settings, filenameList):
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In processFile()"
        print "####################################"
        print ""
    if not os.path.exists("tmp/"):
        os.makedirs("tmp/")
    
    #select correct processing method
    xml = set(['xml', 'htm', 'html'])
    img = set(['pdf', 'png', 'jpg', 'jpeg','tif'])
    text = set(['doc', 'docx', 'odt', 'txt'])
    i = 0
    while i < len(filenameList):
        filename = filenameList[i]
        
        if (filename[-3:].lower() == "htm") or (filename[-4:].lower() == "html"):
            if filename[-3:].lower() == "htm":
                tempName = filename[:-3]+"pdf"
                os.system("wkhtmltopdf "+UPLOAD_FOLDER+filename+" "+UPLOAD_FOLDER+filename[:-3]+"pdf")
            elif filename[-4:].lower() == "html":
                tempName = filename[:-4]+"pdf"
                os.system("wkhtmltopdf "+UPLOAD_FOLDER+filename+" "+UPLOAD_FOLDER+filename[:-4]+"pdf")
            filenameList.append(tempName)
        
        if (Settings[0] == "IMG") and (filename[-3:].lower() == "pdf"):
            reader = pyPdf.PdfFileReader(open(LOCDB+UPLOAD_FOLDER+filename))
            pages = reader.getNumPages()
            if pages == 1:
                if debugMode.lower() == "yes":
                    print "Single Page PDF"
                os.system("convert -density 300 "+LOCDB+UPLOAD_FOLDER+filename+" -quality 90 "+LOCDB+UPLOAD_FOLDER+filename[:-4]+".jpg")
                os.remove(LOCDB+UPLOAD_FOLDER+filename)
                del filenameList[i]
                filenameList.append(filename[:-4]+".jpg")
                continue
            elif pages > 1:                
                os.system("convert -density 300 "+LOCDB+UPLOAD_FOLDER+filename+" -quality 90 "+LOCDB+UPLOAD_FOLDER+filename[:-4]+".jpg")
                os.remove(LOCDB+UPLOAD_FOLDER+filename)
                f = []
                for (dirpath, dirnames, filenames) in os.walk(LOCDB+UPLOAD_FOLDER):
                    f.extend(filenames)
                    break
                for curr3 in f:
                    chunks = curr3.split("-")
                    temp_name = curr3[:0-len(chunks[len(chunks)-1])-1]
                    if  temp_name == filename[:-4]:
                        filenameList.append(curr3)
                del filenameList[i]
                continue
        i += 1
    
    i = 0
    if MAX_PROCESSES == 0:
        MAX_PROCESSES = len(filenameList)
    pool = Pool(processes=MAX_PROCESSES)
    while i < len(filenameList):
        filename = filenameList[i]
        if check_file_extension(filename, xml):
            Settings[0] = "XML"
            pool.apply_async(fileuploadXML, (UPLOAD_FOLDER,OUTPUT_FOLDER, filename,))

        if check_file_extension(filename, img): 
            if check_file_extension(filename, set(['pdf'])) and "TXT" in Settings[0]:
                Settings[0] = "TXT"
                pool.apply_async(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
            else:
                Settings[0] = "IMG"
                pool.apply(fileuploadIMG, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
        if check_file_extension(filename, text):
            Settings[0] = "TXT"
            pool.apply_async(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))        
        i += 1
        
    #sync process
    pool.close()
    pool.join()
    
    result = createResultView(OUTPUT_FOLDER, filenameList)
    return Response(result, content_type='text/xml; charset=utf-8')

        

'''
Description:
method that merges output of multiple input files
Input:
files_list, list containing names of all input files uploaded together
in a single query
Output:
merged xml output of all input files
'''
def mergeOutputXML(OUTPUT_FOLDER, files_list):
    document_root = None
    complete_output = ""
    for filename in files_list:
        document_root = ElementTree.parse(OUTPUT_FOLDER + filename + '/Output' + filename + ".xml").getroot()
        complete_output += "\n"+ElementTree.tostring(document_root)
    return complete_output


'''
Description:
method that looks for result view files
Input:
files_list, list containing names of all input files uploaded together
in a single query
Output:
resultview
'''
def createResultView(OUTPUT_FOLDER, files_list, mode=1):
    resultList = []
    missList = []
        
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In createResultView()"
        print "files_list:",files_list
        print "mode:",mode
        print "####################################"
        print ""
    #find files
    for file in files_list:
        found = False
        for folder in os.listdir("output"):            
            if mode == 1:
                if file == folder:
                    resultList.append(folder)
                    found = True
                elif file[:-4] == folder:
                    resultList.append(folder)
                    found = True
            else:
                if file[:-4] in folder:
                    resultList.append(folder)
                    found = True
                elif file[:-4] == folder:
                    resultList.append(folder)
                    found = True                    
        if not found:
            missList.append(file)    
    
    if debugMode.lower() == "yes":
        print ""
        print "resultList (before):",resultList
    
    resultList = findLatest(resultList)
    if debugMode.lower() == "yes":
        print ""
        print "resultList (after):",resultList
    
    complete_output = "<?xml version=\"1.0\" encoding=\"utf-8\"?><LOCDBViewResults>\n<FilesFound>\n"    
    for r in resultList:
        complete_output += "<filename>" + r + "</filename>\n"
    
    complete_output += "</FilesFound>\n<FilesNotFound>"
    
    for m in missList:
        complete_output += "<filename>" + m + "</filename>\n"
    
    complete_output += "</FilesNotFound>\n"
    complete_output += mergeOutputXML(OUTPUT_FOLDER, resultList)
    complete_output += "</LOCDBViewResults>"
    
    return complete_output


'''
Description:
method removes older versions
Input:
files_list, list containing names of all input files uploaded together
in a single query
Output:
short list with only latest version
'''
def findLatest(files_list):
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In findLatest()"
        print "files_list:",files_list
        print "####################################"
        print ""
    
    newList = []
    latest_timestamp = files_list[0].split("_",1)[0]
    for i,curr in enumerate(files_list):
        new_timestamp = curr.split("_",1)[0]
        
        if ((i > 0) and (new_timestamp >= old_timestamp)) or (len(files_list) == 1):
            latest_timestamp = new_timestamp
        
        old_timestamp = new_timestamp
    
    if debugMode.lower() == "yes":
        print "latest_timestamp:",latest_timestamp
    
    for curr in files_list:
        temp_timestamp = curr.split("_",1)[0]
        
        if temp_timestamp == latest_timestamp:
            newList.append(curr)
    
    return newList

def filterCropFiles(latestFileNames):
    filesFound = []
    crop_names = []
    non_crop_names = []
    for curr1 in latestFileNames:
        if "crop" in curr1:
            crop_names.append(curr1)
        else:
            non_crop_names.append(curr1)
    
    compare = lambda x,y: collections.Counter(x) == collections.Counter(y)
    
    if debugMode.lower() == "yes":
        print "crop_names:",crop_names 
        print ""
        print "non_crop_names:",non_crop_names
        print ""
    
    for curr2 in non_crop_names:
        found = False
        for curr3 in crop_names:
            if curr2[:-4] in curr3:
                found = True
        if found == True:
            filesFound.append(curr2)
    
    if compare(non_crop_names, filesFound) == False:
        for curr2 in non_crop_names:
            if not(curr2 in filesFound):
                filesFound.append(curr2)
                
    return filesFound

def coordinatesLookup(tempfilename, temp_coordinates):
    return processSegment(tempfilename, temp_coordinates)