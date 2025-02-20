#!/usr/bin/env python
"""
simulator_bp.py

This blueprint integrates the dynamic hedging/gamma scalping simulation engine
with a web dashboard. You can input simulation parameters—including collateral,
position size, entry price, liquidation price, rebalance threshold, hedging cost,
simulation duration, time step, drift, volatility, and position side—and view auto‑calculated
values such as leverage and cumulative profit. The simulation log is processed
into chart data for visualization.
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
        "volatility": 0.8,             # Annual volatility
        "position_side": "long"        # Position side: "long" or "short"
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
            params["position_side"] = request.form.get("position_side", params["position_side"]).lower()
        except Exception as e:
            logger.error("Error parsing simulation parameters: %s", e)

    # Instantiate the simulation engine.
    simulator = PositionSimulator(
        entry_price=params["entry_price"],
        liquidation_price=params["liquidation_price"],
        position_size=params["position_size"],
        rebalance_threshold=params["rebalance_threshold"],
        hedging_cost_pct=params["hedging_cost_pct"],
        collateral=params["collateral"],
        position_side=params["position_side"]
    )

    results = simulator.run_simulation(
        simulation_duration=params["simulation_duration"],
        dt_minutes=params["dt_minutes"],
        drift=params["drift"],
        volatility=params["volatility"]
    )

    # Compute leverage as (effective_entry_price * position_size) / collateral
    leverage = (simulator.effective_entry_price * params["position_size"]) / params["collateral"]

    # Prepare chart data from the simulation log (mapping each step to its attributes)
    chart_data = []
    for log_entry in results["simulation_log"]:
        chart_data.append({
            "step": log_entry["step"],
            "cumulative_profit": log_entry["cumulative_profit"],
            "travel_percent": log_entry["travel_percent"],
            "price": log_entry["price"],
            "unrealized_pnl": log_entry["unrealized_pnl"]
        })

    # Placeholder for live positions data (to be integrated later)
    live_positions = None

    return render_template("simulator_dashboard.html",
                           params=params,
                           results=results,
                           chart_data=chart_data,
                           leverage=leverage,
                           live_positions=live_positions)


@simulator_bp.route('/compare', methods=['GET', 'POST'])
def compare_simulation():
    # Default simulation parameters (all in minutes where applicable)
    params = {
        "entry_price": 10000,
        "liquidation_price": 8000,
        "position_size": 1.0,
        "collateral": 1000.0,
        "rebalance_threshold": -25.0,
        "hedging_cost_pct": 0.001,
        "simulation_duration": 60,
        "dt_minutes": 1,
        "drift": 0.05,
        "volatility": 0.8
    }

    # If the form is posted, update parameters
    if request.method == "POST":
        try:
            params["entry_price"] = float(request.form.get("entry_price", params["entry_price"]))
            params["liquidation_price"] = float(request.form.get("liquidation_price", params["liquidation_price"]))
            params["position_size"] = float(request.form.get("position_size", params["position_size"]))
            params["collateral"] = float(request.form.get("collateral", params["collateral"]))
            params["rebalance_threshold"] = float(
                request.form.get("rebalance_threshold", params["rebalance_threshold"]))
            params["hedging_cost_pct"] = float(request.form.get("hedging_cost_pct", params["hedging_cost_pct"]))
            params["simulation_duration"] = float(
                request.form.get("simulation_duration", params["simulation_duration"]))
            params["dt_minutes"] = float(request.form.get("dt_minutes", params["dt_minutes"]))
            params["drift"] = float(request.form.get("drift", params["drift"]))
            params["volatility"] = float(request.form.get("volatility", params["volatility"]))
        except Exception as e:
            logger.error("Error parsing simulation parameters: %s", e)

    # Run the simulation using your existing simulator (adjust if you want to add more options, such as side)
    from simulator.simulation import PositionSimulator
    simulator = PositionSimulator(
        entry_price=params["entry_price"],
        liquidation_price=params["liquidation_price"],
        position_size=params["position_size"],
        rebalance_threshold=params["rebalance_threshold"],
        hedging_cost_pct=params["hedging_cost_pct"],
        collateral=params["collateral"]
    )
    sim_results = simulator.run_simulation(
        simulation_duration=params["simulation_duration"],
        dt_minutes=params["dt_minutes"],
        drift=params["drift"],
        volatility=params["volatility"]
    )
    leverage = (simulator.effective_entry_price * params["position_size"]) / params["collateral"]

    # Prepare chart data for simulation (e.g., cumulative profit over time)
    sim_chart_data = []
    for log_entry in sim_results["simulation_log"]:
        sim_chart_data.append({
            "step": log_entry["step"],
            "cumulative_profit": log_entry["cumulative_profit"],
            "price": log_entry["price"],
            "travel_percent": log_entry["travel_percent"],
            "unrealized_pnl": log_entry["unrealized_pnl"]
        })

    # Get real data from the database (using your existing PositionService and CalcServices)
    from positions.position_service import PositionService
    from utils.calc_services import CalcServices
    real_positions = PositionService.get_all_positions()
    real_totals = CalcServices().calculate_totals(real_positions)

    # (Optional) If you have snapshots/history data, you could also prepare a time-series chart
    # for real data. For now, we pass the aggregated totals.

    return render_template("simulator_compare.html",
                           params=params,
                           sim_results=sim_results,
                           sim_chart_data=sim_chart_data,
                           leverage=leverage,
                           real_totals=real_totals,
                           real_positions=real_positions)


if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(simulator_bp, url_prefix="/simulator")
    app.run(debug=True)
