import boto3, botocore
import logging
import os
import sys, getopt
# Retrieve the list of existing buckets

s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")
    
def upload_images(root_path, experiment_name):
    
    for folder in os.listdir(root_path):
        print(folder)
        if "cam" in folder:
            for image in os.listdir(root_path+"/"+folder):
                print(image)
                try:
                    response = s3.upload_file(folder + "/" + image, "braingeneers", "imaging/streamscope/"+ experiment_name + "/" + folder + "/" + image)
                except botocore.exceptions.ClientError as e:
                    logging.error(e)
                    print(e)
    
def main(argv):
    
    experiment_name = ''
    root_directory = ''
    opts, args = getopt.getopt(argv,"he:d:",["experimentname=","rootdirectory="])
    for opt, arg in opts:
        if opt == '-h':
            print ('image_batch_upload.py -e <experiment-name> -d <root-directory>')
            sys.exit()
        elif opt in ("-e", "--experimentname"):
            experiment_name = arg
        elif opt in ("-d", "--rootdirectory"):
            root_directory = arg
            
    upload_images(root_directory, experiment_name)
    
if __name__ == "__main__":
    main(sys.argv[1:])
