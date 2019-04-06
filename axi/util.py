import argparse
import subprocess
import sys

from .device import Device

def reset():
    d = Device()
    d.disable_motors()
    d.pen_up()

def draw(drawing, progress=True):
    # TODO: support drawing, list of paths, or single path
    d = Device()
    d.enable_motors()
    d.run_drawing(drawing, progress)
    d.disable_motors()

def calibrate(device, bounds):
    x1, y1, x2, y2 = bounds
    paths = [
        [(x1, y1), (x2, y1), (x2, y2)],
        [(x2, y2), (x1, y2), (x1, y1)],
    ]
    device.pen_up()
    stop = False
    while not stop:
        for path in paths:
            device.run_path(path)
            r = raw_input("Continue? [y/n/q] ").lower()
            if r == "q":
                sys.exit(0)
            if r != "y":
                stop = True
                break
            
class Cli(argparse.ArgumentParser):
    def parse_args(self, *args, **kwargs):
        self._parsed_args = argparse.ArgumentParser.parse_args(self, *args, **kwargs)
        return self._parsed_args

    def draw(self, drawing):
        if not hasattr(self, "_parsed_args"):
            self._parsed_args = self.parse_args()
        args = self._parsed_args

        drawing = drawing.rotate_and_scale_to_fit(args.width, args.height, step=90)
        drawing = drawing.sort_paths()

        if args.simplify >= 0:
            drawing = drawing.join_paths(args.simplify).simplify_paths(args.simplify)

        if args.output is not None:
            drawing.dump(args.output)

        if args.render is not None:
            image = drawing.render()
            image.write_to_png(args.render)
            if args.show:
                subprocess.check_call(["eog", args.render])

        if args.calibrate or args.draw:
            d = Device()
            d.enable_motors()

            if args.calibrate:
                calibrate(d, drawing.bounds)

            if args.draw:
                d.run_drawing(drawing, progress=not args.no_progress)

            d.disable_motors()

def cli():
    parser = Cli()
    parser.add_argument("-o", "--output", help="export to .axi file")
    parser.add_argument("-r", "--render", help="render as image to this path")
    parser.add_argument("-S", "--show", action="store_true", help="show rendered image with eog")
    parser.add_argument("-d", "--draw", action="store_true", help="output drawing on AxiDraw")
    parser.add_argument("-W", "--width", default=12., type=float, help="width of output image, in inches")
    parser.add_argument("-H", "--height", default=8.5, type=float, help="height of output image, in inches")
    parser.add_argument("-s", "--simplify", default=0.002, type=float, help="simplify and join paths with this threshold, negative to disable")
    parser.add_argument("-c", "--calibrate", action="store_true", help="outline bounding box to center canvas")
    parser.add_argument("-P", "--no-progress", action="store_true", help="disable showing progress")
    return parser
