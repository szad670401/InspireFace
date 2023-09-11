//
// Created by tunm on 2023/9/8.
//

#ifndef HYPERFACEREPO_FACERECOGNITION_H
#define HYPERFACEREPO_FACERECOGNITION_H
#include "extract/Extract.h"
#include "common/face_info/FaceObject.h"
#include "middleware/camera_stream/camera_stream.h"
#include "features_block/FeatureBlock.h"


namespace hyper {

class HYPER_API FaceRecognition {
public:
    FaceRecognition(ModelLoader &loader, bool enable_recognition, MatrixCore core = MC_OPENCV, int feature_block_num = 5);

    // 计算余弦相似性
    static int32_t CosineSimilarity(const std::vector<float>& v1, const std::vector<float>& v2, float &res);

    int32_t FaceExtract(CameraStream &image, const FaceObject& face, Embedded &embedded);

    int32_t RegisterFaceFeature(const std::vector<float>& feature, int featureIndex);

    int32_t SearchFaceFeature(const std::vector<float>& queryFeature, SearchResult &searchResult, float threshold = 0.5f);

    int32_t DeleteFaceFeature(int featureIndex);

    int32_t GetFaceFeatureCount();



private:
    int32_t InitExtractInteraction(Model *model);

private:

    shared_ptr<Extract> m_extract_;

    std::vector<shared_ptr<FeatureBlock>> m_feature_matrix_list_;


    // 临时固定
    const int32_t NUM_OF_FEATURES_IN_BLOCK = 512;
};

}   // namespace hyper

#endif //HYPERFACEREPO_FACERECOGNITION_H