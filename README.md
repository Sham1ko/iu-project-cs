# School Schedule Generator with Genetic Algorithm

Automatic generation of school schedules using a genetic algorithm.

## Description

The system uses a genetic algorithm to create an optimal class schedule based on data about:

- Classes (12 classes: 5A-11A)
- Teachers (16 teachers)
- Subjects (15 subjects)

## Project Structure

```
iu-project-cs/
├── data/
│   ├── classes.json      # Class data
│   ├── teachers.json     # Teacher data
│   ├── subjects.json     # Subject data
│   ├── v1/              # First generation results
│   │   ├── schedule.json
│   │   └── *.csv files
│   ├── v2/              # Second generation results
│   │   ├── schedule.json
│   │   └── *.csv files
│   └── v3/              # Third generation results (and so on...)
│       ├── schedule.json
│       └── *.csv files
├── services/
│   ├── data_service.py          # Data service
│   └── genetic_scheduler.py     # Genetic algorithm
├── main.py               # Main application menu
└── validate_data.py      # Data validation script
```

## Schedule Parameters

- **5 days** per week (Monday - Friday)
- **6 lessons** per day
- **12 classes** (5A, 5B, 6A, 6B, 7A, 7B, 8A, 8B, 9A, 9B, 10A, 11A)

## Genetic Algorithm

### Parameters:

- Population size: 50
- Number of generations: 200
- Mutation probability: 0.1
- Tournament size: 5

### Constraints:

**Hard Constraints** (mandatory):

- A teacher cannot teach two lessons simultaneously
- A teacher can only teach their assigned subjects

**Soft Constraints** (desirable):

- Minimize gaps (empty lessons) for teachers
- Minimize gaps for classes
- Minimize empty slots before the first lesson of the day for classes
- Even distribution of lessons across weekdays

### Genetic Operators:

- **Initialization**: random filling without teacher conflicts
- **Selection**: tournament selection (choosing the best from random samples)
- **Crossover**: single-point exchange of days between schedules
- **Mutation**:
  - Standard mutation (70%): random modification of several lessons
  - Compaction mutation (30%): shifts lessons to the start of the day to eliminate early gaps

## Usage

### Running the program:

```bash
python main.py
```

### Menu:

```
1. Generate new schedule (Genetic Algorithm) - Generate a new schedule
2. Validate data (Check teacher availability) - Check if there are enough teachers
3. Show data information - Display data information
4. Exit - Exit the program
```

### Schedule Generation:

1. Select option "1" in the menu
2. The algorithm will automatically:
   - Create an initial population of 50 schedules
   - Evolve them over 200 generations
   - Select the best schedule
   - Save the result to a new version folder (e.g., `data/v1/`, `data/v2/`, etc.)
   - Create CSV files for convenient viewing
3. Progress will be displayed every 20 generations
4. Upon completion, the final fitness score will be shown

**Version Management:**

- Each generation creates a new versioned folder (v1, v2, v3, ...)
- Previous results are never overwritten
- You can compare different generations
- All files for a generation are stored together in its version folder

### Data Validation:

Before generating a schedule, you can validate your data:

1. Select option "2" in the menu
2. The validator will check:
   - **Teachers per Subject** - How many teachers can teach each subject
   - **Subject Coverage** - Whether all subjects have at least one teacher
   - **Teacher Workload Analysis** - If teachers have capacity for all classes
   - **Class Requirements** - Whether each class can get all subjects
   - **Potential Conflicts** - Bottlenecks like single-teacher subjects

The validation report will show:
- ✓ Green checkmarks for passed checks
- ⚠ Yellow warnings for potential issues
- ✗ Red X marks for critical problems

**When to run validation:**
- Before your first schedule generation
- After adding or removing teachers
- After changing subject assignments
- When schedules have poor fitness scores

### Output File Format:

#### JSON file (`schedule.json`):

```json
{
  "schedule": {
    "Monday": {
      "1": {
        "5A": {"teacher": "John Doe", "subject": "Math"},
        "5B": null,
        ...
      },
      ...
    },
    ...
  },
  "fitness_score": 1001.76,
  "generation": 185,
  "statistics": {
    "total_lessons": 180,
    "teacher_conflicts": 0,
    "teacher_gaps": 17,
    "class_gaps": 13,
    "early_gaps": 0
  }
}
```

