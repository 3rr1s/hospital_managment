import csv
import time
import ast
import operator
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict

# -------------------------------
# Safe Logic Evaluation (no eval)
# -------------------------------
SAFE_OPERATORS = {
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

def safe_eval(expr: str, variables: dict) -> bool:
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body, variables)
    except Exception:
        return False

def _eval_node(node, variables: dict):
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, variables) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_node(node.operand, variables)
    elif isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, variables)
            if not SAFE_OPERATORS[type(op)](left, right):
                return False
        return True
    elif isinstance(node, ast.Name):
        return variables.get(node.id, False)
    elif isinstance(node, ast.Constant):
        return node.value
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")

# -------------------------------
# Patient Class
# -------------------------------
class Patient:
    def __init__(self, id: str, name: str, age: int, illness: str, score: float = 0.0, logic_expr: str = ""):
        self.id = id
        self.name = name
        self.age = int(age)
        self.illness = illness
        self.score = float(score)
        self.logic_expr = logic_expr

    def __str__(self):
        return (f"ID: {self.id} | Name: {self.name} | Age: {self.age} | "
                f"Illness: {self.illness} | Score: {self.score} | Logic: {self.logic_expr}")

    def to_tuple(self):
        return (self.id, self.name, self.age, self.illness, self.score, self.logic_expr)

    def evaluate_logic(self) -> bool:
        expr = self.logic_expr.strip()
        if not expr:
            return False
        expr = (expr
                .replace("∧", " and ")
                .replace("∨", " or ")
                .replace("¬", " not ")
                .replace("→", "<=")
                .replace("⇔", "=="))
        variables = {"age": self.age, "score": self.score, "p": self.score > 5, "q": self.age > 30}
        return safe_eval(expr, variables)

    def numeral_summary(self) -> str:
        age_bin = bin(self.age)
        age_oct = oct(self.age)
        age_hex = hex(self.age)
        score_int = int(self.score)
        score_bin = bin(score_int)
        score_oct = oct(score_int)
        score_hex = hex(score_int)
        return (f"  Age  -> Binary: {age_bin}, Octal: {age_oct}, Hex: {age_hex}\n"
                f"  Score(int) -> Binary: {score_bin}, Octal: {score_oct}, Hex: {score_hex}")

# --------------------------
# PatientReport — Subclass of Patient
# --------------------------
class PatientReport(Patient):
    def __init__(self, id: str, name: str, age: int, illness: str, score: float = 0.0, logic_expr: str = "", notes: str = ""):
        super().__init__(id, name, age, illness, score, logic_expr)
        self.notes: str = notes
        self.is_high_risk: bool = score > 7
        self.risk_level: str = self._classify_risk()
        self.age_group: str = self._classify_age()

    def _classify_risk(self) -> str:
        if self.score >= 8.0:
            return "HIGH"
        elif self.score >= 5.0:
            return "MEDIUM"
        return "LOW"

    def _classify_age(self) -> str:
        if self.age < 18:
            return "Child"
        elif self.age < 60:
            return "Adult"
        return "Senior"

    def summary(self) -> str:
        return (f"[REPORT] {self.name} | Age Group: {self.age_group} | "
                f"Risk: {self.risk_level} | High Risk Flag: {self.is_high_risk} | "
                f"Notes: {self.notes if self.notes else 'None'}")

    def to_tuple(self):
        base: tuple = super().to_tuple()
        return base + (self.risk_level, self.age_group, self.notes)

# --------------------------
# Sorting Strategy (Abstract Base Class)
# --------------------------
class SortingStrategy(ABC):
    @abstractmethod
    def sort(self, data: List[Patient], key: str) -> List[Patient]:
        pass

    @staticmethod
    def get_value(patient: Patient, key: str):
        val = getattr(patient, key)
        if key in ('age', 'score'):
            return float(val)
        return str(val).lower()

class BubbleSort(SortingStrategy):
    def sort(self, data: List[Patient], key: str) -> List[Patient]:
        n = len(data)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.get_value(data[j], key) > self.get_value(data[j + 1], key):
                    data[j], data[j + 1] = data[j + 1], data[j]
        return data

