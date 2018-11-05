'''
Please comment the correct ABSOLUT paths for the dependencies and 
do not forget to change the input and output paths if you do not want the default one.
For the upload and output folders change the paths in the app.py 
'''
# Directory which contains the locdb app plus slash
LOCDB = "/home/<username>/LOCDB-V3/"

# Directory which contains parscit for the reference extraction (bin Directory in ParsCit)
parsCit = ""

# Directory in which the jar of pdf inspector is located to convert pdf to txt
# name of the jar should be: "docears-pdf-inspector.jar"
pdfInspector = ""

# Path to detectron directory
detectronDir = ""

# Directory in which files will be uploaded
uploadDir = "/home/<username>/LOCDB-V3/upload/"

# URL of the opeartional Grobid Service
grobid = "<url to Grobid Service>/api/"

# Directory where images of manual corrections are uploaded for re-training
imagesDir = ""

# Directory where annotation files of manual corrections are uploaded for re-training
annotationsDir = ""

# Directory where images for saving final model after re-training
outputPath = ""

# Directory containing default model for Reference Detection is placed
modelPath = ""

# Directory containing default model for Column Detection is placed
modelPath2 = ""

# Switch for enabling Debug Mode
debugMode = "no"
