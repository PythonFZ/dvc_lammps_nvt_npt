import pathlib

from src import (
    EinsteinDiffusionNode,
    LammpsSimulator,
    MDSuiteDB,
    RadialDistributionFunctionNode,
)

if __name__ == "__main__":

    npt_simulator = LammpsSimulator(
        template_file=pathlib.Path("templates", "npt.lmp"),
        input_trajectory="NaCl.xyz",
        name="NPT",
        temperature=-1,
    )
    npt_simulator.write_graph()

    nvt_simulator = LammpsSimulator(
        template_file=pathlib.Path("templates", "nvt.lmp"),
        input_simulation=npt_simulator,
        name="NVT",
        temperature=-1,
    )
    nvt_simulator.write_graph()

    MDSuiteDB(simulator=nvt_simulator).write_graph()
    EinsteinDiffusionNode().write_graph()
    RadialDistributionFunctionNode().write_graph()
