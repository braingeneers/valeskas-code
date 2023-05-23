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

url_signer = URLSigner(session)

experiment_list = []

cur_cam_list = []

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

    cur_cam_list = dir_list

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

    assert cam_name is not None
    assert experiment_name is not None
    assert page_size is not None
    assert cur_img_index is not None


    BUCKET_NAME = "streamscope"

    s3 = boto3.client('s3', endpoint_url="https://s3-west.nrp-nautilus.io")

    ROOT_DIR = ""

    prefix = ROOT_DIR + experiment_name + "/" + cam_name+"/"

    max_images_per_page = page_size

    file_name = ""

    # paginator = s3.get_paginator("list_objects_v2")
    # response = paginator.paginate(Bucket=BUCKET_NAME, PaginationConfig={"PageSize": max_images_per_page, "Prefix": prefix+chosen_cam+"/"})
    # for page in response:
    #     print("getting 2 files from S3")
    #     files = page.get("Contents")
    #     for file in files:
    #         print(f"file_name: {file['Key']}, size: {file['Size']}")
    #     print("#" * 10)

    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix, Delimiter='/')

    camera_dir_list = []

    cam_names = []

    file_list = []

    # TODO: Use this for more than 1,000 files in the subdirectory
    # s3 = boto3.resource('s3')
    # bucket = s3.Bucket('mybucket')
    # prefix="subfolder1/sub_subfolder1/....."
    # for object_summary in bucket.objects.filter(Prefix=prefix):
    #     print(object_summary.key)

    for content in response.get('Contents', []):
        path = content['Key']
        if path == "/":
            continue
        file_list.append(path)
        print(path)

    last_i = 0

    images = []
    file_names = []

    for i in range(cur_img_index, max_images_per_page+cur_img_index):
        if i == len(file_list):
            break
        last_i = i
        path = file_list[i]
        file_names.append(path.split(prefix)[1].replace("/", ""))

        try:
            s3_response_object = s3.get_object(Bucket=BUCKET_NAME, Key=path)
            object_content = s3_response_object['Body'].read()
            images.append(base64.b64encode(BytesIO(object_content).getvalue()).decode('utf-8'))
        except Exception as e:
            print(e)
            raise

    return dict(images=images, file_names=file_names)



# ---------------------------------------



@action('add', method=["GET", "POST"])
@action.uses('add.html', url_signer, db, session, auth.user)
def add():
    # Insert form: no record= in it.
    form = Form(db.bird, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # We simply redirect; the insertion already happened.
        redirect(URL('index'))
    # Either this is a GET request, or this is a POST but not accepted = with errors.
    return dict(form=form)

@action('edit/<bird_id:int>', method=["GET", "POST"])
@action.uses('edit.html', url_signer.verify(), db, session, auth.user)
def edit(bird_id=None):
    assert bird_id is not None
    # We read the product being edited from the db.
    # p = db(db.product.id == product_id).select().first()
    b = db.bird[bird_id]
    if b is None:
        # Nothing found to be edited!
        redirect(URL('index'))
    # Edit form: it has record=
    form = Form(db.bird, record=b, deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        # The update already happened!
        redirect(URL('index'))
    return dict(form=form)

@action('inc/<bird_id:int>')
@action.uses(db, session, auth.user, url_signer.verify())
def inc(bird_id=None):
    assert bird_id is not None
    bird = db.bird[bird_id]
    num = db(db.bird.id == bird_id).select().first()['n_sightings']
    db(db.bird.id == bird_id).update(n_sightings = num+1)
    redirect(URL('index'))