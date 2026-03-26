from src.simulation.engines.cone import PlotCone
from src.simulation.engines.mcu import PlotMCU
from src.simulation.engines.membrane import PlotMembrane
from src.core.ml.ml import PlotML
from src.core.ml.sim_to_real import PlotSimToReal

SIMULATIONS = [
    # (sim_key, label, PlotClass, in_presentation)
    ("mcu",          "MCU 2D",                      PlotMCU,          True),
    ("cone",         "Cône 3D",                     PlotCone,         True),
    ("membrane",     "Membrane 3D",                 PlotMembrane,     True),
    ("ml",           "Machine Learning",            PlotML,           True),
    ("sim_to_real",  "Sim-to-Real",                 PlotSimToReal,    True),
]
