import os
import shutil
from multiprocessing import Pool
from xml.etree import ElementTree

from xmlProcessing import fileuploadXML
from textProcessing import fileuploadText
from imgProcessing import fileuploadIMG
from logWriter import retrieveSettings

'''
Description:
method that checks if a inputfile has any extesion of a set of extensions
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
    if not os.path.exists("tmp/"):
        os.makekdirs("tmp/")
    #select correct processing method
    xml = set(['xml'])
    img = set(['pdf', 'png', 'jpg', 'jpeg','tif'])
    text = set(['doc', 'docx', 'odt', 'txt'])
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
                #pool.apply_async(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
                pool.apply(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
            else:
                Settings[0] = "IMG"
                #pool.apply_async(fileuploadIMG, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
                pool.apply(fileuploadIMG, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
        if check_file_extension(filename, text):
            Settings[0] = "TXT"
            #pool.apply_async(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
            pool.apply(fileuploadText, (UPLOAD_FOLDER,OUTPUT_FOLDER, Settings, filename,))
        
        i += 1 


'''
Description:
method that processes the inputfile
Input:
input_folder, output_folder from app
MAX_PROCESSES: number of parallel processes
Output:
start the processFilesmethod for the remaining queued files
'''
def processRestore(UPLOAD_FOLDER,OUTPUT_FOLDER, MAX_PROCESSES):        
    #remove tmp files
    #shutil.rmtree(ocropy + "/processedFiles/")
    
    #clean tmp
    shutil.rmtree("tmp/")
    if not os.path.exists("tmp/"):
        os.makedirs("tmp/")
   
    #list which need to be restored
    filenameFP_List = os.listdir(UPLOAD_FOLDER)
    
    #get the correct settings
    for f in filenameFP_List:
        settings, found = retrieveSettings(f)
        if not found:
            settings = ["Unknown", True,0]
        
        #call process method
        processFile(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES, settings, filenameFP_List)

'''
Description:
method that merges output of multiple input files
Input:
files_list, list containing names of all input files uploaded together in a single query
Output:
merged xml output of all input files
'''
def mergeOutputXML(output_folder, files_list):
    document_root = None
    complete_output = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
    for filename in files_list:
        document_root = ElementTree.parse(output_folder + filename + '/Output' + filename+ ".xml").getroot()
        complete_output += "\n"+ElementTree.tostring(document_root)
    return complete_output