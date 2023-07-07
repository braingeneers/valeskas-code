import cv2
import matplotlib.pyplot as plt
import numpy as np

%matplotlib inline

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib import colors

import math
import os
import re
import os

best_conversion_vals = []
volume_deltas = []

def get_cone_coefficient(fluid_height):
    #return 0.0776 + (-2.54*(10**-3))*fluid_height + (5.76*(10**-5))*(fluid_height**2) + (-6.55*(10**-7))*(fluid_height**3) + (3.86*(10**-9))*(fluid_height**4) + (-1.14*(10**-11))*(fluid_height**5) + (1.32*(10**-14))*(fluid_height**6)
    return 0.0401 + (-1.05*(10**-4))*fluid_height + (-5.37*(10**-8))*fluid_height**2 + (8.45*(10**-10))*fluid_height**3
    
def calculate_volume(fluid_level_y, bottom_y, top_of_tube, full_volume, image=None, inputted_fluid_volume=0, true_volume=None):
    #print("bottom:", contours[27])
    #print("top:", contours[38])

    # actually 450 microliters
    cone_volume = 2 - 0.50

    #print("volume of cone:", cone_volume)

    # x,y,w,h = cv2.boundingRect(contours[27])
    # print("bottom:", x, y, w, h)

    # x,y,w,h = cv2.boundingRect(contours[38])
    # print("top:", x, y, w, h)

    #print("top of tube:", top_of_tube)

    tube_height =  bottom_y - top_of_tube

    #print(tube_height)

    fluid_level_height =  abs(bottom_y - fluid_level_y)

    # TODO: This seems to be over-estimated!
    #print("fluid level height:", fluid_level_height)

    # cone section is 0.209 of the tube height visible at 13.2 mL

    #tube_height *= (1 - 0.209)

    # TODO: Update this
    cone_height = 230#tube_height * (0.219)

    non_cone_volume = full_volume - cone_volume

    fluid_non_cone = fluid_level_height - cone_height

    tube_height_non_cone = tube_height - cone_height
    tube_height_non_cone = 855.6875

    #print("tube height non cone, fluid non cone, non cone volume:", tube_height_non_cone, fluid_non_cone, non_cone_volume)

    #print("cone height:", cone_height)

    #print(fluid_level_height / tube_height)

    # radius per mm of height is 0.208

    radius_per_mm = 9.8/23.64

    # mm to pixel is 0.096

    #mm_to_pixels = 0.096

    mm_to_pixels = float(23.0 / cone_height)
    
    #print("mm to pixels:", mm_to_pixels)
    
    cone_fluid_height = fluid_level_height
    
    if cone_fluid_height > cone_height:
        cone_fluid_height = cone_height
    
    if true_volume is not None:
        if true_volume < 1.5:
            mm_to_pixels = ((40 * (3/math.pi) ** (1/3)) * (true_volume) ** (1/3)) / (((23) ** (2/3)) * cone_fluid_height)
            #print("Best mm_to_pixels val:", mm_to_pixels)
            best_conversion_vals.append(mm_to_pixels)
            #mm_to_pixels = get_cone_coefficient(cone_fluid_height)

