//
// Created by tunm on 2023/9/17.
//
#pragma once
#ifndef HYPERFACEREPO_FACEDATATYPE_H
#define HYPERFACEREPO_FACEDATATYPE_H

#include "../../DataType.h"
#include "../face_info/FaceObject.h"

namespace hyper {

typedef struct FaceRect {
    int x;
    int y;
    int width;
    int height;
} FaceRect;

typedef struct HPoint {
    float x;
    float y;
} HPoint;

typedef struct TransMatrix {
    double m00;
    double m01;
    double m10;
    double m11;
    double tx;
    double ty;
} TransMatrix;

typedef struct HyperFaceData {
    int trackState;
    int inGroupIndex;
    int trackId;
    int trackCount;
    FaceRect rect;
    TransMatrix trans;
    HPoint keyPoints[5];
} HyperFaceData;

}

#endif //HYPERFACEREPO_FACEDATATYPE_H
