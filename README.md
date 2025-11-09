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
│   └── schedule.json     # Generated schedule (created automatically)
├── services/
│   ├── data_service.py          # Data service
│   └── genetic_scheduler.py     # Genetic algorithm
└── main.py               # Main application menu
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
- Even distribution of lessons across weekdays

### Genetic Operators:

- **Initialization**: random filling without teacher conflicts
- **Selection**: tournament selection (choosing the best from random samples)
- **Crossover**: single-point exchange of days between schedules
- **Mutation**: random modification of several lessons

## Usage

### Running the program:

```bash
python main.py
```

### Menu:

```
1. Generate new schedule (Genetic Algorithm) - Generate a new schedule
2. Show data information - Display data information
3. Exit - Exit the program
```

### Schedule Generation:

1. Select option "1" in the menu
2. The algorithm will automatically:
   - Create an initial population of 50 schedules
   - Evolve them over 200 generations
   - Select the best schedule
   - Save the result to `data/schedule.json`
   - Create CSV files for convenient viewing
3. Progress will be displayed every 20 generations
4. Upon completion, the final fitness score will be shown

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
    "class_gaps": 13
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
```

This means:

- No teacher conflicts (mandatory requirement met)
- Minimized gaps for teachers and classes
- 180 lessons created for the week for all classes

## Working with CSV Files

After schedule generation, the system creates several CSV files for convenient viewing.
For a detailed guide on working with CSV files, see **[CSV_GUIDE.md](CSV_GUIDE.md)**

Quick file list:

- `schedule_full.csv` - full schedule (all classes × all days)
- `schedule_monday.csv` ... `schedule_friday.csv` - schedules by day
- `schedule_class_5A.csv` ... `schedule_class_11A.csv` - schedules by class
- `schedule_teachers.csv` - teacher schedule

All files can be opened in Excel or Google Sheets for viewing and printing.

## Requirements

- Python 3.8+
- Standard Python libraries (json, random, copy, csv, pathlib, typing)

## Authors

Project developed for managing school class schedules.
