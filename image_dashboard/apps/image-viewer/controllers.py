import base64
from py4web import action, request, abort, redirect, URL, Field
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET

import uuid

import boto3, botocore
import logging
import os
import sys, getopt
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from io import BytesIO
import zlib
import pandas as pd
from PIL import Image
import cv2

url_signer = URLSigner(session)

experiment_list = []

cur_cam_list = []

def create_timelapse(image_files, fps=10):
    local_path = "timelapse.mp4"
    frame = cv2.imdecode(image_files[0], cv2.IMREAD_COLOR)
    height, width, layers = frame.shape
    #cv2.imwrite("result.jpg", frame)

    #print("image_files:", image_files)

    # Determine common size for all images
    # TODO: Should probably eliminate this
    for image_file in image_files:
        image = cv2.imdecode(image_file, cv2.IMREAD_COLOR)
        if image.shape != (height, width, layers):
            height, width, layers = image.shape

    # Create video writer object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(local_path, fourcc, fps, (width, height))

    # Write frames to video
    for image_file in image_files:
        image = cv2.imdecode(image_file, cv2.IMREAD_COLOR)

        # Resize image if necessary
        if image.shape != (height, width, layers):
            image = cv2.resize(image, (width, height))

        video.write(image)

    # Release resources
    cv2.destroyAllWindows()
    video.release()
    contents = None
    with open(local_path, mode="rb") as video_file:
        contents = video_file.read()
        return base64.b64encode(contents).decode('utf-8') 

@action('index', method=["GET", "POST"])
@action.uses('index.html', db, session)
def index():

    # TODO: Delete all DB values on a regular basis

    # Retrieve the list of existing buckets
    BUCKET_NAME = "streamscope"

    # TODO: Consider closing the client connection, if applicable

    s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")

    ROOT_DIR = ""

    result = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=ROOT_DIR, Delimiter='/')

    dir_list = []

    #db.experiments.truncate()
    #db.cam_names.truncate()

    for o in result.get('CommonPrefixes'):
        path = o.get('Prefix')
        if path == "/":
            continue
        dir_list.append(path.replace("/", ""))
        #dir_list.append(path.split(ROOT_DIR)[1].replace("/", ""))
        db.experiments.update_or_insert(experiment_name=path.replace("/", ""))

    # experiment_form = Form([Field("experiment_name", requires=IS_IN_SET(dir_list))], deletable=False, csrf_session=session, formstyle=FormStyleBulma)

    # if experiment_form.accepted:
    #     # The update already happened!
    #     print("experiment_form:", experiment_form.vars)
        
    #     redirect(URL('index'))

    #rows = db(db.bird.user_email == get_user_email()).select()

    get_experiments_url = URL('get_experiments')
    set_experiment_url = URL('set_experiment')
    set_camera_url = URL('set_camera')
    images_url = URL('images')

    return dict(images_url=images_url, set_camera_url=set_camera_url, get_experiments_url=get_experiments_url, set_experiment_url=set_experiment_url, experiment_names=dir_list, cam_names=[""], chosen_experiment_name="", chosen_cam_name="")
    #return dict(images = request.query.get('images', images))

@action('get_experiments')
@action.uses(db)
def get_experiments():
    BUCKET_NAME = "streamscope"

    # TODO: Consider closing the client connection, if applicable

    s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")

    ROOT_DIR = ""

    result = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=ROOT_DIR, Delimiter='/')

    experiment_names = []

    #db.experiments.truncate()
    #db.cam_names.truncate()

    for o in result.get('CommonPrefixes'):
        path = o.get('Prefix')
        if path == "/":
            continue
        experiment_names.append(path.replace("/", ""))
        #dir_list.append(path.split(ROOT_DIR)[1].replace("/", ""))
        db.experiments.update_or_insert(experiment_name=path.replace("/", ""))

    return dict(experiment_names=experiment_names)


@action('set_experiment', method=["GET", "POST"])
@action.uses(db, session)
def set_experiment():
    experiment_name = request.params.get("experiment_name")
    assert experiment_name is not None

    # Retrieve the list of existing buckets
    BUCKET_NAME = "streamscope"

    # TODO: Consider closing the client connection, if applicable

    s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")

    ROOT_DIR = "" + experiment_name + "/"

    result = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=ROOT_DIR, Delimiter='/')

    dir_list = []

    experiment_id = db(db.experiments.experiment_name == experiment_name).select(db.experiments.id).first()['id']
    print("Experiment ID:", experiment_id)

    for o in result.get('CommonPrefixes'):
        path = o.get('Prefix')
        if path == "/":
            continue
        dir_list.append(path.split(ROOT_DIR)[1].replace("/", ""))
        db.cam_names.update_or_insert(cam_name=path.split(ROOT_DIR)[1].replace("/", ""), experiment_id=experiment_id)

    dir_list = sorted(dir_list, key=lambda x: x.split("cam")[1])

    #rows = db(db.bird.user_email == get_user_email()).select()
    return dict(cam_names=dir_list)
    #return dict(images = request.query.get('images', images))

