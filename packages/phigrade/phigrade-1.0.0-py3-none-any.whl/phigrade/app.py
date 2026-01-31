"""
FastAPI app for phigrade local server
"""
import logging
import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from tinydb import TinyDB, Query
from phigrade.compare import calculate_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SubmissionCreate(BaseModel):
    """Request model for creating submissions"""
    code_files: Dict[str, str]
    is_reference: bool


class SubmissionRead(BaseModel):
    """Response model for submissions"""
    id: str
    course_id: str
    assignment_id: str
    code_files: Dict[str, str]
    is_reference: bool
    is_active: bool


class UtestCreate(BaseModel):
    """Request model for creating utests"""
    module_name: str
    utest_name: str
    max_points: float = 1.0
    aggregation: str = "fail_fast"
    num_comparisons: int = 0


class UtestRead(BaseModel):
    """Response model for utests"""
    id: str
    course_id: str
    assignment_id: str
    module_name: str
    utest_name: str
    max_points: float
    aggregation: str
    num_comparisons: int


class UtestAttemptCreate(BaseModel):
    """Request model for utest attempts"""
    module_name: str
    utest_name: str


class UtestAttemptRead(BaseModel):
    """Response model for utest attempts"""
    id: str
    submission_id: str
    utest_id: str
    aggregate_score: float
    is_correct: Optional[bool]


class UtestRefComparisonCreate(BaseModel):
    """Request model for reference comparisons"""
    module_name: str
    utest_name: str
    comparison_name: str
    reference_output: Any
    comparison_info: Dict[str, Any]
    points: float = 1.0
    weight: float = 1.0


class UtestStudentComparisonCreate(BaseModel):
    """Request model for student attempt comparisons"""
    module_name: str
    utest_name: str
    comparison_name: str
    student_output: Any


class UtestRefComparisonRead(BaseModel):
    """Response model for reference comparisons"""
    id: str
    course_id: str
    assignment_id: str
    module_name: str
    utest_name: str
    comparison_name: str
    reference_output: Any
    comparison_info: Dict[str, Any]
    points: float
    weight: float


class UtestStudentComparisonRead(BaseModel):
    """Response model for attempt comparison results"""
    id: str
    course_id: str
    assignment_id: str
    module_name: str
    utest_name: str
    comparison_name: str
    student_output: Any
    is_correct: bool
    score: float


