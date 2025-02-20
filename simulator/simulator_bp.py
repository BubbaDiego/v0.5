#!/usr/bin/env python
"""
simulator_bp.py

This blueprint integrates the dynamic hedging/gamma scalping simulation engine
with a web dashboard. You can input simulation parameters—including collateral,
position size, entry price, liquidation price, rebalance threshold, hedging cost,
simulation duration, time step, drift, and volatility—and view auto‑calculated
values such as leverage and cumulative profit. The simulation log is processed
into chart data for visualization. (Live positions data and real‑time updates via
SocketIO can be added later as enhancements.)
"""

from flask import Blueprint, render_template, request, jsonify, current_app, url_for
import logging
from simulator.simulation import PositionSimulator

simulator_bp = Blueprint('simulator', __name__, template_folder='templates')
logger = logging.getLogger("SimulatorBP")

@simulator_bp.route('/simulation', methods=['GET', 'POST'])
def simulator_dashboard():
    # Default simulation parameters (all in minutes where applicable)
    params = {
        "entry_price": 10000,           # Price at which the position is entered
        "liquidation_price": 8000,       # Price at which the position would be liquidated
        "position_size": 1.0,            # Size of the position (in units)
        "collateral": 1000.0,            # Collateral backing the position (in dollars)
        "rebalance_threshold": -25.0,    # Trigger hedge when travel percent <= -25%
        "hedging_cost_pct": 0.001,       # Hedging cost as a fraction (0.1%)
        "simulation_duration": 60,       # Total simulation duration in minutes
        "dt_minutes": 1,               # Time step (minutes)
        "drift": 0.05,                 # Annual drift rate
        "volatility": 0.8              # Annual volatility
    }

    if request.method == "POST":
        try:
            params["entry_price"] = float(request.form.get("entry_price", params["entry_price"]))
            params["liquidation_price"] = float(request.form.get("liquidation_price", params["liquidation_price"]))
            params["position_size"] = float(request.form.get("position_size", params["position_size"]))
            params["collateral"] = float(request.form.get("collateral", params["collateral"]))
            params["rebalance_threshold"] = float(request.form.get("rebalance_threshold", params["rebalance_threshold"]))
            params["hedging_cost_pct"] = float(request.form.get("hedging_cost_pct", params["hedging_cost_pct"]))
            params["simulation_duration"] = float(request.form.get("simulation_duration", params["simulation_duration"]))
            params["dt_minutes"] = float(request.form.get("dt_minutes", params["dt_minutes"]))
            params["drift"] = float(request.form.get("drift", params["drift"]))
            params["volatility"] = float(request.form.get("volatility", params["volatility"]))
        except Exception as e:
            logger.error("Error parsing simulation parameters: %s", e)

    # Instantiate the simulation engine.
    # The PositionSimulator now accepts a 'collateral' parameter.
    simulator = PositionSimulator(
        entry_price=params["entry_price"],
        liquidation_price=params["liquidation_price"],
        position_size=params["position_size"],
        rebalance_threshold=params["rebalance_threshold"],
        hedging_cost_pct=params["hedging_cost_pct"],
        collateral=params["collateral"]
    )

    results = simulator.run_simulation(
        simulation_duration=params["simulation_duration"],
        dt_minutes=params["dt_minutes"],
        drift=params["drift"],
        volatility=params["volatility"]
    )

    # Compute leverage as (effective_entry_price * position_size) / collateral
    leverage = (simulator.effective_entry_price * params["position_size"]) / params["collateral"]

    # Prepare chart data from the simulation log (mapping each step to its cumulative profit)
    chart_data = []
    for log_entry in results["simulation_log"]:
        chart_data.append({
            "step": log_entry["step"],
            "cumulative_profit": log_entry["cumulative_profit"]
        })

    # Placeholder for live positions data (to be integrated later)
    live_positions = None

    return render_template("simulator_dashboard.html",
                           params=params,
                           results=results,
                           chart_data=chart_data,
                           leverage=leverage,
                           live_positions=live_positions)

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(simulator_bp, url_prefix="/simulator")
    app.run(debug=True)
