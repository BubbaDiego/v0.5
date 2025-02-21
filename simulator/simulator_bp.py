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

from flask import Blueprint, render_template, request, current_app, url_for
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
        collateral=params["collateral"],
        rebalance_threshold=params["rebalance_threshold"],
        hedging_cost_pct=params["hedging_cost_pct"],
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


from flask import Blueprint, render_template, request
import logging
from simulator.simulation import PositionSimulator
from data.data_locker import DataLocker
from datetime import datetime

simulator_bp = Blueprint('simulator', __name__, template_folder='templates')
logger = logging.getLogger("SimulatorBP")


@simulator_bp.route('/compare', methods=['GET', 'POST'])
def compare_simulation():
    # Define default baseline simulation parameters.
    baseline_params = {
        "entry_price": 10000.0,
        "liquidation_price": 8000.0,
        "position_size": 1.0,
        "collateral": 1000.0,
        "rebalance_threshold": -25.0,
        "hedging_cost_pct": 0.001,
        "simulation_duration": 60,  # minutes
        "dt_minutes": 1,
        "drift": 0.05,
        "volatility": 0.8,
        "position_side": "long"
    }

    # Override defaults with POSTed form data, if available.
    if request.method == "POST":
        try:
            baseline_params["entry_price"] = float(request.form.get("entry_price", baseline_params["entry_price"]))
            baseline_params["liquidation_price"] = float(
                request.form.get("liquidation_price", baseline_params["liquidation_price"]))
            baseline_params["position_size"] = float(
                request.form.get("position_size", baseline_params["position_size"]))
            baseline_params["collateral"] = float(request.form.get("collateral", baseline_params["collateral"]))
            baseline_params["rebalance_threshold"] = float(
                request.form.get("rebalance_threshold", baseline_params["rebalance_threshold"]))
            baseline_params["hedging_cost_pct"] = float(
                request.form.get("hedging_cost_pct", baseline_params["hedging_cost_pct"]))
            baseline_params["simulation_duration"] = float(
                request.form.get("simulation_duration", baseline_params["simulation_duration"]))
            baseline_params["dt_minutes"] = float(request.form.get("dt_minutes", baseline_params["dt_minutes"]))
            baseline_params["drift"] = float(request.form.get("drift", baseline_params["drift"]))
            baseline_params["volatility"] = float(request.form.get("volatility", baseline_params["volatility"]))
            baseline_params["position_side"] = request.form.get("position_side",
                                                                baseline_params["position_side"]).lower()
        except Exception as e:
            logger.error("Error parsing simulation parameters: %s", e)

    # Create tweaked parameters (for example, increasing collateral by 10%).
    tweaked_params = baseline_params.copy()
    tweaked_params["collateral"] = baseline_params["collateral"] * 1.10

    # Run the baseline simulation.
    baseline_simulator = PositionSimulator(
        entry_price=baseline_params["entry_price"],
        liquidation_price=baseline_params["liquidation_price"],
        position_size=baseline_params["position_size"],
        collateral=baseline_params["collateral"],
        rebalance_threshold=baseline_params["rebalance_threshold"],
        hedging_cost_pct=baseline_params["hedging_cost_pct"],
        position_side=baseline_params["position_side"]
    )
    baseline_results = baseline_simulator.run_simulation(
        simulation_duration=baseline_params["simulation_duration"],
        dt_minutes=baseline_params["dt_minutes"],
        drift=baseline_params["drift"],
        volatility=baseline_params["volatility"]
    )

    # Run the tweaked simulation.
    tweaked_simulator = PositionSimulator(
        entry_price=tweaked_params["entry_price"],
        liquidation_price=tweaked_params["liquidation_price"],
        position_size=tweaked_params["position_size"],
        collateral=tweaked_params["collateral"],
        rebalance_threshold=tweaked_params["rebalance_threshold"],
        hedging_cost_pct=tweaked_params["hedging_cost_pct"],
        position_side=tweaked_params["position_side"]
    )
    tweaked_results = tweaked_simulator.run_simulation(
        simulation_duration=tweaked_params["simulation_duration"],
        dt_minutes=tweaked_params["dt_minutes"],
        drift=tweaked_params["drift"],
        volatility=tweaked_params["volatility"]
    )

    # Prepare simulation chart data (e.g. step vs cumulative_profit).
    baseline_chart = [[entry["step"], entry["cumulative_profit"]] for entry in baseline_results["simulation_log"]]
    tweaked_chart = [[entry["step"], entry["cumulative_profit"]] for entry in tweaked_results["simulation_log"]]
    chart_data = {
        "simulated": baseline_chart,
        "real": tweaked_chart  # For demonstration, using tweaked simulation as the "historical" series.
    }

    # Connect to the database to get historical data.
    data_locker = DataLocker.get_instance()
    # Fetch historical positions from the database.
    historical_positions = data_locker.get_positions()

    # Fetch portfolio history (snapshots) and convert to chart series.
    portfolio_history = data_locker.get_portfolio_history()
    historical_chart = []
    for entry in portfolio_history:
        try:
            # Convert ISO timestamp to a UNIX timestamp in milliseconds.
            dt = datetime.fromisoformat(entry["snapshot_time"])
            timestamp = int(dt.timestamp() * 1000)
            historical_chart.append([timestamp, entry.get("total_value", 0.0)])
        except Exception as e:
            logger.error("Error processing portfolio snapshot: %s", e)
    # Use historical_chart as the "real" data series if available.
    if historical_chart:
        chart_data["real"] = historical_chart

    return render_template(
        "compare.html",
        chart_data=chart_data,
        baseline_compare=baseline_chart,
        tweaked_compare=tweaked_chart,
        simulated_positions=[],  # You can set these if needed.
        real_positions=historical_positions,
        timeframe=24  # Example timeframe; adjust as needed.
    )
