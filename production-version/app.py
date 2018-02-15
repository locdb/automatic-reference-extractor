# We need to import request to access the details of the POST request
# and render_template, to render our templates (form and response)
# we'll use url_for to get some URLs for the app on the templates
import os
import shutil

from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename

from fileProcessor import processFile, check_file_extension, processRestore, mergeOutputXML
from logWriter import writeLog
from pathParameter import ocropy


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
    number of colums - 1 the file has (singlepage = 0 , doublepage = 1)
MAX_PROCESSES: number of parallel processes
'''

UPLOAD_FOLDER = 'upload/'
OUTPUT_FOLDER = 'output/'
ALLOWED_EXTENSIONS = set([ 'pdf', 'png', 'jpg', 'jpeg','tif','xml','odt','doc','docx','txt'])
Settings = ["Unknown", "True","0"]
MAX_PROCESSES = 1


# Initialize the Flask application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Define a route for the default URL, which loads the form
@app.route('/')
def form():
    return render_template('form_submitocr.html')


#processes the files from last startup with correct settings
@app.route('/restoreprocess/', methods=['GET','POST'])
def restoreprocess():
    if os.path.exists("tmp/"):
        shutil.rmtree("tmp/")
    os.makedirs("tmp/")
    ocroFiles = ocropy + "/processedFiles/"
    if os.path.exists(ocroFiles):
        shutil.rmtree(ocroFiles)
    print "Restarted at timestamp: " + datetime.now().strftime('%m%d%H%M%S')
    processRestore(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES)
    return redirect('/')


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
    os.makedirs("upload/")
    os.makedirs("tmp/")
    with open("processLog.txt", "w") as f:
        f.write("")
    print "Cleared App at timestamp: " + datetime.now().strftime('%m%d%H%M%S')
    return redirect("/")


#removes all output files
@app.route('/deleteoutput/', methods=['GET','POST'])
def deleteoutput():
    if os.path.exists("output/"):
        shutil.rmtree("output/")
    os.makedirs("output/")
    print "Output removed at timestamp: " + datetime.now().strftime('%m%d%H%M%S')
    return redirect("/")


#sets the number of parallel processes
@app.route('/setprocesses/', methods=['GET','POST'])
def setprocesses():
    MAX_PROCESSES = int(request.form.get('processes'))
    print "Set number of parallel to " + str(MAX_PROCESSES) + " processes at timestamp: " + datetime.now().strftime('%m%d%H%M%S')
    return redirect("/")


@app.route('/fileupload/', methods=['GET','POST'])
def fileupload():
    print ""
    print ""
    print "----------------------------------------"
    print "request: ",request
    print "request.files: ",request.files
    print "request.url: ",request.url
    print "request.form: ",request.form
    print "----------------------------------------"
    print ""
    print ""
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
        if request.form.get('colBool'):
            Settings[2] = str(int(request.form.get('colNumb')) - 1)
        else:
            Settings[2] = "0"
        filenameFP_List = []
        for uploadedFile in fileList:
            if uploadedFile.filename == '':
                flash('No selected inputfile')
                return redirect(request.url)    
            if uploadedFile and check_file_extension(uploadedFile.filename, ALLOWED_EXTENSIONS):
                filenameFP = secure_filename(uploadedFile.filename)
                print 'Uploaded inputfile : '+filenameFP
                #adding timestamp
                ts= datetime.now().strftime('%m%d%H%M%S')
                filenameFP= ts+"_" + filenameFP
                writeLog(filenameFP,Settings, False)
                uploadedFile.save(os.path.join(UPLOAD_FOLDER, filenameFP))
                filenameFP_List.append(filenameFP)
        processFile(UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_PROCESSES, Settings, filenameFP_List)
        return mergeOutputXML(OUTPUT_FOLDER, filenameFP_List)
        #return redirect("/")
        
    return "Error"


# Run the app :)
if __name__ == '__main__':
    app.run( 
        host="0.0.0.0",
        port=int("8080")
    )
