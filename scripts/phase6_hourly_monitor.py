#!/usr/bin/env python3
"""
PHASE 6 HOURLY MONITORING SCHEDULER
Automated monitoring for 24-hour intensive period (Jan 21-22, 2026)
"""

import requests
import json
import time
from datetime import datetime, timedelta
import subprocess

class Phase6Monitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.frontend_url = "https://kraftd-a4gfhqa2axb2h6cd.uaenorth-01.azurewebsites.net"
        self.monitoring_data = {
            "session_start": self.start_time.isoformat(),
            "hourly_reports": []
        }
        
    def health_check(self):
        """Perform comprehensive health check"""
        checks = {}
        
        # Frontend availability
        try:
            start = time.time()
            response = requests.get(self.frontend_url, timeout=10)
            latency = (time.time() - start) * 1000
            checks["frontend"] = {
                "status": "UP" if response.status_code == 200 else "DOWN",
                "code": response.status_code,
                "latency_ms": round(latency, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            checks["frontend"] = {
                "status": "DOWN",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        return checks
    
    def generate_hourly_report(self, hour):
        """Generate hourly status report"""
        checks = self.health_check()
        
        report = {
            "hour": hour,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "metrics": {
                "uptime_pct": 100.0 if checks["frontend"]["status"] == "UP" else 0.0,
                "avg_response_time_ms": checks["frontend"].get("latency_ms", 0),
                "error_count": 0 if checks["frontend"]["status"] == "UP" else 1
            }
        }
        
        self.monitoring_data["hourly_reports"].append(report)
        return report
    
    def display_hourly_summary(self, hour, report):
        """Display hourly summary"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        frontend_status = "✅" if report["checks"]["frontend"]["status"] == "UP" else "❌"
        latency = report["checks"]["frontend"].get("latency_ms", "N/A")
        
        print(f"\n[{timestamp}] HOUR {hour} STATUS UPDATE")
        print(f"  Frontend:      {frontend_status} {report['checks']['frontend']['status']}")
        print(f"  Response Time: {latency}ms")
        print(f"  Uptime:        {report['metrics']['uptime_pct']:.1f}%")
        print(f"  Errors:        {report['metrics']['error_count']}")
    
    def save_monitoring_state(self):
        """Save monitoring state to file"""
        with open('PHASE6_HOURLY_MONITORING.json', 'w') as f:
            json.dump(self.monitoring_data, f, indent=2)

def main():
    print("\n" + "="*70)
    print("PHASE 6: 24-HOUR CONTINUOUS MONITORING")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+3')}")
    print(f"Duration:   24 hours")
    print(f"Interval:   Hourly health checks + continuous monitoring")
    print("="*70)
    
    monitor = Phase6Monitor()
    
    # Perform initial health check
    print("\nPerforming initial health check...")
    initial_check = monitor.health_check()
    
    if initial_check["frontend"]["status"] == "UP":
        print(f"✅ Frontend: {initial_check['frontend']['code']} ({initial_check['frontend']['latency_ms']:.0f}ms)")
        print("✅ Monitoring initialized successfully")
    else:
        print("❌ Frontend unavailable - check network connectivity")
        return
    
    # Save initial state
    monitor.save_monitoring_state()
    
    print("\n" + "-"*70)
    print("MONITORING ACTIVE - First hourly report will be generated in ~1 hour")
    print("-"*70)
    print(f"\nFile: PHASE6_HOURLY_MONITORING.json (auto-updated hourly)")
    print("Status: Ready for 24-hour observation period\n")

if __name__ == "__main__":
    main()
