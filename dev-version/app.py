# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
import os
import shutil
import time

from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory, Response, send_file
#from flask_sslify import SSLify
from multiprocessing import Pool
from werkzeug.utils import secure_filename

from fileProcessor import processFile, check_file_extension, processRestore, mergeOutputXML, createResultView, findLatest
from logWriter import writeLog, writeUserLog, updateHTML
from pathParameter import ocropy
from time import sleep
from distutils.filelist import FileList


'''
Requirements:
parscit -> get citation information
pdf-inspector -> converts pdfs to txt
libre office -> converts different text extensions to txt
imageMagick -> to convert the pdf to png
pdftk -> to get the number of pages in the pdf

Configuration:
UPLOAD_FOLDER: the upload directory
OUTPUT_FOLDER: the output directory
ALLOWED_EXTENSIONS: the allowed formats for the processing
Settings:
    ProcessingType is Unknown for first run and set during processing
    Text_dummy does text files need a dummy or not
    number of columns - 1 the file has (singlepage = 0 , doublepage = 1)
MAX_PROCESSES: number of parallel processes
'''

UPLOAD_FOLDER = 'upload/'
OUTPUT_FOLDER = 'output/'
ALLOWED_EXTENSIONS = set([ 'pdf', 'png', 'jpg', 'jpeg','tif','xml','odt','doc','docx','txt'])
Settings = ["Unknown", "True"]
#Settings = ["Unknown", "True","0"]
MAX_PROCESSES = 1

#refresh userlog
if os.path.exists("visibleUserLog.txt"):
    os.remove("visibleUserLog.txt")
with open("visibleUserLog.txt", "w") as f:
    f.write("To get information if a uploaded file is finished press the update button.\nIt updates on every request. \nThis is the user log.\n")

# Initialize the Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key"


# Define a route for the default URL, which loads the form
@app.route('/')
def form():
    #return render_template('form_submitocr.html')
    writeUserLog("App started")
    return updateHTML()

#processes the files from last startup with correct settings
@app.route('/restoreprocess/', methods=['GET','POST'])
def restoreprocess():
    if os.path.exists("tmp/"):
        shutil.rmtree("tmp/")
    os.makedirs("tmp/")
    ocroFiles = ocropy + "/processedFiles/"
    if os.path.exists(ocroFiles):
        shutil.rmtree(ocroFiles)
    print "Restarted at timestamp: " + datetime.now().strftime('%Y%m%d%H%M%S')
    writeUserLog("Restarted the app")
    processRestore(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES)
    #return redirect('/')
    return updateHTML()

#restarts the app and reset everything
@app.route('/resetapp/', methods=['GET','POST'])
def resetapp():
    if os.path.exists("upload/"):
        shutil.rmtree("upload/")
    if os.path.exists("tmp/"):
        shutil.rmtree("tmp/")
    ocroFiles = ocropy + "/processedFiles/"
    if os.path.exists(ocroFiles):
        shutil.rmtree(ocroFiles)
    if os.path.exists("processLog.txt"):
        os.remove("processLog.txt")
    if os.path.exists("visibleUserLog.txt"):
        os.remove("visibleUserLog.txt")
    os.makedirs("upload/")
    os.makedirs("tmp/")
    with open("processLog.txt", "w") as f:
        f.write("")
    with open("visibleUserLog.txt", "w") as f:
        f.write("")
    print "Cleared App at timestamp: " + datetime.now().strftime('%Y%m%d%H%M%S')
    writeUserLog("Resetted the app")
    #return redirect("/")
    return updateHTML()

#removes all output files
@app.route('/deleteoutput/', methods=['GET','POST'])
def deleteoutput():
    if os.path.exists("output/"):
        shutil.rmtree("output/")
    os.makedirs("output/")
    print "Output removed at timestamp: " + datetime.now().strftime('%Y%m%d%H%M%S')
    writeUserLog("Output removed")
    #return redirect("/")
    return updateHTML()

#sets the number of parallel processes
@app.route('/setprocesses/', methods=['GET','POST'])
def setprocesses():
    MAX_PROCESSES = int(request.form.get('processes'))
    print "Set number of parallel to " + str(MAX_PROCESSES) + " processes at timestamp: " + datetime.now().strftime('%Y%m%d%H%M%S')
    writeUserLog("Parallel number of processes set to " + str(MAX_PROCESSES))
    #return redirect("/") 
    return updateHTML()


#updates the user log
@app.route('/logupdate/', methods=['GET','POST'])
def logupdate():
    return updateHTML()

@app.route('/fileupload/', methods=['GET','POST'])
def fileupload():
    #checks the upload and stores it to the upload folder
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
        #if request.form.get('colBool'):
            #Settings[2] = str(int(request.form.get('colNumb')) - 1)
        #else:
            #Settings[2] = "0"
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
                writeUserLog("Uploaded inputfile : " + filenameFP)
                #adding timestamp
                ts= datetime.now().strftime('%Y%m%d%H%M%S')
                filenameFP= ts+"_" + filenameFP
                writeLog(filenameFP,Settings, False)
                uploadedFile.save(os.path.join(UPLOAD_FOLDER, filenameFP))
                filenameFP_List.append(filenameFP)
                filenameString += filenameFP + "\n"
        
        processFile(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES, Settings, filenameFP_List)
        
        #sync process
        result = createResultView(OUTPUT_FOLDER, filenameFP_List)
        return Response(result, content_type='text/xml; charset=utf-8')
        
        if autoview:
            return render_template("form_submitocr.html",waiting="1",filesText = filenameString)
        else: 
            return updateHTML()
            
    return "Error"


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
    
          
#method used for the file browser to view already finished files
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
                filenameFP_List.append(filenameFP)    
    
        result = createResultView(OUTPUT_FOLDER, filenameFP_List)
        
        return Response(result, content_type='text/xml; charset=utf-8')
    
    return "Error"


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
        # print "securefname",securefname,type(securefname)
        # print "fileList[0]",fileList[0]
        # print "+++++++++++++++++++++",os.path.splitext(securefname)[1].lower()
        if os.path.splitext(securefname)[1].lower() == ".pdf":
            #print "Correct File Format..."
            filenameFP_List = []
            for uploadedFile in fileList:
                if uploadedFile.filename == '':
                    flash('No selected inputfile')
                    return redirect(request.url)
                if uploadedFile and check_file_extension(uploadedFile.filename, ALLOWED_EXTENSIONS):
                    filenameFP = secure_filename(uploadedFile.filename)
                    filenameFP_List.append(filenameFP)

            resultList = []
            missList = []
            # find files
            for file in filenameFP_List:
                found = False
                for folder in os.listdir("output"):
                    if file in folder:
                        resultList.append(folder)
                        found = True
                if not found:
                    missList.append(file)
            if len(missList) > 0:
                return "Error: No such processed file found with name ",missList[0]
            results = findLatest(resultList)
            #print "results :",results
            image_path = OUTPUT_FOLDER+results[0]+"/"+results[0]+".png"
            if os.path.isfile(image_path):
                return send_file(image_path, mimetype="image/png")
            else:
                return "Error: No such processed file found with name ",results[0]
        else:
            return "Wrong File Type: Please upload a pdf file"

    return "Error"

# Run the app :)
if __name__ == '__main__':
    app.run( 
        host="0.0.0.0",
        port=int("8000")
    )
    #sslify = SSLify(app)
