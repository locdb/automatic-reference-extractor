'''
Please comment the correct ABSOLUT paths for the dependencies and 
do not forget to change the input and output paths if you do not want the default one.
For the upload and output folders change the paths in the app.py 
'''
# Directory which contains the locdb app plus slash
LOCDB = "/home/locdb/LOCDB/LOCDB-dev/"

# Directory which contains parscit for the reference extraction
parsCit = "/home/rizvi/ParsCit/bin"

# Directory in which the jar of pdf inspector is located to convert pdf to txt
# name of the jar should be: "docears-pdf-inspector.jar"
pdfInspector = "/home/locdb/LOCDB/LOCDB-dev"

# Path to detectron directory
detectronDir = "/home/locdb/detectron/"

# Directory in which files will be uploaded
uploadDir = "/home/locdb/LOCDB/LOCDB-dev/upload/"

# URL of the opeartional Grobid Service
grobid = "http://pc-4112:8070/api/"

# Directory where images of manual corrections are uploaded for re-training
imagesDir = "/home/locdb/detectron/detectron/datasets/data/LOCDB-finetune/images/"

# Directory where annotation files of manual corrections are uploaded for re-training
annotationsDir = "/home/locdb/detectron/detectron/datasets/data/LOCDB-finetune/xml/"

# Directory where images for saving final model after re-training
outputPath = "/home/locdb/detectron/detectron/datasets/data/LOCDB-finetune/"

# Directory containing default model for Reference Detection is placed
modelPath = "/home/locdb/detectron/models/reference-detector/"

# Directory containing default model for Column Detection is placed
modelPath2 = "/home/locdb/detectron/models/column-detector/"

# Switch for enabling Debug Mode
debugMode = "yes"