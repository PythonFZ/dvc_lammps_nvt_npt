import matplotlib.pyplot as plt
import mdsuite as mds
import pandas as pd
from zntrack import Node, dvc, zn

from . import LammpsSimulator


class MDSuiteDB(Node):
    simulator: LammpsSimulator = zn.deps()
    project_path = dvc.outs("mdsuite")

    def __init__(self, simulator: LammpsSimulator = None, **kwargs):
        super().__init__(**kwargs)
        self.simulator = simulator

    def run(self):
        project = mds.Project(self.project_path)
        project.add_experiment(
            name="NaCl_example_data",
            timestep=self.simulator.parameters.timestep,
            temperature=self.simulator.parameters.temperature,
            units="metal",
            simulation_data=self.simulator.dump_file,
        )


class EinsteinDiffusionNode(Node):
    project: MDSuiteDB = zn.deps(MDSuiteDB)

    analysis = zn.metrics()
    data_range = zn.params(100)
    correlation_time = zn.params(1)

    def run(self):
        project = mds.Project(self.project.project_path)

        data = project.run.EinsteinDiffusionCoefficients(
            plot=False,
            data_range=self.data_range,
            correlation_time=self.correlation_time,
        )

        self.analysis = {
            "[Na] diffusion_coefficient * 10^9": data["NaCl_example_data"]["Na"][
                "diffusion_coefficient"
            ]
            * 10 ** 9,
            "[Na] uncertainty * 10^9": data["NaCl_example_data"]["Na"]["uncertainty"]
            * 10 ** 9,
            "[Cl] diffusion_coefficient * 10^9": data["NaCl_example_data"]["Cl"][
                "diffusion_coefficient"
            ]
            * 10 ** 9,
            "[Cl] uncertainty * 10^9": data["NaCl_example_data"]["Cl"]["uncertainty"]
            * 10 ** 9,
        }


class RadialDistributionFunctionNode(Node):
    project: MDSuiteDB = zn.deps(MDSuiteDB)
    plot = dvc.outs_no_cache("rdf.png")
    rdf: pd.DataFrame = zn.plots(x="r",  x_label="distance r", y_label="g(r)")

    def run(self):
        project = mds.Project(self.project.project_path)
        data = project.run.RadialDistributionFunction(
            plot=False,
        )

        fig, ax = plt.subplots()
        ax.plot(
            data["NaCl_example_data"]["Na_Cl"]["x"],
            data["NaCl_example_data"]["Na_Cl"]["y"],
        )
        fig.savefig(self.plot)

        self.rdf = pd.DataFrame({"g(r)": data["NaCl_example_data"]["Na_Cl"]["y"]})
        self.rdf.index = data["NaCl_example_data"]["Na_Cl"]["x"]
        self.rdf.index.name = "r"
