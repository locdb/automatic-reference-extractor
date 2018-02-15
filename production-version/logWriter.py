from datetime import datetime

'''
method that stores the settings of each input file until it is processed
'''
def writeLog(filename, Settings, Processed):
    with open("processLog.txt","a") as f:
        ts= datetime.now().strftime('%m%d%H%M%S')
        text = ts + " , " + filename + " , "
        for s in Settings:
            text += str(s) + " , " 
        text += str(Processed) + "\n"
        f.write(text)

'''
Description:
method that retrieves the correct settings from log.txt
Output:
Settings: list of all settings
Found: if the settings are found for the file
'''
def retrieveSettings(filename):
    with open("processLog.txt", "r") as f:
        settings = []
        for line in reversed(f.readlines()):
            splitLine = line.split(",")
            settings = splitLine[2:-1]
            if filename in splitLine[1] and "False" in splitLine[-1]:
                return settings, True
        return  settings, False
    
'''
Description:
method that removes correct processed files
'''
def writeCorrect(filename):
    newLog = []
    with open("processLog.txt", "r") as f:
        for line in reversed(f.readlines()):
            splitLine = line.split(",")
            if filename != splitLine[1].strip():
                newLog.append(line)
    with open("processLog.txt", "w") as f:
        for l in newLog:
            f.write(l)