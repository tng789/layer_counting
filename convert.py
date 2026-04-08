from pathlib import Path

def main():
    source_dir = Path("d:\\workspace\\pillar_yolo")
    target_dir = Path("d:\\workspace\\pile_yolo")
    if not target_dir.exists():
        target_dir.mkdir()

    for yolo_file in source_dir.glob("P*.txt"):

        target_file = target_dir / yolo_file.name
        # print(f"处理 {yolo_file}:")
        
        zeros = []
        ones = []
        twos = []

        zero = one = two = False

        with open(yolo_file,"rt") as f:
            for line in f:
                yolo = [float(d) for d in line.split()]
                if yolo[0] == 0:
                    zeros.append(line)
                    zero = True
                elif yolo[0] == 1:
                    ones.append(line)
                    one = True
                elif yolo[0] == 2:
                    twos.append(line)
                    two = True
                else:
                    continue

        if zero and not one and not two:   # 有零，无1无2, 方形实心
            with open(target_file, "wt") as f:
                for line in zeros:
                    f.write(line)
        elif zero and one and not two:     # 有零，有1无2， 方形空心
            with open(target_file, "wt") as f:
                for line  in zeros:
                    c,x,y,w,h = line.split()
                    new_line = f"{1} {x} {y} {w} {h}\n"
                    f.write(new_line)
        elif not zero and one and two:      # 无零，有1有2，圆形空心
            with open(target_file, "wt") as f:
                for line  in twos:
                    # c,x,y,w,h = line.split()
                    # new_line = f"{2} {x} {y} {w} {h}\n"
                    # f.write(new_line)
                    f.write(line)
        elif not zero and one and not two:   # 无零，有1无2，没有管桩
            with open(target_file, "wt") as f:
                pass
        elif zero and one and two:   # 有零，有1有2
            print(f"有疑问，待查  {yolo_file}")
            with open(target_file, "wt") as f:
                for line  in zeros:
                    c,x,y,w,h = line.split()
                    new_line = f"{1} {x} {y} {w} {h}\n"
                    f.write(new_line)
                for line  in twos:
                    # c,x,y,w,h = line.split()
                    # new_line = f"{2} {x} {y} {w} {h}\n"
                    # f.write(new_line)
                    f.write(line)
        else:
            print(f"无法处理 {yolo_file}")
            continue

if __name__ == "__main__":
    main()  