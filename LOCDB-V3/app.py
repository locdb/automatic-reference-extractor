# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, Response, send_file
#from flask_sslify import SSLify
from werkzeug.utils import secure_filename

from fileProcessor import processFile, check_file_extension, createResultView, findLatest, coordinatesLookup, filterCropFiles
from logWriter import writeLog, writeUserLog, updateHTML
from pathParameter import LOCDB, detectronDir, outputPath, modelPath, imagesDir, annotationsDir, debugMode
import zipfile
from io import BytesIO
from werkzeug.serving import WSGIRequestHandler
import json
from bs4 import BeautifulSoup
import subprocess

from rq import Queue
from rq.job import Job
from worker import conn

UPLOAD_FOLDER = 'upload/'
OUTPUT_FOLDER = 'output/'
ALLOWED_EXTENSIONS = set([ 'pdf', 'png', 'jpg', 'jpeg','tif','xml','odt','doc','docx','txt', 'htm', 'html', 'xhtml'])
Settings = ["Unknown", "True"]
MAX_PROCESSES = 1

#refresh userlogLOCDB
if os.path.exists("visibleUserLog.txt"):
    os.remove("visibleUserLog.txt")
with open("visibleUserLog.txt", "w") as f:
    f.write("To get information if a uploaded file is finished press the update button.\nIt updates on every request. \nThis is the user log.\n")

# Initialize the Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key"

q = Queue(connection=conn)


# Define a route for the default URL, which loads the form
@app.route('/')
def form():
    writeUserLog("App started")
    return updateHTML()

#updates the user log
@app.route('/logupdate/', methods=['GET','POST'])
def logupdate():
    return updateHTML()

@app.route('/fileupload/', methods=['GET','POST'])
def fileupload(): 
    if debugMode.lower() == "yes":
        print ""
        print "####################################"
        print "In fileupload()"
        print "####################################"
        print ""
        
    #checks the upload request parameters and stores it to the upload folder
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part')
            return redirect(request.url)
        #requested files and pdf mode are retrieved from flask
        fileList = request.files.getlist('files')
        if request.form.get('pdfFlag'):
            Settings[0] = "IMG"
        else:
            Settings[0] = "TXT"
        if request.form.get('Txt_Dummy'):
            Settings[1] = "True"
        else:
            Settings[1] = "False"
        
        autoview = False
        if request.form.get('autoviewResults'):
            autoview = True
        filenameFP_List = []
        filenameString =""
        for uploadedFile in fileList:
            if uploadedFile.filename == '':
                flash('No selected inputfile')
                return redirect(request.url)
            if uploadedFile and check_file_extension(uploadedFile.filename, ALLOWED_EXTENSIONS):
                filenameFP = secure_filename(uploadedFile.filename)
                print 'Uploaded inputfile : '+filenameFP
                print ""
                writeUserLog("Uploaded inputfile : " + filenameFP)
                #adding timestamp
                ts= datetime.now().strftime('%Y%m%d%H%M%S')
                filenameFP= ts+"_" + filenameFP
                writeLog(filenameFP,Settings, False)
                uploadedFile.save(os.path.join(LOCDB+UPLOAD_FOLDER, filenameFP))
                filenameFP_List.append(filenameFP)
                filenameString += filenameFP + "\n"
            else:
                return "Error: Invalid file extension..."
        try:
            job = q.enqueue_call(
            func=processFile, args=(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES, Settings, filenameFP_List,), result_ttl=8000, timeout=10000
            )
            print(job.get_id())
            
            return job.get_id()
            
            #sync process
            result = createResultView(OUTPUT_FOLDER, filenameFP_List)
            return Response(result, content_type='text/xml; charset=utf-8')
        except:
            return "An Error occured during file processing..."
        
        if autoview:
            return render_template("form_submitocr.html",waiting="1",filesText = filenameString)
        else: 
            return updateHTML()
            
    return "Error"


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)
    
    if job.is_finished:
        return job.result, 200
    else:
        return "In Processing!", 202

#method that checks if result is ready and after that returs it
@app.route('/pollresult/', methods=['GET','POST'])
def pollresult():
    fileString = request.form.get('filenames_field')
    resultList = []
    file_list = fileString.strip().splitlines()
    for file in file_list:
        for folder in os.listdir("upload"):
            if file in folder:
                resultList.append(folder)
    if len(resultList) == 0:
        result = createResultView(OUTPUT_FOLDER, file_list)
        return Response(result, content_type='text/xml; charset=utf-8')  
    else:
        return render_template("form_submitocr.html",waiting="1",filesText = fileString)

       
