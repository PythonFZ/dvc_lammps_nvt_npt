from __future__ import annotations

import dataclasses
import pathlib
import subprocess

import jinja2
from zntrack import Node, dvc, zn


@dataclasses.dataclass
class Params:
    name: str
    timestep: float = 0.001
    dump_interval: int = 1000
    temperature: float = 1100
    thermo_intervall: int = 1000
    steps: int = 200000
    barostat_factor: int = 500
    pressure: float = 1.0
    input_nstep: int = 0

    @property
    def input_file(self):
        return pathlib.Path(f"{self.name}.in")

    @property
    def dump_file(self):
        return f"{self.name}.lammpstraj"

    @property
    def log_file(self):
        return f"{self.name}.log"


class LammpsSimulator(Node):
    input_trajectory = dvc.deps()
    input_simulation: LammpsSimulator = dvc.deps()
    template_file = dvc.deps()
    parameters = zn.Method()

    input_script: pathlib.Path = dvc.outs_no_cache()
    dump_file = dvc.outs()
    log_file = dvc.outs()

    def __init__(
        self,
        template_file=None,
        temperature=None,
        input_trajectory=None,
        input_simulation: LammpsSimulator = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if not self.is_loaded:
            self.parameters = Params(self.node_name)
            self.template_file = pathlib.Path(template_file)
            self.input_simulation = input_simulation
            self.input_trajectory = input_trajectory

            # update temperature
            self.parameters.temperature = temperature

            # Let DVC know which files to track
            self.input_script = self.parameters.input_file
            self.dump_file = self.parameters.dump_file
            self.log_file = self.parameters.log_file

    def render_file(self):
        template = jinja2.Template(self.template_file.read_text())
        if self.input_trajectory is not None:
            input_trajectory = self.input_trajectory
        else:
            input_trajectory = self.input_simulation.dump_file
            self.parameters.input_nstep = self.input_simulation.parameters.steps

        self.input_script.write_text(
            template.render(
                **dataclasses.asdict(self.parameters),
                dump_file=self.parameters.dump_file,
                log_file=self.parameters.log_file,
                input_trajectory=input_trajectory,
            )
        )

    def run(self):
        self.render_file()
        subprocess.check_call([f"lmp_stable -in {self.input_script}"], shell=True)
