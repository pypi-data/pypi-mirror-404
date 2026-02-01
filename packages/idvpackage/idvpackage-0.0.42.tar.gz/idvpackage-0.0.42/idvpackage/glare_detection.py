import cv2
import numpy as np
from skimage import measure
import imutils

def crop_using_vertices(image_np, vertices):
    """
    Crops the image using the vertices, plots the cropped image, and returns it.
    """
    left = int(vertices[0].x)
    top = int(vertices[0].y)
    right = int(vertices[2].x)
    bottom = int(vertices[2].y)

    # Crop the image
    cropped_image = image_np[top:bottom, left:right]


    return cropped_image

def detect_glare(image_np,vertices,filepath=None,filename=None, threshold=237, glare_pixel_threshold=400):
    """
    Crops using vertices.
    Detects glare in an image using contour detection and glare percentage and HSV method.

    Returns two if any two of the methods return True.

    """
    image_np = crop_using_vertices(image_np, vertices)



    # Convert to grayscale and apply a Gaussian blur
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (11, 11), 0)

    thresh = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)[1]


    # Perform erosions and dilations to remove noise
    thresh = cv2.erode(thresh, None, iterations=2)
    thresh = cv2.dilate(thresh, None, iterations=4)

    # Perform connected component analysis
    labels = measure.label(thresh, connectivity=2, background=0)
    mask = np.zeros(thresh.shape, dtype="uint8")

    # Loop over the unique components
    for label in np.unique(labels):
        if label == 0:
            continue

        labelMask = np.zeros(thresh.shape, dtype="uint8")
        labelMask[labels == label] = 255
        numPixels = cv2.countNonZero(labelMask)

        if numPixels > glare_pixel_threshold:
            mask = cv2.add(mask, labelMask)


    # Find contours in the mask
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    if not contours:
        contours_result = False

    else:
        contours_result = True

    return contours_result
