"""Generate sample airline operations dataset for DS-Star demo."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


# Airlines and their typical characteristics
AIRLINES = {
    "AA": {"name": "American Airlines", "otp_base": 0.82},
    "UA": {"name": "United Airlines", "otp_base": 0.79},
    "DL": {"name": "Delta Air Lines", "otp_base": 0.85},
    "SW": {"name": "Southwest Airlines", "otp_base": 0.80},
    "JB": {"name": "JetBlue Airways", "otp_base": 0.76},
}

# Major US airports
AIRPORTS = [
    "ATL", "DFW", "DEN", "ORD", "LAX", "JFK", "LAS", "MCO", "MIA", "CLT",
    "SEA", "PHX", "EWR", "SFO", "IAH", "BOS", "FLL", "MSP", "LGA", "DTW",
]

# Delay causes with typical frequency weights
DELAY_CAUSES = {
    "weather": 0.30,
    "mechanical": 0.20,
    "crew": 0.15,
    "traffic": 0.25,
    "security": 0.10,
}


def generate_flight_record(
    flight_num: int,
    date: datetime,
    airline_code: str,
) -> Dict:
    """Generate a single flight record with realistic distributions.
    
    Args:
        flight_num: Sequential flight number
        date: Date of the flight
        airline_code: Two-letter airline code
    
    Returns:
        Dictionary containing flight record data
    """
    airline_info = AIRLINES[airline_code]
    
    # Generate origin and destination (ensure they're different)
    origin = random.choice(AIRPORTS)
    destination = random.choice([a for a in AIRPORTS if a != origin])
    
    # Generate scheduled departure time (throughout the day)
    hour = random.randint(5, 22)
    minute = random.choice([0, 15, 30, 45])
    scheduled_departure = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Determine if flight is cancelled (2-3% cancellation rate)
    cancelled = random.random() < 0.025
    
    if cancelled:
        return {
            "flight_id": f"{airline_code}{flight_num:04d}",
            "airline": airline_code,
            "origin": origin,
            "destination": destination,
            "scheduled_departure": scheduled_departure.isoformat(),
            "actual_departure": "",
            "delay_minutes": 0,
            "delay_cause": "",
            "load_factor": 0.0,
            "turnaround_minutes": 0,
            "cancelled": True,
            "date": date.date().isoformat(),
        }
    
    # Determine if flight is delayed based on airline's OTP
    otp = airline_info["otp_base"]
    is_on_time = random.random() < otp
    
    if is_on_time:
        # On-time: 0-14 minutes delay
        delay_minutes = random.randint(0, 14)
        delay_cause = ""
    else:
        # Delayed: 15-180 minutes, with exponential distribution favoring shorter delays
        delay_minutes = min(int(random.expovariate(1/30) + 15), 180)
        # Select delay cause based on weights
        delay_cause = random.choices(
            list(DELAY_CAUSES.keys()),
            weights=list(DELAY_CAUSES.values()),
            k=1
        )[0]
    
    actual_departure = scheduled_departure + timedelta(minutes=delay_minutes)
    
    # Generate load factor (passenger capacity utilization)
    # Typically 75-95% with normal distribution
    load_factor = random.gauss(0.85, 0.08)
    load_factor = max(0.50, min(1.0, load_factor))  # Clamp to realistic range
    
    # Generate turnaround time (time between arrival and next departure)
    # Typically 30-90 minutes with some variation
    turnaround_minutes = int(random.gauss(60, 15))
    turnaround_minutes = max(25, min(120, turnaround_minutes))
    
    return {
        "flight_id": f"{airline_code}{flight_num:04d}",
        "airline": airline_code,
        "origin": origin,
        "destination": destination,
        "scheduled_departure": scheduled_departure.isoformat(),
        "actual_departure": actual_departure.isoformat(),
        "delay_minutes": delay_minutes,
        "delay_cause": delay_cause,
        "load_factor": round(load_factor, 3),
        "turnaround_minutes": turnaround_minutes,
        "cancelled": False,
        "date": date.date().isoformat(),
    }


def generate_dataset(
    num_records: int = 1000,
    start_date: datetime = None,
    end_date: datetime = None,
) -> List[Dict]:
    """Generate complete airline operations dataset.
    
    Args:
        num_records: Number of flight records to generate
        start_date: Start date for flight records (default: 90 days ago)
        end_date: End date for flight records (default: today)
    
    Returns:
        List of flight record dictionaries
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)
    if end_date is None:
        end_date = datetime.now()
    
    # Calculate date range
    date_range = (end_date - start_date).days
    
    records = []
    airline_codes = list(AIRLINES.keys())
    
    for i in range(num_records):
        # Distribute flights across date range
        days_offset = random.randint(0, date_range)
        flight_date = start_date + timedelta(days=days_offset)
        
        # Select airline (roughly equal distribution)
        airline_code = airline_codes[i % len(airline_codes)]
        
        record = generate_flight_record(i + 1, flight_date, airline_code)
        records.append(record)
    
    # Sort by date and scheduled departure
    records.sort(key=lambda x: (x["date"], x["scheduled_departure"]))
    
    return records


def save_to_csv(records: List[Dict], output_path: str) -> None:
    """Save flight records to CSV file.
    
    Args:
        records: List of flight record dictionaries
        output_path: Path to output CSV file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "flight_id",
        "airline",
        "origin",
        "destination",
        "scheduled_departure",
        "actual_departure",
        "delay_minutes",
        "delay_cause",
        "load_factor",
        "turnaround_minutes",
        "cancelled",
        "date",
    ]
    
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Generated {len(records)} flight records")
    print(f"Saved to: {output_file.absolute()}")


def main():
    """Generate and save sample airline operations dataset."""
    # Generate 1200 records to ensure we have 1000+ after any filtering
    records = generate_dataset(num_records=1200)
    
    # Save to default location
    output_path = "./data/airline_operations.csv"
    save_to_csv(records, output_path)
    
    # Print summary statistics
    total = len(records)
    cancelled = sum(1 for r in records if r["cancelled"])
    delayed = sum(1 for r in records if not r["cancelled"] and r["delay_minutes"] >= 15)
    
    print(f"\nDataset Summary:")
    print(f"  Total flights: {total}")
    print(f"  Cancelled: {cancelled} ({cancelled/total*100:.1f}%)")
    print(f"  Delayed (15+ min): {delayed} ({delayed/total*100:.1f}%)")
    print(f"  Airlines: {', '.join(AIRLINES.keys())}")
    print(f"  Airports: {len(AIRPORTS)} major US airports")


if __name__ == "__main__":
    main()