class MergeSort(SortingStrategy):
    def sort(self, data: List[Patient], key: str) -> List[Patient]:
        def merge(left, right):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                if self.get_value(left[i], key) <= self.get_value(right[j], key):
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        def recursive_sort(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = recursive_sort(arr[:mid])
            right = recursive_sort(arr[mid:])
            return merge(left, right)

        return recursive_sort(data)

# --------------------------
# Recursive Patient Search
# --------------------------
def recursive_search(patients: List[Patient], query: str, index: int = 0) -> List[Patient]:
    if index >= len(patients):
        return []
    matches = []
    p = patients[index]
    if query.lower() in p.name.lower() or query.lower() in p.illness.lower() or query == p.id:
        matches.append(p)
    return matches + recursive_search(patients, query, index + 1)

# --------------------------
# Main Management System
# --------------------------
class HospitalManagementSystem:
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.unique_illnesses: set = set()
        self._silent_load()

    def _silent_load(self):
        filename = "hospital_patients.csv"
        try:
            df = pd.read_csv(filename)
            df.columns = [c.strip().lower() for c in df.columns]
            col_map = {
                'patientid': 'id', 'patient_id': 'id', 'name': 'name', 'age': 'age',
                'condition': 'illness', 'illness': 'illness', 'diagnosis': 'illness',
                'severitylevel': 'score', 'severity_level': 'score', 'score': 'score',
                'logicalexpression': 'logic_expr', 'logical_expression': 'logic_expr', 'logic_expr': 'logic_expr'
            }
            df.rename(columns=col_map, inplace=True)
            for _, row in df.iterrows():
                try:
                    pid = str(row['id'])
                    self.patients[pid] = Patient(pid, str(row['name']), int(row['age']),
                                                  str(row.get('illness', 'Unknown')),
                                                  float(row.get('score', 0.0)),
                                                  str(row.get('logic_expr', '')))
                    self.unique_illnesses.add(str(row.get('illness', 'Unknown')))
                except Exception:
                    pass
        except Exception:
            pass

    def _autosave(self):
        try:
            records = [
                {'id': p.id, 'name': p.name, 'age': p.age,
                 'illness': p.illness, 'score': p.score, 'logic_expr': p.logic_expr}
                for p in self.patients.values()
            ]
            df = pd.DataFrame(records)
            df.to_csv("hospital_patients.csv", index=False)

            excel_records = [
                {'ID': p.id, 'Name': p.name, 'Age': p.age,
                 'Illness': p.illness, 'Score (0-10)': p.score,
                 'Logical Expression': p.logic_expr}
                for p in self.patients.values()
            ]
            pd.DataFrame(excel_records).to_excel("hospital_patients.xlsx", index=False)
        except Exception as e:
            print(f"  Auto-save failed: {e}")

    def add_patient(self):
        try:
            pid = input("Enter patient ID: ").strip()
            if not pid:
                print("  Error: Patient ID cannot be empty.")
                return
            if pid in self.patients:
                print(f"  Error: Patient ID '{pid}' already exists. Use a unique ID.")
                return
            name = input("Enter patient name: ").strip()
            if not name:
                print("  Error: Patient name cannot be empty.")
                return
            age_input = input("Enter patient age (whole number): ").strip()
            if not age_input.isdigit():
                print(f"  Error: Age must be a whole number (e.g. 25). You entered: '{age_input}'")
                return
            age = int(age_input)
            valid_ages: range = range(0, 151)
            if age not in valid_ages:
                print(f"  Error: Age {age} is outside the valid range (0–150).")
                return
            illness = input("Enter patient illness: ").strip()
            if not illness:
                print("  Error: Illness field cannot be empty.")
                return
            score_input = input("Enter patient score (0.0 – 10.0): ").strip()
            try:
                score = float(score_input)
                if not (0.0 <= score <= 10.0):
                    print(f"  Error: Score must be between 0.0 and 10.0. You entered: {score}")
                    return
            except ValueError:
                print(f"  Error: Score must be a decimal number (e.g. 7.5). You entered: '{score_input}'")
                return
            print("\n  --- Logical Expression Help ---")
            print("  You can write a condition using the patient's age and score.")
            print("  Available variables:  age   score")
            print("  Available operators:  >  <  >=  <=  ==  and  or  not")
            print("  Examples:")
            print("    age > 50                  (patient is older than 50)")
            print("    score > 7                 (score is above 7)")
            print("    age > 50 and score > 7    (both conditions must be true)")
            print("    age < 30 or score >= 9    (either condition is true)")
            print("    not age > 60              (patient is NOT older than 60)")
            print("  Press Enter to skip (no expression).")
            print("  -------------------------------")
            logic_expr = input("  Enter logical expression: ").strip()

            patient = Patient(pid, name, age, illness, score, logic_expr)
            self.patients[pid] = patient
            self.unique_illnesses.add(illness)
            self._autosave()
            print(f"  Patient '{name}' (ID: {pid}) added and saved to CSV.")
        except Exception as e:
            print(f"  Unexpected error while adding patient: {e}")

    def view_patients(self, patients: List[Patient] = None, show_numerals: bool = False):
        patient_list = patients if patients is not None else list(self.patients.values())
        if not patient_list:
            print("No patients to display.")
            return

        self.unique_illnesses = set(p.illness for p in patient_list)
        print(f"\n--- Patients ({len(patient_list)}) ---")
        for p in patient_list:
            print(p)
            if show_numerals:
                print(p.numeral_summary())
        print(f"\nUnique illnesses on record: {self.unique_illnesses}")

    def edit_patient(self):
        try:
            pid = input("Enter the ID of the patient to edit: ").strip()
            if pid not in self.patients:
                print(f"  Error: No patient found with ID '{pid}'. Use option 2 to view all IDs.")
                return

            patient = self.patients[pid]
            print(f"  Editing: {patient}")

            name = input(f"  New name (blank = keep '{patient.name}'): ").strip() or patient.name

            age_input = input(f"  New age (blank = keep '{patient.age}'): ").strip()
            if age_input:
                if not age_input.isdigit():
                    print(f"  Error: Age must be a whole number. Keeping current value ({patient.age}).")
                    age = patient.age
                else:
                    age = int(age_input)
                    if age not in range(0, 151):
                        print(f"  Error: Age {age} out of range (0–150). Keeping current value ({patient.age}).")
                        age = patient.age
            else:
                age = patient.age

            illness = input(f"  New illness (blank = keep '{patient.illness}'): ").strip() or patient.illness

            score_input = input(f"  New score (blank = keep '{patient.score}'): ").strip()
            if score_input:
                try:
                    score = float(score_input)
                    if not (0.0 <= score <= 10.0):
                        print(f"  Error: Score must be 0.0–10.0. Keeping current value ({patient.score}).")
                        score = patient.score
                except ValueError:
                    print(f"  Error: '{score_input}' is not a valid number. Keeping current value ({patient.score}).")
                    score = patient.score
            else:
                score = patient.score

            logic_expr = input(f"  New logical expression (blank = keep '{patient.logic_expr}'): ").strip() or patient.logic_expr

            patient.name    = name
            patient.age     = age
            patient.illness = illness
            patient.score   = score
            patient.logic_expr = logic_expr
            self.unique_illnesses.add(illness)
            self._autosave()
            print(f"  Patient '{pid}' updated and saved to CSV.")
        except Exception as e:
            print(f"  Unexpected error while editing patient: {e}")

    def delete_patient(self):
        pid = input("Enter patient ID to delete: ").strip()
        if pid not in self.patients:
            print("  Patient not found.")
            return
        patient = self.patients[pid]
        confirm = input(f"  Delete [{pid}] {patient.name}? (yes/no): ").strip().lower()
        if confirm == 'yes':
            del self.patients[pid]
            self._autosave()
            print(f"  Patient [{pid}] {patient.name} deleted and removed from both files.")
        else:
            print("  Deletion cancelled.")

    def search_patients(self):
        query = input("Enter name, illness, or ID to search: ").strip()
        if not query:
            print("  Please enter a search term.")
            return
        try:
            results = recursive_search(list(self.patients.values()), query)
            if results:
                print(f"\n  Found {len(results)} result(s) for '{query}':")
                print(f"  {'ID':<10} {'Name':<15} {'Illness':<15} {'Score':<8} {'Cond A':<8} {'Cond B':<8} {'Result'}")
                print(f"  {'-'*75}")
                for p in results:
                    A, B, op, result = self._get_two_conditions(p)
                    a_str = str(A) if A is not None else 'N/A'
                    b_str = str(B) if B is not None else 'N/A'
                    r_str = 'TRUE' if result else 'FALSE'
                    print(f"  {p.id:<10} {p.name:<15} {p.illness:<15} {p.score:<8} {a_str:<8} {b_str:<8} {r_str}")
            else:
                print(f"  No patients found matching '{query}'. Check the spelling and try again.")
        except Exception as e:
            print(f"  Search error: {e}")

    def _get_two_conditions(self, p: 'Patient'):
        expr = p.logic_expr.strip() if p.logic_expr and p.logic_expr != 'nan' else ''
        variables = {"age": p.age, "score": p.score, "p": p.score > 5, "q": p.age > 30}
        if not expr:
            return None, None, 'N/A', False
        norm = (expr.replace("∧"," and ").replace("∨"," or ")
                    .replace("¬"," not ").replace("→","<=").replace("⇔","=="))
        if ' and ' in norm:
            parts = norm.split(' and ', 1)
            A = safe_eval(parts[0].strip(), variables)
            B = safe_eval(parts[1].strip(), variables)
            return A, B, 'AND', (A and B)
        elif ' or ' in norm:
            parts = norm.split(' or ', 1)
            A = safe_eval(parts[0].strip(), variables)
            B = safe_eval(parts[1].strip(), variables)
            return A, B, 'OR', (A or B)
        else:
            A = safe_eval(norm, variables)
            return A, None, 'SINGLE', A

    def sort_patients(self, algorithm: str):
        if not self.patients:
            print("  No patients to sort.")
            return

        key_map = {'1': 'id', '2': 'name', '3': 'age', '4': 'score'}
        print("\nSort by:\n1. ID\n2. Name\n3. Age\n4. Score")
        key_choice = input("Choose sort key (1-4): ").strip()
        if key_choice not in key_map:
            print("  Invalid choice. Defaulting to Name.")
        key = key_map.get(key_choice, 'name')
        algo_name = 'Bubble Sort' if algorithm == 'bubble' else 'Merge Sort'

        try:
            strategy = BubbleSort() if algorithm == 'bubble' else MergeSort()
            start_time = time.time()
            sorted_data = strategy.sort(list(self.patients.values()), key)
            sorted_data.sort(key=lambda p: (not p.evaluate_logic(),))
            end_time = time.time()

            label_map = {'id': 'ID', 'name': 'Name', 'age': 'Age', 'score': 'Score'}
            print(f"\n--- {algo_name} | Sorted by {label_map[key]} | Truth Table (2 Conditions) ---")
            print(f"  {'#':<4} {label_map[key]:<14} {'Cond A':<8} {'Cond B':<8} {'Op':<6} {'Result'}")
            print(f"  {'-'*60}")
            for i, p in enumerate(sorted_data, 1):
                A, B, op, result = self._get_two_conditions(p)
                val = str(getattr(p, key))
                a_str = str(A) if A is not None else 'N/A'
                b_str = str(B) if B is not None else 'N/A'
                r_str = 'TRUE' if result else 'FALSE'
                print(f"  {i:<4} {val:<14} {a_str:<8} {b_str:<8} {op:<6} {r_str}  | {p.logic_expr}")
            print(f"\n  Sorting took {round(end_time - start_time, 6)} seconds.")
        except Exception as e:
            print(f"  Sorting failed: {e}")

    def show_truth_table(self):
        if not self.patients:
            print("No patients in the system.")
            return
        print("\n========== Truth Table (Logical Expression Evaluation) ==========")
        print("  p = (score > 5)   |   q = (age > 30)\n")
        for p in self.patients.values():
            expr = p.logic_expr.strip()
            if not expr or expr == 'nan':
                continue
            variables = {"age": p.age, "score": p.score,
                         "p": p.score > 5, "q": p.age > 30}
            norm_expr = (expr.replace("∧"," and ").replace("∨"," or ")
                             .replace("¬"," not ").replace("→","<=").replace("⇔","=="))

            # Try to split into two sub-parts (A and/or B)
            connector = None
            parts = None
            if ' and ' in norm_expr:
                parts = norm_expr.split(' and ', 1)
                connector = 'AND'
            elif ' or ' in norm_expr:
                parts = norm_expr.split(' or ', 1)
                connector = 'OR'

            print(f"  Patient: {p.name} (ID: {p.id}) | age={p.age}, score={p.score}")
            print(f"  Expression: {expr}")

            if parts and connector:
                A_expr, B_expr = parts[0].strip(), parts[1].strip()
                A_actual = safe_eval(A_expr, variables)
                B_actual = safe_eval(B_expr, variables)

                col1 = f"A: {A_expr}"[:22]
                col2 = f"B: {B_expr}"[:22]
                print(f"  +{'-'*24}+{'-'*24}+{'-'*10}+")
                print(f"  | {col1:<22} | {col2:<22} | {'Result':<8} |")
                print(f"  +{'-'*24}+{'-'*24}+{'-'*10}+")
                for A in [True, False]:
                    for B in [True, False]:
                        result = (A and B) if connector == 'AND' else (A or B)
                        marker = " <--" if (A == A_actual and B == B_actual) else ""
                        print(f"  | {str(A):<22} | {str(B):<22} | {str(result):<8} |{marker}")
                print(f"  +{'-'*24}+{'-'*24}+{'-'*10}+")
            else:
                result = safe_eval(norm_expr, variables)
                print(f"  +{'-'*30}+{'-'*10}+")
                print(f"  | {'Expression':<28} | {'Result':<8} |")
                print(f"  +{'-'*30}+{'-'*10}+")
                print(f"  | {expr:<28} | {str(result):<8} |")
                print(f"  +{'-'*30}+{'-'*10}+")
            print()

    def compare_sorting(self):
        if not self.patients:
            print("  No patients to sort.")
            return
        key_map = {'1': 'id', '2': 'name', '3': 'age', '4': 'score'}
        print("\nCompare sorting by:\n1. ID\n2. Name\n3. Age\n4. Score")
        key_choice = input("Choose sort key (1-4): ").strip()
        if key_choice not in key_map:
            print("  Invalid choice. Defaulting to Name.")
        key = key_map.get(key_choice, 'name')
        RUNS = 3
        bubble = BubbleSort()
        merge  = MergeSort()
        data   = list(self.patients.values())

        b_sort_times  = []
        m_sort_times  = []
        b_logic_times = []
        m_logic_times = []

        for _ in range(RUNS):
            t0 = time.time()
            bubble.sort(data[:], key)
            b_sort_times.append(time.time() - t0)

            t0 = time.time()
            merge.sort(data[:], key)
            m_sort_times.append(time.time() - t0)

            t0 = time.time()
            r1 = bubble.sort(data[:], key)
            r1.sort(key=lambda p: (not p.evaluate_logic(),))
            b_logic_times.append(time.time() - t0)

            t0 = time.time()
            r2 = merge.sort(data[:], key)
            r2.sort(key=lambda p: (not p.evaluate_logic(),))
            m_logic_times.append(time.time() - t0)

        b_sort_avg  = sum(b_sort_times)  / RUNS
        m_sort_avg  = sum(m_sort_times)  / RUNS
        b_logic_avg = sum(b_logic_times) / RUNS
        m_logic_avg = sum(m_logic_times) / RUNS

        n = len(self.patients)
        print(f"\n{'='*60}")
        print(f"  MEASUREMENT 1: Sort Only  ({n} patient(s), {RUNS} runs each)")
        print(f"{'='*60}")
        print(f"  {'Algorithm':<22} {'Run 1':<12} {'Run 2':<12} {'Run 3':<12} {'Average'}")
        print(f"  {'-'*58}")
        print(f"  {'Bubble Sort':<22}" + "".join(f"{t:.6f}s   " for t in b_sort_times) + f"  {b_sort_avg:.6f}s")
        print(f"  {'Merge Sort (recursive)':<22}" + "".join(f"{t:.6f}s   " for t in m_sort_times) + f"  {m_sort_avg:.6f}s")
        w1 = "Bubble Sort" if b_sort_avg <= m_sort_avg else "Merge Sort"
        print(f"\n  Winner (sort only): {w1}")

        print(f"\n{'='*60}")
        print(f"  MEASUREMENT 2: Sort + Truth Table Evaluation  ({RUNS} runs each)")
        print(f"{'='*60}")
        print(f"  {'Algorithm':<22} {'Run 1':<12} {'Run 2':<12} {'Run 3':<12} {'Average'}")
        print(f"  {'-'*58}")
        print(f"  {'Bubble + Logic':<22}" + "".join(f"{t:.6f}s   " for t in b_logic_times) + f"  {b_logic_avg:.6f}s")
        print(f"  {'Merge + Logic':<22}" + "".join(f"{t:.6f}s   " for t in m_logic_times) + f"  {m_logic_avg:.6f}s")
        w2 = "Bubble Sort" if b_logic_avg <= m_logic_avg else "Merge Sort"
        print(f"\n  Winner (sort + truth table): {w2}")

        print(f"\n{'='*60}")
        print(f"  IMPACT OF TRUTH TABLE EVALUATION (recursion overhead included)")
        print(f"{'='*60}")
        b_overhead = b_logic_avg - b_sort_avg
        m_overhead = m_logic_avg - m_sort_avg
        print(f"  Bubble Sort overhead: +{b_overhead:.6f}s")
        print(f"  Merge Sort overhead:  +{m_overhead:.6f}s")
        overall = "Bubble Sort" if b_logic_avg <= m_logic_avg else "Merge Sort"
        print(f"\n  Overall fastest (with truth table): {overall}")

    def show_numeral_systems(self):
        if not self.patients:
            print("No patients in the system.")
            return
        print("\n--- Numeral System Representation ---")
        self.view_patients(show_numerals=True)

    def show_pandas_summary(self):
        if not self.patients:
            print("No patients in the system.")
            return
        fields = ('ID', 'Name', 'Age', 'Illness', 'Score', 'Logic')
        records = [
            dict(zip(fields, p.to_tuple()))
            for p in self.patients.values()
        ]
        df = pd.DataFrame(records)
        print("\n--- Pandas Summary ---")
        print(df.to_string(index=False))
        print("\n--- Numeric Stats ---")
        print(df[['Age', 'Score']].describe().round(2))

        high_risk = df[df['Score'] > 7]
        if not high_risk.empty:
            print(f"\n--- High Risk Patients (Score > 7) ---")
            print(high_risk.to_string(index=False))

    def load_from_csv(self):
        filename = "hospital_patients.csv"
        try:
            df = pd.read_csv(filename)
            df.columns = [c.strip().lower() for c in df.columns]

            col_map = {
                'patientid': 'id', 'patient_id': 'id',
                'name': 'name',
                'age': 'age',
                'condition': 'illness', 'illness': 'illness', 'diagnosis': 'illness',
                'severitylevel': 'score', 'severity_level': 'score', 'score': 'score',
                'logicalexpression': 'logic_expr', 'logical_expression': 'logic_expr', 'logic_expr': 'logic_expr'
            }
            df.rename(columns=col_map, inplace=True)

            loaded = 0
            for _, row in df.iterrows():
                try:
                    pid = str(row['id'])
                    name = str(row['name'])
                    age = int(row['age'])
                    illness = str(row.get('illness', 'Unknown'))
                    score = float(row.get('score', 0.0))
                    logic_expr = str(row.get('logic_expr', ''))
                    self.patients[pid] = Patient(pid, name, age, illness, score, logic_expr)
                    self.unique_illnesses.add(illness)
                    loaded += 1
                except Exception as e:
                    print(f"  Skipped row: {e}")
            print(f"\n  Loaded {loaded} patient(s) from '{filename}'. Press 2 to view them.")
        except FileNotFoundError:
            print(f"\n  File '{filename}' not found.")
        except Exception as e:
            print(f"\n  Error loading CSV: {e}")

    def save_to_csv(self):
        filename = "hospital_patients.csv"
        try:
            records = [
                {'id': p.id, 'name': p.name, 'age': p.age,
                 'illness': p.illness, 'score': p.score, 'logic_expr': p.logic_expr}
                for p in self.patients.values()
            ]
            df = pd.DataFrame(records)
            df.to_csv(filename, index=False)
            print("\n================================================")
            print(f"  SAVED {len(records)} patient(s) to '{filename}'.")
            print("  Patients in file:")
            for r in records:
                print(f"    - [{r['id']}] {r['name']}, Age {r['age']}, {r['illness']}")
            print("================================================")
        except Exception as e:
            print(f"\n  ERROR saving CSV: {e}")


# --------------------------
# Main Menu
# --------------------------
def main():
    system = HospitalManagementSystem()
    menu = {
        '1':  ('Add Patient',            system.add_patient),
        '2':  ('View Patients',          lambda: system.view_patients()),
        '3':  ('Edit Patient',           system.edit_patient),
        '4':  ('Delete Patient',         system.delete_patient),
        '5':  ('Search Patients',        system.search_patients),
        '6':  ('Sort (Bubble Sort)',           lambda: system.sort_patients('bubble')),
        '7':  ('Sort (Merge Sort)',            lambda: system.sort_patients('merge')),
        '8':  ('Sort Performance Comparison',  system.compare_sorting),
        '9':  ('Truth Table',                  system.show_truth_table),
        '10': ('Numeral Systems View',         system.show_numeral_systems),
        '11': ('Pandas Summary & Stats',       system.show_pandas_summary),
        '12': ('Load from CSV',                system.load_from_csv),
        '13': ('Exit',                         None),
    }

    while True:
        print("\n========== Hospital Management System ==========")
        for key, (label, _) in menu.items():
            print(f"  {key:>2}. {label}")
        print("================================================")
        choice = input("Choose option: ").strip()

        if choice == '13':
            print("Goodbye!")
            break
        elif choice in menu:
            menu[choice][1]()
        else:
            print("Invalid choice. Please enter a number from the menu.")

if __name__ == '__main__':
    main()