#         x = mm_to_pixels * cone_fluid_height
#         print("Best radius_per_mm val:", math.sqrt(true_volume/math.pi*1000/x)/x)
#         radius_per_mm = math.sqrt(true_volume/math.pi*1000/x)/x
#         best_conversion_vals.append(radius_per_mm)
    
    # min_radius = 6.15

    mm_to_pixels = 23.64/cone_height
    
    #print("mm to pixels:", mm_to_pixels)
    
    rel_height = 0
    fluid_volume = 0
    
    ml_per_pixel = non_cone_volume / tube_height_non_cone

    #print("ml per pixel:", ml_per_pixel)

    top_cone_y = bottom_y - cone_height
    #print("top cone y:", top_cone_y)

    if image is not None:
        imageCopy = image.copy()
        x = 0
        w = 2500

        # ml_y
        height = 0
        #fluid_volume = 12
        #print("fluid volume:", inputted_fluid_volume)
        #print("cone volume:", cone_volume)
        if inputted_fluid_volume > cone_volume:
            fluid_height = (inputted_fluid_volume - cone_volume) / ml_per_pixel
            #print("fluid height:", fluid_height)
            height = top_cone_y - fluid_height
        elif fluid_volume == cone_volume:
            #print("equal condition:")
            height = top_cone_y
        else:
            #print("In cone:")
            height = bottom_y - ((40 * (3/math.pi) ** (1/3)) * (true_volume) ** (1/3)) / (((23) ** (2/3)) * mm_to_pixels)

        #height = top_cone_y
        #print("height:", height)
        height = int(height)

        # Start coordinate, here (0, 0)
        # represents the top left corner of image
        start_point = (x, height)

        # End coordinate, here (250, 250)
        # represents the bottom right corner of image
        end_point = (w, height)

        # Green color in BGR
        color = (0, 255, 0)

        # Line thickness of 9 px
        thickness = 1

        img = cv2.line(imageCopy, start_point, end_point, color, thickness)

        start_point = (x, int(top_cone_y))

        # End coordinate, here (250, 250)
        # represents the bottom right corner of image
        end_point = (w, int(top_cone_y))

        img = cv2.line(img, start_point, end_point, color, thickness)

        plt.imshow(img)
        cv2.imwrite(f"test/line_estimate-{true_volume}.jpg", img)
        #img = cv2.rectangle(imageCopy,(x,y),(x+w,y+h),(0,255,0),2)
    
    # This is if the fluid level is at or above the top of the cone section of the tube.
    if fluid_non_cone >= 0:

        rel_height = fluid_non_cone / tube_height_non_cone
        fluid_volume = rel_height * non_cone_volume + cone_volume
        #print("Fluid level at or above cone section, good!")
    else:
        #print("Fluid level within cone section, low fluid level!")
        cone_fluid_height = fluid_level_height
        #print("cone fluid height:", cone_fluid_height)
        fluid_volume = (math.pi*(radius_per_mm * (cone_fluid_height * mm_to_pixels))**2*((cone_fluid_height*mm_to_pixels)))/3/1000

        
    if cone_fluid_height == cone_height + 5 or cone_fluid_height == cone_height - 5:
        fluid_volume = cone_volume
    
    print("volume (mL:)", fluid_volume)
    if true_volume is not None:
        print("Delta Volume (mL:)", true_volume-fluid_volume)
        volume_deltas.append((true_volume-fluid_volume, true_volume, fluid_volume, fluid_non_cone, tube_height_non_cone, non_cone_volume, cone_fluid_height))
    else:
        volume_deltas.append((math.nan, math.nan, fluid_volume, fluid_non_cone, tube_height_non_cone, non_cone_volume, cone_fluid_height))
            
    return fluid_volume
    
def show_contours(indices, contours=None):
    imageCopy = indices[3].copy()

    if contours is None:
        contours = indices[4]
    
    img = None

    for index in indices[0:3]:
        cnt = contours[index]
        #print("Index:", index)
        # compute the bounding rectangle of the contour
        #print(cv2.contourArea(cnt))
        x,y,w,h = cv2.boundingRect(cnt)
        #print(x, y, w, h)

        # draw contour
        img = cv2.drawContours(imageCopy,[cnt],0,(0,255,255),2)

        # draw the bounding rectangle
        img = cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)

    return img
    
full_volume = 13.5 # mL
full_volume_2 = 13.5 # mL

tube_one_indices = []

