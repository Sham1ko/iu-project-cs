# CSV Schedule Files Guide

After schedule generation, the system creates several CSV files in a versioned folder (e.g., `data/v1/`, `data/v2/`) for convenient viewing and printing.

**Version Management:** Each generation creates a new version folder (v1, v2, v3...), so previous results are never overwritten. You can keep and compare multiple schedule versions.

## Generated Files

### 1. `schedule_full.csv` - Full Schedule

**Purpose:** Complete overview of the entire schedule  
**Format:**

- Rows = classes (5A, 5B, 6A, ...)
- Columns = time slots (Mon 1, Mon 2, ..., Fri 6)
- Cells = "Subject (Teacher)"

**How to use:**

- Open in Excel/Google Sheets
- Use for general analysis
- Apply filters and conditional formatting
- Convenient for school administration

---

### 2. `schedule_monday.csv` to `schedule_friday.csv` - By Day

**Purpose:** Schedule for a specific day  
**Format:**

- Rows = classes
- Columns = lessons (Lesson 1 - Lesson 6)
- Cells = Subject and Teacher (on separate lines)

**How to use:**

- Open the desired day in Excel
- Print for display on bulletin boards
- Convenient for daily planning
- Can be sent to teachers for the day

**Examples:**

- `schedule_monday.csv` - Monday schedule
- `schedule_friday.csv` - Friday schedule

---

### 3. `schedule_class_*.csv` - For Each Class

**Purpose:** Weekly schedule for an individual class  
**Format:**

- Rows = lesson numbers (Lesson 1 - Lesson 6)
- Columns = weekdays (Monday - Friday)
- Cells = Subject and Teacher

**How to use:**

- Open the file for the desired class (e.g., `schedule_class_5A.csv`)
- Print and distribute to students
- Display in the classroom
- Send to parents

**Examples:**

- `schedule_class_5A.csv` - schedule for class 5A
- `schedule_class_11A.csv` - schedule for class 11A

---

### 4. `schedule_teachers.csv` - Teacher Schedule

**Purpose:** Workload for all teachers  
**Format:**

- Rows = teachers
- Columns = time slots (Mon 1, Mon 2, ..., Fri 6)
- Cells = "Subject (Class)"

**How to use:**

- Open in Excel/Google Sheets
- Check teacher workload
- Find gaps (empty lessons) in the schedule
- Print individual schedules for each teacher
- Use for planning substitutions

---

## Tips for Working in Excel/Google Sheets

### Improving Readability:

1. **Auto-fit columns:**

   - Excel: Select all → Format → AutoFit Column Width
   - Google Sheets: Double-click between column headers

2. **Text wrapping in cells:**

   - Excel: Select cells → Format → Wrap Text
   - Google Sheets: Format → Text wrapping → Wrap

3. **Freeze headers:**

   - Excel: View → Freeze Panes → Freeze Top Row
   - Google Sheets: View → Freeze → 1 row

4. **Conditional formatting:**
   - Highlight different subjects with different colors
   - Highlight gaps (empty cells)
   - Highlight lessons for a specific teacher

### Printing:

1. **Page setup:**

   - Orientation: Landscape (for wide tables)
   - Scale: Fit to page
   - Margins: Narrow

2. **For classes:**

   - Use `schedule_class_*.csv` files
   - A4 format in portrait orientation

3. **For bulletin boards:**
   - Use daily files (`schedule_monday.csv`, etc.)
   - Increase font size for better visibility
   - A3 or A2 format

### Data Analysis:

1. **Find all lessons for a subject:**

   - Use Ctrl+F to search (e.g., "Math")

2. **Check teacher workload:**

   - Open `schedule_teachers.csv`
   - Find the row for the desired teacher
   - Count non-empty cells

3. **Check for gaps:**
   - Empty cells between lessons = gaps
   - Fewer gaps = better schedule

---

## Encoding and Compatibility

- All CSV files are saved in **UTF-8 with BOM** encoding
- Open correctly in:

  - Microsoft Excel (Windows/Mac)
  - Google Sheets
  - LibreOffice Calc
  - Apple Numbers

- If text displays incorrectly:
  - Excel: Data → From Text → Select UTF-8
  - Google Sheets: File → Import → Upload file

---

## Generating a New Schedule

To create a new schedule version:

```bash
python main.py
```

Select option "1" - the system will:

1. Automatically detect existing versions (v1, v2, v3...)
2. Create a new version folder with the next number
3. Save all schedule files to the new version folder
4. Keep all previous versions intact

**Example:**

- First generation → saved to `data/v1/`
- Second generation → saved to `data/v2/`
- Third generation → saved to `data/v3/`
- And so on...

---

## Notes

- Empty cells (or "-") indicate a free lesson
- Cell format with data: "Subject (Teacher)" or "Subject\nTeacher"
- All files for a generation are stored together in its version folder
- Each new generation creates a separate version folder
- CSV files can be manually edited, but changes do not affect the JSON
- Previous versions are preserved and never overwritten
