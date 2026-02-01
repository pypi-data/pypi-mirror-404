import matplotlib as mpl
import matplotlib.pyplot as plt


class Plot:
    def __init__(self, figname: str, max_cols: int, max_rows: int, *args, **kwargs) -> None:
        self.figname = figname
        self.cols = max_cols
        self.rows = max_rows
        self.index = 1
        self.ax_names = {}

        self.fig = plt.figure(figname, *args, **kwargs)

    def locate_plot(self) -> tuple[int, int]:
        col = self.index % self.cols
        row = int((self.index - 1) / self.cols)
        return col, row + 1

    def add_plot(self, name: str, **kwargs) -> mpl.axes.Axes:
        ax = self.fig.add_subplot(self.rows, self.cols, self.index, **kwargs)
        self.ax_names[name] = ax

        self.figname = f"{self.figname}_{name}-{self.index}"
        self.index += 1

    def __call__(self, name: str, **add_kwargs) -> mpl.axes.Axes:
        if name not in list(self.ax_names.keys()):
            self.add_plot(name, **add_kwargs)
        return self.ax_names[name]

    def save(self, path: str, **kwargs) -> None:
        plt.tight_layout()
        plt.savefig(f"{path}/{self.figname}.pdf", **kwargs)

    def show(self):
        plt.tight_layout()
        plt.show()