# Method used for the file browser to view already finished files
@app.route('/fileview/', methods=['GET','POST'])
def fileview():
    #checks the upload and stores it to the upload folder
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part')
            return redirect(request.url)
        #requested files and pdf mode are retrieved from flask
        fileList = request.files.getlist('files')
        filenameFP_List = []
        for uploadedFile in fileList:
            if uploadedFile.filename == '':
                flash('No selected inputfile')
                return redirect(request.url)    
            if uploadedFile and check_file_extension(uploadedFile.filename, ALLOWED_EXTENSIONS):
                filenameFP = secure_filename(uploadedFile.filename)
                print "filenameFP:",filenameFP
                filenameFP_List.append(filenameFP)
                
        if debugMode.lower() == "yes":
            print "filenameFP_List:",filenameFP_List
            print "OUTPUT_FOLDER:",OUTPUT_FOLDER
        result = createResultView(OUTPUT_FOLDER, filenameFP_List, 2)
        
        return Response(result, content_type='text/xml; charset=utf-8')
    
    return "Error: Results not found"

# method used for the file browser to view already finished files
@app.route('/getimage/', methods=['GET', 'POST'])
def getimage():
    # checks the upload and stores it to the upload folder
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        # requested files and pdf mode are retrieved from flask
        fileList = request.files.getlist('files')
        securefname = secure_filename(fileList[0].filename)
        
        if os.path.splitext(securefname)[1].lower() == ".pdf":
            filenameFP_List = []
            for uploadedFile in fileList:
                if uploadedFile.filename == '':
                    flash('No selected inputfile')
                    return redirect(request.url)
                if uploadedFile and check_file_extension(uploadedFile.filename, ALLOWED_EXTENSIONS):
                    filenameFP = secure_filename(uploadedFile.filename)
                    filenameFP_List.append(filenameFP)
            
            allFilenames3 = os.listdir("images")
            tempFilesList = []
            for currFile1 in filenameFP_List:
                for currFile2 in allFilenames3:
                    if currFile1[:-4] in currFile2:
                        tempFilesList.append(currFile2)
                
                if debugMode.lower() == "yes":
                    print "tempFilesList:",len(tempFilesList)
                
                tempFilesList = filterCropFiles(tempFilesList)
                if len(tempFilesList) != 0:
                    latestFileNames = findLatest(tempFilesList)
                    
                    if debugMode.lower() == "yes":
                        print "latestFileNames:",latestFileNames
                    
                    currDir = os.getcwd()
                    os.chdir(LOCDB+"images/")
                    memory_file = BytesIO()
                    with zipfile.ZipFile(memory_file, 'w') as zf:
                        for individualFile in latestFileNames:
                            zf.write(individualFile)
                    os.chdir(currDir)
                    memory_file.seek(0)
                    return send_file(memory_file, attachment_filename=currFile1+'.zip', as_attachment=True)
                else:
                    return "Error: No Files Found..."
        else:
            return "Wrong File Type: Please upload a pdf file"

    return "Error: Results not found"

@app.route('/segmentReference/', methods = ['POST', 'GET'])
def segmentReference():
    if request.method == 'POST':      
        filename = request.form.get('filename').encode('utf8')
        if debugMode.lower() == "yes":
            print "filename:",filename
        coordinates = request.form.get('coordinates')
        coordinates = coordinates.strip().split(' ')
        
        if debugMode.lower() == "yes":
            print "coordinates:",coordinates
        coordinates = map(int, coordinates)
        
        if filename and coordinates:
            # For single filename only
            filename = [filename]
            tempFilesList = []
            for currFile1 in filename:
                for currFile2 in os.listdir("images"):
                    if currFile1[:-4] in currFile2:
                        tempFilesList.append(currFile2)
            latest_filename = findLatest(tempFilesList)
          
            try:
                result = coordinatesLookup(latest_filename,coordinates)
                return Response(result, content_type='text/xml; charset=utf-8')
            except ValueError:
                return "Error processing the given coordinates"
                
    return 'Error: Results not found'

@app.route('/uploadCorrections/', methods = ['POST'])
def upload_corrections():
   if request.method == 'POST':
      allowed_extensions = ['jpg','png','jpeg','tif'] 
      
      f = request.files.getlist('files')
      if debugMode.lower() == "yes":
          print "files:",f
      for curr in f:
          securedFilename = secure_filename(curr.filename)
          if securedFilename[-3:].lower() == "xml":
              curr.save(os.path.join(annotationsDir+securedFilename))
          elif securedFilename[-3:].lower() in allowed_extensions:
              curr.save(os.path.join(imagesDir+securedFilename))
          else:
              return "Unsupported File Found: Please use jpg, png, jpeg, tif and xml extensions only."
          
      return 'File uploaded successfully'

