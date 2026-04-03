# BHSawesome vs CSAwesome: Comprehensive Comparison Report

## Executive Summary

BHSawesome reorganizes CSAwesome's 5-unit structure (aligned to the prior AP CSA
curriculum) into ~14 topical chapters, reordering and simplifying the
presentation. The 2025 AP CSA CED has **4 units** (1-4); inheritance (the former
Unit 5) was removed from the curriculum. BHSawesome correctly omits Unit 5.

Of the 53 CED topics (1.1-1.15, 2.1-2.12, 3.1-3.9, 4.1-4.17), BHSawesome
covers **all of them** to some degree. However, three topics have only partial
coverage, and three topic files are orphaned (exist on disk but not included in
the book).

## Fork History

- **Common ancestor**: Both repos share history through commit `2e22a7fa`
  (2025-06-29)
- **BHSawesome divergence**: 374 commits after the fork point
- **Major reorganization**: Commit `48d843c2` (2025-06-27) replaced the
  Unit-based directory structure with topical chapters
- **Editing sweep**: 24+ "first pass" editing commits from late June through
  mid-August 2025

## CED Topic Coverage Matrix

### Unit 1: Using Objects and Methods (CED 1.1-1.15)

| CED Topic | CSAwesome File | BHSawesome Coverage | BHS File(s) |
|-----------|---------------|-------------------|-------------|
| 1.1 Intro to Algorithms | topic-1-1-intro-algorithms.ptx | Full | introduction/topic-1-1-intro-algorithms.ptx |
| 1.2 Variables and Data Types | topic-1-2-variables.ptx | Full | primitive-types-and-variables/topic-1-2-variables.ptx |
| 1.3 Expressions and Output | topic-1-3-expressions.ptx | Full | primitive-types-and-variables/topic-1-3-expressions.ptx |
| 1.4 Assignment Statements | topic-1-4-assignment.ptx | Full | primitive-types-and-variables/topic-1-4-assignment.ptx |
| 1.5 Casting and Range | topic-1-5-casting.ptx | Full | primitive-types-and-variables/topic-1-5-casting.ptx |
| 1.6 Compound Assignment Operators | topic-1-6-compound-operators.ptx | **Full** | primitive-types-and-variables/topic-1-4-assignment.ptx (merged in) |
| 1.7 API and Libraries | topic-1-7-APIs-and-libraries.ptx | Full | methods/topic-1-7-APIs-and-libraries.ptx |
| 1.8 Comments | topic-1-8-comments.ptx | Full | abstraction-and-program-design/topic-1-8-comments.ptx |
| 1.9 Method Signatures | topic-1-9-method-signatures.ptx | Full | methods/topic-1-9-method-signatures.ptx |
| 1.10 Calling Class Methods | topic-1-10-calling-class-methods.ptx | **Partial** | methods/topic-1-9-method-signatures.ptx, methods/topic-1-11-Math.ptx (spread across two files, no dedicated coverage) |
| 1.11 Math Class | topic-1-11-Math.ptx | Full | methods/topic-1-11-Math.ptx |
| 1.12 Objects: Instances of Classes | topic-1-12-objects.ptx | **Partial** | objects/turtles.ptx, classes/topic-3-3-anatomy-of-class.ptx (scattered; **orphaned file** exists at objects/topic-1-12-objects.ptx but not in toctree) |
| 1.13 Object Creation | topic-1-13-constructors.ptx | **Full** | classes/topic-3-4-constructors.ptx (covers all AP 1.13 standards; **orphaned file** exists at objects/topic-1-13-constructors.ptx but not in toctree) |
| 1.14 Calling Instance Methods | topic-1-14-calling-instance-methods.ptx | **Full** | classes/topic-3-5-methods.ptx (covers dot operator, NullPointerException; **orphaned file** exists but not in toctree) |
| 1.15 String Manipulation | topic-1-15-strings.ptx | Full | strings/topic-1-15-strings.ptx |

### Unit 2: Selection and Iteration (CED 2.1-2.12)

