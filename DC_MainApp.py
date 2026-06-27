from DC_Dashboard import DCDashboard
from DC_Editor import DCEditor
from DC_PendencyEngine import DCPendencyEngine


class DCMainApp:
    def __init__(self, loader):
        self.loader = loader
        self.editor = DCEditor(loader)
        self.pendency_engine = DCPendencyEngine(loader)
        self.dashboard = DCDashboard(loader, self.pendency_engine)

    def print_banner(self):
        print(
            """
  ============================================================
    DC MANAGEMENT SYSTEM - PUNE ZONE v2.0
    Modes: Web App + Terminal Admin Menu
  ============================================================
"""
        )

    def wait_enter(self):
        input("\nPress Enter to continue...")

    def parse_col_values(self):
        values = {}
        while True:
            entry = input("  col=value (or done): ").strip()
            if entry.lower() in ("done", ""):
                break
            if "=" in entry:
                key, value = entry.split("=", 1)
                values[int(key.strip())] = value.strip()
        return values

    def show_pendency(self):
        data = self.dashboard.build_dashboard_data()
        pend = data["pendency"]
        print("\nPendency Summary")
        print("-" * 60)
        print(f"Minor DC      : SW={pend['minor']['sw']} CW={pend['minor']['cw']} TOTAL={pend['minor']['total']}")
        print(f"Major DC      : SW={pend['major']['sw']} CW={pend['major']['cw']} TOTAL={pend['major']['total']}")
        print(f"Suspension    : SW={pend['suspension']['sw']} CW={pend['suspension']['cw']} TOTAL={pend['suspension']['total']}")
        print(f"Appeal        : SW={pend['appeal']['sw']} CW={pend['appeal']['cw']} TOTAL={pend['appeal']['total']}")

    def run(self):
        while True:
            self.print_banner()
            print("  [1] View Sheet Structure")
            print("  [2] Search Employee by CPF")
            print("  [3] Add Record")
            print("  [4] Update Record")
            print("  [5] Delete Record")
            print("  [6] Extract DC Numbers")
            print("  [7] View Pendency Summary")
            print("  [8] View Closed Cases")
            print("  [0] Exit")
            choice = input("\nEnter choice: ").strip()

            if choice == "1":
                sheet = input("Sheet name: ").strip()
                try:
                    info = self.editor.view_sheet(sheet)
                    print(info)
                except Exception as exc:
                    print(exc)
                self.wait_enter()
            elif choice == "2":
                sheet = input("Sheet name: ").strip()
                cpf = input("CPF No: ").strip()
                rows = self.editor.find_by_cpf(sheet, cpf)
                for row in rows:
                    print(f"Row {row['row_number']}: {row['row_data'][:12]}")
                self.wait_enter()
            elif choice == "3":
                sheet = input("Sheet name: ").strip()
                print("Enter column values")
                try:
                    result = self.editor.add_record(sheet, self.parse_col_values())
                    print(result)
                except Exception as exc:
                    print(exc)
                self.wait_enter()
            elif choice == "4":
                sheet = input("Sheet name: ").strip()
                row_number = int(input("Row number: ").strip())
                print("Enter updated column values")
                try:
                    result = self.editor.update_record(sheet, row_number, self.parse_col_values())
                    print(result)
                except Exception as exc:
                    print(exc)
                self.wait_enter()
            elif choice == "5":
                sheet = input("Sheet name: ").strip()
                row_number = int(input("Row number: ").strip())
                try:
                    result = self.editor.delete_record(sheet, row_number)
                    print(result)
                except Exception as exc:
                    print(exc)
                self.wait_enter()
            elif choice == "6":
                try:
                    print(self.editor.extract_all_dc())
                except Exception as exc:
                    print(exc)
                self.wait_enter()
            elif choice == "7":
                self.show_pendency()
                self.wait_enter()
            elif choice == "8":
                for item in self.editor.load_closed()[:20]:
                    print(item)
                self.wait_enter()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
                self.wait_enter()
