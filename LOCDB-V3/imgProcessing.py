import bs4 as bs
from shutil import copyfile
import os
from PIL import Image
import subprocess
from pathParameter import LOCDB, parsCit, detectronDir, grobid, modelPath, debugMode, modelPath2
from logWriter import writeLog, writeUserLog
import numpy as np
import requests
import cv2


def fileuploadIMG(UPLOAD_FOLDER, OUTPUT_FOLDER, settings, filename):
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In fileuploadIMG()"
        print "####################################"
        print ""
        print "detectronDir:",detectronDir
    
    column_confidence_threshold = 0.91 
    
    # Resize if input image is huge (> 3500 width or height)
    temp_im = Image.open(UPLOAD_FOLDER+filename)
    width, height = temp_im.size
    if (width > 3500) or (height > 3500):
        os.system("convert "+UPLOAD_FOLDER+filename+" -resize 3500x3500 -quality 100 -density 300x300 "+UPLOAD_FOLDER+filename)
    
    copyfile(UPLOAD_FOLDER + filename, LOCDB+"images-tmp/"+filename)
    
    # Detecting layout Here (Number of columns)
    resultsFile = open(LOCDB+"tmp"+"/layout-inference-results-"+filename[:-4]+".txt","w")
    resultsFile.close()
    try:
        subprocess.call(["python2 tools/infer_simple-custom2.py --cfg "+detectronDir+"configs/custom/e2e_faster_rcnn_R-50-C4_1x-column-detector.yaml --output-dir "+LOCDB + "tmp"+" --image-ext "+filename[-3:]+" --wts "+modelPath2+"default_model_layout.pkl "+LOCDB+"images-tmp/"+filename], shell=True, cwd=detectronDir)
    except:
        return "An error occurred during layout inference stage..."
    
    os.system("mv "+LOCDB+"tmp/layout-inference-results.txt "+LOCDB+"tmp/layout-inference-results-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"tmp/"+filename+".pdf "+LOCDB+"processed-files/"+filename+"-layout.pdf")
    
    
    ################ Splitting Page into Columns ##############################
    f = open(LOCDB +"tmp/"+"layout-inference-results-"+filename[:-4]+".txt", "r")
    all_lines = f.readlines()
    f.close()
    
    if debugMode.lower() == "yes":
        print "len(all_lines):",len(all_lines)
    
    columns_confidence = []
    columns_boxes = []
    for line in all_lines:
        if line[0] == "\n":
            continue
        if line[0] == "/":
            name = line.split('/')[(len(line.split('/'))-1)]
            if name.strip() == filename.strip():
                currFile = True
            else:
                currFile = False
            continue
        
        if currFile == True:
            chunks = line.strip().split(" ")
            columns_boxes.append([int(float(chunks[0])),int(float(chunks[1])),int(float(chunks[2])),int(float(chunks[3]))])
            columns_confidence.append(float(chunks[4]))
        
    temp_j = 0
    for curr1, curr2 in zip(columns_confidence, columns_boxes):
        if curr1 < column_confidence_threshold:
            del columns_confidence[temp_j]
            del columns_boxes[temp_j]
            continue
        temp_j += 1
    
    number_of_columns = len(columns_confidence)
    
    curr_fileNames = []
    if number_of_columns > 1:
        # Sort Coordinates from left to right
        for i,curr1 in enumerate(columns_boxes):
            for j,curr2 in enumerate(columns_boxes):
                if columns_boxes[i][0] < columns_boxes[j][0]:
                     columns_boxes[i], columns_boxes[j] =  columns_boxes[j], columns_boxes[i]
                     columns_confidence[i], columns_confidence[j] =  columns_confidence[j], columns_confidence[i]
        
        if debugMode.lower() == "yes":    
            print "columns_boxes:",columns_boxes
            print "Total Columns Found:",number_of_columns
        
        img = cv2.imread(LOCDB+"images-tmp/"+filename)
        height, width, channels = img.shape
        if debugMode.lower() == "yes":
            print "height:",height
            print "width:",width
            print "channels:",channels
        if number_of_columns == 2:
            # crop 1
            crop_img1 = img[0:height, 0:columns_boxes[1][0]-1]
            cv2.imwrite(UPLOAD_FOLDER+filename[:-4]+"-crop1."+filename[-3:], crop_img1)
            curr_fileNames.append(filename[:-4]+"-crop1."+filename[-3:])
            
            # crop 2
            crop_img2 = img[0:height, columns_boxes[1][0]:width]
            cv2.imwrite(UPLOAD_FOLDER+filename[:-4]+"-crop2."+filename[-3:], crop_img2)
            curr_fileNames.append(filename[:-4]+"-crop2."+filename[-3:])
            if debugMode.lower() == "yes":
                print "crop_img1.shape:",crop_img1.shape
                print "crop_img2.shape:",crop_img2.shape
        
        elif number_of_columns == 3:
            # crop 1
            crop_img1 = img[0:height, 0:columns_boxes[1][0]-1]
            cv2.imwrite(UPLOAD_FOLDER+filename[:-4]+"-crop1."+filename[-3:], crop_img1)
            curr_fileNames.append(filename[:-4]+"-crop1."+filename[-3:])
            
            # crop 2
            crop_img2 = img[0:height, columns_boxes[1][0]:columns_boxes[2][0]-1]
            cv2.imwrite(UPLOAD_FOLDER+filename[:-4]+"-crop2."+filename[-3:], crop_img2)
            curr_fileNames.append(filename[:-4]+"-crop2."+filename[-3:])
            
            # crop 3
            crop_img3 = img[0:height, columns_boxes[2][0]:width]
            cv2.imwrite(UPLOAD_FOLDER+filename[:-4]+"-crop3."+filename[-3:], crop_img3)
            curr_fileNames.append(filename[:-4]+"-crop3."+filename[-3:])
            
        os.system("mv "+LOCDB+"images-tmp/"+filename+" "+LOCDB+"images/" + filename)
    else:
        curr_fileNames.append(filename)
    if debugMode.lower() == "yes":
        print "curr_fileNames:",curr_fileNames                        
    
    all_tags = []
    for count,currFilename in enumerate(curr_fileNames):
        copyfile(UPLOAD_FOLDER+currFilename, LOCDB+"images-tmp/"+currFilename)
        try:
            subprocess.call(["python2 tools/infer_simple-custom.py --cfg "+detectronDir+"configs/custom/e2e_mask_rcnn_R-50-C4_1x-LOCDB.yaml --output-dir "+LOCDB + "tmp"+" --image-ext "+currFilename[-3:]+" --wts "+modelPath+"default_model.pkl "+LOCDB+"images-tmp/"+currFilename], shell=True, cwd=detectronDir)
        except:
            return "An error occurred during inference stage..."
        
        os.system("mv "+LOCDB+"tmp/bbox-inference-results.txt "+LOCDB+"tmp/bbox-inference-results-"+currFilename[:-4]+".txt")
        os.system("mv "+LOCDB+"tmp/"+filename+".pdf "+LOCDB+"processed-files/"+filename+"-ref-detection.pdf")
        os.makedirs(LOCDB + "tmp/"+currFilename[:-4])
        copyfile(UPLOAD_FOLDER + currFilename, "tmp/" + currFilename)
        
        try:
            ocrIMGTesseract(UPLOAD_FOLDER,currFilename)
        except:
            return "An error occurred during performing OCR..."
        
        try:
            finalizedCoordinates,finalizedStrings = combineOcrOutputsTesseract(currFilename)
        except:
            return "An error occurred during combining OCR output..."
        
        try:        
            outputXMLsoup = ParscitImg(UPLOAD_FOLDER, OUTPUT_FOLDER, currFilename, finalizedCoordinates, finalizedStrings)
        except:
            return "An error occurred during Parcit processing..."
        
        parsXmltags = outputXMLsoup.find_all('BibStructured')
        
        # Correcting Coordinates for second and/or third column
        if count == 1:
            for ip,tp in enumerate(parsXmltags):
                if debugMode.lower() == "yes":
                    print "parsXmltags[ip].rawString['coordinates']:",parsXmltags[ip].rawString['coordinates']
                coordinatesString = parsXmltags[ip].rawString['coordinates']
                chunks = coordinatesString.split(" ")
                parsXmltags[ip].rawString['coordinates'] = str(int(chunks[0])+columns_boxes[1][0])+" "+chunks[1]+" "+str(int(chunks[2])+columns_boxes[1][0])+" "+chunks[3]
        elif count == 2:
            for ip,tp in enumerate(parsXmltags):
                if debugMode.lower() == "yes":
                    print "parsXmltags[ip].rawString['coordinates']:",parsXmltags[ip].rawString['coordinates']
                coordinatesString = parsXmltags[ip].rawString['coordinates']
                chunks = coordinatesString.split(" ")
                parsXmltags[ip].rawString['coordinates'] = str(int(chunks[0])+columns_boxes[2][0])+" "+chunks[1]+" "+str(int(chunks[2])+columns_boxes[2][0])+" "+chunks[3]
        
        all_tags.extend(parsXmltags)
    
    if debugMode.lower() == "yes":
        print "all_tags:",all_tags
    
    if not os.path.exists(OUTPUT_FOLDER + filename):
        os.makedirs(OUTPUT_FOLDER + filename + "/")
    
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    algotag = soup.algorithm
    soup.find('algorithm')['name']='LOCDB Web service'
    soup.find('algorithm')['fname']=filename.split("_",1)[1]
    
    for currTag in all_tags:
        algotag.append(currTag)
    
    os.system("mv "+LOCDB+UPLOAD_FOLDER+filename+" "+LOCDB+"images/" + filename)
    with open(OUTPUT_FOLDER + filename + "/Output" + filename + ".xml",'w') as xmlf:
        xmlf.write(soup.encode('utf-8'))
    
    outputfile = OUTPUT_FOLDER + filename + "/Output" + filename+'.xml'
    outputcurrFilename = filename.replace(filename.split("_")[0], "")[1:]
    if os.path.exists(outputfile):
        print ""
        print "Finished inputfile : " + outputcurrFilename
        writeUserLog("Finished inputfile : " + outputcurrFilename) 
    else:
        print ""
        print "Error inputfile : " + outputcurrFilename
        writeUserLog("Error inputfile : " + outputcurrFilename)
    os.system("mv "+LOCDB+"tmp/layout-inference-results-"+filename[:-4]+".txt "+LOCDB+"processed-files/layout-inference-results-"+filename[:-4]+".txt")
    return algotag
  

def createBibstruct(filename, finalizedCoordinates,finalizedStrings):
    if debugMode.lower() == "yes":
        print "filename:",filename
        print "finalizedCoordinates:",finalizedCoordinates
        print "finalizedStrings:",finalizedStrings
    
    #collect all parscit data
    with open(LOCDB+"tmp/" + filename + '_ParsIMG.xml') as f1:
        xmldata = f1.read()#.encode('utf-8')
        parsXmlsoup = bs.BeautifulSoup(xmldata,'xml')
        
    with open(LOCDB+"tmp/" + filename + '_ParsTXT.xml') as f2:
        xmldata2 = f2.read()#.encode('utf-8')
        parsXmlsoup2 = bs.BeautifulSoup(xmldata2,'xml')
    
    if debugMode.lower() == "yes":
        print "Collecting all ParsCit processed data..."
    
    #select relevant tags
    xmltags= parsXmlsoup.find_all('rawString',text=True)
    
    if debugMode.lower() == "yes":
        print ""
        print "xmltags:",xmltags
        
    #create structure of output file and insert correct tags   
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    
    algotag = soup.algorithm
    soup.find('algorithm')['name']='LOCDB Web service'
    soup.find('algorithm')['fname']=filename.split("_",1)[1]
    
    #adds all citations found by parscit
    parsXmltags2 = parsXmlsoup2.find_all('citation', attrs={"valid" : "true"})
    
    for parsCitSoup2 in parsXmltags2:
        parsCitSoup2.name = "BibStructured"
        del parsCitSoup2['valid']
        flag = False
        if flag == False:
            if debugMode.lower() == "yes":
                print os.path.isfile(LOCDB +"tmp/"+"all-text1-"+filename[:-4]+".txt")
                print os.path.isfile(LOCDB +"tmp/"+"all-text-boxes-"+filename[:-4]+".txt")
            
            f1 = open(LOCDB +"tmp/"+"all-text1-"+filename[:-4]+".txt", "r")
            temp_lines = f1.readlines()
            f1.close()
            
            f2 = open(LOCDB +"tmp/"+"all-text-boxes-"+filename[:-4]+".txt", "r")
            temp_boxes = f2.readlines()
            f2.close()
            
            f3 = open(LOCDB +"tmp/"+"all-text-indeces-"+filename[:-4]+".txt", "r")
            temp_indeces = f3.readlines()
            f3.close()
            
            f4 = open(LOCDB +"tmp/"+"all-text2-"+filename[:-4]+".txt", "r")
            temp_one_line = f4.read()
            f4.close()
            
            temp_string = parsCitSoup2.rawString.string.strip()
            temp_string = temp_string.encode("utf8")
            temp_coordinates = []
            
            if debugMode.lower() == "yes":
                print ""
                print "temp_string:",temp_string
                print len(temp_string),len(temp_string.decode('utf8'))
                print len(temp_one_line)
                print "temp_one_line:",temp_one_line
            
            try:
                startIndex = -1
                endIndex = -1
                temp_string = temp_string.decode('utf8')
                temp_one_line = temp_one_line.decode('utf8')
                    
                startIndex = temp_one_line.index(temp_string)
                if debugMode.lower() == "yes":
                    print "startIndex:",startIndex
                endIndex = startIndex + len(temp_string)
                if debugMode.lower() == "yes":
                    print "Found at index: ",startIndex,"till",endIndex
                    print "temp_one_line[startIndex:endIndex]:",temp_one_line[startIndex:endIndex]
                
                lineIndex_start = None
                lineIndex_end = None
                for temp_index,tempCurr in enumerate(temp_indeces):
                    temp_chunks = tempCurr.split(' ')
                    temp_chunks = map(int, temp_chunks)
                    
                    if (startIndex >= temp_chunks[0]) and (startIndex <= temp_chunks[1]):
                        if debugMode.lower() == "yes":
                            print "temp_chunks:",temp_chunks
                        lineIndex_start = temp_index
                        if debugMode.lower() == "yes":
                            print "lineIndex_start:",lineIndex_start
                            print "temp_boxes[lineIndex_start]:",temp_boxes[lineIndex_start]
                    if (endIndex >= temp_chunks[0]) and (endIndex <= temp_chunks[1]):
                        if debugMode.lower() == "yes":
                            print "temp_chunks:",temp_chunks
                        lineIndex_end = temp_index
                        if debugMode.lower() == "yes":
                            print "lineIndex_end:",lineIndex_end
                            print "temp_boxes[lineIndex_end]:",temp_boxes[lineIndex_end]
                        
                
                temp_index2 = lineIndex_start
                while temp_index2 <= lineIndex_end:
                    if debugMode.lower() == "yes":
                        print "temp_lines[temp_index2]:",temp_lines[temp_index2]
                        print "temp_index2:",temp_index2
                    temp_chunks2 = temp_boxes[temp_index2].strip().split(" ")
                    temp_chunks2 = map(int, temp_chunks2)
                    temp_coordinates.append(temp_chunks2)
                    if debugMode.lower() == "yes":
                        print "temp_chunks2:",temp_chunks2
                    temp_index2 += 1
            except ValueError:
                print "Exact string Not found in file..."
            
            if debugMode.lower() == "yes":
                print "temp_coordinates:",temp_coordinates
            
            if len(temp_coordinates) == 0:
                if debugMode.lower() == "yes":
                    print ""
                    print "Putting Zeros in coordinates"
                temp_coordinates = [[0, 0, 0, 0]]
            
            parscit_coordinates = []
            temp_j = 0
            while temp_j < 4:
                temp_min = temp_coordinates[0][temp_j]
                temp_max = temp_coordinates[0][temp_j]
                temp_i = 1
                while temp_i < len(temp_coordinates):
                    if (temp_j == 0 or temp_j == 1) and temp_coordinates[temp_i][temp_j] < temp_min:
                        temp_min = temp_coordinates[temp_i][temp_j]
                    elif (temp_j == 2 or temp_j == 3) and temp_coordinates[temp_i][temp_j] > temp_max:
                        temp_max = temp_coordinates[temp_i][temp_j]
                        
                    temp_i += 1
                if (temp_j == 0 or temp_j == 1):
                    parscit_coordinates.append(temp_min)
                else:
                    parscit_coordinates.append(temp_max)
                temp_j += 1
            if debugMode.lower() == "yes":
                print ""
                print "temp_coordinates:",temp_coordinates
                print "parscit_coordinates:",parscit_coordinates
                print len(temp_lines),len(temp_boxes)
            
            parsCitSoup2.rawString['coordinates'] = str(parscit_coordinates[0])+" "+str(parscit_coordinates[1])+" "+str(parscit_coordinates[2])+" "+str(parscit_coordinates[3])
            bibTag = None
            if parscit_coordinates in finalizedCoordinates:
                parsCitSoup2['detector'] = 'Image'
                parsCitSoup2['namer'] = 'ParsCit'
                grobid_output1 = processIndividualGrobid(parsCitSoup2.rawString.string)
                if debugMode.lower() == "yes":
                    print "grobid_output1.BibStructured:",grobid_output1.BibStructured
                tempsoup = bs.BeautifulSoup('<rawString></rawString>','xml')
                if debugMode.lower() == "yes":
                    print "parsCitSoup2.rawString.string:",parsCitSoup2.rawString.string
                    print "tempsoup.rawString.string:",tempsoup.rawString.string
                    print "parsCitSoup2.rawString['coordinates']:",parsCitSoup2.rawString['coordinates']
                tempsoup.rawString.string = parsCitSoup2.rawString.string
                tempsoup.rawString['coordinates'] = parsCitSoup2.rawString['coordinates']
                grobid_output1.BibStructured.append(tempsoup.rawString)
                grobid_output1.BibStructured['detector'] = 'Image'
                grobid_output1.BibStructured['namer'] = 'Grobid'
                bibTag = grobid_output1.BibStructured
            else:
                parsCitSoup2['detector'] = 'ParsCit'
                parsCitSoup2['namer'] = 'ParsCit'
            
            if parsCitSoup2['detector'] == 'Image':
                algotag.append(parsCitSoup2)
                algotag.append(bibTag)
            else:
                algotag.append(parsCitSoup2)            
    
    parsXmltags3 = algotag.find_all('rawString',text=True)
    for index,temp_str in enumerate(finalizedStrings):
        flag = False
        for currString in parsXmltags3:
            currString2 = currString.string.encode("utf8").strip()
            
            if levenshtein(temp_str.strip().replace(" ",""), currString2.replace(" ","")) < 10:
                flag = True
        
        if flag == False:
            soup2 = bs.BeautifulSoup('<BibStructured><rawString></rawString></BibStructured>','xml')
            tag4 = soup2.BibStructured
            tag2 = soup2.rawString
            tag2.string = temp_str
            tag4['detector'] = 'Image'
            tag4['namer'] = 'Grobid'
            tag2['coordinates'] = str(finalizedCoordinates[index][0]) + ' ' + str(finalizedCoordinates[index][1]) + ' ' + str(finalizedCoordinates[index][2]) + ' ' + str(finalizedCoordinates[index][3])
            
            if debugMode.lower() == "yes":
                print "temp_str:",temp_str
            grobid_output2 = processIndividualGrobid(temp_str)
            if debugMode.lower() == "yes":
                print "11111"
            tempsoup = bs.BeautifulSoup('<rawString></rawString>','xml')
            if debugMode.lower() == "yes":
                print "22222"
            tempsoup.rawString.string = temp_str
            tempsoup.rawString['coordinates'] = tag2['coordinates']
            grobid_output2.BibStructured['detector'] = 'Image'
            grobid_output2.BibStructured['namer'] = 'Grobid'
            grobid_output2.BibStructured.append(tempsoup.rawString)
            bibTag = grobid_output2.BibStructured
            if debugMode.lower() == "yes":
                print "bibTag:",bibTag
            algotag.append(bibTag)
    
    return soup


def ocrIMGTesseract(UPLOAD_FOLDER,filename):
    os.system("tesseract "+LOCDB+UPLOAD_FOLDER+filename+" "+LOCDB + "tmp/"+filename[:-4]+"/output"+" -l eng+deu hocr")
    return 0

def parseHOCRTesseract(filename):
    textLines = []
    linesBoxes = []
    parsXmlsoup = ""
    if debugMode.lower() == "yes":
        print "File Exists2:",os.path.isfile(LOCDB + "tmp/"+filename[:-4]+"/output.hocr")
        print LOCDB + "tmp/"+filename[:-4]+"/output.hocr"
    
    with open(LOCDB + "tmp/"+filename[:-4]+"/output.hocr") as f:
        xmldata = f.read()#.encode('utf8')
        parsXmlsoup = bs.BeautifulSoup(xmldata,'xml')
    
    linetags= parsXmlsoup.find_all('span',attrs={"class": "ocr_line"})    
    for line in linetags:
        tempLineString = ""
        chunks = line["title"].split(" ")
        
        wordtags= line.find_all('span',attrs={"class": "ocrx_word"})
        for word in wordtags:
            tempLineString = tempLineString + " " + word.string
        
        if tempLineString.strip() != "":
            textLines.append(tempLineString.strip())
            linesBoxes.append([int(chunks[1]),int(chunks[2]),int(chunks[3]),int(chunks[4].replace(";",""))])
    
    if debugMode.lower() == "yes":        
        print "No of Lines Detected:",len(linesBoxes)
        print "No of Boxes Dettected:",len(textLines)
        print "--------------"
    
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    lengthCounter = -1
    f1= open(LOCDB + "tmp/all-text1-"+filename[:-4]+".txt", 'w')
    f4= open(LOCDB + "tmp/all-text2-"+filename[:-4]+".txt", 'w')
    f3= open(LOCDB + "tmp/all-text-indeces-"+filename[:-4]+".txt", 'w')
    for curr1 in textLines:
        len1 = len(curr1)
        aaa = curr1.encode('utf8')
        bbb = aaa.decode('utf8')
        aaa = aaa.strip()
        f1.write(str(aaa)+"\n")
        if (aaa[-1:] == "-"):
            if(aaa[-2:-1] in digits):
                if debugMode.lower() == "yes":
                    print "Digit Found..."
            else:
                aaa = str(aaa)[:-1]
                len1 -= 1
        else:
            aaa= str(aaa)+" "
            len1 += 1
        
        f4.write(aaa)
        if debugMode.lower() == "yes":
            print "lengthCounter:",lengthCounter
            print "bbb:","########"+bbb+"########"
            print "len(bbb):",len(bbb)
        
        f3.write(str(lengthCounter+1)+" "+str(lengthCounter+len1)+"\n")
        lengthCounter = lengthCounter+len1
    f1.close()
    f3.close()
    f4.close()  
    
    
    
    with open(LOCDB + "tmp/"+"all-text-boxes-"+filename[:-4]+".txt", 'w+') as f2:
        for curr2 in linesBoxes:
            aaa = str(curr2[0])+" "+str(curr2[1])+" "+str(curr2[2])+" "+str(curr2[3])
            f2.write(aaa+"\n")
    f2.close()
    return textLines,linesBoxes

'''
Description:
method that processes OCR output Files through ParsCit
Input:
UPLOAD_FOLDER: the folder from which the file is taken
OUTPUT_FOLDER: the output folder
Output:
outputfile is created in json format
'''
def ParscitImg(UPLOAD_FOLDER, OUTPUT_FOLDER, filename, finalizedCoordinates,finalizedStrings):
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In ParscitImg()"
        print "####################################"
        print ""
    if debugMode.lower() == "yes":
        print "./citeExtract.pl -m extract_citations " + LOCDB +"tmp/all-ref-text-"+filename[:-4]+".txt ", LOCDB + "tmp/" + filename +"_ParsIMG.xml"
    p = subprocess.Popen(["./citeExtract.pl -m extract_citations " + LOCDB +"tmp/all-ref-text-"+filename[:-4]+".txt ", LOCDB + "tmp/" + filename +"_ParsIMG.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
    parscitstring = p.communicate()[0]
    
    with open(LOCDB+"tmp/" + filename + "_ParsIMG.xml", 'w') as f:
        f.write(parscitstring)
    
    print "ParsCit Processing completed for: Image-based results"
    p = subprocess.Popen(["./citeExtract.pl -m extract_citations " + LOCDB +"tmp/all-text1-"+filename[:-4]+".txt ", LOCDB + "tmp/" + filename +"_ParsTXT.xml"],shell=True,stdout=subprocess.PIPE,cwd=parsCit)
    parscitstring = p.communicate()[0]
    
    with open(LOCDB+"tmp/" + filename + "_ParsTXT.xml", 'w') as f:
        f.write(parscitstring)
    
    print "ParsCit Processing completed for: only Text-based results"
    outputxmlsoup_unsorted = createBibstruct(filename, finalizedCoordinates, finalizedStrings)
    outputxmlsoup = sortResults(outputxmlsoup_unsorted,filename)
    
    # Removing Erronous Tags With Random Coordinates
    parsXmltags = outputxmlsoup.find_all('BibStructured')
    if debugMode.lower() == "yes":
        print "parsXmltags:",parsXmltags
    for completeSoup in parsXmltags:
        if debugMode.lower() == "yes":
            print ""
            print "completeSoup:",completeSoup
        if completeSoup.rawString.has_attr('coordinates'):
            if debugMode.lower() == "yes":
                print "Coordinates Exist..."
                print "completeSoup.rawString['coordinates']:",completeSoup.rawString['coordinates']
        else:
            if debugMode.lower() == "yes":
                print "Coordinates do not Exist..."
        if completeSoup.rawString.has_attr('coordinates') and completeSoup.rawString['coordinates'] == "0 0 0 0":
            if debugMode.lower() == "yes":
                print "//////////////////////////////////"
                print "completeSoup:",completeSoup
                print "completeSoup.rawString:",completeSoup.rawString
                print "//////////////////////////////////"
            completeSoup.decompose()
    if debugMode.lower() == "yes":
        print "parsXmltags:",parsXmltags
    
    settings = []
    settings.append("IMG")
    writeLog(filename, settings, True)
    os.remove(UPLOAD_FOLDER + filename)
    
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "creating Output Directory"
        print "####################################"
        print ""
    
    moveProcessedFiles(filename)
    os.remove(LOCDB+"tmp/" + filename)
    return outputxmlsoup

def bb_intersection(pbox, obox):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(pbox[0], obox[0])
    yA = max(pbox[1], obox[1])
    xB = min(pbox[2], obox[2])
    yB = min(pbox[3], obox[3])
    
    # compute the area of intersection rectangle
    interArea = max(0,(xB - xA)) * max(0,(yB - yA))        
    oboxArea = (obox[2] - obox[0] + 1) * (obox[3] - obox[1] + 1)    
    percent = float(interArea) / oboxArea
    
    return percent


def sortByCoordinates(coordinatesList,stringList):
    index1 = 0
    while index1 < len(coordinatesList):
        index2 = 0
        while index2 < len(coordinatesList)-1:
            if coordinatesList[index2][1] > coordinatesList[index2+1][1]:
                coordinatesList[index2],coordinatesList[index2+1] = coordinatesList[index2+1],coordinatesList[index2]
                stringList[index2],stringList[index2+1] = stringList[index2+1],stringList[index2]
            if coordinatesList[index2][1] == coordinatesList[index2+1][1]:
                if coordinatesList[index2][0] > coordinatesList[index2+1][0]:
                    coordinatesList[index2],coordinatesList[index2+1] = coordinatesList[index2+1],coordinatesList[index2]
                stringList[index2],stringList[index2+1] = stringList[index2+1],stringList[index2]
            index2 += 1
        index1 += 1
    return coordinatesList,stringList

def combineOcrOutputsTesseract(filename):
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In combineOcrOutputsTesseract()"
        print "####################################"
        print ""
    confidence_threshold = 0.75
    iou = 0.7
    mergedBoxesCoordinates = []
    mergedBoxesStrings = []
    
    ocrLines, ocrBoxes = parseHOCRTesseract(filename)
    
    if debugMode.lower() == "yes":
        print "len(ocrBoxes):",len(ocrBoxes),ocrBoxes
        print "len(ocrLines):",len(ocrLines)
    
    inferenceBoxes = []
    inferenceBoxes_confidence = []
    f = open(LOCDB +"tmp/"+"bbox-inference-results-"+filename[:-4]+".txt", "r")
    lines = f.readlines()
    f.close()
    
    name = None
    for line in lines:
        if line[0] == "\n":
            continue
        if line[0] == "/":
            name = line.split('/')[(len(line.split('/'))-1)]
            #print "name:",name
            if name.strip() == filename.strip():
                currFile = True
            else:
                currFile = False
            continue
        
        if currFile == True:
            chunks = line.strip().split(" ")
            inferenceBoxes.append([int(float(chunks[0])),int(float(chunks[1])),int(float(chunks[2])),int(float(chunks[3]))])
            inferenceBoxes_confidence.append(float(chunks[4]))
    if debugMode.lower() == "yes":
        print len(inferenceBoxes),len(inferenceBoxes_confidence)
        print len(ocrBoxes),len(ocrLines)
    iou2 = 0.5
    for curr4,currConfidence in zip(inferenceBoxes, inferenceBoxes_confidence):
        curr4 = [curr4[0],curr4[1],curr4[2],curr4[3]+10]
        if currConfidence >= confidence_threshold:
            tempBox = []
            tempBoxString = ""
            for curr3,currLine in zip(ocrBoxes,ocrLines):
                www = abs(bb_intersection(curr4, curr3))
                if www > 0:
                    if debugMode.lower() == "yes":
                        print ""
                        print "iou:",www
                        print currLine
                        print "curr4:",curr4
                        print "curr3:",curr3
                        print "tempBox:",tempBox
                
                if abs(bb_intersection(curr4, curr3)) > iou2:
                    tempBox.append(curr3)
                    tempBoxString += " "+currLine
                else:
                    continue
            
            tempBoxString = tempBoxString.strip()
            temp_x1 = []
            temp_y1 = []
            temp_x2 = []
            temp_y2 = []
            if len(tempBox) > 0:
                for curr5 in tempBox:
                    temp_x1.append(curr5[0])
                    temp_y1.append(curr5[1])
                    temp_x2.append(curr5[2])
                    temp_y2.append(curr5[3])
            else:
                continue
            
            if abs(bb_intersection(curr4, [min(temp_x1), min(temp_y1), max(temp_x2), max(temp_y2)],)) > iou:
                if debugMode.lower() == "yes":
                    print "tempBoxString:",tempBoxString
                mergedBoxesCoordinates.append([min(temp_x1), min(temp_y1), max(temp_x2), max(temp_y2)])
                mergedBoxesStrings.append(tempBoxString)
            
    tempRead = open(LOCDB+"dummy.txt","r")
    dummyText = tempRead.read()
    tempRead.close()
    if debugMode.lower() == "yes":
        print len(mergedBoxesStrings)
    
    tempFile4 = open(LOCDB +"tmp/"+"all-ref-text-"+filename[:-4]+".txt","w") 
    tempFile4.write(dummyText+"\n")
    tempFile4.write("\n")
    
    for ind, currStr in enumerate(mergedBoxesStrings):
        if debugMode.lower() == "yes":
            print "type(currStr):",type(currStr)
            print "currStr:",currStr
        tempFile4.write(str(ind+1)+".\t"+str(currStr.encode("utf8"))+"\n")
        tempFile4.write("\n")
    tempFile4.close()
    if debugMode.lower() == "yes":
        print len(mergedBoxesCoordinates),len(mergedBoxesStrings)
    return mergedBoxesCoordinates,mergedBoxesStrings


def levenshtein(seq1, seq2): 
    if isinstance(seq1, unicode):
        seq1 = seq1.encode('utf8')
    if isinstance(seq2, unicode):
        seq2 = seq2.encode('utf8')
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))
    for x in xrange(size_x):
        matrix [x, 0] = x
    for y in xrange(size_y):
        matrix [0, y] = y

    for x in xrange(1, size_x):
        for y in xrange(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return (matrix[size_x - 1, size_y - 1])


def mapXmlOutputIndividual(xmlstring):
    if debugMode.lower() == "yes":
        print ""
        print " In mapXmlOutputIndividual()"
        print ""
    soup = bs.BeautifulSoup('<algorithm name="LOCDB Web service"></algorithm>','xml')
    algotag = soup.algorithm    
    parsXmlsoup = bs.BeautifulSoup(xmlstring.decode('utf-8', 'ignore'),'xml')
     
    reftags= parsXmlsoup.find_all('biblStruct')  
    if debugMode.lower() == "yes":
        print "reftags:",reftags
    for currref in reftags:
        soup2 = bs.BeautifulSoup('<BibStructured></BibStructured>','xml')
        citationtag = soup2.BibStructured                
        authorstags= currref.find_all('author')
        tempAuthors = []
        for currAuthor in authorstags:
            temp_name = ""
            fname = ""
            mname = ""
            lname = ""
            currfName = currAuthor.find_all('forename',type="first")
            currmName = currAuthor.find_all('forename',type="middle")
            currlName = currAuthor.find_all('surname')
            
            for name1 in currfName:      
                fname = name1.string
            for name2 in currmName:      
                mname = name2.string
            for name3 in currlName:      
                lname = name3.string
            if debugMode.lower() == "yes":
                print "fname:",fname
                print "mname:",mname
                print "lname:",lname
            if (mname != "") and (mname != None):
                temp_name = fname+" "+mname+" "+lname
            else:
                temp_name = fname+" "+lname
            
            tempAuthors.append(temp_name.encode('utf8').strip())
        
        if len(tempAuthors) > 0:
            soup3 = bs.BeautifulSoup('<authors></authors>','xml')
            authorstag2 = soup3.authors
            
            for curr1 in tempAuthors:
                soup4 = bs.BeautifulSoup('<author></author>','xml')
                tempAuthorTag2 = soup4.author
                tempAuthorTag2.string = curr1
                authorstag2.append(tempAuthorTag2)
            
            citationtag.append(authorstag2)
            if debugMode.lower() == "yes":
                print "tempAuthors:",tempAuthors
                print "algotag:",algotag
        
        titletags = currref.find_all('title', level='a')
        if titletags == []:
            titletags = currref.find_all('title', level='m')
        tempTitle = ""
        for currtitle in titletags:
            if debugMode.lower() == "yes":
                print "currtitle:",currtitle
            tempTitle = tempTitle+currtitle.string+" "
        
        if tempTitle.strip() != "":
            soup3 = bs.BeautifulSoup('<title></title>','xml')
            titletag2 = soup3.title
            titletag2.string = tempTitle.encode('utf8').strip()
            citationtag.append(titletag2)
            if debugMode.lower() == "yes":
                print "tempTitle:",tempTitle.strip()
        
        journaltags= currref.find_all('title', level='j')
        tempJournal = ""
        for currjournal in journaltags:
            tempJournal = tempJournal+currjournal.string+" "
        
        if tempJournal.strip() != "":
            soup3 = bs.BeautifulSoup('<journal></journal>','xml')
            journaltag2 = soup3.journal
            journaltag2.string = tempJournal.encode('utf8').strip()
            citationtag.append(journaltag2)
            if debugMode.lower() == "yes":
                print "tempJournal:",tempJournal.strip()
        
        datetag= currref.find('date',type="published")
        if datetag != None:
            tempdate = datetag['when']
            soup3 = bs.BeautifulSoup('<date></date>','xml')
            datetag2 = soup3.date
            datetag2.string = tempdate
            citationtag.append(datetag2)
            
            if debugMode.lower() == "yes":
                print "tempdate:",tempdate
        
        temppublisher = ""
        publishertag= currref.find('publisher')
        if publishertag != None:
            temppublisher = publishertag.string
            soup3 = bs.BeautifulSoup('<publisher></publisher>','xml')
            publishertag2 = soup3.publisher
            publishertag2.string = temppublisher
            citationtag.append(publishertag2)
            
            if debugMode.lower() == "yes":
                print "temppublisher:",temppublisher
        
        templocation = ""
        locationtag= currref.find('pubPlace')
        if locationtag != None:
            templocation = locationtag.string
            soup3 = bs.BeautifulSoup('<location></location>','xml')
            locationtag2 = soup3.location
            locationtag2.string = templocation
            citationtag.append(locationtag2)
            
            if debugMode.lower() == "yes":
                print "templocation:",templocation
        
        tempvolume = ""
        volumetag= currref.find('biblScope', unit="volume")
        if volumetag != None:
            tempvolume = volumetag.string
            soup3 = bs.BeautifulSoup('<volume></volume>','xml')
            volumetag2 = soup3.volume
            volumetag2.string = tempvolume
            citationtag.append(volumetag2)
            
            if debugMode.lower() == "yes":
                print "tempvolume:",tempvolume
        
        tempissue = ""
        issuetag= currref.find('biblScope', unit="issue")
        if issuetag != None:
            tempissue = issuetag.string
            soup3 = bs.BeautifulSoup('<issue></issue>','xml')
            issuetag2 = soup3.issue
            issuetag2.string = tempissue
            citationtag.append(issuetag2)
            
            if debugMode.lower() == "yes":
                print "tempissue:",tempissue    
        
        temppages = ""
        pagestag= currref.find('biblScope', to=True)
        if pagestag != None:
            temppages = pagestag['from']+"-"+pagestag['to']
        else:
            pagestag= currref.find('biblScope', unit="page")
            if pagestag != None:
                temppages = pagestag.string
            
        if temppages != "":
            soup3 = bs.BeautifulSoup('<pages></pages>','xml')
            pagestag2 = soup3.pages
            pagestag2.string = temppages
            citationtag.append(pagestag2)
            if debugMode.lower() == "yes":
                print "temppages:",temppages
        
        if debugMode.lower() == "yes":
            print ""
        algotag.append(citationtag)
    return soup

def processIndividualGrobid(tempString):
    grobid_url = grobid+"processCitation"
    files = {}
    values = {'citations': tempString}
    try:
        response = requests.post(grobid_url, files=files, data=values)
    except:
        return "Error accessing Grobid Service"
    
    xmlString = response.text.encode('utf8')
    if debugMode.lower() == "yes":
        print "xmlString:",type(xmlString)
        print xmlString
        print ""
        print ""
    return mapXmlOutputIndividual(xmlString)

def processSegment(filename, coordinates): 
    try:
        if filename and coordinates:
            if debugMode.lower() == "yes":
                print ""
                print "filename:",filename
                print "coordinates:",coordinates

            f1 = open(LOCDB +"processed-files/"+"all-text1-"+filename[0][:-4]+".txt", "r")
            temp_lines = f1.readlines()
            f1.close()
            
            f2 = open(LOCDB +"processed-files/"+"all-text-boxes-"+filename[0][:-4]+".txt", "r")
            temp_boxes = f2.readlines()
            f2.close()
            
            lines_found = ""
            boxes_found = []
            for curr1,curr2  in zip(temp_boxes,temp_lines):
                curr1 = curr1.split(' ')
                curr1 = map(int, curr1)
                temp_iou = bb_intersection(coordinates, curr1)
                
                if abs(temp_iou) >= 0.5:
                    lines_found = lines_found+curr2.strip()+" "
                    boxes_found.append(curr1)
                    
            lines_found = lines_found.strip()
            temp_x1 = []
            temp_y1 = []
            temp_x2 = []
            temp_y2 = []
            if len(boxes_found) > 0:
                for curr5 in boxes_found:
                    temp_x1.append(curr5[0])
                    temp_y1.append(curr5[1])
                    temp_x2.append(curr5[2])
                    temp_y2.append(curr5[3])
                finalBox = [min(temp_x1), min(temp_y1), max(temp_x2), max(temp_y2)]
                
                if debugMode.lower() == "yes":
                    print "boxes_found:",boxes_found
                    print "finalBox:",finalBox
                    print "lines_found:",lines_found
                output = processIndividualGrobid(lines_found)                
                soup = bs.BeautifulSoup('<rawString></rawString>','xml')
                rawStringTag = soup.rawString
                rawStringTag.string = lines_found
                rawStringTag['coordinates'] = str(finalBox[0])+" "+str(finalBox[1])+" "+str(finalBox[2])+" "+str(finalBox[3])
                tag4 = output.algorithm.BibStructured
                tag4['detector'] = 'Image'
                tag4['namer'] = 'Grobid'
                output.algorithm.BibStructured.append(rawStringTag)
                if debugMode.lower() == "yes":
                    print output
                return str(output)
            else:
                return 'Error: No text found in given coordinates'
        else:
            return "Error: No valid coordinates or filename"
    except:
        return 'Error: Error processing the given coordinates'

def sortResults(xmlsoup,filename):
    xmltags= xmlsoup.find_all('BibStructured')
    
    if debugMode.lower() == "yes":
        i = 0
        while i < len(xmltags):
            print xmltags[i].rawString['coordinates']
            i += 1
    
    for i,curr1 in enumerate(xmltags):
        for j,curr2 in enumerate(xmltags):
            if int(xmltags[i].rawString['coordinates'].strip().split(' ')[1]) < int(xmltags[j].rawString['coordinates'].strip().split(' ')[1]):
                 xmltags[i], xmltags[j] =  xmltags[j], xmltags[i]
    if debugMode.lower() == "yes":
        print ""
        i = 0
        while i < len(xmltags):
            print xmltags[i].rawString['coordinates']
            i += 1
    
    soup = bs.BeautifulSoup("<algorithm></algorithm>",'xml')
    algotag = soup.algorithm
    algotag['name']='LOCDB Web service'
    algotag['fname']=filename.split("_",1)[1]
    for curr in xmltags:
        algotag.append(curr)
    
    return soup
     
def moveProcessedFiles(filename):
    os.system("mv "+LOCDB+"tmp/"+filename+".pdf "+LOCDB+"processed-files/"+filename+".pdf")
    os.system("mv "+LOCDB+"tmp/"+filename+"_ParsIMG.xml "+LOCDB+"processed-files/"+filename+"_ParsIMG.xml")
    os.system("mv "+LOCDB+"tmp/"+filename+"_ParsTXT.xml "+LOCDB+"processed-files/"+filename+"_ParsTXT.xml")
    os.system("mv "+LOCDB+"tmp/"+filename[:-4]+" "+LOCDB+"processed-files")
    os.system("mv "+LOCDB+"tmp/all-text-indeces-"+filename[:-4]+".txt "+LOCDB+"processed-files/all-text-indeces-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"tmp/all-text-boxes-"+filename[:-4]+".txt "+LOCDB+"processed-files/all-text-boxes-"+filename[:-4]+".txt")    
    os.system("mv "+LOCDB+"tmp/bbox-inference-results-"+filename[:-4]+".txt "+LOCDB+"processed-files/bbox-inference-results-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"tmp/all-ref-text-"+filename[:-4]+".txt "+LOCDB+"processed-files/all-ref-text-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"tmp/all-text1-"+filename[:-4]+".txt "+LOCDB+"processed-files/all-text1-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"tmp/all-text2-"+filename[:-4]+".txt "+LOCDB+"processed-files/all-text2-"+filename[:-4]+".txt")
    os.system("mv "+LOCDB+"images-tmp/"+filename+" "+LOCDB+"images/" + filename)

    