@action('set_camera', method=["GET", "POST"])
@action.uses(db, session)
def set_camera():
    experiment_name = request.params.get("experiment_name")
    cam_name = request.params.get("cam_name")

    assert cam_name is not None
    assert experiment_name is not None

    #rows = db(db.bird.user_email == get_user_email()).select()
    return dict(experiment_names=experiment_list, cam_names=cur_cam_list, chosen_experiment_name=experiment_name, chosen_cam_name=cam_name)
    #return dict(images = request.query.get('images', images))

@action('images', method=["GET", "POST"])
@action.uses(db, session)
def get_images():
    experiment_name = request.params.get("experiment_name")
    cam_name = request.params.get("cam_name")
    page_size = int(request.params.get("page_size"))
    cur_img_index = int(request.params.get("cur_img_index"))
    make_timelapse = request.params.get("make_timelapse")
    fps = request.params.get("fps")
    index_provided = request.params.get("index_provided")
    #img_start_index = int(request.params.get("start_index"))

    assert cam_name is not None
    assert experiment_name is not None
    assert page_size is not None
    assert cur_img_index is not None
    #assert img_start_index is not None
    assert index_provided is not None

    if index_provided == "false":
        index_provided = False
    else:
        index_provided = True
        
    #print("make_timelapse:", make_timelapse)
    if make_timelapse == "false" or make_timelapse == "null":
        make_timelapse = False
    else:
        make_timelapse = True

    if fps is None:
        fps = 10
    else:
        fps = int(fps)


    BUCKET_NAME = "streamscope"

    s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")

    ROOT_DIR = ""

    prefix = ROOT_DIR + experiment_name + "/" + cam_name+"/"

    max_images_per_page = page_size

    # paginator = s3.get_paginator("list_objects_v2")
    # response = paginator.paginate(Bucket=BUCKET_NAME, PaginationConfig={"PageSize": max_images_per_page, "Prefix": prefix+chosen_cam+"/"})
    # for page in response:
    #     print("getting 2 files from S3")
    #     files = page.get("Contents")
    #     for file in files:
    #         print(f"file_name: {file['Key']}, size: {file['Size']}")
    #     print("#" * 10)

    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix, Delimiter='/')

    file_list = []

    # TODO: Use this for more than 1,000 files in the subdirectory
    # s3 = boto3.resource('s3')
    # bucket = s3.Bucket('mybucket')
    # prefix="subfolder1/sub_subfolder1/....."
    # for object_summary in bucket.objects.filter(Prefix=prefix):
    #     print(object_summary.key)

    # TODO: Ensure that only images are counted.
    for content in response.get('Contents', []):
        path = content['Key']
        if path == "/":
            continue
        file_list.append(path)
        #print(path)

    file_list = sorted(file_list, key=lambda x: int(x.split(prefix)[1].replace("/", "").split("_")[1].split(".")[0]))

    max_file_index = int(file_list[-1].split(prefix)[1].replace("/", "").split("_")[1].split(".")[0])

    images = []
    file_names = []

    print("Len file list:", len(file_list), " max index:", max_file_index)

    file_dict = {}

    for file in file_list:
        file_dict[int(file.split(prefix)[1].replace("/", "").split("_")[1].split(".")[0])] = file

    #print("file_dict:", file_dict)

    #print("Sorted file_list:", file_list)

    print("cur_img_index before:", cur_img_index)
    if max_file_index <= cur_img_index+max_images_per_page:
        cur_img_index = max_file_index-max_images_per_page

    print("cur_img_index after:", cur_img_index, " cur_img_index + page size:", cur_img_index + max_images_per_page)

    #print("file_list:", file_list[cur_img_index:max_images_per_page+cur_img_index])
    print("index_provided:", index_provided)

    for i in range(cur_img_index, max_images_per_page+cur_img_index):
        if i not in file_dict and index_provided:
            print("continued!")
            # TODO: Consider the case of a discontinuity, such as having page size of 5 and indices 100, 101, 102, 103, 107. You'd return only four results even though five exist.
            continue
        #print("in here")
        path = ""
        if index_provided:
            path = file_dict[i]
        else:
            path = file_list[i]

        #print("path:", path, " i:", i)

        file_names.append(path.split(prefix)[1].replace("/", "").split("_")[1].split(".")[0])

        try:
            s3_response_object = s3.get_object(Bucket=BUCKET_NAME, Key=path)
            object_content = s3_response_object['Body'].read()
            images.append(base64.b64encode(BytesIO(object_content).getvalue()).decode('utf-8'))
        except Exception as e:
            print(e)
    if make_timelapse:
        print("timelapse in:")
        return dict(timelapse=create_timelapse(np.array([np.asarray(bytearray(base64.b64decode(image)), dtype="uint8") for image in images]), fps))
    # TODO: change total image count name to be more clear about the difference between count and indices
    return dict(images=images, file_names=file_names, total_image_count=max_file_index)