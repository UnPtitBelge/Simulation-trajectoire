from src.simulations.cone import PlotCone
from src.simulations.mcu import PlotMCU
from src.simulations.membrane import PlotMembrane
from src.simulations.ml import PlotML
from src.simulations.sim_to_real import PlotSimToReal

SIMULATIONS = [
    # (sim_key, label, PlotClass, in_presentation)
    ("mcu",          "MCU 2D",                      PlotMCU,          True),
    ("cone",         "Cône 3D",                     PlotCone,         True),
    ("membrane",     "Membrane 3D",                 PlotMembrane,     True),
    ("ml",           "Machine Learning",            PlotML,           True),
    ("sim_to_real",  "Sim-to-Real",                 PlotSimToReal,    True),
]
