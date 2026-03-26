"""Analysis endpoint: image upload and body composition analysis.

Receives images as multipart/form-data with metadata as form
fields (ADR-007). Converts to ``AnalysisInput`` for internal
pipeline, then orchestrates the full CV → estimation flow.
"""

import uuid
from typing import Annotated

import cv2
import numpy as np
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.core.exceptions import (
    AnalysisError,
    CalibrationError,
    PoseDetectionError,
)
from app.models.orm.analysis import Analysis
from app.models.orm.user import User
from app.models.schemas.analysis import (
    AnalysisInput,
    AnalysisResult,
    AnalysisWarning,
)
from app.models.schemas.common import BiologicalSex, PoseCapture
from app.modules.calibration.service import calibrate
from app.modules.estimation.engine import estimate_body_metrics
from app.modules.measurements.service import (
    calculate_measurements,
)
from app.modules.pose.service import extract_landmarks

router = APIRouter(tags=["analysis"])


async def _decode_image(file: UploadFile) -> np.ndarray:
    """Read an UploadFile into an OpenCV BGR image.

    Args:
        file: Uploaded image file.

    Returns:
        Decoded image as numpy array (BGR).

    Raises:
        HTTPException: If the image cannot be decoded.
    """
    contents = await file.read()
    arr = np.frombuffer(contents, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {file.filename}",
        )
    return image


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
)
async def analyze(
    front_image: Annotated[
        UploadFile,
        File(description="Frontal pose image (required)."),
    ],
    height_cm: Annotated[
        float,
        Form(description="Height in centimeters."),
    ],
    weight_kg: Annotated[
        float,
        Form(description="Weight in kilograms."),
    ],
    age: Annotated[
        int,
        Form(description="Age in years."),
    ],
    sex: Annotated[
        BiologicalSex,
        Form(description="Biological sex."),
    ],
    lateral_image: Annotated[
        UploadFile | None,
        File(description="Lateral pose image (recommended)."),
    ] = None,
    dorsal_image: Annotated[
        UploadFile | None,
        File(description="Dorsal pose image (optional)."),
    ] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(
        lambda: None  # public endpoint — user is optional
    ),
) -> AnalysisResult:
    """Run body composition analysis from uploaded images.

    Frontal image is mandatory. Lateral improves accuracy.
    Dorsal is optional (Fase 2).

    The pipeline: pose detection → calibration → measurements
    → body composition estimation.
    """
    warnings: list[AnalysisWarning] = []
    poses_used: list[PoseCapture] = []
    images: dict[PoseCapture, np.ndarray] = {}

    front_decoded = await _decode_image(front_image)
    images[PoseCapture.FRONT] = front_decoded
    poses_used.append(PoseCapture.FRONT)

    if lateral_image is not None:
        lateral_decoded = await _decode_image(lateral_image)
        images[PoseCapture.LATERAL] = lateral_decoded
        poses_used.append(PoseCapture.LATERAL)

    if dorsal_image is not None:
        dorsal_decoded = await _decode_image(dorsal_image)
        images[PoseCapture.DORSAL] = dorsal_decoded
        poses_used.append(PoseCapture.DORSAL)

    analysis_input = AnalysisInput(
        images=images,
        height_cm=height_cm,
        weight_kg=weight_kg,
        age=age,
        sex=sex,
    )

    # --- Pipeline ---

    # Step 1: Pose detection
    try:
        landmarks = extract_landmarks(analysis_input)
    except PoseDetectionError as exc:
        if exc.pose == PoseCapture.FRONT.value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Could not detect pose in frontal image. "
                    "Please ensure your full body is visible."
                ),
            ) from exc
        warnings.append(
            AnalysisWarning(
                code="POSE_DETECTION_PARTIAL",
                message=str(exc),
                affected_metric=exc.pose,
            )
        )

    # Step 2: Calibration (pixels → cm)
    try:
        calibrated = calibrate(landmarks, height_cm)
    except CalibrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Step 3: Anthropometric measurements
    measurements = calculate_measurements(calibrated)

    # Step 4: Body composition estimation
    try:
        metrics = estimate_body_metrics(
            measurements=measurements,
            weight_kg=weight_kg,
            height_cm=height_cm,
            age=age,
            sex=sex,
        )
    except AnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    analysis_id = uuid.uuid4()

    result = AnalysisResult(
        analysis_id=analysis_id,
        user_id=(current_user.id if current_user else None),
        measurements=measurements,
        metrics=metrics,
        poses_used=poses_used,
        warnings=warnings,
    )

    # Persist via Pydantic serialization (ADR: validated JSONB)
    db_analysis = Analysis(
        id=analysis_id,
        user_id=(current_user.id if current_user else None),
        poses_used=[p.value for p in poses_used],
        height_cm=height_cm,
        weight_kg=weight_kg,
        age=age,
        sex=sex.value,
        measurements=measurements.model_dump(),
        metrics=metrics.model_dump(),
    )
    db.add(db_analysis)

    return result
