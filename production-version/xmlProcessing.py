import bs4 as bs
import os
import subprocess

from pathParameter import parsCit,LOCDB
from logWriter import writeLog, writeCorrect

'''
Description:
method that creates a bib structure for the given xml and stores it as xml file
Input:
UPLOAD_FOLDER: the folder from which the file is taken
OUTPUT_FOLDER: the output folder
filename: the filename with timestamp
Output:
outputfile is created 
'''
def fileuploadXML(UPLOAD_FOLDER, OUTPUT_FOLDER,filename):
    #try:
    #open input file
    with open(UPLOAD_FOLDER+filename,'r') as f:
        xmlsoup = bs.BeautifulSoup(f.read(),'xml')
    
    prepareXML(xmlsoup, filename)
    p = subprocess.Popen(["./citeExtract.pl -m extract_citations " + LOCDB +"tmp/" + filename+ "_XMLdummy.txt ", LOCDB+ "tmp/" + filename +"_ParsXML.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
    parscitstring= p.communicate()[0]
    with open("tmp/" + filename + "_ParsXML.xml", 'w') as f:
        f.write(parscitstring)
    
    outputxmlsoup = createBibstruct(xmlsoup, filename)
    
        #delete tmp files
    os.remove("tmp/" + filename+'_XMLdummy.txt')
    os.remove("tmp/" + filename+'_ParsXML.xml')
    
    with open(OUTPUT_FOLDER + "Output" + filename+'.xml','w') as xmlf:
        xmlf.write(outputxmlsoup.encode('utf-8'))

    settings = []
    settings.append("XML")
    writeLog(filename, settings, True)       
    #writeCorrect(filename)
    
    os.remove(UPLOAD_FOLDER + filename)
    
    outputfile = OUTPUT_FOLDER + "Output" + filename+'.xml'
    outputfilename = filename.replace(filename.split("_")[0], "")[1:]
    if os.path.exists(outputfile):
        print "Finished inputfile : " + outputfilename 
    else:
        print "Error inputfile : " + outputfilename
        
        
'''
Description:
method that prepares the xml for processing, converts it into suitable txt
Input:
xmlsoup: the xml of the input xml file
filename: the filename with timestamp
Output:
XMLdummy.txt is created 
'''
def prepareXML(xmlsoup ,filename):
    #loads xml as bs structure and extracts all citations
    xmltags= xmlsoup.find_all('Citation')
    refList = []
    for bib in xmltags:
        for node in bib.find_all('BibUnstructured'):
            ref = '[' + bib.get('ID') + '] ' + ''.join(node.find_all(text=True))
            refList.append(ref)
    
    #reads dummy text
    with open('dummy.txt','r') as dummy:
        text=dummy.read()

    #stores the dummy text and references as XMLdummy.txt
    with open("tmp/" + filename+ '_XMLdummy.txt','w') as dummyxml:
        dummyxml.write(text+'\n')
        dummyxml.write("REFERENCES\n\n")
        for ref in refList:
            dummyxml.write(ref.replace("\n", "").encode('utf-8') + '\n')

'''
Description:
method that create the bibstruct out of the ParsXML.xml
Input:
xmlsoup: the xml of the input xml file
filename: the filename with timestamp
Output:
bib struct is returned as bs
'''
def createBibstruct(xmlsoup ,filename):
    #finds all citations
    xmltags= xmlsoup.find_all('Citation')
    
    #find all parcit citations
    with open("tmp/" + filename+ "_ParsXML.xml",'r') as f:
        parsXmlsoup = bs.BeautifulSoup(f.read(),'xml')
    parsXmltags= parsXmlsoup.find_all('citation', attrs={"valid" : "true"})    
        
    #compares the original ciations with the parscit citations to match correct
    for citSoup in xmltags:
        citSoupRef = citSoup.find_all('BibUnstructured')
        ref = ""
        for node in citSoupRef:
            ref = ''.join(node.find_all(text=True)).replace("\n","").encode('utf-8')
        for parsCitSoup in parsXmltags:
            if ref == parsCitSoup.find('rawString', text=True).text.encode('utf-8'):
                new = parsCitSoup
                new.name = "BibStructured"
                del new['valid']
                citSoup.append(new)
                break
    
    #create structure of output file and insert correct tags
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    
    original_tag = soup.algorithm
    new_tag = xmlsoup.find('Publisher')
    if new_tag != None:
        original_tag.append(new_tag)
    
    soup.find('algorithm')['name']='LOCDB Web service'
    soup.find('algorithm')['fname']=filename.split("_",1)[1]
    
    return soup