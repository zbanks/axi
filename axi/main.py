import axi
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

draw_parser = subparsers.add_parser("draw", help="draw an .axi file")
draw_parser.add_argument("axi", help=".axi file to draw")

render_parser = subparsers.add_parser("render", help="render an .axi file to an image")
render_parser.add_argument("axi", help=".axi file to render")
render_parser.add_argument("-o", "--output", default="out.png", help="output file name")

move_parser = subparsers.add_parser("move", help="move head (in inches)")
move_parser.add_argument("dx", type=float, help="relative X movement, in inches")
move_parser.add_argument("dy", type=float, help="relative Y movement, in inches")

move_parser = subparsers.add_parser("goto", help="goto to a given coordinate (in inches)")
move_parser.add_argument("x", type=float, help="X coordinate, in inches")
move_parser.add_argument("y", type=float, help="Y coordinate, in inches")

subparsers.add_parser("zero", help="set current position to (0, 0)")
subparsers.add_parser("home", help="move to (0, 0)")
subparsers.add_parser("up", help="move pen to up position")
subparsers.add_parser("down", help="move pen to down position")
subparsers.add_parser("on", help="turn motors on")
subparsers.add_parser("off", help="turn motors off")

def main():
    args = parser.parse_args()
    d = None
    #if args.axi is not None:

    if args.command == 'render':
        d = axi.Drawing.load(args.axi)
        d = d.rotate_and_scale_to_fit(12, 8.5, step=90)
        im = d.render()
        im.write_to_png(args.output)
        return
    device = axi.Device()
    if args.command == 'zero':
        device.zero_position()
    elif args.command == 'home':
        device.home()
    elif args.command == 'up':
        device.pen_up()
    elif args.command == 'down':
        device.pen_down()
    elif args.command == 'on':
        device.enable_motors()
    elif args.command == 'off':
        device.disable_motors()
    elif args.command == 'move':
        device.move(args.dx, args.dy)
    elif args.command == 'goto':
        device.goto(args.x, args.y)
    elif args.command == 'draw':
        d = axi.Drawing.load(args.axi)
        axi.draw(d)
    else:
        parser.error("command required")

if __name__ == '__main__':
    main()
