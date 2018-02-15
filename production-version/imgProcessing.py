import bs4 as bs
from shutil import copyfile
import os
from PIL import Image
import shutil
import subprocess

from pathParameter import ocropy, LOCDB, parsCit
from logWriter import writeLog, writeCorrect
from crop_morphology import process_image

'''
Description:
method that creates a bib structure for the given img and stores it as xml file
Input:
UPLOAD_FOLDER: the folder from which the file is taken
OUTPUT_FOLDER: the output folder
columnNumber:number of coulmn thedocument has -1
filename: the filename with timestamp
Output:
outputfile is created 
'''
def fileuploadIMG(UPLOAD_FOLDER, OUTPUT_FOLDER, settings, filename):
    #try:
    columnNumber = int(settings[2])
    if not os.path.exists(ocropy + "/processedFiles/"):
        os.makedirs(ocropy + "/processedFiles/")
    
    #check if pdf
    pdfFlag = False
    im = 0
    if '.' in filename and filename.rsplit('.', 1)[1] in set(['pdf']):
        pdfFlag = True
    else:
        #check if image is valid
        im = Image.open(UPLOAD_FOLDER + filename)
        im = im.getcolors()
        
    if pdfFlag or im == None or len(im) != 0:        
        #process the image file extract text of it
        prepareIMG(UPLOAD_FOLDER, OUTPUT_FOLDER, filename, columnNumber)
    
        #stop if no text found
        if os.path.exists(ocropy + "/processedFiles/"+filename+'/ocrWdummy.txt'):
        
            p = subprocess.Popen(["./citeExtract.pl -m extract_citations " + ocropy +"/processedFiles/" +filename+"/ocrWdummy.txt", LOCDB + "tmp/" + filename +"_ParsIMG.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
            parscitstring= p.communicate()[0]
            with open("tmp/" + filename + "_ParsIMG.xml", 'w') as f:
                f.write(parscitstring)
            
            outputxmlsoup = createBibstruct(filename)
            
            #delete tmp files
            os.remove("tmp/" + filename+'_ParsIMG.xml')
                
            #with open(OUTPUT_FOLDER + "Output" + filename +'.xml','w') as xmlf:
            #    xmlf.write(outputxmlsoup.encode('utf-8'))    
            with open(ocropy + "/processedFiles/" + filename + '/xmloutput.xml','w') as xmlf:
                xmlf.write(outputxmlsoup.encode('utf-8'))
            
            copyfile(ocropy + "/processedFiles/" + filename + "/xmloutput.xml", OUTPUT_FOLDER + filename + "/Output" + filename + ".xml")
            copyfile(ocropy + "/processedFiles/" + filename + "/temp.html", OUTPUT_FOLDER + filename + "/filenameTemp.html")
            copyfile(ocropy + "/processedFiles/" + filename + "/tempcorrection.html", OUTPUT_FOLDER + filename + "/filenameTempcorrection.html")  
            
            #uncomment to remove tmp data images
            shutil.rmtree(ocropy + "/processedFiles/" + filename)

    settings = []
    settings.append("IMG")
    settings.append(columnNumber)
    writeLog(filename, settings, True)
    #writeCorrect(filename)
    
    os.remove(UPLOAD_FOLDER + filename)
    
    outputfile = OUTPUT_FOLDER + filename + "/Output" + filename+'.xml'
    outputfilename = filename.replace(filename.split("_")[0], "")[1:]
    if os.path.exists(outputfile):
        print "Finished inputfile : " + outputfilename 
    else:
        print "Error inputfile : " + outputfilename

     
'''
Description:
method that preprocesses the img file and stores it as txt for further processing
Input:
UPLOAD_FOLDER: the folder from which the file is taken
OUTPUT_FOLDER: the output folder foor all files
filename: the filename with timestamp
columnNumber:number of coulmn thedocument has -1
Output:
Textdummy.txt is created
'''
def prepareIMG(UPLOAD_FOLDER, OUTPUT_FOLDER, filename, columnNumber):
    processingFileName = filename
    pdf_to_image = False
    
    #convert pdf to image file
    if '.' in filename and filename.rsplit('.', 1)[1] in set(['pdf']):
        subprocess.call(["convert -density 300 -trim " + UPLOAD_FOLDER + filename + " -quality 100 -append tmp/" + filename + ".png"], shell=True)
        processingFileName = filename + ".png"
        pdf_to_image = True
        
        #calculate correct columnNumber with respect to pages
        p = subprocess.Popen(["pdftk " + UPLOAD_FOLDER + filename + " dump_data | grep NumberOfPages  | sed 's/[^0-9]*//'"],shell=True,stdout=subprocess.PIPE)
        pageNumber = int(p.communicate()[0])
    
        if pageNumber > 1:
            columnNumber = pageNumber * (columnNumber + 1) - 1
    else:
        copyfile(UPLOAD_FOLDER + filename, "tmp/" + filename)
 
    #crop the image before processing starts
    process_image("tmp/" + processingFileName, "tmp/" + processingFileName + ".crop.png", columnNumber)
    
    processingFileNameOrg = processingFileName
    processingFileName = processingFileName + ".crop.png"
    
    #stop if no text found
    if not os.path.exists("tmp/" + processingFileName):
        if pdf_to_image:
            os.remove("tmp/" + filename + ".png")
        else:
            os.remove("tmp/" + filename)
        return
    
    #image bin, segmentation etc.
    subprocess.call(["ocropus-nlbin -n -Q 4 "+ LOCDB +"tmp/" +processingFileName+" -o " + "processedFiles/" + filename], shell=True,cwd=ocropy)
    subprocess.call(["ocropus-gpageseg -n -Q 4 " + "processedFiles/"+filename+"/????.bin.png"], shell=True,cwd=ocropy)
    subprocess.call(["ocropus-rpred -Q 4 " + "processedFiles/"+filename+"/????/??????.bin.png"], shell=True,cwd=ocropy)
    subprocess.call(["cat " + "processedFiles/"+filename+"/????/??????.txt > " + "processedFiles/"+filename+"/ocr.txt"], shell=True,cwd=ocropy)
    
    #adding dummy text for further processing
    with open(ocropy + "/processedFiles/"+filename+'/ocr.txt','r') as f:
        ocrtext=f.read()
    with open('dummy.txt','r') as dummy:
        text=dummy.read()
    with open(ocropy + "/processedFiles/"+filename+'/ocrWdummy.txt','w') as dummyocr:
        dummyocr.write(text+'\n')
        dummyocr.write("REFERENCES\n\n")
        dummyocr.write(ocrtext)    
    
    #adding the ocr Text
    subprocess.call(["ocropus-hocr " + "processedFiles/"+filename+"/????.bin.png"+" -o " + "processedFiles/"+filename+"/temp.html"], shell=True,cwd=ocropy)
    subprocess.call(["ocropus-gtedit html " + "processedFiles/"+filename+"/????/??????.bin.png"+" -o " + "processedFiles/"+filename+"/tempcorrection.html"], shell=True,cwd=ocropy)
    
    #create output folder for image file    
    if not os.path.exists(OUTPUT_FOLDER + filename):
        os.makedirs(OUTPUT_FOLDER + filename + "/")
    copyfile("tmp/" + processingFileName, OUTPUT_FOLDER + filename + "/" + processingFileName)
    #remove tmp image files
    os.remove("tmp/" + processingFileNameOrg)
    os.remove("tmp/" + processingFileName)  
    

'''
Description:
method that create the bibstruct out of the ocropy and parscit file
Input:
filename: the filename with timestamp
Output:
bib struct is returned as bs
'''
def createBibstruct(filename):    
    #collect all parscit data
    with open("tmp/" + filename + '_ParsIMG.xml') as f:
        xmldata = f.read()
        parsXmlsoup = bs.BeautifulSoup(xmldata,'xml')

    #collect all ocropy data
    with open(ocropy + "/processedFiles/"+filename+'/temp.html','r') as htmlf:
        htmldata=htmlf.read()
    htmlsoup=bs.BeautifulSoup(htmldata,'html.parser')

    # select relevant tags
    xmltags = parsXmlsoup.find_all('rawString', text=True)
    taghtmlsoup = htmlsoup.find_all('span', attrs={'class': 'ocr_line'})
    # print "xmltags:",xmltags
    processed_line_number = -1
    # creates data for the new tags e.g. coordinates
    for ip, tp in enumerate(xmltags):
        line = str(tp)[11:-13].decode('utf-8')
        taghtmlsoup = htmlsoup.find_all('span', attrs={'class': 'ocr_line'})
        # print "*******************************"
        # print line
        # print taghtmlsoup
        # print "*******************************"
        """for i,t in enumerate(taghtmlsoup):
            if(t.text[2:-1] in line and len(t.text)>=15):
                starttag=''
                endtag=''
                try:

                    if(taghtmlsoup[i+1].text[:-1] in line):
                        try:
                            if(taghtmlsoup[i+2].text[:-1] in line):
                                #print "\nreference is "+t.text+taghtmlsoup[i+1].text[:-2]+taghtmlsoup[i+2].text[:-2]
                                starttag=taghtmlsoup[i]['title']
                                endtag=taghtmlsoup[i+2]['title']

                        except:
                                #print "\nreference is "+t.text+taghtmlsoup[i+1].text[:-2]
                                starttag=taghtmlsoup[i]['title']
                                endtag=taghtmlsoup[i+1]['title']
                        else:
                                #print "\nreference is "+t.text+taghtmlsoup[i+1].text[:-2]
                                starttag=taghtmlsoup[i]['title']
                                endtag=taghtmlsoup[i+1]['title']
                except:
                        #print "\nreference is "+t.text
                        starttag=taghtmlsoup[i]['title']
                        endtag=taghtmlsoup[i]['title']
                else:
                        #print "\nreference is "+t.text
                        starttag=taghtmlsoup[i]['title']
                        endtag=taghtmlsoup[i]['title']

                startx=starttag.split(' ')[1]
                starty=endtag.split(' ')[2]
                endx=starttag.split(' ')[3]
                endy=starttag.split(' ')[4]
                xmltags[ip]['coordinates']= startx+' '+starty+' '+endx+' '+endy
                break
        """
        ################ Tahseen ###############

        for i, t in enumerate(taghtmlsoup):
            if i <= processed_line_number:
                # print "Skipping because ", i, "is greater than ", processed_line_number
                continue
            if t.text[:-1] in line and len(t.text) >= 5:
                # print ""
                # print ""
                # print "++++++++++++++++++++++++++++++++++++++++++++++"
                # print "line: ", line
                # print "line no.",i+1,": ",t.text
                # print "++++++++++++++++++++++++++++++++++++++++++++++"
                starttag = ''
                endtag = ''
                try:
                    if ((i + 1) < len(taghtmlsoup)) and (taghtmlsoup[i + 1].text[:-1] in line):
                        starttag = taghtmlsoup[i]['title']
                        endtag = taghtmlsoup[i + 1]['title']
                        unmatched_lines = 0
                        matching_lines_iterator = 2
                        # print "Here 1"
                        try:
                            while unmatched_lines < 2:
                                # print "Here 2"
                                if ((i + matching_lines_iterator) < len(taghtmlsoup)) and (
                                    taghtmlsoup[i + matching_lines_iterator].text[:-1] in line):
                                    starttag = taghtmlsoup[i]['title']
                                    endtag = taghtmlsoup[i + matching_lines_iterator]['title']
                                    # print "Citation Continues........................................................."

                                else:
                                    # print "Here 3"
                                    unmatched_lines += 1
                                    if unmatched_lines >= 2:
                                        break

                                matching_lines_iterator += 1

                            # print "Here 4"
                            starttag = taghtmlsoup[i]['title']
                            endtag = taghtmlsoup[i + matching_lines_iterator - 2]['title']
                            # print "i: ", i
                            # print "matching_lines_iterator: ", matching_lines_iterator
                        except:
                            # print "except in 1...."
                            # #print "\nreference is "+t.text+taghtmlsoup[i+1].text[:-2]
                            # endtag = taghtmlsoup[i + 1]['title']
                            starttag = taghtmlsoup[i]['title']
                            endtag = taghtmlsoup[i + 1]['title']
                            # print "Here 5"
                    else:
                        # print "Else if not in 1....."
                        # print "\nreference is "+t.text
                        starttag = taghtmlsoup[i]['title']
                        endtag = taghtmlsoup[i]['title']
                        # print "i: ", i
                        # print "matching_lines_iterator: ", matching_lines_iterator
                        # print "In else, line: ", line
                        # print "In else, t.text line no.", i + 1, ": ", t.text
                        # print "Here 6"
                except:
                    # print "Except in current..."
                    # print "\nreference is "+t.text
                    starttag = taghtmlsoup[i]['title']
                    endtag = taghtmlsoup[i]['title']
                # print "Here 7"
                # print "starttag: ",starttag
                # print "endtag: ",endtag

                startx = starttag.split(' ')[1]
                starty = starttag.split(' ')[2]
                endx = starttag.split(' ')[3]
                endy = endtag.split(' ')[4]
                # print "Here 8"
                xmltags[ip]['coordinates'] = startx + ' ' + starty + ' ' + endx + ' ' + endy
                # print "----------------------------------"
                # print startx + ' ' + starty + ' ' + endx + ' ' + endy
                # print "//////////////////////////////////"
                processed_line_number = i
                break
            """else:
                #print "In else, line: ", line
                #print "In else, t.text line no.", i + 1, ": ", t.text
                if t.text[:-1] in line:
                    #print "In else: Found..."
                else:
                    #print "In else: Not Found..."
                #print "len(t.text): ",len(t.text)
            """
            ########################################

    #create structure of output file and insert correct tags   
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    
    algotag = soup.algorithm
    soup.find('algorithm')['name']='LOCDB Web service'
    soup.find('algorithm')['fname']=filename.split("_",1)[1]
        
    #adds all citations found by parscit
    parsXmltags= parsXmlsoup.find_all('citation', attrs={"valid" : "true"})
    for parsCitSoup in parsXmltags:
        new = parsCitSoup
        new.name = "BibStructured"
        del new['valid']
        algotag.append(new)

    return soup    