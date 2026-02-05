import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class DataService:
    """Service for working with schedule data."""

    def __init__(
        self,
        data_dir: str = "data",
        teachers_file: str = "teachers.json",
        excel_file: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        self.data_dir = Path(data_dir)
        self.teachers_file = teachers_file
        self.excel_file: Optional[Path] = None
        self._subjects: Optional[List[Dict[str, Any]]] = None
        self._teachers: Optional[List[Dict[str, Any]]] = None
        self._classes: Optional[List[Dict[str, Any]]] = None

        if excel_file:
            excel_path = Path(excel_file)
            if not excel_path.is_absolute():
                excel_path = self.data_dir / excel_path
            self.excel_file = excel_path
        else:
            default_excel = self.data_dir / "dataset.xlsx"
            if default_excel.exists():
                self.excel_file = default_excel

        if payload is not None:
            self._subjects = payload.get("subjects")
            self._teachers = payload.get("teachers")
            self._classes = payload.get("classes")
            if (
                self._subjects is None
                or self._teachers is None
                or self._classes is None
            ):
                raise ValueError(
                    "Dataset payload must include 'subjects', 'teachers', and 'classes'."
                )
        elif self.excel_file is not None:
            from .excel_loader import load_dataset_from_excel

            if not self.excel_file.exists():
                raise FileNotFoundError(f"Excel dataset not found: {self.excel_file}")
            dataset = load_dataset_from_excel(self.excel_file)
            self._subjects = dataset["subjects"]
            self._teachers = dataset["teachers"]
            self._classes = dataset["classes"]
    
    def load_subjects(self) -> List[Dict[str, Any]]:
        """Load list of subjects"""
        if self._subjects is not None:
            return self._subjects
        with open(self.data_dir / "subjects.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["subjects"]
    
    def load_teachers(self) -> List[Dict[str, Any]]:
        """Load list of teachers"""
        if self._teachers is not None:
            return self._teachers
        with open(self.data_dir / self.teachers_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["teachers"]
    
    def load_classes(self) -> List[Dict[str, Any]]:
        """Load list of classes"""
        if self._classes is not None:
            return self._classes
        with open(self.data_dir / "classes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["classes"]
    
    def get_subject_by_id(self, subject_id: int) -> Dict[str, Any] | None:
        """Get subject by ID"""
        subjects = self.load_subjects()
        return next((s for s in subjects if s["id"] == subject_id), None)
    
    def get_teacher_by_id(self, teacher_id: int) -> Dict[str, Any] | None:
        """Get teacher by ID"""
        teachers = self.load_teachers()
        return next((t for t in teachers if t["id"] == teacher_id), None)
    
    def get_class_by_id(self, class_id: int) -> Dict[str, Any] | None:
        """Get class by ID"""
        classes = self.load_classes()
        return next((c for c in classes if c["id"] == class_id), None)
    
    def get_teachers_by_subject(self, subject_id: int) -> List[Dict[str, Any]]:
        """Get all teachers teaching the given subject"""
        teachers = self.load_teachers()
        return [t for t in teachers if subject_id in t["subjects"]]
    
    def get_classes_by_grade(self, grade: int) -> List[Dict[str, Any]]:
        """Get all classes of the given grade"""
        classes = self.load_classes()
        return [c for c in classes if c["grade"] == grade]
