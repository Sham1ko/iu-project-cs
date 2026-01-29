import json
from pathlib import Path
from typing import List, Dict, Any


class DataService:
    """Service for working with schedule data"""
    
    def __init__(self, data_dir: str = "data", teachers_file: str = "teachers.json"):
        self.data_dir = Path(data_dir)
        self.teachers_file = teachers_file
    
    def load_subjects(self) -> List[Dict[str, Any]]:
        """Load list of subjects"""
        with open(self.data_dir / "subjects.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["subjects"]
    
    def load_teachers(self) -> List[Dict[str, Any]]:
        """Load list of teachers"""
        with open(self.data_dir / self.teachers_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["teachers"]
    
    def load_classes(self) -> List[Dict[str, Any]]:
        """Load list of classes"""
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