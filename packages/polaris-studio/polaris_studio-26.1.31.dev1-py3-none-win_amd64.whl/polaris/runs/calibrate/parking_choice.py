# Copyright (c) 2026, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import math
from pathlib import Path

import pandas as pd
from polaris.runs.calibrate.utils import calculate_normalized_rmse, log_data
from polaris.runs.convergence.config.convergence_config import ConvergenceConfig
from polaris.runs.convergence.convergence_iteration import ConvergenceIteration
from polaris.runs.scenario_file import get_scenario_value, load_json, write_json
from polaris.utils.database.db_utils import attach_to_conn, read_and_close
from polaris.utils.logging_utils import function_logging
from polaris.utils.math_utils import clamp


@function_logging("Calibrating parking choice")
def calibrate(config: ConvergenceConfig, current_iteration: ConvergenceIteration):
    cconfig = config.calibration

    sc_json = load_json(current_iteration.scenario_file)
    if not bool(get_scenario_value(sc_json, "simulate_parking", default=False)):
        return -1

    model_file = Path(get_scenario_value(sc_json, "parking_choice_model_file"))
    if not (config.data_dir / model_file).exists():
        raise FileNotFoundError("No parking choice file to calibrate")

    target = load_target(cconfig.target_csv_dir / "parking_choice_targets.csv")
    simulated = load_simulated(current_iteration.files.demand_db, current_iteration.files.supply_db)

    top_level_key = "Parking_Choice_Model"
    output_dict = load_json(current_iteration.output_dir / "model_files" / model_file.name)[top_level_key]

    # Get the current value - if it doesn't exist we will create it and give it a starting value of 1.0
    v = float(output_dict.get(OS_CONST_VAR, 0.0))
    delta = cconfig.step_size * math.log(target.get("onstreet_share") / simulated.get("onstreet_share"))
    new_v = clamp(v + delta, -5, 5)
    output_dict[OS_CONST_VAR] = new_v

    data = []
    data.append([OS_CONST_VAR, v, new_v, target.get("onstreet_share"), simulated.get("onstreet_share")])

    log_data(data, ["variable", "asc", "new_asc", "target", "modelled"])

    write_json(config.data_dir / model_file, {top_level_key: output_dict})
    return calculate_normalized_rmse(simulated, target)


## File example
# garage_share  onstreet_share
# 0.12          0.88
def load_target(target_file):
    return pd.read_csv(target_file).set_index("var")["target"].to_dict()


def load_simulated(demand_database, supply_database):
    with read_and_close(demand_database) as conn:
        attach_to_conn(conn, {"a": supply_database})
        sql = """SELECT garage_choices * 1.0 / (onstreet_choices + garage_choices) as garage_share,
                        onstreet_choices * 1.0 / (onstreet_choices + garage_choices) as onstreet_share
                FROM (SELECT SUM(CASE WHEN p.type IN ('garage', 'airport') THEN 1 ELSE 0 END) AS garage_choices,
                        SUM(CASE WHEN p.type NOT IN ('garage', 'airport') THEN 1 ELSE 0 END) AS onstreet_choices
                        FROM Parking_Records pr JOIN a.Parking p ON pr.Parking_ID = p.parking
                        JOIN a.zone z ON p.zone = z.zone WHERE Parking_ID <> -1 AND z.area_type < 4);"""
        df = pd.read_sql(sql, conn)
        simulated = {"garage_share": df.garage_share.values[0], "onstreet_share": df.onstreet_share.values[0]}
        return simulated


OS_CONST_VAR = "Const_OS"
