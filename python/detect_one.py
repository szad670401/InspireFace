import cv2
import inspireface as isf

image0 = cv2.imread("/Users/tunm/Downloads/iph.jpg")
image1 = cv2.imread("/Users/tunm/work/HyperFace/python/test/data/pose/right_wryneck.png")

engine = isf.create_engine("/Users/tunm/work/HyperFace/test_res/model_zip/Optimus-t1", param=isf.EngineCustomParameter())
tracker = isf.FaceTrackerModule(engine)

tracker.execute(image0)
faces = tracker.execute(image1)
print(faces)