def create_app(local_db_file: str) -> FastAPI:
    """Create and configure the FastAPI app."""
    app = FastAPI(
        title="PhiGrade Local Server",
        description="Local development server for phigrade testing",
        version="1.0.0"
    )

    # Validate database file path
    if not local_db_file:
        raise ValueError("local_db_file cannot be None or empty")

    # Ensure the directory exists
    import os
    db_dir = os.path.dirname(os.path.abspath(local_db_file))
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Initialize database
    db = TinyDB(local_db_file, sort_keys=True, indent=4, separators=(',', ': '))
    references = db.table("references")
    submissions = db.table("submissions")
    utests = db.table("utests")
    utest_attempts = db.table("utest_attempts")

    @app.get("/ping", response_model=dict)
    def ping() -> dict:
        """Health check endpoint"""
        return {"status": "success"}

    @app.post("/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions", response_model=SubmissionRead)
    def create_submission(course_id: str, assignment_id: str, submission: SubmissionCreate) -> SubmissionRead:
        """Create a regular submission (not reference) - NOT stored in local mode"""
        if submission.is_reference:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reference submissions must use the reference submission endpoint"
            )

        print(f"Creating student submission (not persisted in local mode)...")

        submission_id = str(uuid.uuid4())

        submission_data = {
            "id": submission_id,
            "course_id": str(course_id),
            "assignment_id": str(assignment_id),
            "code_files": submission.code_files,
            "is_reference": submission.is_reference,
            "is_active": True
        }

        # In local mode, we don't persist student submissions
        # Just return the data without storing it
        return SubmissionRead(**submission_data)

    @app.post("/api/v1/courses/{course_id}/assignments/{assignment_id}/reference-submissions", response_model=SubmissionRead)
    def create_reference_submission(course_id: str, assignment_id: str, submission: SubmissionCreate) -> SubmissionRead:
        """Create a reference submission and deactivate all existing reference submissions for the assignment"""
        if not submission.is_reference:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is only for reference submissions"
            )

        print(f"Creating reference submission...")

        # Clear the entire database to start completely fresh
        db.drop_tables()
        print(f"Cleared entire database for completely fresh start")

        submission_id = str(uuid.uuid4())

        submission_data = {
            "id": submission_id,
            "course_id": str(course_id),
            "assignment_id": str(assignment_id),
            "code_files": submission.code_files,
            "is_reference": submission.is_reference,
            "is_active": True
        }

        submissions.insert(submission_data)
        return SubmissionRead(**submission_data)

    @app.post("/api/v1/courses/{course_id}/assignments/{assignment_id}/utests", response_model=UtestRead)
    def create_utest(course_id: str, assignment_id: str, utest: UtestCreate) -> UtestRead:
        """Create a utest definition"""
        existing = utests.get(
            (Query().course_id == str(course_id)) &
            (Query().assignment_id == str(assignment_id)) &
            (Query().module_name == utest.module_name) &
            (Query().utest_name == utest.utest_name)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Utest already exists")

        utest_id = str(uuid.uuid4())
        utest_data = {
            "id": utest_id,
            "course_id": str(course_id),
            "assignment_id": str(assignment_id),
            "module_name": utest.module_name,
            "utest_name": utest.utest_name,
            "max_points": utest.max_points,
            "aggregation": utest.aggregation,
            "num_comparisons": utest.num_comparisons,
        }
        utests.insert(utest_data)
        return UtestRead(**utest_data)

    @app.post("/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/utest-attempts", response_model=UtestAttemptRead)
    def create_utest_attempt(
        course_id: str,
        assignment_id: str,
        submission_id: str,
        attempt: UtestAttemptCreate,
    ) -> UtestAttemptRead:
        """Create a utest attempt for a submission."""
        utest = utests.get(
            (Query().course_id == str(course_id)) &
            (Query().assignment_id == str(assignment_id)) &
            (Query().module_name == attempt.module_name) &
            (Query().utest_name == attempt.utest_name)
        )
        if not utest:
            raise HTTPException(status_code=404, detail="Utest not found")

        # Check if this is for a reference submission by looking up the submission
        # Note: For student submissions that aren't stored, we can't look them up,
        # so we'll use a heuristic: if submission_id exists in stored submissions, it's reference
        submission = submissions.get(Query().id == str(submission_id))
        is_reference_attempt = submission is not None and submission.get("is_reference", False)

        if is_reference_attempt:
            # For reference submissions, check if attempt already exists and store it
            existing = utest_attempts.get(
                (Query().submission_id == str(submission_id)) &
                (Query().utest_id == utest["id"])
            )
            if existing:
                return UtestAttemptRead(**existing)

            print(f"Creating reference utest attempt...")
            attempt_id = str(uuid.uuid4())
            attempt_data = {
                "id": attempt_id,
                "submission_id": str(submission_id),
                "utest_id": utest["id"],
                "aggregate_score": 0.0,
                "is_correct": None,
            }
            utest_attempts.insert(attempt_data)
            return UtestAttemptRead(**attempt_data)
        else:
            # For student submissions, don't store - just return data
            print(f"Creating student utest attempt (not persisted)...")
            attempt_id = str(uuid.uuid4())
            attempt_data = {
                "id": attempt_id,
                "submission_id": str(submission_id),
                "utest_id": utest["id"],
                "aggregate_score": 0.0,
                "is_correct": None,
            }
            return UtestAttemptRead(**attempt_data)

    def phigrade_compare(reference_data: dict, student_output: Any) -> float:
        """Compare student result against reference and calculate score"""
        return calculate_score(
            reference_output=reference_data["reference_output"],
            student_output=student_output,
            comparison_info=reference_data["comparison_info"],
            max_points=reference_data["points"]
        )

    @app.post(
        "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/utest-attempts/{attempt_id}/ref-comparisons",
        response_model=UtestRefComparisonRead,
    )
    def submit_ref_comparison(
        course_id: str,
        assignment_id: str,
        submission_id: str,
        attempt_id: str,
        comparison: UtestRefComparisonCreate,
    ) -> UtestRefComparisonRead:
        """Submit a reference comparison."""
        submission = submissions.get(Query().id == str(submission_id))
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        attempt = utest_attempts.get(
            (Query().id == str(attempt_id)) &
            (Query().submission_id == str(submission_id))
        )
        if not attempt:
            raise HTTPException(status_code=404, detail="Utest attempt not found")

        utest = utests.get(Query().id == attempt["utest_id"])
        if not utest:
            raise HTTPException(status_code=404, detail="Utest not found")
        if utest["module_name"] != comparison.module_name or utest["utest_name"] != comparison.utest_name:
            raise HTTPException(status_code=400, detail="Utest metadata does not match attempt")

        reference_data = {
            "id": str(uuid.uuid4()),
            "course_id": str(course_id),
            "assignment_id": str(assignment_id),
            "module_name": comparison.module_name,
            "utest_name": comparison.utest_name,
            "comparison_name": comparison.comparison_name,
            "reference_output": comparison.reference_output,
            "comparison_info": comparison.comparison_info,
            "points": comparison.points,
            "weight": comparison.weight
        }

        references.upsert(
            reference_data,
            (Query().course_id == str(course_id)) &
            (Query().assignment_id == str(assignment_id)) &
            (Query().module_name == comparison.module_name) &
            (Query().utest_name == comparison.utest_name) &
            (Query().comparison_name == comparison.comparison_name)
        )

        return UtestRefComparisonRead(**reference_data)

    @app.post(
        "/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/utest-attempts/{attempt_id}/student-comparisons",
        response_model=UtestStudentComparisonRead,
    )
    def submit_student_comparison(
        course_id: str,
        assignment_id: str,
        submission_id: str,
        attempt_id: str,
        comparison: UtestStudentComparisonCreate,
    ) -> UtestStudentComparisonRead:
        """Submit a student comparison."""
        # For student comparisons, we don't require stored submissions/attempts
        # Just validate that the utest exists
        utest = utests.get(
            (Query().course_id == str(course_id)) &
            (Query().assignment_id == str(assignment_id)) &
            (Query().module_name == comparison.module_name) &
            (Query().utest_name == comparison.utest_name)
        )
        if not utest:
            raise HTTPException(status_code=404, detail="Utest not found")

        stored_reference = references.get(
            (Query().course_id == str(course_id)) &
            (Query().assignment_id == str(assignment_id)) &
            (Query().module_name == comparison.module_name) &
            (Query().utest_name == comparison.utest_name) &
            (Query().comparison_name == comparison.comparison_name)
        )

        if not stored_reference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Reference comparison not found: "
                    f"assignment={assignment_id}, module={comparison.module_name}, "
                    f"utest={comparison.utest_name}, comparison={comparison.comparison_name}"
                )
            )

        score = phigrade_compare(stored_reference, comparison.student_output)
        is_correct = (score == stored_reference["points"])

        result_data = {
            "id": str(uuid.uuid4()),
            "course_id": str(course_id),
            "assignment_id": str(assignment_id),
            "module_name": comparison.module_name,
            "utest_name": comparison.utest_name,
            "comparison_name": comparison.comparison_name,
            "student_output": comparison.student_output,
            "is_correct": is_correct,
            "score": score
        }

        return UtestStudentComparisonRead(**result_data)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app(local_db_file="phigrade_db.json")
    uvicorn.run(app, host="0.0.0.0", port=8765)
