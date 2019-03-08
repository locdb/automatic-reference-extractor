import bs4 as bs
import os
import subprocess
import requests

from pathParameter import parsCit,LOCDB, pdfInspector, grobid
from logWriter import writeLog, writeUserLog
#from imageProcessing import processIndividualGrobid
from imgProcessing import mapXmlOutputIndividual

def check_file_extension(filename, ext):
    return '.' in filename and \
       filename.rsplit('.', 1)[1] in ext          

'''
Description:
method that creates a bib structure for the given text and stores it as xml file
Input:
UPLOAD_FOLDER: the folder from which the file is taken
OUTPUT_FOLDER: the output folder
Settings: list of all settings -> see app for more info
filename: the filename with timestamp
Output:
outputfile is created 
'''
def fileuploadText(UPLOAD_FOLDER, OUTPUT_FOLDER, settings, filename):    
    #checks the file extension and preprocesses the file based on it
    if "True" in settings[1]:
        Txt_Dummy = True
    else:
        Txt_Dummy = False
        
    prepareText(UPLOAD_FOLDER, Txt_Dummy, filename)
     
    mode = "extract_meta"
    if Txt_Dummy: 
        mode = "extract_citations"
        
    p = subprocess.Popen(["./citeExtract.pl -m" + mode + " " +LOCDB+"tmp/" + filename+ "_Textdummy.txt ",LOCDB+"tmp/" +  filename + "_ParsText.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
    parscitstring= p.communicate()[0]
    with open("tmp/" + filename + "_ParsText.xml", 'w') as f:
        f.write(parscitstring)
     
    outputxmlsoup =createBibstruct(filename)
    
    if filename[-3:].lower() == "pdf":
        output_grobid = processfileGrobid(UPLOAD_FOLDER, filename)
        xmltags3 = output_grobid.find_all('BibStructured')
        
        algotag3 = outputxmlsoup.algorithm
        for curr in xmltags3:
            algotag3.append(curr)
     
    os.system("mv "+LOCDB+"tmp/"+filename+'_Textdummy.txt '+LOCDB+"processed-files/"+filename+'_Textdummy.txt')
    os.system("mv "+LOCDB+"tmp/"+filename+'_ParsText.txt '+LOCDB+"processed-files/"+filename+'_ParsText.txt')

    os.makedirs(OUTPUT_FOLDER + filename)
    with open(OUTPUT_FOLDER + filename + "/Output" + filename+'.xml','w') as xmlf:
        xmlf.write(outputxmlsoup.encode('utf-8'))
    
    settings = []
    settings.append("TXT")
    settings.append(Txt_Dummy)
    writeLog(filename, settings, True)    
    os.remove(UPLOAD_FOLDER + filename)    
    os.makedirs(OUTPUT_FOLDER + filename)
    outputfile = OUTPUT_FOLDER + filename + "/Output" + filename+'.xml'
    outputfilename = filename.replace(filename.split("_")[0], "")[1:]
    if os.path.exists(outputfile):
        print "Finished inputfile : " + outputfilename
        writeUserLog("Finished inputfile : " + outputfilename)
    else:
        print "Error inputfile : " + outputfilename
        writeUserLog("Error inputfile : " + outputfilename)    

'''
Description:
method that pre-processes the text file and stores it as txt for further processing
Input:
UPLOAD_FOLDER: the folder from which the file is taken
Txt_Dummy: decide if text needs a dummy
filename: the filename with timestamp
Output:
Textdummy.txt is created
'''
def prepareText(UPLOAD_FOLDER, Txt_Dummy, filename):
    #checks the file extension and converts the file to txt
    if check_file_extension(filename,set(['pdf'])):
        print "LOCDB:",LOCDB
        print "UPLOAD_FOLDER:",UPLOAD_FOLDER
        print "filename:",filename
        print "java -jar docears-pdf-inspector.jar -title -text -out " +LOCDB +"tmp/" + filename+ "_Textdummy.txt " +LOCDB + UPLOAD_FOLDER + filename
        subprocess.call(["java -jar docears-pdf-inspector.jar -title -text -out " +LOCDB +"tmp/" + filename+ "_Textdummy.txt " +LOCDB + UPLOAD_FOLDER + filename],shell=True,stdout=subprocess.PIPE,cwd=pdfInspector)
        
        #removes the wrong title which is created by pdf-inspector
        with open("tmp/" + filename+'_Textdummy.txt','r') as fin:
            lines = fin.readlines()
            firstline = lines[0].split("|")
            if len(firstline) > 1:
                lines[0] = firstline[1] 
                
        with open("tmp/" + filename+'_Textdummy.txt', 'w') as fout:
            for line in lines:
                fout.write(line)
    elif check_file_extension(filename, set(['txt'])):
        with open(UPLOAD_FOLDER + filename, 'r') as f:
            text = f.read()
        with open("tmp/" + filename+'_Textdummy.txt', 'w') as f:
            f.write(text) 
    else:        
        path = UPLOAD_FOLDER + filename
        args = ['libreoffice', '--headless', '--convert-to',
            'txt', path]    
        subprocess.call(args, shell=False)
        os.rename(filename.rsplit('.', 1)[0] + ".txt", "tmp/" + filename + "_Textdummy.txt")
        
    if Txt_Dummy:
        #reads dummy text
        with open('dummy.txt','r') as dummy:
            text=dummy.read()
         
        #stores the dummy text and references as XMLdummy.txt
        with open("tmp/" + filename+ '_Textdummy.txt','r') as dummytext:
            content = dummytext.read()
            
        with open("tmp/" + filename+ "_Textdummy.txt","w") as dummytext:
            dummytext.write(text+'\n')
            dummytext.write("REFERENCES\n\n")
            dummytext.write(content)
    
'''
Description:
method that create the bibstruct out of the ParsText.xml
Input:
filename: the filename with timestamp
Output:
bib struct is returned as bs
'''
def createBibstruct(filename):
    #find all parcit citations
    with open("tmp/" + filename+"_ParsText.xml",'r') as f:
        parsXmlsoup = bs.BeautifulSoup(f.read(),'xml')
    parsXmltags= parsXmlsoup.find_all('citation', attrs={"valid" : "true"})
    
    #finds headerinformation for the output bs created by parscit
    parsXmltagsHead = parsXmlsoup.find('variant')
    
    #create structure of output file and insert correct tags   
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    
    algotag = soup.algorithm
    soup.find('algorithm')['name']='LOCDB Web service'
    soup.find('algorithm')['fname']=filename.split("_",1)[1]
    
    #adds the header in correct format
    if parsXmltagsHead is not None:
        parsXmltagsHead.name = "HeadInformation"
        del parsXmltagsHead['no']
        algotag.append(parsXmltagsHead)
    
    #adds all citations found by parscit
    for parsCitSoup in parsXmltags:
        new = parsCitSoup
        new.name = "BibStructured"
        new['detector'] = "ParsCit"
        new['namer'] = "ParsCit"
        del new['valid']
        if new.contexts is not None:
            new.contexts.extract()
        algotag.append(new)
    
    #removes confidence tag from everything
    for c in algotag.find_all_next(confidence=True):
        del c['confidence']

    return soup

def processfileGrobid(UPLOAD_FOLDER, filename):
    grobid_url = grobid+"processReferences"
    files = {'input': open(LOCDB+UPLOAD_FOLDER+filename, 'rb')}
    try:
        response = requests.post(grobid_url, files=files)
    except:
        print "Error accessing Grobid Service"
    
    xmlString = response.text.encode('utf8')
    output = mapXmlOutputIndividual(xmlString)
    xmltags= output.find_all('BibStructured')
    for tag4 in xmltags:
        tag4['detector'] = 'Grobid'
        tag4['namer'] = 'Grobid'
    
    return output