#### CSV files (for viewing in Excel/Google Sheets):

The system creates several CSV files for different views:

1. **`schedule_full.csv`** - Full schedule

   - Rows: all classes
   - Columns: all lessons of all days (Mon 1, Mon 2, ..., Fri 6)
   - Cells: Subject (Teacher)

2. **`schedule_monday.csv` to `schedule_friday.csv`** - By day

   - Rows: all classes
   - Columns: lessons of the day (Lesson 1 - Lesson 6)
   - Convenient for printing daily schedules

3. **`schedule_class_*.csv`** - For each class

   - Rows: lesson numbers (Lesson 1 - Lesson 6)
   - Columns: weekdays
   - Convenient for distributing schedules to classes

4. **`schedule_teachers.csv`** - Teacher schedule
   - Rows: all teachers
   - Columns: all lessons of all days
   - Cells: Subject (Class)
   - Convenient for planning teacher workload

## Interpreting Results

### Fitness Score:

- **> 1000** - excellent schedule
- **900-1000** - good schedule with minimal drawbacks
- **700-900** - acceptable schedule
- **< 700** - improvement needed

### Statistics:

- `total_lessons` - total number of lessons in the schedule
- `teacher_conflicts` - number of teacher conflicts (should be 0!)
- `teacher_gaps` - number of gaps for teachers
- `class_gaps` - number of gaps for classes
- `early_gaps` - number of empty slots before the first lesson of the day (should be 0!)

## Example Results

Typical algorithm output:

```
Best fitness: 1001.76
Found at generation: 185

Statistics:
  - Total lessons: 180
  - Teacher conflicts: 0 ✓
  - Teacher gaps: 17
  - Class gaps: 13
  - Early gaps: 0 ✓
```

This means:

- No teacher conflicts (mandatory requirement met)
- No empty slots before the first lesson of the day
- Minimized gaps for teachers and classes
- 180 lessons created for the week for all classes

## Working with CSV Files

After schedule generation, the system creates several CSV files in a versioned folder for convenient viewing.
For a detailed guide on working with CSV files, see **[CSV_GUIDE.md](CSV_GUIDE.md)**

Quick file list (in each version folder, e.g., `data/v1/`):

- `schedule_full.csv` - full schedule (all classes × all days)
- `schedule_monday.csv` ... `schedule_friday.csv` - schedules by day
- `schedule_class_5A.csv` ... `schedule_class_11A.csv` - schedules by class
- `schedule_teachers.csv` - teacher schedule

All files can be opened in Excel or Google Sheets for viewing and printing.

**Note:** Each generation creates a new version folder, so you can keep and compare multiple schedule versions.

## Version Management

The system automatically versions each schedule generation:

### How It Works:

1. **Automatic Detection**: The system scans the `data/` folder for existing version directories (v1, v2, v3...)
2. **Next Version**: Automatically determines the next version number
3. **New Folder**: Creates a new folder (e.g., `data/v4/`) for the current generation
4. **All Files Saved**: Both JSON and all CSV files are saved to the version folder
5. **Previous Versions Preserved**: Old schedules are never overwritten

### Example Directory Structure:

```
data/
├── classes.json
├── teachers.json
├── subjects.json
├── v1/                    # First generation (Monday, 10:00 AM)
│   ├── schedule.json
│   ├── schedule_full.csv
│   └── ... (all CSV files)
├── v2/                    # Second generation (Monday, 2:30 PM)
│   ├── schedule.json
│   ├── schedule_full.csv
│   └── ... (all CSV files)
└── v3/                    # Third generation (Tuesday, 9:15 AM)
    ├── schedule.json
    ├── schedule_full.csv
    └── ... (all CSV files)
```

### Benefits:

- **Compare Results**: Keep multiple schedule versions and compare their fitness scores
- **No Data Loss**: Previous schedules are never accidentally overwritten
- **Easy Rollback**: If a new schedule isn't satisfactory, use a previous version
- **Track Progress**: See how different algorithm runs perform over time

For detailed information about the version management update, see **[CHANGELOG.md](CHANGELOG.md)**

## Requirements

- Python 3.8+
- Standard Python libraries (json, random, copy, csv, pathlib, typing)

## Authors

Project developed for managing school class schedules.
