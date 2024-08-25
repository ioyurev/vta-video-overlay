from pathlib import Path

import click
from loguru import logger as log
from PySide6 import QtWidgets
from tqdm import tqdm

from vta_video_overlay.__main__ import set_appdata_folder
from vta_video_overlay.data_collections import ProcessProgress, ProcessResult
from vta_video_overlay.tda_file import Data
from vta_video_overlay.worker import Worker

log.configure(handlers=[dict(sink=lambda msg: tqdm.write(msg, end=""), colorize=True)])


@click.command()
@click.argument("tda_file", type=click.Path(exists=True))
@click.argument("video_file", type=click.Path(exists=True))
@click.option(
    "--calibration/--no-calibration", "-C /", default=True, help="Enable calibration"
)
def main(tda_file: str, video_file: str, calibration=False):
    output_path = Path(video_file)
    output_path = output_path.with_name(
        Path(output_path).stem + "_overlay"
    ).with_suffix(".mp4")
    if output_path.exists():
        raise FileExistsError(f"File {output_path} already exists")
    App().run(Path(tda_file), Path(video_file), output_path, calibration)


class App(QtWidgets.QApplication):
    def run(
        self, tda_file: Path, video_file: Path, output_file: Path, calibration: int
    ):
        self.pbar_stage = tqdm(
            total=100, desc="Stage 1/3 progress", unit="%", leave=False
        )
        set_appdata_folder()
        data = Data(tda_file)
        self.worker = Worker(
            video_file_path_input=video_file,
            video_file_path_output=output_file,
            data=data,
        )
        self.worker.stage_progress.connect(self.at_stage_progress)
        self.worker.stage_finished.connect(self.at_stage_finish)
        self.worker.work_finished.connect(self.at_work_finish)
        self.worker.start()
        self.exec()

    def at_work_finish(self, tpl: ProcessResult):
        self.pbar_stage.close()
        self.worker.quit()
        del self.worker
        if not tpl.is_success:
            print(tpl.traceback_msg)
        exit()

    def at_stage_progress(self, tpl: ProcessProgress):
        self.pbar_stage.update(tpl.value - self.pbar_stage.n)

    def at_stage_finish(self, tpl):
        new_total, stage_str, unit = tpl
        self.pbar_stage.close()
        self.pbar_stage = tqdm(
            total=new_total, desc=f"Stage {stage_str} progress", unit=unit, leave=False
        )


if __name__ == "__main__":
    main()
