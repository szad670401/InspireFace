//
// Created by tunm on 2024/4/6.
//
#include <iostream>
#include "track_module/face_track.h"
#include "recognition_module/face_recognition.h"
#include "log.h"

using namespace inspire;

int main() {
    InspireArchive archive("test_res/model_zip/Pikachu");

    FaceTrack track;
    FaceRecognition recognition(archive, true);

    auto ret = track.Configuration(archive);
    LOGD("ret=%d", ret);

    auto image = cv::imread("test_res/data/bulk/kun.jpg");
    CameraStream stream;
    stream.SetDataBuffer(image.data, image.rows, image.cols);
    stream.SetDataFormat(BGR);
    stream.SetRotationMode(ROTATION_0);

    track.UpdateStream(stream, true);

    if (!track.trackingFace.empty()) {
        auto const &face = track.trackingFace[0];
        cv::rectangle(image, face.GetRectSquare(), cv::Scalar(200, 0, 20), 2);
    }

    cv::imshow("w", image);
    cv::waitKey(0);

    return 0;
}