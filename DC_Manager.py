"""
DC Manager entrypoint.

Default mode starts the offline web app.
Use --cli to open the terminal menu.
"""

import json
import sys

from DC_Dashboard import DCDashboard
from DC_DataLoader import DCDataLoader
from DC_Editor import DCEditor
from DC_MainApp import DCMainApp
from DC_PendencyEngine import DCPendencyEngine
from DC_Reports import DCReports


def print_usage():
    print("Usage:")
    print("  python DC_Manager.py                 # start offline web app (network mode)")
    print("  python DC_Manager.py --web           # start offline web app (network mode)")
    print("  python DC_Manager.py --standalone    # start offline web app (localhost only)")
    print("  python DC_Manager.py --cli           # start terminal menu")
    print("  python DC_Manager.py --pendency      # print pendency summary JSON")
    print("  python DC_Manager.py --structure 6DC # show sheet structure")
    print("  python DC_Manager.py --find 6DC 2208334")
    print("  python DC_Manager.py --extract       # extract DC numbers")
    print("  python DC_Manager.py --export-csv    # export pendency CSV")
    print("  python DC_Manager.py --export-json   # export pendency JSON")


def run_cli(loader):
    DCMainApp(loader).run()


def run_pendency(loader):
    dashboard = DCDashboard(loader, DCPendencyEngine(loader))
    data = dashboard.build_dashboard_data()
    print(json.dumps(data["pendency"], indent=2))


def run_structure(loader, sheet_name):
    editor = DCEditor(loader)
    print(json.dumps(editor.view_sheet(sheet_name), indent=2))


def run_find(loader, sheet_name, cpfno):
    editor = DCEditor(loader)
    print(json.dumps(editor.find_by_cpf(sheet_name, cpfno), indent=2))


def run_extract(loader):
    editor = DCEditor(loader)
    print(json.dumps(editor.extract_all_dc(), indent=2))


def run_export(loader, fmt):
    engine = DCPendencyEngine(loader)
    reports = DCReports(engine)
    all_dc = loader.load_all(use_cache=False)
    if fmt == "csv":
        path = reports.export_pendency_csv(all_dc)
    else:
        path = reports.export_pendency_json(all_dc)
    print(path)


def run_web(loader, standalone=False):
    from DC_WebApp import run_server

    host = "127.0.0.1" if standalone else "0.0.0.0"
    run_server(loader, host=host)


if __name__ == "__main__":
    loader = DCDataLoader()

    if len(sys.argv) == 1 or sys.argv[1] == "--web":
        run_web(loader)
    elif sys.argv[1] == "--standalone":
        run_web(loader, standalone=True)
    elif sys.argv[1] == "--cli":
        run_cli(loader)
    elif sys.argv[1] == "--pendency":
        run_pendency(loader)
    elif sys.argv[1] == "--structure" and len(sys.argv) > 2:
        run_structure(loader, sys.argv[2])
    elif sys.argv[1] == "--find" and len(sys.argv) > 3:
        run_find(loader, sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "--extract":
        run_extract(loader)
    elif sys.argv[1] == "--export-csv":
        run_export(loader, "csv")
    elif sys.argv[1] == "--export-json":
        run_export(loader, "json")
    else:
        print_usage()
