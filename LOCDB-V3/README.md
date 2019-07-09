# Installing Automatic-Reference-Extractor

Following are the instructions to install Automatic-Refefence-Extractor and its dependencies.

**Requirements:**

- Linux, NVIDIA GPU with at least 8 GB RAM, Python2, Java 1.8.0.*

## Installing Dependencies

- To install [Detectron](https://github.com/facebookresearch/Detectron), follow the [installation instructions](https://github.com/facebookresearch/Detectron/blob/master/INSTALL.md)

- To install [ParsCit](https://github.com/knmnyn/ParsCit), follow the [installation instructions](https://github.com/knmnyn/ParsCit/blob/master/INSTALL)

- Install [Redis](https://redis.io):

```
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```

- Install [Grobid](https://github.com/kermitt2/grobid):

```
git clone https://github.com/kermitt2/grobid.git
wget https://github.com/kermitt2/grobid/zipball/master
unzip master
```

- Install [wkhtmltopdf](https://wkhtmltopdf.org/):

```
sudo apt install wkhtmltopdf
```

- Install [Tesseract](https://github.com/tesseract-ocr/tesseract):

```
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-deu
```

- Download and unzip [Docears-pdf-inspector](http://docear.org/downloads/docears-pdf-inspector.zip)

- Install Python dependencies:

```
pip install -r requirements.txt
```

## Configurations

Once the installation of above mentioned dependencies is complete, following configurations are needed to be made:

- Copy both files from [`tools/`](tools/) to `DetectronDir/tools` directory
- Set paths in [`pathParameter.py`](pathParameter.py)

## Getting Started

After successfully completing the above mentioned steps, now its time to start all the services:

- Start Grobid Service by running the following command under main `grobid/` directory:

```
./gradlew run
```

- Start Redis Service by running the following command under main `redis/` directory:

```
src/redis-server
```

- Under main directory of this project, run the following commands in separate terminal windows:

```
python worker.py
python app.py
```

## Usage

Once all services are up and running, the web interface of the system can be accessed at:

```
http://localhost:8000
```

Processed results of an uploaded file can be visualized at:

```
http://localhost:8000/results/<process-id>
http://localhost:8000/visualizeResults/
```
