import unittest

import numpy as np

from test import *
import inspireface as isf
import cv2


class FaceRecognitionBaseCase(unittest.TestCase):
    """
    This case is mainly used to test the basic functions of face recognition.
    """

    def setUp(self) -> None:
        # Prepare material
        track_mode = isf.DETECT_MODE_IMAGE
        param = isf.EngineCustomParameter()
        param.enable_recognition = True
        self.engine = isf.create_engine(bundle_file=TEST_MODEL_PATH, param=param,
                                        detect_mode=track_mode)
        self.assertEqual(True, self.engine.check(), "Failed to create engine.")
        # Create a tracker
        self.tracker = isf.FaceTrackerModule(self.engine)
        # Create a recognition
        self.recognition = isf.FaceRecognitionModule(self.engine)

    def test_face_feature_extraction(self):
        self.tracker.set_track_mode(mode=isf.DETECT_MODE_IMAGE)
        # Prepare a image
        image = cv2.imread(get_test_data("bulk/kun.jpg"))
        self.assertIsNotNone(image)
        # Face detection
        faces = self.tracker.execute(image)
        # "kun.jpg" has only one face
        self.assertEqual(len(faces), 1)
        face = faces[0]
        box = (face.top_left, face.bottom_right)
        expect_box = ((98, 146), (233, 272))
        # Calculate the location of the detected box and the expected box
        iou = calculate_overlap(box, expect_box)
        self.assertAlmostEqual(iou, 1.0, places=3)
        self.assertIsNone(face.feature)

        # Extract feature
        self.recognition.extract_feature(image, face)
        self.assertIsNotNone(face.feature)
        self.assertEqual(TEST_MODEL_FACE_FEATURE_LENGTH, face.feature.size)

    def test_face_comparison(self):
        self.tracker.set_track_mode(mode=isf.DETECT_MODE_IMAGE)
        # Prepare two pictures of someone
        images_path_list = [get_test_data("bulk/kun.jpg"), get_test_data("bulk/jntm.jpg")]
        self.assertEqual(len(images_path_list), 2, "Only 2 photos can be used for the 1v1 scene.")
        images = [cv2.imread(pth) for pth in images_path_list]
        faces_list = [self.tracker.execute(img) for img in images]
        # Check num of faces detection
        self.assertEqual(len(faces_list[0]), 1)
        self.assertEqual(len(faces_list[1]), 1)
        # Extract features
        [self.recognition.extract_feature(images[idx], faces[0]) for idx, faces in enumerate(faces_list)]
        face_1 = faces_list[0][0]
        face_2 = faces_list[1][0]
        self.assertEqual(face_1.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        self.assertEqual(face_2.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        # Comparison
        similarity = self.recognition.face_comparison1v1(face_1, face_2)
        self.assertEqual(True, similarity > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)

        # Prepare a picture of a different person
        woman = cv2.imread(get_test_data("bulk/woman.png"))
        self.assertIsNotNone(woman)
        woman_faces = self.tracker.execute(woman)
        self.assertEqual(len(woman_faces), 1)
        face_3 = woman_faces[0]
        self.recognition.extract_feature(woman, face_3)
        self.assertEqual(face_3.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        # Comparison
        similarity = self.recognition.face_comparison1v1(face_1, face_3)
        self.assertEqual(True, similarity < TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
        similarity = self.recognition.face_comparison1v1(face_2, face_3)
        self.assertEqual(True, similarity < TEST_FACE_COMPARISON_IMAGE_THRESHOLD)


@optional(ENABLE_CRUD_TEST, "All CRUD related tests have been closed.")
class FaceRecognitionCRUDMemoryCase(unittest.TestCase):
    """
    This case is mainly used to test the CRUD functions of face recognition.
    """

    engine = None
    default_faces_num = 10000

    @classmethod
    def setUpClass(cls):
        track_mode = isf.DETECT_MODE_IMAGE
        param = isf.EngineCustomParameter()
        param.enable_recognition = True
        cls.engine = isf.create_engine(bundle_file=TEST_MODEL_PATH, param=param,
                                       detect_mode=track_mode)
        batch_import_lfw_faces(LFW_FUNNELED_DIR_PATH, cls.engine, cls.default_faces_num)
        cls.track = isf.FaceTrackerModule(cls.engine)
        cls.recognition = isf.FaceRecognitionModule(cls.engine)

    def test_face_search(self):
        num_current = self.recognition.get_face_count()
        registered = cv2.imread(get_test_data("bulk/kun.jpg"))
        self.assertIsNotNone(registered)
        faces = self.track.execute(registered)
        self.assertEqual(len(faces), 1)
        face = faces[0]
        self.recognition.extract_feature(registered, face)
        self.assertEqual(face.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        # Insert a new face
        registered_identity = isf.FaceIdentity(face, custom_id=num_current + 1, tag="Kun")
        self.recognition.face_register(registered_identity)

        # Prepare a picture of searched face
        searched = cv2.imread(get_test_data("bulk/jntm.jpg"))
        self.assertIsNotNone(searched)
        faces = self.track.execute(searched)
        self.assertEqual(len(faces), 1)
        searched_face = faces[0]
        self.recognition.extract_feature(searched, searched_face)
        self.assertEqual(searched_face.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        searched_result = self.recognition.face_search(searched_face)
        self.assertEqual(True, searched_result.confidence > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
        self.assertEqual(searched_result.similar_identity.tag, registered_identity.tag)
        self.assertEqual(searched_result.similar_identity.custom_id, registered_identity.custom_id)

        # Prepare a picture of a stranger's face
        stranger = cv2.imread(get_test_data("bulk/woman.png"))
        self.assertIsNotNone(stranger)
        faces = self.track.execute(stranger)
        self.assertEqual(len(faces), 1)
        stranger_face = faces[0]
        self.recognition.extract_feature(stranger, stranger_face)
        self.assertEqual(stranger_face.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        stranger_result = self.recognition.face_search(stranger_face)
        self.assertEqual(True, stranger_result.confidence < TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
        self.assertEqual(stranger_result.similar_identity.custom_id, -1)

    def test_face_remove(self):
        query_image = cv2.imread(get_test_data("bulk/Nathalie_Baye_0002.jpg"))
        self.assertIsNotNone(query_image)
        faces = self.track.execute(query_image)
        self.assertEqual(len(faces), 1)
        query_face = faces[0]
        self.recognition.extract_feature(query_image, query_face)
        self.assertEqual(query_face.feature.size, TEST_MODEL_FACE_FEATURE_LENGTH)
        # First search
        result = self.recognition.face_search(query_face)
        self.assertEqual(True, result.confidence > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
        self.assertEqual("Nathalie_Baye", result.similar_identity.tag)

        # Remove that
        remove_id = result.similar_identity.custom_id
        self.recognition.face_remove(remove_id)

        # Second search
        result = self.recognition.face_search(query_face)
        self.assertEqual(True, result.confidence < TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
        self.assertEqual(result.similar_identity.custom_id, -1)

        # Reusability testing
        new_face_image = cv2.imread(get_test_data("bulk/yifei.jpg"))
        self.assertIsNotNone(new_face_image)
        faces = self.track.execute(new_face_image)
        self.assertEqual(len(faces), 1)
        new_face = faces[0]
        self.recognition.extract_feature(new_face_image, new_face)
        # Insert that
        registered_identity = isf.FaceIdentity(new_face, custom_id=remove_id, tag="YF")
        self.recognition.face_register(registered_identity)

    def test_face_update(self):
        pass


@optional(ENABLE_BENCHMARK_TEST, "All benchmark related tests have been closed.")
class FaceRecognitionFeatureExtractCase(unittest.TestCase):
    benchmark_results = list()
    loop = 1

    @classmethod
    def setUpClass(cls):
        cls.benchmark_results = []

    def setUp(self) -> None:
        # Prepare image
        image = cv2.imread(get_test_data("bulk/kun.jpg"))
        self.stream = isf.CameraStream.load_from_cv_image(image)
        self.assertIsNotNone(self.stream)
        # Prepare material
        track_mode = isf.DETECT_MODE_IMAGE
        param = isf.EngineCustomParameter()
        param.enable_recognition = True
        self.engine = isf.create_engine(bundle_file=TEST_MODEL_PATH, param=param,
                                        detect_mode=track_mode)
        self.assertEqual(True, self.engine.check(), "Failed to create engine.")
        # Use tracker module
        self.tracker = isf.FaceTrackerModule(self.engine)
        self.assertIsNotNone(self.tracker)
        # Prepare a face
        faces = self.tracker.execute(self.stream)
        # "kun.jpg" has only one face
        self.assertEqual(len(faces), 1)
        self.face = faces[0]
        box = (self.face.top_left, self.face.bottom_right)
        expect_box = ((98, 146), (233, 272))
        # Calculate the location of the detected box and the expected box
        iou = calculate_overlap(box, expect_box)
        self.assertAlmostEqual(iou, 1.0, places=3)
        self.assertIsNone(self.face.feature)

        # Create a recognition
        self.recognition = isf.FaceRecognitionModule(self.engine)
        self.recognition.extract_feature(image, self.face)

    @benchmark(test_name="Feature Extract", loop=1000)
    def test_benchmark_feature_extract(self):
        self.tracker.set_track_mode(isf.DETECT_MODE_IMAGE)
        for _ in range(self.loop):
            self.recognition.extract_feature(self.stream, self.face)
            self.assertIsNotNone(self.face.feature)
            self.assertEqual(TEST_MODEL_FACE_FEATURE_LENGTH, self.face.feature.size)

    @benchmark(test_name="Face comparison 1v1", loop=1000)
    def test_benchmark_face_comparison1v1(self):
        for _ in range(self.loop):
            self.recognition.face_comparison1v1(self.face, self.face)

    @classmethod
    def tearDownClass(cls):
        print_benchmark_table(cls.benchmark_results)


@optional(ENABLE_SEARCH_BENCHMARK_TEST, "Face search benchmark related tests have been closed.")
class FaceRecognitionSearchCase(unittest.TestCase):
    benchmark_results = list()
    loop = 1
    inventory_level = list()

    # Set the stock level of faces you want to test
    inventory_level_list = [1000, 5000, 10000]

    @classmethod
    def setUpClass(cls):
        cls.benchmark_results = []
        # Prepare image
        image = cv2.imread(get_test_data("bulk/kun.jpg"))

        num = len(cls.inventory_level_list)
        track_mode = isf.DETECT_MODE_IMAGE
        param = isf.EngineCustomParameter()
        param.enable_recognition = True
        cls.inventory_level = [isf.create_engine(bundle_file=TEST_MODEL_PATH, param=param,
                                                 detect_mode=track_mode) for _ in range(num)]
        [batch_import_lfw_faces(LFW_FUNNELED_DIR_PATH, engine, cls.inventory_level_list[idx]) for
         idx, engine in enumerate(cls.inventory_level)]

        # Use tracker module
        # Prepare a face and insert to db
        faces = isf.FaceTrackerModule(cls.inventory_level[0]).execute(image)
        face = faces[0]
        isf.FaceRecognitionModule(cls.inventory_level[0]).extract_feature(image, face)
        identity_list = [isf.FaceIdentity(face, cls.inventory_level_list[idx] + 1, "Kun") for idx in range(num)]
        [isf.FaceRecognitionModule(engine).face_register(identity_list[idx]) for idx, engine in
         enumerate(cls.inventory_level)]

    def setUp(self) -> None:
        # Prepare material
        track_mode = isf.DETECT_MODE_IMAGE
        param = isf.EngineCustomParameter()
        param.enable_recognition = True
        self.engine = isf.create_engine(bundle_file=TEST_MODEL_PATH, param=param,
                                        detect_mode=track_mode)
        # Create a recognition
        self.recognition = isf.FaceRecognitionModule(self.engine)
        self.assertEqual(True, self.engine.check(), "Failed to create engine.")

        searched = cv2.imread(get_test_data("bulk/jntm.jpg"))
        self.assertIsNotNone(searched)
        # Prepare a search face
        faces_search = isf.FaceTrackerModule(self.engine).execute(searched)
        self.assertEqual(len(faces_search), 1)
        self.search_face = faces_search[0]
        self.recognition.extract_feature(searched, self.search_face)
        self.assertIsNotNone(self.search_face.feature)

    @benchmark(test_name="Search Face from 1k", loop=1000)
    def test_benchmark_search_1k(self):
        engine = self.inventory_level[0]
        for _ in range(self.loop):
            searched = isf.FaceRecognitionModule(engine).face_search(self.search_face)
            self.assertEqual(True, searched.confidence > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
            self.assertEqual(searched.similar_identity.tag, "Kun")
            self.assertEqual(searched.similar_identity.custom_id, 1001)

    @benchmark(test_name="Search Face from 5k", loop=1000)
    def test_benchmark_search_5k(self):
        engine = self.inventory_level[1]
        for _ in range(self.loop):
            searched = isf.FaceRecognitionModule(engine).face_search(self.search_face)
            self.assertEqual(True, searched.confidence > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
            self.assertEqual(searched.similar_identity.tag, "Kun")
            self.assertEqual(searched.similar_identity.custom_id, 5001)

    @benchmark(test_name="Search Face from 10k", loop=1000)
    def test_benchmark_search_10k(self):
        engine = self.inventory_level[2]
        for _ in range(self.loop):
            searched = isf.FaceRecognitionModule(engine).face_search(self.search_face)
            self.assertEqual(True, searched.confidence > TEST_FACE_COMPARISON_IMAGE_THRESHOLD)
            self.assertEqual(searched.similar_identity.tag, "Kun")
            self.assertEqual(searched.similar_identity.custom_id, 10001)

    @classmethod
    def tearDownClass(cls):
        print_benchmark_table(cls.benchmark_results)


if __name__ == '__main__':
    unittest.main()