@app.route('/triggerTraining/', methods = ['POST'])
def trigger_training():
    outputFile = "annotations-finetune.json"
    
    filenames_unique = []
    width = []
    height = []
    filenames = []
    x1 =[]
    y1 =[]
    x2 =[]
    y2 =[]
    
    allFilenames = []
    for (dirpath, dirnames, filenames1) in os.walk(annotationsDir):
        allFilenames.extend(filenames1)
        break
    
    allFilenames2 = []
    for (dirpath, dirnames, filenames1) in os.walk(imagesDir):
        allFilenames2.extend(filenames1)
        break
    
    if len(allFilenames) == 0:
        return "No files available for training..."
    
    if len(allFilenames) != len(allFilenames2):
        return "Error: Missing annotation or image files..."
    
    if os.path.isfile(modelPath+"model_final.pkl"):
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        os.system("mv "+modelPath+"model_final.pkl "+ modelPath+ts+"_"+"model_final.pkl")
    
    for currFile in allFilenames:
        with open(annotationsDir+currFile) as f:
            xmldata = f.read().encode('utf-8')
            parsXmlsoup = BeautifulSoup(xmldata,'xml')            
            tempname = parsXmlsoup.filename.string
            if (tempname[-3:]).lower() != "jpg":
                if tempname[-1] == ".":
                    tempname = tempname + "jpg"
                else:
                    tempname = tempname + ".jpg"
            
            if not (parsXmlsoup.filename.string in filenames_unique):
                filenames_unique.append(tempname)
                width.append(int(parsXmlsoup.size.width.string))
                height.append(int(parsXmlsoup.size.height.string))
            
            xmltags= parsXmlsoup.find_all('bndbox')
            for curr in xmltags:
                filenames.append(tempname)
                x1.append(int(curr.xmin.string))
                y1.append(int(curr.ymin.string))
                x2.append(int(curr.xmax.string))
                y2.append(int(curr.ymax.string))
                
    data = {}
    images_list = []
    annotations_list = []
    categories_list = []
    for index, currImage in enumerate(filenames_unique):
        images_dict = dict()
        images_dict["file_name"] = currImage
        images_dict["height"] = height[index]
        images_dict["width"] = width[index]
        images_dict["id"] = index+1
        images_list.append(images_dict)
    
    annotation_id = 1
    for temp_image,tempx1,tempy1,tempx2,tempy2 in zip(filenames,x1,y1,x2,y2):
        temp_id = filenames_unique.index(temp_image)
        temp_box_height = tempy2 - tempy1
        temp_box_width = tempx2 - tempx1
        segmentation_dict = dict()
        segmentation_dict["segmentation"] = [[tempx1,tempy1,tempx1,tempy1+temp_box_height,tempx1+temp_box_width,tempy1+temp_box_height,tempx1+temp_box_width,tempy1]]
        segmentation_dict["area"] = temp_box_height * temp_box_width
        segmentation_dict["iscrowd"] = 0
        segmentation_dict["image_id"] = temp_id+1
        segmentation_dict["id"] = annotation_id
        segmentation_dict["bbox"] = [tempx1,tempy1,temp_box_width,temp_box_height]
        segmentation_dict["category_id"] = 1     # Fixed (Reference Class)
        segmentation_dict["ignore"] = 0
        annotations_list.append(segmentation_dict)
        annotation_id += 1
        
    categories_dict = dict()
    categories_dict["supercategory"] = "none"
    categories_dict["id"] = 1
    categories_dict["name"] = "reference"
    categories_list.append(categories_dict)
    data['images'] = images_list
    data["type"] = "instances"
    data["annotations"] = annotations_list
    data["categories"] = categories_list
    
    with open(outputPath+outputFile, 'w') as outfile:  
        json.dump(data, outfile)
    
    try:
        subprocess.call(["python2 tools/train_net.py --cfg configs/custom/e2e_mask_rcnn_R-50-C4_1x-LOCDB-finetune.yaml"], shell=True, cwd=detectronDir)
    except:
        return "An Error occured during network training..."
    
    os.system("rm "+annotationsDir+"*")
    os.system("rm "+imagesDir+"*")
    
    return 'Training Finished...'

# Run the app :)
if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run( 
        host="0.0.0.0",
        port=int("8000")
    )
    #sslify = SSLify(app)