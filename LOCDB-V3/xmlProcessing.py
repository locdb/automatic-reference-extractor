import bs4 as bs
import os
import subprocess
from pathParameter import parsCit,LOCDB,debugMode
from logWriter import writeLog, writeUserLog

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
    mapOutputsoup = None
    imgOutputXmlSoup = None
    
    #open input file
    with open(UPLOAD_FOLDER+filename,'r') as f:
        xmlsoup = bs.BeautifulSoup(f.read(),'xml')
    response = False
    if filename[-3:].lower() == "xml":
        prepareXML(xmlsoup, filename)
    else:
        response = prepareHTML(xmlsoup, filename)
        if response == True:
            mapOutputsoup = mapHTML(xmlsoup, filename)
    
    p = subprocess.Popen(["./citeExtract.pl -m extract_citations " + LOCDB +"tmp/" + filename+ "_XMLdummy.txt ", LOCDB+ "tmp/" + filename +"_ParsXML.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
    parscitstring= p.communicate()[0]
    with open("tmp/" + filename + "_ParsXML.xml", 'w') as f:
        f.write(parscitstring)
    
    if filename[:-3].lower() == "xml":
        outputxmlsoup = createBibstruct(xmlsoup, filename)
    else:
        outputxmlsoup = createBibstructHTML(filename)
    
    if mapOutputsoup != None:
        bibtags2 = mapOutputsoup.find_all('BibStructured')
        algotag2 = outputxmlsoup.algorithm
        for currtag in bibtags2:
            algotag2.append(currtag)
    
    if imgOutputXmlSoup != None:
        bibtags2 = imgOutputXmlSoup.find_all('BibStructured')
        algotag2 = outputxmlsoup.algorithm
        for currtag in bibtags2:
            algotag2.append(currtag)
    
    os.system("mv "+LOCDB+"tmp/" + filename+ '_XMLdummy.txt '+LOCDB+"processed-files/" + filename+ '_XMLdummy.txt')
    os.system("mv "+LOCDB+"tmp/" + filename+ '_ParsXML.xml '+LOCDB+"processed-files/" + filename+ '_ParsXML.xml')
    
    os.makedirs(LOCDB+OUTPUT_FOLDER + filename)
    with open(LOCDB+OUTPUT_FOLDER + filename + "/Output" + filename+'.xml','w') as xmlf:
        xmlf.write(outputxmlsoup.encode('utf-8'))
    
    settings = []
    settings.append("XML")
    writeLog(filename, settings, True)       
    os.remove(UPLOAD_FOLDER + filename)    
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
method that prepares the xml for processing, converts it into suitable txt
Input:
xmlsoup: the xml of the input xml file
filename: the filename with timestamp
Output:
XMLdummy.txt is created 
'''
def prepareXML(xmlsoup ,filename):
    if debugMode.lower() == "yes":
        print "////////////////////////////////////"
        print "         In prepareXML()            "
        print "////////////////////////////////////"
    
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
                new['detector'] = "ParsCit"
                new['namer'] = "ParsCit"
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


def createBibstructHTML(filename):    
    #find all parcit citations
    with open("tmp/" + filename+ "_ParsXML.xml",'r') as f:
        parsXmlsoup = bs.BeautifulSoup(f.read(),'xml')
    parsXmltags= parsXmlsoup.find_all('citation', attrs={"valid" : "true"})    
    
    #create structure of output file and insert correct tags
    soup =  bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    algotag = soup.algorithm
    algotag['fname']=filename.split("_",1)[1]
        
    #compares the original ciations with the parscit citations to match correct
    for parsCitSoup in parsXmltags:
        new = parsCitSoup
        new.name = "BibStructured"
        new['detector'] = "ParsCit"
        new['namer'] = "ParsCit"
        del new['valid']
        algotag.append(new)
    
    return soup

def prepareHTML(parseHtmlsoup, filename):
    print "////////////////////////////////////"
    print "        In prepareHTML()            "
    print "////////////////////////////////////"
    
    # Old Format
    reftags= parseHtmlsoup.find_all("cite")
    refList = []
    if len(reftags) != 0:
        
        for curr1 in reftags:
            temp_string = curr1.text.replace('\n', '')            
            refList.append(temp_string.encode('utf8')) 
    else:
        # New Format 1
        reftags = parseHtmlsoup.find_all("dl", {"class": "references"})
        for curr1 in reftags:   # Reference Groups
            children1 = curr1.findChildren(recursive=False)
            for curr2 in children1: # Reference Elements
                if curr2['class'] == "label":
                    continue
                else:
                    temp_string = ""
                    children2 = curr2.findChildren(recursive=False)
                    for curr3 in children2:# reference Sub-Elements
                        if curr3.has_attr("class") and curr3['class'] == "ReferenceLinks":
                            break
                        elif curr3.has_attr("class") and curr3['class'] == "contribution":
                            if curr3.strong != None:
                                if type(curr3.strong.previousSibling) != bs.element.NavigableString:
                                    temp_string += curr3.em.previousSibling.encode('utf8').strip()+" "+curr3.em.text.encode('utf8').strip()+" "+curr3.strong.text.encode('utf8').strip()
                                else:
                                    temp_string += curr3.strong.previousSibling.encode('utf8').strip()+". "+curr3.strong.text.encode('utf8').strip()
                            else:
                                temp_string += curr3.string.encode('utf8').strip()
                        else:
                            temp_string += curr3.text.encode('utf8').strip()+" "
                    temp_string = temp_string.replace("\n","")
                    if len(temp_string.strip()) > 5:
                        refList.append(temp_string.strip()+".")
        
        # New Format 2
        reftags2 = parseHtmlsoup.find_all("div", {"class": "pll"})
        for refgroup2 in reftags2:
            allrefs2 = refgroup2.find_all("div", {"class": "media-body mls plxl reference-contains"})
            for currref2 in allrefs2:
               temp_string = currref2.text.replace("\n", '').replace('\\'+'n','').encode('utf8')               
               if (temp_string[0:2] == "['") and (temp_string[-2:] == "']"):
                   temp_string = temp_string[2:-2]
               temp_string = temp_string.strip()
               if temp_string[-1] != ".":
                   temp_string = temp_string+"."
               if len(temp_string.strip()) > 5:
                   refList.append(temp_string)
               
        # New Format 3
        reftags2 = parseHtmlsoup.find_all("div", {"class": "content"})
        for refgroup2 in reftags2:
            allrefs2 = refgroup2.find_all("div", {"class": "CitationContent"})
            for currref2 in allrefs2:
               temp_string = currref2.text.encode('utf8')
               temp_string2 = currref2.span.text.encode('utf8').strip()
               temp_string = temp_string.replace(temp_string2,"")
               temp_string = temp_string.replace('\n', '').strip()
               if temp_string[-1] != ".":
                   temp_string = temp_string+"."
               
               if len(temp_string.strip()) > 5:
                   refList.append(temp_string.strip())
               
        # New Format 4
        allrefs2 = parseHtmlsoup.find_all("td", {"valign": "top"})
        for currref2 in allrefs2:
            temp_string = currref2.text.encode('utf8').replace('\n', '')
            allrefs3 = currref2.find_all("span", {"class": "ref-google"})
            for curr_temp in allrefs3:
                curr_temp_string = curr_temp.text.encode('utf8').strip()
                temp_string = temp_string.replace(curr_temp_string,"")
                
            allrefs3 = currref2.find_all("span", {"class": "ref-xLink"})
            for curr_temp in allrefs3:
                curr_temp_string = curr_temp.text.encode('utf8').strip()
                temp_string = temp_string.replace(curr_temp_string,"")
            
            if len(temp_string.strip()) > 5:
                refList.append(temp_string.strip())
            
    #reads dummy text
    with open('dummy.txt','r') as dummy:
        text=dummy.read()
    #stores the dummy text and references as XMLdummy.txt
    with open("tmp/" + filename+ '_XMLdummy.txt','w') as dummyxml:
        dummyxml.write(text)
        for ref in refList:
            dummyxml.write(ref+'\n'+'\n')
    if len(refList) == 0:
        return False
    else:
        return True

def mapHTML(parseHtmlsoup, filename):
    print "////////////////////////////////////"
    print "          In mapHTML()              "
    print "////////////////////////////////////"
    
    soup =  bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    algotag = soup.algorithm
    algotag['fname']=filename.split("_",1)[1]
    
    reftags = parseHtmlsoup.find_all("cite")
    print "len(reftags):",len(reftags)
    
    # Old Format
    if len(reftags) != 0:
        for curr1 in reftags:
            bibsoup =  bs.BeautifulSoup('<BibStructured></BibStructured>','xml')
            bibtag = bibsoup.BibStructured
            bibtag['detector'] = "Mapping"
            bibtag['namer'] = "Mapping"
            if debugMode.lower() == "yes":
                print ""
            children = curr1.findChildren(recursive=False)
            temp_string = ""
            for child in children:
                if child.string != None:
                    temp_string += child.string + " "
            
            temp_string = temp_string.strip()
            if debugMode.lower() == "yes":
                print "temp_string:"    ,temp_string
            
            authorssoup =  bs.BeautifulSoup("<authors></authors>",'xml')
            temp_authorstag = authorssoup.authors
            authorstags= curr1.find_all("span", {"class": "cit-auth"})
            for curr2 in authorstags:
                authorsoup =  bs.BeautifulSoup("<author></author>",'xml')
                authortag = authorsoup.author
                if debugMode.lower() == "yes":
                    print "Author:",curr2.span.string
                authortag.string = curr2.span.string
                temp_authorstag.append(authortag)
            if len(authorssoup.authors) != 0:
                bibtag.append(temp_authorstag)
            datesoup =  bs.BeautifulSoup("<date></date>",'xml')
            datetag = datesoup.date
            pubDatetags= curr1.find_all("span", {"class": "cit-pub-date"})
            for curr2 in pubDatetags:
                if debugMode.lower() == "yes":
                    print "Date:",curr2.string
                    print "datetag.string:",datetag.string
                if (curr2.string != None) or (len(curr2.string) != 0):
                    datetag.string = curr2.string
                    bibtag.append(datetag)

            titlesoup =  bs.BeautifulSoup("<title></title>",'xml')
            titletag = titlesoup.title
            titletags= curr1.find_all("span", {"class": "cit-article-title"})
            if len(titletags) == 0:
                titletags= curr1.find_all("span", {"class": "cit-source"})
            for curr2 in titletags:
                if debugMode.lower() == "yes":
                    print "Title:",curr2.string            
                if (curr2.string != None) or (len(curr2.string) != 0):
                    titletag.string = curr2.string
                    bibtag.append(titletag)
            
            locationsoup =  bs.BeautifulSoup("<location></location>",'xml')
            locationtag = locationsoup.location
            locationtags= curr1.find_all("span", {"class": "cit-publ-loc"})
            for curr2 in locationtags:
                if debugMode.lower() == "yes":
                    print "Location:",curr2.string
                if (curr2.string != None) or (len(curr2.string) != 0):
                    locationtag.string = curr2.string
                    bibtag.append(locationtag)
            
            publishersoup =  bs.BeautifulSoup("<publisher></publisher>",'xml')
            publishertag = publishersoup.publisher
            publishertags= curr1.find_all("span", {"class": "cit-publ-name"})
            for curr2 in publishertags:
                if debugMode.lower() == "yes":
                    print "Publisher:",curr2.string
                if (curr2.string != None) or (len(curr2.string) != 0):
                    publishertag.string = curr2.string
                    bibtag.append(publishertag)
            
            journalsoup =  bs.BeautifulSoup("<journal></journal>",'xml')
            journaltag = journalsoup.journal
            journaltags= curr1.find_all("span", {"class": "cit-jnl-abbrev"})
            for curr2 in journaltags:
                if debugMode.lower() == "yes":
                    print "Journal:",curr2.string
                if (curr2.string != None) or (len(curr2.string) != 0):
                    journaltag.string = curr2.string
                    bibtag.append(journaltag)
            
            volumesoup =  bs.BeautifulSoup("<volume></volume>",'xml')
            volumetag = volumesoup.volume
            volumetags= curr1.find_all("span", {"class": "cit-vol"})
            for curr2 in volumetags:
                if debugMode.lower() == "yes":
                    print "volume:",curr2.string
                if (curr2.string != None) or (len(curr2.string) != 0):
                    volumetag.string = curr2.string
                    bibtag.append(volumetag)
            
            pagessoup =  bs.BeautifulSoup("<pages></pages>",'xml')
            pagestag = pagessoup.pages
            fpagetags= curr1.find_all("span", {"class": "cit-fpage"})
            lpagetags= curr1.find_all("span", {"class": "cit-lpage"})
            for curr2,curr3 in zip(fpagetags,lpagetags):
                if debugMode.lower() == "yes":
                    print "Pages:",curr2.string+'-'+curr3.string
                
                if (curr2.string != None) or (len(curr2.string) != 0):
                    pagestag.string = curr2.string+'-'+curr3.string
                    bibtag.append(pagestag)
            algotag.append(bibtag)
    return soup