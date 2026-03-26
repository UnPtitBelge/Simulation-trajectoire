from src.model.simulation.cone import PlotCone
from src.model.simulation.mcu import PlotMCU
from src.model.simulation.membrane import PlotMembrane
from src.model.ml.tracking import PlotML
from src.model.ml.sim_to_real import PlotSimToReal

SIMULATIONS = [
    # (sim_key, label, PlotClass, in_normal)
    ("mcu",          "MCU 2D",                      PlotMCU,          True),
    ("cone",         "Cône 3D",                     PlotCone,         True),
    ("membrane",     "Membrane 3D",                 PlotMembrane,     True),
    ("ml",           "Machine Learning",            PlotML,           True),
    ("sim_to_real",  "Sim-to-Real",                 PlotSimToReal,    True),
]
