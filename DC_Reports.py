import csv
import json
import os
from datetime import datetime

from DC_DataLoader import REPORT_DIR


class DCReports:
    def __init__(self, pendency_engine):
        self.pendency_engine = pendency_engine

    def export_pendency_csv(self, all_dc):
        pend = self.pendency_engine.calc_pendency(all_dc)
        month_name = datetime.now().strftime("%B")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(REPORT_DIR, f"{month_name}_35DC_{timestamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Category", "Statewise", "Circlewise", "Total"])
            writer.writerow(["Minor DC", pend["minor"]["sw"], pend["minor"]["cw"], pend["minor"]["total"]])
            writer.writerow(["Major DC", pend["major"]["sw"], pend["major"]["cw"], pend["major"]["total"]])
            writer.writerow(["Suspension", pend["suspension"]["sw"], pend["suspension"]["cw"], pend["suspension"]["total"]])
            writer.writerow(["Suspension Revoked", pend["revoke"]["sw"], pend["revoke"]["cw"], pend["revoke"]["total"]])
            writer.writerow(["Appeal", pend["appeal"]["sw"], pend["appeal"]["cw"], pend["appeal"]["total"]])
            writer.writerow([])
            writer.writerow(["Sheet", "Count"])
            for sheet_name, count in sorted(pend["sheet"].items()):
                writer.writerow([sheet_name, count])
        return path

    def export_pendency_json(self, all_dc):
        pend = self.pendency_engine.calc_pendency(all_dc)
        month_name = datetime.now().strftime("%B")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(REPORT_DIR, f"{month_name}_35DC_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(pend, handle, indent=2)
        return path