tube_two_indices = []
def get_fluid_volume(path):

    try:
        os.mkdir("test")
    except Exception as e:
        pass
    file_name = os.path.splitext(os.path.basename(path))[0]
    #true_volume = float(pattern.search(path).group(0))
    #print("True Volume:", true_volume)
    image = cv2.imread(path)
    print("path:", path)

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(18, 18))
    return_image = clahe.apply(gray)

    cv2.imwrite("test/clahe-pre-binary.jpg", return_image)

    return_image = cv2.fastNlMeansDenoising(return_image, None, 10, 7, 21)

    cv2.imwrite("test/denoising.jpg", return_image)

    kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    close = cv2.morphologyEx(return_image,cv2.MORPH_CLOSE,kernel1)
    div = np.float32(return_image)/(close)
    res = np.uint8(cv2.normalize(div,div,0,255,cv2.NORM_MINMAX))
    
    ret, binary = cv2.threshold(return_image, 120, 255, 
      cv2.THRESH_BINARY_INV)

    dst = cv2.addWeighted(return_image,0.5,binary,0.9,0)

    cv2.imwrite("test/overlayed-blurred-binary.jpg", dst)


    cv2.imwrite("test/binary-image.jpg", binary)

    # find the contours

    blurred = cv2.GaussianBlur(binary, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 180)

    cv2.imwrite("test/edges-denoised.jpg", edges)

    morph_dilate_kernel_size = (7, 7)
    morph_rect_kernel_size = (6, 1)

    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    return_image = clahe.apply(edges)

    cv2.imwrite("test/clahe-image.jpg", return_image)
    
    return_image = cv2.morphologyEx(edges, cv2.MORPH_DILATE, morph_dilate_kernel_size, iterations = 3)
    
    # create a horizontal structural element;
    horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, morph_rect_kernel_size)
    # to the edges, apply morphological opening operation to remove vertical lines from the contour image
    return_image = cv2.morphologyEx(return_image, cv2.MORPH_OPEN, horizontal_structure)

    cv2.imwrite(f"test/morpho-stuff-{file_name}.jpg", return_image)
    dst = cv2.addWeighted(gray,0.5,return_image,0.9,0)

    cv2.imwrite(f"test/overlayed-wide-{file_name}.jpg", dst)

    contours, _ = cv2.findContours(return_image,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

    imageCopy = image.copy()

    # take the first contour
    max_area = 0
    max_index = 0
    max_height = 0
    max_height_index = 0

    max_ratio = 0
    max_ratio_index = 0

    max_width_ratio = 0
    max_width_ratio_index = 0

    max_width_y = 0

    max_height_y = 0
    min_height_y = 0

    max_y = 0
    max_y_index = 0

    top_of_tube = 0
    top_of_tube_index = 0

    # Second Tube

    max_height_2 = 0
    max_height_index_2 = 0

    max_y_2 = 0
    max_y_index_2 = 0

    top_of_tube_2 = 0
    top_of_tube_index_2 = 0
    
    top_of_tube_y_limit = 360

    # first tube x start = 1050, end is 1325
    # second tube x start = 1325, end is 1600
    tube_one_start_x = 1050
    tube_one_end_x = 1325
    tube_two_start_x = 1270
    tube_two_end_x = 1600

    min_fluid_line_width = 40
    max_fluid_line_width = 90
    center_bottom = 0

    for i in range(0, len(contours)):

        imageCopy = image.copy()

        cnt = contours[i]

        # compute the bounding rectangle of the contour
        x,y,w,h = cv2.boundingRect(cnt)

        center = x - w

        if y+h > max_y and y > 300 and y < 1400 and w > min_fluid_line_width and x > tube_one_start_x and x < tube_one_end_x:
            max_y = y+h
            max_y_index = i

        if y+h > max_height and y+h > 300 and y+h < 1440 and x > tube_one_start_x and x < tube_one_end_x and w > 20:
            max_height = y+h
            max_height_index = i
            center_bottom = center

        if y+h > max_y_2 and y+h > 300 and y+h < 1400 and w > min_fluid_line_width and x > tube_two_start_x and x < tube_two_end_x:
            max_y_2 = y+h
            max_y_index_2 = i

        if y > max_height_2 and y > 300 and y < 1440 and x > tube_two_start_x and x < tube_two_end_x and w > 20:
            max_height_2 = y+h
            max_height_index_2 = i

    # TODO: Handle zero volume

    bottom_y = max_height
    bottom_y_index = max_height_index

    imageCopy = image.copy()
    
    tube_one_indices.append((bottom_y_index, max_y_index, top_of_tube_index, imageCopy, contours))

    bottom_y_2 = max_height_2
    bottom_y_index_2 = max_height_index_2

    tube_two_indices.append((bottom_y_index_2, max_y_index_2, top_of_tube_index_2, imageCopy, contours))

    fluid_volume = calculate_volume(max_y_2, bottom_y_2, top_of_tube_2, full_volume_2)
    
    cv2.imwrite(f"test/bounded_2-{fluid_volume}.jpg", show_contours((bottom_y_index_2, max_y_index_2, top_of_tube_index_2, imageCopy), contours))
    
get_fluid_volume("good-images/2023_06_28_T211332_dinolite-t-0.05-o-0.5-f-350-10.0mL.jpg")
