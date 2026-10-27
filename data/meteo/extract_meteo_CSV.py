
import csv
import gzip
from pathlib import Path

folder = Path(__file__).resolve().parent
source = next(folder.glob("Q_44_previous-1950-2024_RR-T-Vent.csv.gz"))
target = folder / "meteo_precipitations_44_2024.csv"

columns = ["NUM_POSTE", "NOM_USUEL", "LAT", "LON", "AAAAMMJJ", "RR", "QRR"]

with gzip.open(source, "rt", encoding="utf-8-sig", newline="") as f_in:
    reader = csv.DictReader(f_in, delimiter=";")
    missing = set(columns) - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    with target.open("x", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=columns, delimiter=",")
        writer.writeheader()
        count = 0
        for row in reader:
            if row["AAAAMMJJ"].startswith("2024") and row["RR"].strip():
                writer.writerow({col: row[col] for col in columns})
                count += 1

print(f"{count} records written to {target}")

# History: 2026-10-28: Made manual preparation checkout-relative, preserved existing outputs and translated console messages.
