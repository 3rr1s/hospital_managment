import csv
import time
import ast
import operator
import pandas as pd
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
# Sorting Strategy (OOP)
# --------------------------
class SortingStrategy:
    def sort(self, data: List[Patient], key: str) -> List[Patient]:
        raise NotImplementedError("This method should be overridden.")

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

    def add_patient(self):
        pid = input("Enter patient ID: ").strip()
        if pid in self.patients:
            print("Patient ID already exists!")
            return
        name = input("Enter patient name: ").strip()
        age_input = input("Enter patient age: ").strip()
        if not age_input.isdigit():
            print("Invalid age. Must be a whole number.")
            return
        age = int(age_input)
        illness = input("Enter patient illness: ").strip()
        score_input = input("Enter patient score (0-10): ").strip()
        try:
            score = float(score_input)
        except ValueError:
            print("Invalid score. Must be a number.")
            return
        logic_expr = input("Enter logical expression (e.g., 'age > 50 and score > 7'): ").strip()

        patient = Patient(pid, name, age, illness, score, logic_expr)
        self.patients[pid] = patient
        self.unique_illnesses.add(illness)
        print("Patient added successfully!")

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
        pid = input("Enter the ID of the patient to edit: ").strip()
        if pid not in self.patients:
            print("Patient not found.")
            return

        patient = self.patients[pid]
        print(f"Editing: {patient}")

        name = input(f"New name (blank = keep '{patient.name}'): ").strip() or patient.name
        age_input = input(f"New age (blank = keep '{patient.age}'): ").strip()
        age = int(age_input) if age_input.isdigit() else patient.age
        illness = input(f"New illness (blank = keep '{patient.illness}'): ").strip() or patient.illness
        score_input = input(f"New score (blank = keep '{patient.score}'): ").strip()
        try:
            score = float(score_input) if score_input else patient.score
        except ValueError:
            score = patient.score
        logic_expr = input(f"New logical expression (blank = keep '{patient.logic_expr}'): ").strip() or patient.logic_expr

        patient.name = name
        patient.age = age
        patient.illness = illness
        patient.score = score
        patient.logic_expr = logic_expr
        self.unique_illnesses.add(illness)
        print("Patient updated successfully!")

    def search_patients(self):
        query = input("Enter name, illness, or ID to search: ").strip()
        results = recursive_search(list(self.patients.values()), query)
        if results:
            print(f"\nFound {len(results)} result(s):")
            self.view_patients(results)
        else:
            print("No matching patients found.")

    def sort_patients(self, algorithm: str):
        if not self.patients:
            print("No patients to sort.")
            return

        key_map = {'1': 'id', '2': 'name', '3': 'age', '4': 'score'}
        print("\nSort by:\n1. ID\n2. Name\n3. Age\n4. Score")
        key_choice = input("Choose sort key (1-4): ").strip()
        key = key_map.get(key_choice, 'name')

        strategy = BubbleSort() if algorithm == 'bubble' else MergeSort()
        print(f"Sorting by '{key}' using {'Bubble Sort' if algorithm == 'bubble' else 'Merge Sort'}...")

        start_time = time.time()
        sorted_data = strategy.sort(list(self.patients.values()), key)
        sorted_data.sort(key=lambda p: (not p.evaluate_logic(),))
        end_time = time.time()

        print("\n--- Sorted Patients (logic=True first) ---")
        for p in sorted_data:
            logic_result = p.evaluate_logic()
            print(f"  [{'+' if logic_result else ' '}] {p}")
        print(f"\nSorting took {round(end_time - start_time, 6)} seconds.")

    def show_patient_tuples(self):
        if not self.patients:
            print("No patients in the system.")
            return
        tuples = [p.to_tuple() for p in self.patients.values()]
        print("\n--- Patient Tuples (id, name, age, illness, score, logic_expr) ---")
        for t in tuples:
            print(t)

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
        records = [
            {'ID': p.id, 'Name': p.name, 'Age': p.age,
             'Illness': p.illness, 'Score': p.score, 'Logic': p.logic_expr}
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
            print(f"Loaded {loaded} patient(s) from '{filename}'.")
        except FileNotFoundError:
            print(f"File '{filename}' not found.")
        except Exception as e:
            print(f"Error loading CSV: {e}")

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
            print(f"Saved {len(records)} patient(s) to '{filename}'.")
        except Exception as e:
            print(f"Error saving CSV: {e}")

# --------------------------
# Main Menu
# --------------------------
def main():
    system = HospitalManagementSystem()
    menu = {
        '1': ('Add Patient',                 system.add_patient),
        '2': ('View Patients',               lambda: system.view_patients()),
        '3': ('Edit Patient',                system.edit_patient),
        '4': ('Search Patients',             system.search_patients),
        '5': ('Sort (Bubble Sort)',          lambda: system.sort_patients('bubble')),
        '6': ('Sort (Merge Sort)',           lambda: system.sort_patients('merge')),
        '7': ('View as Tuples',             system.show_patient_tuples),
        '8': ('Numeral Systems View',        system.show_numeral_systems),
        '9': ('Pandas Summary & Stats',      system.show_pandas_summary),
        '10': ('Load from CSV',             system.load_from_csv),
        '11': ('Save to CSV',               system.save_to_csv),
        '12': ('Exit',                      None),
    }

    while True:
        print("\n========== Hospital Management System ==========")
        for key, (label, _) in menu.items():
            print(f"  {key:>2}. {label}")
        print("================================================")
        choice = input("Choose option: ").strip()

        if choice == '12':
            print("Goodbye!")
            break
        elif choice in menu:
            menu[choice][1]()
        else:
            print("Invalid choice. Please enter a number from the menu.")

if __name__ == '__main__':
    main()
