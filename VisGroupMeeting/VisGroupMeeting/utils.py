import cv2

def get_key_frame():
    vidcap = cv2.VideoCapture('005.avi')
    success,image = vidcap.read()
    count = 0
    success = True
    while success:
      success,image = vidcap.read()
      cv2.imwrite("frame%d.jpg" % count, image)     # save frame as JPEG file
      if cv2.waitKey(10) == 27:
          break
      count += 1