| CED Topic | CSAwesome File | BHSawesome Coverage | BHS File(s) |
|-----------|---------------|-------------------|-------------|
| 2.1 Algorithms with Selection | topic-2-1-algorithms.ptx | Full | booleans-and-conditionals/topic-2-1-algorithms.ptx |
| 2.2 Boolean Expressions | topic-2-2-booleans.ptx | Full | booleans-and-conditionals/topic-2-2-booleans.ptx |
| 2.3 if Statements | topic-2-3-ifs.ptx | Full | booleans-and-conditionals/topic-2-3-ifs.ptx |
| 2.4 Nested if Statements | topic-2-4-nested-ifs.ptx | **Full** | booleans-and-conditionals/topic-2-3-ifs.ptx (merged in; covers nested ifs, multiway selection, all AP 2.4 standards) |
| 2.5 Compound Boolean Expressions | topic-2-5-compound-ifs.ptx | **Full** | booleans-and-conditionals/topic-2-2-booleans.ptx (&&, \|\|, !, short-circuit) and topic-2-6-comparing-booleans.ptx (De Morgan's) |
| 2.6 Comparing Boolean Expressions | topic-2-6-comparing-booleans.ptx | Full | booleans-and-conditionals/topic-2-6-comparing-booleans.ptx |
| 2.7 while Loops | topic-2-7-while-loops.ptx | Full | loops/topic-2-7-while-loops.ptx |
| 2.8 for Loops | topic-2-8-for-loops.ptx | Full | loops/topic-2-8-for-loops.ptx |
| 2.9 Loop Algorithms | topic-2-9-loop-algorithms.ptx | Full | loops/topic-2-9-loop-algorithms.ptx |
| 2.10 String Algorithms | topic-2-10-strings-loops.ptx | Full | strings/topic-2-10-strings-loops.ptx |
| 2.11 Nested Iteration | topic-2-11-nested-loops.ptx | Full | loops/topic-2-11-nested-loops.ptx |
| 2.12 Run-Time Analysis | topic-2-12-loop-analysis.ptx | Full | loops/topic-2-12-loop-analysis.ptx |

### Unit 3: Class Creation (CED 3.1-3.9)

| CED Topic | CSAwesome File | BHSawesome Coverage | BHS File(s) |
|-----------|---------------|-------------------|-------------|
| 3.1 Abstraction and Program Design | topic-3-1-abstraction.ptx | Full | abstraction-and-program-design/topic-3-1-abstraction.ptx |
| 3.2 Impact of Program Design | topic-3-2-impacts.ptx | Full | abstraction-and-program-design/topic-3-2-impacts.ptx |
| 3.3 Anatomy of a Class | topic-3-3-anatomy-of-class.ptx | Full | classes/topic-3-3-anatomy-of-class.ptx |
| 3.4 Constructors | topic-3-4-constructors.ptx | Full | classes/topic-3-4-constructors.ptx |
| 3.5 Methods | topic-3-5-methods.ptx | Full | classes/topic-3-5-methods.ptx |
| 3.6 Methods: References | topic-3-6-methods-references.ptx | Full | objects/topic-3-6-methods-references.ptx |
| 3.7 Class Variables and Methods | topic-3-7-static-vars-methods.ptx | **Full** | objects/topic-3-8-scope-access.ptx (merged in; covers static keyword, class variables, final) |
| 3.8 Scope and Access | topic-3-8-scope-access.ptx | Full | objects/topic-3-8-scope-access.ptx |
| 3.9 this Keyword | topic-3-9-this.ptx | **Full** | classes/instance-variables.ptx (extensive disambiguation coverage; minor gap: limited examples of passing `this` as argument) |

### Unit 4: Data Collections (CED 4.1-4.17)

| CED Topic | CSAwesome File | BHSawesome Coverage | BHS File(s) |
|-----------|---------------|-------------------|-------------|
| 4.1 Data Ethics | topic-4-1-data-ethics.ptx | **Partial** | abstraction-and-program-design/topic-3-2-impacts.ptx (privacy, bias, data quality all covered but embedded in CED 3.2 file, not standalone) |
| 4.2 Using Data Sets | topic-4-2-data-sets.ptx | Full | text-files/topic-4-2-data-sets.ptx |
| 4.3 Array Creation | topic-4-3-array-basics.ptx | Full | arrays/topic-4-3-array-basics.ptx |
| 4.4 Array Traversals | topic-4-4-array-traversal.ptx | Full | arrays/topic-4-4-array-traversal.ptx |
| 4.5 Array Algorithms | topic-4-5-array-algorithms.ptx | Full | arrays/topic-4-5-array-algorithms.ptx |
| 4.6 Using Text Files | topic-4-6-input-files.ptx | Full | text-files/topic-4-6-input-files.ptx |
| 4.7 Wrapper Classes | topic-4-7-wrapper-classes.ptx | Full | array-lists/topic-4-7-wrapper-classes.ptx |
| 4.8 ArrayList Methods | topic-4-8-arraylists.ptx | Full | array-lists/topic-4-8-arraylists.ptx |
| 4.9 ArrayList Traversals | topic-4-9-arraylist-traversal.ptx | Full | array-lists/topic-4-9-arraylist-traversal.ptx |
| 4.10 ArrayList Algorithms | topic-4-10-arraylist-algorithms.ptx | Full | array-lists/topic-4-10-arraylist-algorithms.ptx |
| 4.11 2D Array Creation | topic-4-11-2Darrays.ptx | Full | arrays/two-dimensional-arrays.ptx |
| 4.12 2D Array Traversals | topic-4-12-2Darray-traversal.ptx | Full | arrays/two-dimensional-arrays.ptx |
| 4.13 2D Array Algorithms | topic-4-13-2Darray-algorithms.ptx | Full | arrays/two-dimensional-array-algorithms.ptx |
| 4.14 Searching | topic-4-14-searching.ptx | Full | algorithms/topic-4-14-searching.ptx |
| 4.15 Sorting | topic-4-15-sorting.ptx | Full | algorithms/topic-4-15-sorting.ptx |
| 4.16 Recursion | topic-4-16-recursion.ptx | Full | algorithms/topic-4-16-recursion.ptx |
| 4.17 Recursive Search/Sort | topic-4-17-recursive-search-sort.ptx | Full | algorithms/topic-4-17-recursive-search-sort.ptx |

## Issues Requiring Attention

### 1. Orphaned Files (exist on disk, not included in book)

Three topic files exist in the BHSawesome `pretext/` directory but are **not
referenced by any toctree** and therefore not rendered in the book:

- `pretext/objects/topic-1-12-objects.ptx` — Objects: Instances of Classes
- `pretext/objects/topic-1-13-constructors.ptx` — Object Creation/Instantiation
- `pretext/classes/topic-1-14-calling-instance-methods.ptx` — Calling Instance
  Methods (also a copy in `pretext/reference-types/`)

A detailed comparison of each orphaned file against the active book content
shows that **all three are redundant** — no CED-required concepts are missing
from the active book because of their absence. They are remnants of the
reorganization where content was merged into other chapters and can be safely
deleted.

**topic-1-12-objects.ptx**: The active files `turtles.ptx` and
`topic-3-3-anatomy-of-class.ptx` already cover all current CED 1.12 standards
(objects as instances, class as blueprint, reference variables). The orphaned
file has a Turtle UML diagram and some visual aids that are nice-to-have but
nothing essential. Its inheritance/hierarchy content (CED 1.12.A.2, 1.12.A.3) is
vestigial — inheritance was removed from the 2025 CED.

**topic-1-13-constructors.ptx**: The active `topic-3-4-constructors.ptx` is
*more comprehensive* than the orphaned file, covering everything it does plus
default constructors, `this()` chaining, and more diverse examples. The only
unique content in the orphaned file is a CustomTurtle coding challenge.

**topic-1-14-calling-instance-methods.ptx**: The active `topic-3-5-methods.ptx`
covers both CED 1.14 standards (dot operator, NullPointerException). The
orphaned file has additional scaffolding — a class-vs-instance methods
comparison, method signature instruction, and Turtle-based activities — but
these are pedagogical extras, not missing CED content.

**Recommendation**: These files can be deleted. If desired, the CustomTurtle
challenge from topic-1-13 or the Turtle-based scaffolding activities from
topic-1-14 could be salvaged as supplementary exercises, but they are not needed
for CED coverage.

### 2. Partial Coverage: CED 1.10 (Calling Class Methods)

Coverage of static/class method calling conventions is spread across
topic-1-9-method-signatures.ptx and topic-1-11-Math.ptx. There is no unified
treatment of the concept that class methods are called using ClassName.method()
syntax. The AP standards (1.10.A.1, 1.10.A.2) are mentioned but the topic lacks
a dedicated section.

### 3. Partial Coverage: CED 1.12 (Objects: Instances of Classes)

The class-vs-object distinction and "blueprint" analogy appear in turtles.ptx
and topic-3-3-anatomy-of-class.ptx, but coverage is scattered. The orphaned
topic-1-12-objects.ptx file likely has more complete treatment.

### 4. Partial Coverage: CED 4.1 (Data Ethics)

All substantive CED 4.1 concepts (privacy, algorithmic bias, data quality) are
covered in topic-3-2-impacts.ptx within the abstraction-and-program-design
chapter. The content is thorough but is organizationally embedded in a CED 3.2
file rather than appearing as a standalone data-ethics topic in the data
collections portion of the book.

### 5. Minor Gap: CED 3.9 (this as argument)

The `this` keyword is well-covered for disambiguation (this.x = x), but there
are limited explicit examples of passing `this` as an argument to another
method, which is a specific CED requirement (3.9.A.2).

## Supplemental Content Comparison

### Present in CSAwesome but not BHSawesome

| Content | CSAwesome Location | Notes |
|---------|-------------------|-------|
| Magpie Lab (chatbot) | Unit2 (5 files: magpie1-4, exercises) | AP CS A lab activity |
| Consumer Review Lab | Unit2/ConsumerReviewLab.ptx | AP CS A lab activity |
| Picture Lab | Unit4 (9 files: pictureLabA1-A9) | AP CS A lab activity |
| Community Challenge | Unit3/community-challenge.ptx | Project-based activity |
| JavaSwing GUIs | Unit1/JavaSwingGUIs.ptx | GUI programming enrichment |
| Stories/Interviewees | Stories/ (14 interviewee profiles) | Diversity and inclusion content |
| HashMap | Unit4/hashmap.ptx | Beyond-AP enrichment |
| Timed Tests | TimedTests/ (4 tests) | Assessment |
| Untimed Tests | Tests/ (5 tests) | Assessment |
| Mixed Free Response | MixedFreeResponse/ (4 files) | Practice materials |
| Pretests/Posttests/Survey | Unit0, posttest/ | Assessment and data collection |
| Unit summaries | unit1a-summary.ptx, etc. | Per-section review materials |
| Toggle/write code practice | u1a-toggle-write-code.ptx, etc. (HiddenFiles/) | Interactive practice |
| Parsons problems (Unit-level) | ArrayParsonsPractice.ptx, etc. | Drag-and-drop coding practice |

### Present in BHSawesome but not CSAwesome

| Content | BHSawesome Location | Notes |
|---------|-------------------|-------|
| Turtles chapter | objects/turtles.ptx | Visual programming with turtle graphics |
| Text output (dedicated) | primitive-types-and-variables/text-output.ptx | Separated from expressions |
| Instance variables (dedicated) | classes/instance-variables.ptx | Standalone section |
| Object equality (dedicated) | objects/object-equality.ptx | Standalone section |
| If traps | booleans-and-conditionals/if-traps.ptx | Common pitfalls section |
| Text files as a chapter | text-files/ (2 files) | Elevated from subsection to chapter |

## Legacy Content

CSAwesome retains **Unit 5: Inheritance** (topics 5.1-5.7) from the prior AP CSA
curriculum. This covers: inheritance, subclass constructors, method overriding,
`super` keyword, class hierarchies, polymorphism, and the Object class. The 2025
CED removed this entire unit. BHSawesome's omission of this content is correct
and aligned with the current curriculum. The Unit 5 files still exist on disk in
BHSawesome's repo but are not included in the book.
